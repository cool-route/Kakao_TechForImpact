from contextlib import asynccontextmanager
from pathlib import Path 

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.db import init_db
from app.api.routes import router as route_router

import os
import json
import tempfile
from pydantic import BaseModel, Field
from typing import List

try:
    import whisper
except ImportError:  # pragma: no cover - optional dependency for speech-to-text only
    whisper = None

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency for local preset proxy only
    httpx = None

try:
    import multipart  # type: ignore
except ImportError:  # pragma: no cover - optional dependency for speech upload only
    multipart = None

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
PRESET_CATALOG_PATH = BASE_DIR / "data" / "preset_catalog.json"

_preset_catalog_cache: dict | None = None


def _load_preset_catalog() -> dict:
    global _preset_catalog_cache
    if _preset_catalog_cache is not None:
        return _preset_catalog_cache

    with PRESET_CATALOG_PATH.open(encoding="utf-8") as f:
        _preset_catalog_cache = json.load(f)
    return _preset_catalog_cache


def _build_local_preset_response(text: str) -> dict:
    catalog = _load_preset_catalog()
    label_to_id: dict[str, str] = {}
    alias_to_id: dict[str, str] = {}
    category_to_ids: dict[str, list[str]] = {}

    for category_name, items in catalog.get("categories", {}).items():
        category_to_ids.setdefault(category_name, [])
        for item in items:
            preset_id = item["id"]
            label_to_id[item["label"]] = preset_id
            for alias in item.get("aliases", []):
                alias_to_id[alias] = preset_id
            category_to_ids[category_name].append(preset_id)

    lowered = text.replace(" ", "")
    base_presets: list[str] = []
    sub_presets: list[str] = []

    def add_base(*preset_ids: str) -> None:
        for preset_id in preset_ids:
            if preset_id and preset_id not in base_presets:
                base_presets.append(preset_id)

    def add_sub(*preset_ids: str) -> None:
        for preset_id in preset_ids:
            if preset_id and preset_id not in sub_presets:
                sub_presets.append(preset_id)

    keyword_rules = [
        ("어르신", lambda: add_base("with_elder")),
        ("노약자", lambda: add_base("with_elder")),
        ("강아지", lambda: add_base("with_pet")),
        ("반려동물", lambda: add_base("with_pet")),
        ("유모차", lambda: add_base("with_stroller")),
        ("휠체어", lambda: add_base("mobility_support")),
        ("혼자", lambda: add_base("alone")),
        ("시원", lambda: add_sub("cool_path", "low_tmrt")),
        ("그늘", lambda: add_sub("shady_path")),
        ("쉼터", lambda: add_sub("shelter_route", "shelter_rich")),
        ("평지", lambda: add_sub("flat_path")),
        ("조용", lambda: add_sub("quiet_path")),
        ("녹지", lambda: add_sub("green_path")),
        ("공원", lambda: add_sub("park_route")),
    ]

    for keyword, handler in keyword_rules:
        if keyword in lowered:
            handler()

    duration_rules = [
        ("10분", "walk_10m"),
        ("15분", "walk_15m"),
        ("30분", "walk_30m"),
        ("1시간", "walk_60m"),
        ("2시간", "walk_120m_plus"),
    ]
    for keyword, preset_id in duration_rules:
        if keyword in lowered:
            add_base(preset_id)
            break
    else:
        add_base("walk_30m")

    # Guarantee one place tag even in the local mock.
    place_candidates = category_to_ids.get("place", [])
    if place_candidates:
        chosen_place = place_candidates[sum(ord(ch) for ch in lowered) % len(place_candidates)]
        add_sub(chosen_place)

    # Keep results within the catalog limits.
    return {
        "base_presets": base_presets[:3],
        "sub_presets": sub_presets[:2],
    }

class ConfirmedTextRequest(BaseModel):
    text: str

class PresetResponse(BaseModel):
    base_presets: List[str] = Field(default_factory=list)
    sub_presets: List[str] = Field(default_factory=list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Cool Route API",
    description="Sujigu cool-route recommendation backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(route_router)
model = whisper.load_model("base") if whisper is not None else None

if multipart is not None:

    @app.post("/speech")
    async def speech_to_text(audio: UploadFile = File(...)):
        if model is None:
            raise HTTPException(status_code=503, detail="Whisper 모델이 설치되어 있지 않습니다.")

        # 1. 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_file_path = temp_audio.name
            content = await audio.read()
            temp_audio.write(content)

        try:
            # 2. 로컬 Whisper 모델로 추론
            result = model.transcribe(temp_file_path, language="ko")
            return {"text": result["text"]}
        except Exception as e:
            return {"error": str(e)}
        finally:
            # 3. 임시 파일 삭제
            os.remove(temp_file_path)

# 로컬 임시 서버
@app.post("/localServer")
async def local_server(request: dict):
    text = str(request.get("text") or "")
    if not text:
        return {
            "base_presets": ["with_elder", "walk_30m"],
            "sub_presets": ["shelter_route", "flat_path"],
        }

    return _build_local_preset_response(text)

# 해당 함수는 실제 백서버 주소를 기입한 후에 /api/routes.py에 옮길 예정
@app.post("/preset", response_model=PresetResponse)
async def extract_presets(request: ConfirmedTextRequest):
    user_text = request.text

    if not user_text:
        raise HTTPException(status_code=400, detail="텍스트가 전달되지 않았습니다.")

    if httpx is None:
        raise HTTPException(status_code=503, detail="httpx가 설치되어 있지 않습니다.")

    # PRESET_BACKEND_URL = "실제 백서버 주소"
    PRESET_BACKEND_URL = "http://127.0.0.1:8000/localServer"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PRESET_BACKEND_URL,
                json={"text": user_text},
                timeout=15.0
            )
            response.raise_for_status() 
            preset_data = response.json()

        base_list = preset_data.get("base_presets") or []
        sub_list = preset_data.get("sub_presets") or []

        # 프론트엔드의 화면 제약을 위해 만약 강제로 3개까지만 자르고 싶다면 아래처럼 슬라이싱할 수 있습니다.
        # sub_list = sub_list[:3] 

        print(f"[preset] text:", request.text)
        print(f"[preset] base_presets: {base_list} / sub_presets: {sub_list}\n")

        return PresetResponse(
            base_presets=base_list,
            sub_presets=sub_list
        )
        
    except httpx.RequestError as e:
        print(f"PRESET 서버 통신 에러: {e}")
        raise HTTPException(status_code=502, detail="AI 백엔드 서버와 통신할 수 없습니다.")
    except Exception as e:
        print(f"내부 에러: {e}")
        raise HTTPException(status_code=500, detail="데이터를 처리하는 중 오류가 발생했습니다.")
    
    # 더미
    # dummy_base_presets = ["시민한길", "30분", "반려동물"]
    # dummy_sub_presets = ["그늘", "살리라산", "청지"]
    
    # return PresetResponse(
    #     base_presets=dummy_base_presets,
    #     sub_presets=dummy_sub_presets
    # )

app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
# app.mount("/", StaticFiles(directory="kakaomap_test", html=True), name="testingFrontend")
