from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from app.core.config import MODES, ROUTE_SPECS_PATH
from app.services.geo import Coordinate
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

    routes = []
    for spec in load_route_specs():
        route_mode = spec["mode"]
        if mode is not None and route_mode != mode:
            continue
        start = tuple(spec["start"])
        end = tuple(spec["end"])
        result = shortest_cool_route(route_mode, start, end)
        routes.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "mode": route_mode,
                "heat_score_avg": result["heat_score_avg"],
                "distance_m": result["distance_m"],
                "geojson": result["path"],
                "shelters": result["shelters"],
                "is_dummy": result["is_dummy"],
            }
        )
    _recommended_routes_cache[cache_key] = routes
    return deepcopy(routes)


def clear_route_caches() -> None:
    clear_graph_cache()
    _recommended_routes_cache.clear()


def load_route_specs(path: Path = ROUTE_SPECS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        specs = json.load(file)

    if not isinstance(specs, list):
        raise ValueError("route_specs.json must be a JSON array")
    for spec in specs:
        missing = {"id", "mode", "name", "start", "end"} - set(spec)
        if missing:
            raise ValueError(f"route spec is missing required fields: {sorted(missing)}")
        if spec["mode"] not in MODES:
            raise ValueError(f"unsupported route mode in route_specs.json: {spec['mode']}")
    return specs
