import networkx as nx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import MODES
from app.schemas.routes import Mode, RecommendedRouteResponse, RouteRequest, RouteResponse
from app.services.route_service import get_recommended_routes, shortest_cool_route


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
    "/routes",
    summary="추천 경로 13개 목록 조회",
    description="수지구 내 추천 경로 13개를 반환합니다. mode 파라미터로 필터링 가능합니다 (노약자 5개 / 반려동물 5개 / 일반 3개).",
    response_model=list[RecommendedRouteResponse],
)
def list_routes(mode: Mode | None = Query(default=None, description="모드 필터 — 생략 시 전체 반환")) -> list[dict]:
    if mode is not None and mode not in MODES:
        return []
    return get_recommended_routes(mode=mode)
