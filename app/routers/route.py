from typing import Literal

import networkx as nx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.routing import MODES, get_recommended_routes, shortest_cool_route


router = APIRouter(tags=["routes"])
Mode = Literal["노약자", "반려동물", "일반"]


class RouteRequest(BaseModel):
    mode: Mode = Field(..., description="이동 모드: 노약자 | 반려동물 | 일반")
    start: tuple[float, float] = Field(..., description="출발지 [lat, lng] — 예: [37.3219, 127.0972]")
    end: tuple[float, float] = Field(..., description="목적지 [lat, lng] — 예: [37.3247, 127.1245]")


class RouteResponse(BaseModel):
    path: dict = Field(..., description="GeoJSON FeatureCollection — 경로 LineString 목록")
    heat_score_avg: float = Field(..., description="경로 평균 Heat Score (낮을수록 시원함)")
    distance_m: float = Field(..., description="총 거리 (미터)")
    shelters: list[dict] = Field(..., description="경로상 무더위쉼터 목록 (노약자 모드)")
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


@router.post(
    "/route",
    summary="시원한 경로 계산",
    description="출발지·목적지·모드를 받아 Heat Score 기반 최적 경로를 반환합니다. 노약자 모드는 무더위쉼터를 경유하고, 반려동물 모드는 지면 더위 지수가 높은 구간에 패널티를 적용합니다.",
    response_model=RouteResponse,
)
def create_route(request: RouteRequest) -> dict:
    try:
        return shortest_cool_route(
            mode=request.mode,
            start=request.start,
            end=request.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except nx.NetworkXNoPath as exc:
        raise HTTPException(status_code=404, detail="No route found for the requested coordinates") from exc
    except nx.NodeNotFound as exc:
        raise HTTPException(status_code=404, detail="Nearest graph node was not found") from exc


@router.get(
    "/routes",
    summary="추천 경로 13개 목록 조회",
    description="수지구 내 추천 경로 13개를 반환합니다. mode 파라미터로 필터링 가능합니다 (노약자 5개 / 반려동물 5개 / 일반 3개).",
    response_model=list[RecommendedRouteResponse],
)
def list_routes(mode: Mode | None = Query(default=None, description="모드 필터 — 생략 시 전체 반환")) -> list[dict]:
    if mode is not None and mode not in MODES:
        return []
    return get_recommended_routes(mode=mode)
