from contextlib import asynccontextmanager
from pathlib import Path 

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.db import init_db
from app.api.routes import router as route_router

import os
import json
import whisper
import tempfile
import httpx
from pydantic import BaseModel, Field
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

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
model = whisper.load_model("base")
@app.post("/speech")
async def speech_to_text(audio: UploadFile = File(...)):
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
    return {
        "base_presets": ["base1", "base2", "base3"],
        "sub_presets": ["sub1", "sub2", "sub3"]
    }

# 해당 함수는 실제 백서버 주소를 기입한 후에 /api/routes.py에 옮길 예정
@app.post("/preset", response_model=PresetResponse)
async def extract_presets(request: ConfirmedTextRequest):
    user_text = request.text

    if not user_text:
        raise HTTPException(status_code=400, detail="텍스트가 전달되지 않았습니다.")

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
