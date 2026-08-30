import httpx
import networkx as nx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import MODES
from app.schemas.routes import Mode, NearestRouteResponse, RecommendedRouteResponse, RouteRequest, RouteResponse, ShelterResponse
from app.schemas.preset_extraction import PresetExtractionRequest, PresetExtractionResult
from app.services.agent_client import call_preset_agent
from app.services.preset_parser import extract_preset_ids, classify_presets
from app.services.route_service import (
    find_nearest_route,
    get_all_shelters,
    get_recommended_routes,
    shortest_cool_route,
    select_top_k_routes,
)

router = APIRouter(tags=["routes"])
_last_extracted_presets = []
_last_recommended_routes = []

# 출발 -> 목적 일직선 (사용 지양)
@router.post(
    "/route",
    summary="시원한 경로 계산",
    description="출발지·목적지·모드를 받아 Heat Score 기반 최적 경로를 반환합니다. 노약자 모드는 무더위쉼터를 경유하고, 반려동물 모드는 지면 더위 지수가 높은 구간에 패널티를 적용합니다.",
    response_model=RouteResponse,
)
def create_route(request: RouteRequest) -> dict:
    print(f"[route] 출발: {request.start} -> 도착: {request.end}\n모드: {request.mode}\n", flush=True)
    try:
        route_result = shortest_cool_route(
            mode=request.mode,
            start=request.start,
            end=request.end,
        )
        print(f"[route] 거리: {route_result.get('distance_m')}m\n", flush=True)
        return route_result
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
    print(f"[shelters] 무더위쉼터 목록 호출\n", flush=True)
    return get_all_shelters()

@router.get(
    "/routes",
    summary="추천 경로 13개 목록 조회",
    description="수지구 내 추천 경로 13개를 반환합니다. mode 파라미터로 필터링 가능합니다 (노약자 5개 / 반려동물 5개 / 일반 3개).",
    response_model=list[RecommendedRouteResponse],
)
def list_routes(
    mode: Mode | None = Query(default=None, description="모드 필터 — 생략 시 전체 반환"),
    presets: list[str] | None = Query(default=None, description="수신된 프리셋 목록") # 💡 태그를 받을 수 있도록 파라미터 추가
) -> list[dict]:
    global _last_extracted_presets, _last_recommended_routes

    print(f"[routes] 실제 수신한 프리셋: {presets}\n", flush=True)

    if presets:
        print(f"[routes] 파라미터 사용: 수신된 태그({presets})로 경로 탐색\n", flush=True)
        routes_to_return = select_top_k_routes(preferred_tags=presets, k=3, mode=mode)
        
        route_names = [r.get("name", "Unknown") for r in routes_to_return]
        print(f"[routes] 맞춤 경로 반환: {len(routes_to_return)}개\n{route_names}\n", flush=True)
        return routes_to_return

    if not presets and _last_recommended_routes:
        print(f"[routes] 캐시 사용: 전송값 없음 -> 캐시된 프리셋({_last_extracted_presets}) 적용\n", flush=True)
        routes_to_return = _last_recommended_routes
        
        route_names = [r.get("name", "Unknown") for r in routes_to_return]
        print(f"[routes] 맞춤 경로 반환: {len(routes_to_return)}개\n{route_names}\n", flush=True)
        
        _last_extracted_presets = []
        _last_recommended_routes = []
        
        return routes_to_return

    print(f"[routes] 수신한 모드: {mode}\n", flush=True)

    if mode is not None and mode not in MODES:
        print(f"[routes] 경고: 유효하지 않은 모드({mode})로 빈 리스트 반환\n", flush=True)
        return []
    
    routes = get_recommended_routes(mode=mode)
    print(f"[routes] 데이터 반환: {len(routes)}개의 추천 경로를 반환합니다.\n", flush=True)
    return routes

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


@router.post(
    "/preset",
    summary="STT 텍스트 → 프리셋 추출 → Top-k 경로 추천",
    description="프론트에서 확인/수정한 STT 텍스트를 클라이밋팟 에이전트로 보내 프리셋을 추출하고, 검증된 프리셋으로 Top-3 경로를 반환합니다.",
    response_model=PresetExtractionResult,
)
async def receive_preset_text(request: PresetExtractionRequest) -> dict:
    global _last_extracted_presets, _last_recommended_routes

    print(f"[preset] 입력받은 텍스트: '{request.text}'\n", flush=True)
    try:
        agent_text = await call_preset_agent(request.text)
        # print(f"[preset] 에이전트 응답: {agent_text}\n", flush=True)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="클라이밋팟 에이전트 호출 실패") from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="클라이밋팟 에이전트 응답 시간 초과") from exc

    preset_ids, dropped_ids = extract_preset_ids(agent_text)
    base_presets, sub_presets = classify_presets(preset_ids)
    print(f"[preset] preset_ids: {preset_ids}\n(dropped_ids: {dropped_ids})", flush=True)

    routes = select_top_k_routes(preferred_tags=preset_ids, k=3, mode=None)

    _last_extracted_presets = preset_ids
    _last_recommended_routes = routes
    print(f"[preset] 캐시: preset_ids({preset_ids}) routes({len(routes)} 개) 임시 저장\n", flush=True)

    return {
        "preset_ids": preset_ids,
        "base_presets": base_presets,
        "sub_presets": sub_presets,
        "dropped_ids": dropped_ids,
        "routes": routes,
    }