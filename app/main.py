from contextlib import asynccontextmanager
from pathlib import Path 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.db import init_db
from app.api.routes import router as route_router

import os
from fastapi import UploadFile, File
import whisper
import tempfile

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

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

# BASE_DIR = Path(__file__).resolve().parents[1]
# FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
# app.mount("/", StaticFiles(directory="kakaomap_test", html=True), name="testingFrontend")
