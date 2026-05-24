from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from app.core.config import MODES, ROUTE_OUTPUTS_DIR, ROUTE_OUTPUTS_SHELTERS_DIR, SHELTERS_PATH
from app.services.geo import Coordinate, haversine_m, point_to_segment_distance_m
from app.services.geojson_loader import load_shelters
from app.services.graph_loader import clear_graph_cache, load_route_graph
from app.services.pathfinder import nearest_node, pairwise, shortest_path_for_mode
from app.services.route_geojson import to_feature_collection, unique_shelters


_recommended_routes_cache: dict[str, list[dict]] = {}


def shortest_cool_route(mode: str, start: Coordinate, end: Coordinate) -> dict:
    if mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")

    graph, is_dummy = load_route_graph()
    source = nearest_node(graph, start)
    target = nearest_node(graph, end)
    path = shortest_path_for_mode(graph, mode, source, target)
    edges = list(pairwise(path))
    edge_attrs = [graph.edges[u, v] for u, v in edges]
    distance_m = sum(float(attrs["distance_m"]) for attrs in edge_attrs)
    heat_score_avg = sum(float(attrs["heat_score"]) for attrs in edge_attrs) / len(edge_attrs)
    shelters = unique_shelters(edge_attrs, graph)

    return {
        "path": to_feature_collection(graph, edges, edge_attrs, mode),
        "heat_score_avg": round(heat_score_avg, 3),
        "distance_m": round(distance_m, 1),
        "shelters": shelters,
        "is_dummy": is_dummy,
    }


def get_recommended_routes(mode: str | None = None) -> list[dict]:
    cache_key = mode or "__all__"
    if cache_key in _recommended_routes_cache:
        return deepcopy(_recommended_routes_cache[cache_key])

    routes = _load_precomputed_routes()
    if mode is not None:
        routes = [r for r in routes if r["mode"] == mode]

    _recommended_routes_cache[cache_key] = routes
    return deepcopy(routes)


def _load_precomputed_routes() -> list[dict]:
    routes = []
    route_id = 1

    route_directories = [(ROUTE_OUTPUTS_DIR, None)]
    if ROUTE_OUTPUTS_SHELTERS_DIR is not None:
        route_directories.append((ROUTE_OUTPUTS_SHELTERS_DIR, True))

    for directory, has_shelters_override in route_directories:
        if not directory.exists():
            continue
        for edges_path in sorted(directory.glob("*_edges.geojson")):
            nodes_path = edges_path.with_name(edges_path.name.replace("_edges", "_nodes"))
            if not nodes_path.exists():
                continue
            has_shelters = has_shelters_override
            if has_shelters is None:
                has_shelters = "shelter" in edges_path.stem
            route = _build_route_from_files(route_id, edges_path, nodes_path, has_shelters)
            routes.append(route)
            route_id += 1

    return routes


def _build_route_from_files(
    route_id: int, edges_path: Path, nodes_path: Path, has_shelters: bool
) -> dict:
    with edges_path.open(encoding="utf-8") as f:
        edges_data = json.load(f)
    with nodes_path.open(encoding="utf-8") as f:
        nodes_data = json.load(f)

    node_map: dict[str, dict] = {}
    for feat in nodes_data["features"]:
        props = feat["properties"]
        osmid = str(props["osmid"])
        node_map[osmid] = {
            "lat": float(props["y"]),
            "lng": float(props["x"]),
            "felt_temp": float(props.get("felt_temp") or 36.0),
            "heat_grade": float(props.get("heat_grade") or 5.0),
            "shade": float(props.get("shade") or 0.2),
        }

    features = []
    total_dist = 0.0
    total_heat = 0.0

    for feat in edges_data["features"]:
        props = feat["properties"]
        u = str(props["u"])
        v = str(props["v"])
        u_node = node_map.get(u, {})
        v_node = node_map.get(v, {})

        length = float(props.get("length") or 0.0)
        heat_score = float(props.get("heat_score") or 22.0)
        temperature = (u_node.get("felt_temp", 36.0) + v_node.get("felt_temp", 36.0)) / 2
        shade_ratio = (u_node.get("shade", 0.2) + v_node.get("shade", 0.2)) / 2
        ground_temp = (u_node.get("heat_grade", 5.0) + v_node.get("heat_grade", 5.0)) / 2

        total_dist += length
        total_heat += heat_score

        features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": {
                "mode": "노약자",
                "heat_score": round(heat_score, 3),
                "distance_m": round(length, 1),
                "temperature": round(temperature, 2),
                "uv": 0.0,
                "shade_ratio": round(shade_ratio, 3),
                "wind": 0.0,
                "ground_temp": round(ground_temp, 2),
                "shelter_name": None,
            },
        })

    n = len(features)
    heat_score_avg = round(total_heat / n, 3) if n > 0 else 0.0

    shelters = _find_shelters_near_nodes(node_map) if has_shelters else []

    return {
        "id": route_id,
        "name": _make_route_name(edges_path.stem),
        "mode": "노약자",
        "heat_score_avg": heat_score_avg,
        "distance_m": round(total_dist, 1),
        "geojson": {"type": "FeatureCollection", "features": features},
        "shelters": shelters,
        "is_dummy": False,
    }


def _make_route_name(stem: str) -> str:
    m = re.search(r"shelter\d+_(\d+km)", stem)
    if m:
        return f"쉼터 경유 {m.group(1)} 경로"
    m = re.search(r"shelter(\d+)_route", stem)
    if m:
        return f"쉼터 경유 추천 경로 {m.group(1)}"
    m = re.search(r"(\d+km)_route_?(\d+)", stem)
    if m:
        return f"{m.group(1)} 추천 경로 {m.group(2)}"
    return stem


def _find_shelters_near_nodes(node_map: dict, radius_m: float = 300.0) -> list[dict]:
    all_shelters = load_shelters(SHELTERS_PATH)
    found = []
    seen: set[str] = set()
    for shelter in all_shelters:
        for node in node_map.values():
            dist = haversine_m((shelter["lat"], shelter["lng"]), (node["lat"], node["lng"]))
            if dist <= radius_m and shelter["name"] not in seen:
                seen.add(shelter["name"])
                found.append({
                    "name": shelter["name"],
                    "lat": shelter["lat"],
                    "lng": shelter["lng"],
                    "address": shelter.get("address", ""),
                    "operating_hours": shelter.get("operating_hours", "09:00-18:00"),
                })
                break
    return found


def find_nearest_route(lat: float, lng: float) -> dict:
    routes = get_recommended_routes()
    if not routes:
        raise ValueError("추천 경로 데이터가 없습니다.")

    user_pos: Coordinate = (lat, lng)
    best_route = None
    best_dist = float("inf")

    for route in routes:
        dist = _min_distance_to_geojson(user_pos, route["geojson"])
        if dist < best_dist:
            best_dist = dist
            best_route = route

    return {**best_route, "distance_to_user_m": round(best_dist, 1)}


def _min_distance_to_geojson(pos: Coordinate, geojson: dict) -> float:
    """GeoJSON FeatureCollection(LineString들) 내 모든 엣지에서 pos까지의 최소 거리."""
    min_dist = float("inf")
    for feature in geojson.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        coords = geom.get("coordinates", [])  # [[lng, lat], ...]
        for i in range(len(coords) - 1):
            # GeoJSON은 [lng, lat] 순서
            a: Coordinate = (coords[i][1], coords[i][0])
            b: Coordinate = (coords[i + 1][1], coords[i + 1][0])
            d = point_to_segment_distance_m(pos, a, b)
            if d < min_dist:
                min_dist = d
    return min_dist


def get_all_shelters() -> list[dict]:
    return load_shelters(SHELTERS_PATH)


def clear_route_caches() -> None:
    clear_graph_cache()
    _recommended_routes_cache.clear()

