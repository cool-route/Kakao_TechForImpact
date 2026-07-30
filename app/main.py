from contextlib import asynccontextmanager
from pathlib import Path 
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.db import init_db
from app.api.routes import router as route_router

# 1. main.py 위치를 기준으로 frontend/dist의 절대 경로를 동적으로 계산합니다.
# Path(__file__).resolve()는 main.py의 절대 경로
# .parent는 app 폴더
# .parent.parent는 최상위 Kakao_TechForImpact 폴더
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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(route_router)

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
# app.mount("/", StaticFiles(directory="kakaomap_test", html=True), name="testingFrontend")
