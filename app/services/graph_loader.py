from __future__ import annotations

import networkx as nx

from app.core.config import EDGES_PATH, LEGACY_GRAPH_PATH, NODES_PATH, SHELTERS_PATH
from app.services.geo import haversine_m
from app.services.geojson_loader import load_graph_from_geojson, load_graph_from_nodes_and_edges


_graph_cache: tuple[nx.Graph, bool] | None = None


def build_dummy_graph() -> nx.Graph:
    graph = nx.Graph()
    nodes = {
        "suji_office": (37.3219, 127.0972),
        "library": (37.3232, 127.1010),
        "shade_walk": (37.3250, 127.1052),
        "direct_hot": (37.3262, 127.1090),
        "pet_safe": (37.3198, 127.1055),
        "windy_road": (37.3221, 127.1117),
        "jukjeon": (37.3247, 127.1245),
    }
    for node_id, (lat, lng) in nodes.items():
        graph.add_node(node_id, lat=lat, lng=lng)

    add_edge(graph, "suji_office", "direct_hot", heat_score=0.82, temperature=34.0, uv=0.88, shade_ratio=0.10, wind=0.20, ground_temp=35.5)
    add_edge(graph, "direct_hot", "jukjeon", heat_score=0.78, temperature=33.5, uv=0.84, shade_ratio=0.12, wind=0.22, ground_temp=34.0)

    add_edge(graph, "suji_office", "library", heat_score=0.32, temperature=29.5, uv=0.61, shade_ratio=0.55, wind=0.45, ground_temp=28.4, shelter_name="수지도서관", shelter_node="library")
    add_edge(graph, "library", "shade_walk", heat_score=0.25, temperature=28.8, uv=0.48, shade_ratio=0.72, wind=0.36, ground_temp=27.5, shelter_name="수지도서관", shelter_node="library")
    add_edge(graph, "shade_walk", "jukjeon", heat_score=0.38, temperature=30.0, uv=0.55, shade_ratio=0.64, wind=0.30, ground_temp=28.1)

    add_edge(graph, "suji_office", "pet_safe", heat_score=0.45, temperature=30.5, uv=0.58, shade_ratio=0.48, wind=0.42, ground_temp=26.9)
    add_edge(graph, "pet_safe", "windy_road", heat_score=0.36, temperature=30.2, uv=0.52, shade_ratio=0.40, wind=0.75, ground_temp=26.4)
    add_edge(graph, "windy_road", "jukjeon", heat_score=0.42, temperature=30.8, uv=0.56, shade_ratio=0.36, wind=0.80, ground_temp=26.8)

    return graph


def load_route_graph() -> tuple[nx.Graph, bool]:
    global _graph_cache
    if _graph_cache is not None:
        return _graph_cache
    if NODES_PATH.exists() and EDGES_PATH.exists():
        result = load_graph_from_nodes_and_edges(NODES_PATH, EDGES_PATH, SHELTERS_PATH), False
    elif LEGACY_GRAPH_PATH.exists():
        result = load_graph_from_geojson(LEGACY_GRAPH_PATH), False
    else:
        result = build_dummy_graph(), True
    _graph_cache = result
    return result


def clear_graph_cache() -> None:
    global _graph_cache
    _graph_cache = None


def add_edge(graph: nx.Graph, source: str, target: str, **attrs: float | str) -> None:
    source_coord = (graph.nodes[source]["lat"], graph.nodes[source]["lng"])
    target_coord = (graph.nodes[target]["lat"], graph.nodes[target]["lng"])
    graph.add_edge(source, target, distance_m=haversine_m(source_coord, target_coord), **attrs)
