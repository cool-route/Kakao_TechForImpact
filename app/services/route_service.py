from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from app.core.config import (
    DATA_DIR,
    MODES,
    ROUTE_GEOM_DIR,
    ROUTE_META_DIR,
    ROUTE_OUTPUTS_DIR,
    ROUTE_OUTPUTS_SHELTERS_DIR,
    SHELTERS_PATH,
)
from app.services.geo import Coordinate, haversine_m, point_to_segment_distance_m
from app.services.geojson_loader import load_shelters
from app.services.graph_loader import clear_graph_cache, load_route_graph
from app.services.pathfinder import nearest_node, pairwise, shortest_path_for_mode
from app.services.route_geojson import to_feature_collection, unique_shelters


_recommended_routes_cache: dict[str, list[dict]] = {}
_route_tags_config: dict | None = None
_preset_catalog_maps: dict | None = None


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

    tag_weights = _route_tags_config.get("tag_weights", {})
    normalized_weights: dict[str, float] = {}
    for raw_tag, weight in tag_weights.items():
        normalized_weights[_normalize_tag_id(raw_tag)] = float(weight)
    _route_tags_config["tag_weights"] = normalized_weights
    return _route_tags_config


def _load_preset_catalog_maps() -> dict:
    global _preset_catalog_maps
    if _preset_catalog_maps is not None:
        return _preset_catalog_maps

    path = DATA_DIR / "preset_catalog.json"
    with path.open(encoding="utf-8") as f:
        catalog = json.load(f)

    id_index: dict[str, dict] = {}
    label_to_id: dict[str, str] = {}
    alias_to_id: dict[str, str] = {}
    category_to_ids: dict[str, list[str]] = {}

    for category_name, items in catalog.get("categories", {}).items():
        category_to_ids.setdefault(category_name, [])
        for item in items:
            preset_id = item["id"]
            id_index[preset_id] = {
                "label": item["label"],
                "category": category_name,
                "type": item.get("type", "sub"),
                "enabled": bool(item.get("enabled", False)),
                "aliases": list(item.get("aliases", [])),
            }
            label_to_id[item["label"]] = preset_id
            for alias in item.get("aliases", []):
                alias_to_id[alias] = preset_id
            category_to_ids[category_name].append(preset_id)

    _preset_catalog_maps = {
        "catalog": catalog,
        "id_index": id_index,
        "label_to_id": label_to_id,
        "alias_to_id": alias_to_id,
        "category_to_ids": category_to_ids,
    }
    return _preset_catalog_maps


def _normalize_tag_id(tag: str) -> str:
    maps = _load_preset_catalog_maps()
    if tag in maps["id_index"]:
        return tag
    if tag in maps["label_to_id"]:
        return maps["label_to_id"][tag]
    if tag in maps["alias_to_id"]:
        return maps["alias_to_id"][tag]
    return tag


def _place_tag_id(location_label: str | None, route_id: int | None = None) -> str | None:
    if not location_label:
        return None
    maps = _load_preset_catalog_maps()
    tag_id = maps["label_to_id"].get(location_label) or maps["alias_to_id"].get(location_label)
    if tag_id:
        return tag_id

    place_ids = maps["category_to_ids"].get("place", [])
    if not place_ids:
        return None

    # Fallback: stable assignment by route_id to guarantee one place tag.
    index = (route_id - 1) % len(place_ids) if route_id else 0
    return place_ids[index]


def _duration_tag_id(duration_label: str | None, distance_m: float) -> str:
    maps = _load_preset_catalog_maps()
    label_map = maps["label_to_id"]

    if duration_label:
        tag_id = label_map.get(duration_label)
        if tag_id:
            return tag_id

    if distance_m <= 700:
        return label_map.get("10분") or "walk_10m"
    if distance_m <= 1400:
        return label_map.get("15분") or "walk_15m"
    if distance_m <= 3200:
        return label_map.get("30분") or "walk_30m"
    if distance_m <= 6500:
        return label_map.get("1시간") or "walk_60m"
    return label_map.get("2시간 이상") or "walk_120m_plus"


def _build_route_tags_from_meta(meta: dict, route_id: int | None = None) -> list[str]:
    maps = _load_preset_catalog_maps()
    tags: list[str] = []

    # All current outputs represent the elder/walking support route set.
    condition_tag = _normalize_tag_id("어르신과")
    if condition_tag in maps["id_index"]:
        tags.append(condition_tag)

    duration_tag = _duration_tag_id(meta.get("duration"), float(meta.get("distance_m") or 0.0))
    if duration_tag not in tags:
        tags.append(duration_tag)

    location = meta.get("location") or []
    place_tag = _place_tag_id(location[0] if location else None, route_id=route_id)
    if place_tag and place_tag not in tags:
        tags.append(place_tag)

    heat = meta.get("heat_score") or {}
    heat_value = float(heat.get("value") or 0.0)
    heat_grade = str(heat.get("grade") or "")
    data = meta.get("data") or {}
    slope = float((data.get("slope_over_15deg") or {}).get("normalized") or 0.0)
    tmrt = float((data.get("tmrt") or {}).get("normalized") or 0.0)
    svf = float((data.get("sky_view_factor") or {}).get("normalized") or 0.0)
    green = (data.get("green") or {}).get("normalized")
    shelter_count = int((data.get("shelter") or {}).get("count") or 0)

    # Heat / comfort tags
    if heat_grade == "q1" or heat_value <= 35:
        tags.append(_normalize_tag_id("시원한길"))
    if tmrt <= 0.25 or heat_value <= 40:
        tags.append(_normalize_tag_id("복사열 낮은 노면"))
    if svf <= 0.22:
        tags.append(_normalize_tag_id("그늘 많은 길"))
    if green is not None and float(green) >= 0.2:
        tags.append(_normalize_tag_id("녹지 많은 길"))
    if slope <= 0.03:
        tags.append(_normalize_tag_id("평지"))
    if shelter_count >= 1:
        tags.append(_normalize_tag_id("무더위쉼터 경유"))
        tags.append(_normalize_tag_id("쉼터많음"))

    # Mobility-support style rule based on the data we actually have.
    if slope <= 0.01 and svf <= 0.15:
        tags.append(_normalize_tag_id("휠체어·보행 보조"))

    feature_candidates = {
        _normalize_tag_id("시원한길"),
        _normalize_tag_id("복사열 낮은 노면"),
        _normalize_tag_id("그늘 많은 길"),
        _normalize_tag_id("녹지 많은 길"),
        _normalize_tag_id("평지"),
        _normalize_tag_id("무더위쉼터 경유"),
        _normalize_tag_id("쉼터많음"),
        _normalize_tag_id("휠체어·보행 보조"),
    }

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for tag in tags:
        normalized = _normalize_tag_id(tag)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)

    # Ensure mandatory categories are represented even if heuristic tags are sparse.
    if duration_tag not in seen:
        deduped.insert(1 if deduped else 0, duration_tag)
    if place_tag and place_tag not in seen:
        insert_at = 2 if len(deduped) >= 2 else len(deduped)
        deduped.insert(insert_at, place_tag)

    if not any(tag in feature_candidates for tag in deduped):
        deduped.append(_normalize_tag_id("시원한길") if heat_value <= 60 else _normalize_tag_id("평지"))

    return deduped


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
        tags.add(_normalize_tag_id("시원한길"))
    if avg_shade >= 0.35:
        tags.add(_normalize_tag_id("그늘 많은 길"))
    if shelters_count >= 1:
        tags.add(_normalize_tag_id("무더위쉼터 경유"))
        tags.add(_normalize_tag_id("쉼터많음"))

    # duration tags
    if dist <= 900:
        tags.add(_duration_tag_id(None, 800))
    elif dist <= 3000:
        tags.add(_duration_tag_id(None, 2000))
    elif dist <= 5000:
        tags.add(_duration_tag_id(None, 4000))
    else:
        tags.add(_duration_tag_id(None, 7000))

    # always include mode tag if present
    mode = route.get("mode")
    if mode:
        if mode == "노약자":
            tags.add(_normalize_tag_id("어르신과"))
        else:
            tags.add(_normalize_tag_id(mode))

    return sorted(tags)


def select_top_k_routes(preferred_tags: list[str] | None = None, k: int = 3, mode: str | None = None) -> list[dict]:
    """Return top-k recommended routes ranked by matching score against preferred_tags.

    Tie-breakers follow config: lower heat_score_avg, shorter distance_m, more shelters.
    """
    tag_cfg = _load_route_tags_config()
    weights = tag_cfg.get("tag_weights", {}) if tag_cfg else {}

    routes = get_recommended_routes(mode=mode)
    scored = []
    preferred_tag_ids = [_normalize_tag_id(tag) for tag in (preferred_tags or [])]
    for r in routes:
        route = deepcopy(r)
        route_tags = [_normalize_tag_id(tag) for tag in route.get("tags", [])]
        if not route_tags:
            route_tags = _derive_tags_for_route(route, tag_cfg)
        route["tags"] = route_tags

        # compute match score
        match_score = 0.0
        if preferred_tag_ids:
            for t in preferred_tag_ids:
                if t in route_tags:
                    match_score += float(weights.get(t, 0.0))

        # fallback: if no preferred tags provided, score by sum of all tag weights
        if not preferred_tag_ids:
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
    routes = _load_real_route_outputs()
    if routes:
        return routes

    routes = []
    route_id = 1

    # Legacy support for older route output directories.
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


def _load_real_route_outputs() -> list[dict]:
    routes = []
    if not ROUTE_META_DIR.exists() or not ROUTE_GEOM_DIR.exists():
        return routes

    for meta_path in sorted(ROUTE_META_DIR.glob("*.json")):
        route_id = int(meta_path.stem)
        geom_path = ROUTE_GEOM_DIR / f"{meta_path.stem}_edges.geojson"
        if not geom_path.exists():
            continue

        with meta_path.open(encoding="utf-8") as f:
            meta = json.load(f)
        with geom_path.open(encoding="utf-8") as f:
            geojson = json.load(f)

        route_tags = meta.get("tags") or _build_route_tags_from_meta(meta, route_id=route_id)
        route_name = _make_route_name_from_meta(meta)
        heat_score = float((meta.get("heat_score") or {}).get("value") or 0.0)

        routes.append(
            {
                "id": route_id,
                "name": route_name,
                "mode": "노약자",
                "heat_score_avg": round(heat_score, 3),
                "distance_m": round(float(meta.get("distance_m") or 0.0), 1),
                "geojson": geojson,
                "shelters": [],
                "is_dummy": False,
                "tags": route_tags,
            }
        )

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
            location_label = _load_preset_catalog_maps()["category_to_ids"].get("place", [])[i % max(1, len(_load_preset_catalog_maps()["category_to_ids"].get("place", [])))] if _load_preset_catalog_maps()["category_to_ids"].get("place") else None
            duration_tag = _duration_tag_id(None, 1000.0 + i * 100.0)
            route = {
                "id": sid,
                "name": f"추천 경로 {sid}",
                "mode": "노약자",
                "heat_score_avg": 25.0 - (i % 5),
                "distance_m": 1000.0 + i * 100.0,
                "geojson": {"type": "FeatureCollection", "features": []},
                "shelters": shelters_sample if i % 3 == 0 else [],
                "is_dummy": True,
                "tags": [t for t in ["with_elder", location_label, duration_tag] if t],
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
            "tags": _build_route_tags_from_meta(
                {
                    "location": [spec.get("name", "")],
                    "distance_m": 1000.0 + i * 100.0,
                    "duration": None,
                    "heat_score": {"value": 22.0 + (i % 5), "grade": "q1"},
                    "data": {"slope_over_15deg": {"normalized": 0.0}, "tmrt": {"normalized": 0.2}, "sky_view_factor": {"normalized": 0.1}, "shelter": {"count": len(shelters)}},
                },
                route_id=sid,
            ),
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


def _make_route_name_from_meta(meta: dict) -> str:
    locations = meta.get("location") or []
    duration = meta.get("duration") or ""
    if locations:
        return f"{locations[0]} {duration}".strip()
    if duration:
        return str(duration)
    return f"추천 경로 {meta.get('route_id', '')}".strip()


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


