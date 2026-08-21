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
from pydantic import BaseModel
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

class PresetRequest(BaseModel):
    text: str

class PresetResponse(BaseModel):
    base_presets: List[str]
    sub_presets: List[str]

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

@app.post("/preset", response_model=PresetResponse)
async def extract_presets(request: PresetRequest):
    user_text = request.text

    if not user_text:
        raise HTTPException(status_code=400, detail="텍스트가 전달되지 않았습니다.")

    # 실제 AI 처리를 담당하는 분리된 백엔드 서버의 URL (실제 주소로 변경하세요)
    PRESET_BACKEND_URL = "http://localhost:8000/preset"

    try:
        # 외부 AI 서버로 프론트에서 받은 텍스트(user_text)를 전송하고 결과를 기다립니다.
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PRESET_BACKEND_URL,
                json={"text": user_text},
                timeout=15.0 # 통신 대기 시간 15초 설정
            )
            response.raise_for_status() # 200번대 정상 응답이 아니면 에러 발생
            
            # 외부 AI 서버에서 보내준 JSON 데이터 받기
            ai_data = response.json()

        # 받은 데이터(ai_data)에서 태그 배열을 꺼내 프론트엔드로 전달
        return PresetResponse(
            base_presets=ai_data.get("base_presets", []),
            sub_presets=ai_data.get("sub_presets", [])
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
