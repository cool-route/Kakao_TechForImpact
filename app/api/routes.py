import networkx as nx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import MODES
from app.schemas.routes import Mode, NearestRouteResponse, RecommendedRouteResponse, RouteRequest, RouteResponse, ShelterResponse
from app.services.route_service import (
    find_nearest_route,
    get_all_shelters,
    get_recommended_routes,
    shortest_cool_route,
    select_top_k_routes,
)


router = APIRouter(tags=["routes"])


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
    "/shelters",
    summary="무더위쉼터 목록 조회",
    description="수지구 내 무더위쉼터 전체 목록을 반환합니다. 지도 마커 표시에 사용합니다.",
    response_model=list[ShelterResponse],
)
def list_shelters() -> list[dict]:
    return get_all_shelters()


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


@router.get(
    "/nearest-route",
    summary="사용자 위치 기반 가장 가까운 경로 추천",
    description="사용자 위치(위도·경도)를 받아 모든 추천 경로의 엣지 기준으로 가장 가까운 경로 1개를 반환합니다.",
    response_model=NearestRouteResponse,
)
def get_nearest_route(
    lat: float = Query(..., description="사용자 위도 — 예: 37.3219"),
    lng: float = Query(..., description="사용자 경도 — 예: 127.0972"),
) -> dict:
    try:
        return find_nearest_route(lat=lat, lng=lng)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc



@router.get(
    "/routes/top",
    summary="Top-k 추천 경로",
    description="선호 태그(선택)를 기반으로 상위 k개의 추천 경로(기본 k=3)를 반환합니다.",
    response_model=list[RecommendedRouteResponse],
)
def list_top_routes(tags: list[str] | None = Query(default=None, description="선호 태그 목록"), mode: Mode | None = Query(default=None, description="모드 필터 — 생략 시 전체 반환")) -> list[dict]:
    if mode is not None and mode not in MODES:
        return []
    return select_top_k_routes(preferred_tags=tags, k=3, mode=mode)
