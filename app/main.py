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
    
    # TODO: 추후 여기에 GPT/LLM 연동을 통한 실제 태그 추출 로직 작성
    # 현재는 프론트엔드 연동 테스트를 위해 더미 데이터를 반환합니다.
    dummy_base_presets = ["시민한길", "30분", "반려동물"]
    dummy_sub_presets = ["그늘", "살리라산", "청지"]
    
    return PresetResponse(
        base_presets=dummy_base_presets,
        sub_presets=dummy_sub_presets
    )

app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
# app.mount("/", StaticFiles(directory="kakaomap_test", html=True), name="testingFrontend")
