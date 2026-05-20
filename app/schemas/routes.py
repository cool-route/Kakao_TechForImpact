from typing import Literal

from pydantic import BaseModel, Field


Mode = Literal["노약자"]


class RouteRequest(BaseModel):
    mode: Mode = Field(..., description="이동 모드: 노약자")
    start: tuple[float, float] = Field(..., description="출발지 [lat, lng] — 예: [37.3219, 127.0972]")
    end: tuple[float, float] = Field(..., description="목적지 [lat, lng] — 예: [37.3247, 127.1245]")


class RouteResponse(BaseModel):
    path: dict = Field(..., description="GeoJSON FeatureCollection — 경로 LineString 목록")
    heat_score_avg: float = Field(..., description="경로 평균 Heat Score (낮을수록 시원함)")
    distance_m: float = Field(..., description="총 거리 (미터)")
    shelters: list[dict] = Field(..., description="경로상 무더위쉼터 목록")
    is_dummy: bool = Field(..., description="더미 그래프 사용 여부 — 실데이터 연동 시 false")


class RecommendedRouteResponse(BaseModel):
    id: int = Field(..., description="추천 경로 ID")
    name: str = Field(..., description="추천 경로 이름")
    mode: Mode = Field(..., description="추천 경로 모드")
    heat_score_avg: float = Field(..., description="경로 평균 Heat Score (낮을수록 시원함)")
    distance_m: float = Field(..., description="총 거리 (미터)")
    geojson: dict = Field(..., description="GeoJSON FeatureCollection — 추천 경로")
    shelters: list[dict] = Field(..., description="경로상 무더위쉼터 목록")
    is_dummy: bool = Field(..., description="더미 그래프 사용 여부 — 실데이터 연동 시 false")
