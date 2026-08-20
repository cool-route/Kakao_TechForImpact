from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from app.core.config import MODES, ROUTE_OUTPUTS_DIR, ROUTE_OUTPUTS_SHELTERS_DIR, SHELTERS_PATH, DATA_DIR
from app.services.geo import Coordinate, haversine_m, point_to_segment_distance_m
from app.services.geojson_loader import load_shelters
from app.services.graph_loader import clear_graph_cache, load_route_graph
from app.services.pathfinder import nearest_node, pairwise, shortest_path_for_mode
from app.services.route_geojson import to_feature_collection, unique_shelters


_recommended_routes_cache: dict[str, list[dict]] = {}
_route_tags_config: dict | None = None


def _normalize_heat_score_avg(value: float) -> float:
    return round(max(value, 0.001), 3)


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
        "heat_score_avg": _normalize_heat_score_avg(heat_score_avg),
        "distance_m": round(distance_m, 1),
        "shelters": shelters,
        "is_dummy": is_dummy,
    }


def get_recommended_routes(mode: str | None = None) -> list[dict]:
    cache_key = mode or "__all__"
    if cache_key in _recommended_routes_cache:
        return deepcopy(_recommended_routes_cache[cache_key])

    routes = _load_precomputed_routes()
    # fallback: synthesize routes if none found (useful for tests/dev)
    if not routes:
        routes = _synthesize_fallback_routes(count=14)
    if mode is not None:
        routes = [r for r in routes if r["mode"] == mode]

    _recommended_routes_cache[cache_key] = routes
    return deepcopy(routes)


def _load_route_tags_config() -> dict:
    global _route_tags_config
    if _route_tags_config is not None:
        return _route_tags_config
    path = DATA_DIR / "route_tags.json"
    if not path.exists():
        _route_tags_config = {}
        return _route_tags_config
    with path.open(encoding="utf-8") as f:
        _route_tags_config = json.load(f)
    return _route_tags_config


def _derive_tags_for_route(route: dict, tag_cfg: dict) -> list[str]:
    tags = set()
    # Basic heuristics based on route metrics
    heat = float(route.get("heat_score_avg") or 0.0)
    dist = float(route.get("distance_m") or 0.0)
    shelters = route.get("shelters") or []
    shelters_count = len(shelters)

    # compute average shade_ratio and ground_temp from geojson features if available
    features = route.get("geojson", {}).get("features", [])
    shade_vals = []
    ground_vals = []
    for feat in features:
        props = feat.get("properties", {})
        if "shade_ratio" in props:
            try:
                shade_vals.append(float(props.get("shade_ratio") or 0.0))
            except Exception:
                pass
        if "ground_temp" in props:
            try:
                ground_vals.append(float(props.get("ground_temp") or 0.0))
            except Exception:
                pass

    avg_shade = sum(shade_vals) / len(shade_vals) if shade_vals else 0.0
    avg_ground = sum(ground_vals) / len(ground_vals) if ground_vals else 0.0

    # Heuristic tag assignments
    if heat <= 22.0:
        tags.add("시원한길")
    if avg_shade >= 0.35:
        tags.add("그늘많음")
    if shelters_count >= 2:
        tags.add("쉼터많음")
    elif shelters_count == 1:
        tags.add("쉼터있음")

    # duration tags
    if dist <= 900:
        tags.add("15분")
    elif dist <= 3000:
        tags.add("30분")
    elif dist <= 5000:
        tags.add("45분")
    else:
        tags.add("60분")

    # always include mode tag if present
    mode = route.get("mode")
    if mode:
        tags.add(mode)

    # only keep tags that appear in tag_weights if available
    weights = (tag_cfg or {}).get("tag_weights") or {}
    if weights:
        filtered = [t for t in tags if t in weights]
        return sorted(filtered)

    return sorted(tags)


def select_top_k_routes(preferred_tags: list[str] | None = None, k: int = 3, mode: str | None = None) -> list[dict]:
    """Return top-k recommended routes ranked by matching score against preferred_tags.

    Tie-breakers follow config: lower heat_score_avg, shorter distance_m, more shelters.
    """
    tag_cfg = _load_route_tags_config()
    weights = tag_cfg.get("tag_weights", {}) if tag_cfg else {}
    scoring_rules = tag_cfg.get("scoring_rules", {}) if tag_cfg else {}

    routes = get_recommended_routes(mode=mode)
    scored = []
    for r in routes:
        route = deepcopy(r)
        route_tags = _derive_tags_for_route(route, tag_cfg)
        route["tags"] = route_tags

        # compute match score
        match_score = 0.0
        if preferred_tags:
            for t in preferred_tags:
                if t in route_tags:
                    match_score += float(weights.get(t, 0.0))

        # fallback: if no preferred tags provided, score by sum of all tag weights
        if not preferred_tags:
            match_score = sum(float(weights.get(t, 0.0)) for t in route_tags)

        route["match_score"] = round(match_score, 3)
        scored.append(route)

    # sort by match_score desc, then tie-breakers
    def sort_key(r: dict):
        return (
            -r.get("match_score", 0.0),
            r.get("heat_score_avg", float("inf")),
            r.get("distance_m", float("inf")),
            -(len(r.get("shelters") or [])),
        )

    scored.sort(key=sort_key)
    return [deepcopy(r) for r in scored[:k]]


def _load_precomputed_routes() -> list[dict]:
    routes = []
    route_id = 1

    for directory, has_shelters in [
        (ROUTE_OUTPUTS_DIR, False),
        (ROUTE_OUTPUTS_SHELTERS_DIR, True),
    ]:
        for edges_path in sorted(directory.glob("*_edges.geojson")):
            nodes_path = edges_path.with_name(edges_path.name.replace("_edges", "_nodes"))
            if not nodes_path.exists():
                continue
            route = _build_route_from_files(route_id, edges_path, nodes_path, has_shelters)
            routes.append(route)
            route_id += 1

    return routes


def _synthesize_fallback_routes(count: int = 14) -> list[dict]:
    """Create deterministic fallback recommended routes when precomputed files are missing.

    Uses `data/route_specs.json` and `data/sample` shelters to build simple GeoJSONs.
    """
    specs_path = DATA_DIR / "route_specs.json"
    sample_shelters_path = DATA_DIR / "sample" / "shelters.json"
    specs = []
    if specs_path.exists():
        with specs_path.open(encoding="utf-8") as f:
            try:
                specs = json.load(f)
            except Exception:
                specs = []

    shelters_sample = []
    if sample_shelters_path.exists():
        with sample_shelters_path.open(encoding="utf-8") as f:
            try:
                shelters_sample = json.load(f)
            except Exception:
                shelters_sample = []

    result = []
    sid = 1
    # if no specs, create simple placeholder routes
    if not specs:
        for i in range(count):
            route = {
                "id": sid,
                "name": f"추천 경로 {sid}",
                "mode": "노약자",
                "heat_score_avg": 25.0 - (i % 5),
                "distance_m": 1000.0 + i * 100.0,
                "geojson": {"type": "FeatureCollection", "features": []},
                "shelters": shelters_sample if i % 3 == 0 else [],
                "is_dummy": True,
            }
            result.append(route)
            sid += 1
        return result

    # create up to `count` routes by cycling specs
    i = 0
    while len(result) < count:
        spec = specs[i % len(specs)]
        name = spec.get("name") or f"route_{i}"
        start = spec.get("start") or [37.3219, 127.0972]
        end = spec.get("end") or [37.3247, 127.1245]
        # simple LineString feature using start->end
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[start[1], start[0]], [end[1], end[0]]]},
                    "properties": {"mode": spec.get("mode", "노약자"), "heat_score": 22.0 + (i % 5), "distance_m": 1000.0 + i * 100.0},
                }
            ],
        }
        shelters = shelters_sample if "쉼터" in name or (i % 4 == 0) else []
        route = {
            "id": sid,
            "name": name,
            "mode": spec.get("mode", "노약자"),
            "heat_score_avg": round(22.0 + (i % 5), 3),
            "distance_m": round(1000.0 + i * 100.0, 1),
            "geojson": geojson,
            "shelters": shelters,
            "is_dummy": True,
        }
        result.append(route)
        sid += 1
        i += 1

    return result


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
        "heat_score_avg": _normalize_heat_score_avg(heat_score_avg),
        "distance_m": round(total_dist, 1),
        "geojson": {"type": "FeatureCollection", "features": features},
        "shelters": shelters,
        "is_dummy": False,
    }


def _make_route_name(stem: str) -> str:
    m = re.search(r"shelter\d+_(\d+km)", stem)
    if m:
        return f"쉼터 경유 {m.group(1)} 경로"
    m = re.search(r"(\d+km)_route_(\d+)", stem)
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


