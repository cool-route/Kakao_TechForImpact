from __future__ import annotations

from typing import Iterable

import networkx as nx

from app.core.config import PET_GROUND_TEMP_LIMIT
from app.services.geo import Coordinate, haversine_m


def edge_weight(mode: str, attrs: dict) -> float:
    heat = float(attrs["heat_score"])
    distance = float(attrs["distance_m"])
    shade = float(attrs["shade_ratio"])
    wind = float(attrs["wind"])
    ground_temp = float(attrs["ground_temp"])
    shelter_bonus = 2.0 if attrs.get("shelter_name") else 0.0

    # heat_score는 ~16-29, shade는 0-1, wind는 0-5 m/s 범위
    # 계수 조정: shade/wind가 경로 선택에 실질적 영향을 주도록
    if mode == "노약자":
        comfort_penalty = heat * 0.5 - shade * 8.0 - shelter_bonus
    elif mode == "반려동물":
        hot_ground_penalty = 12.0 if ground_temp > PET_GROUND_TEMP_LIMIT else 0.0
        comfort_penalty = heat * 0.5 + hot_ground_penalty - shade * 4.0
    else:
        comfort_penalty = heat * 0.5 - shade * 3.0 - wind * 0.5

    return distance * max(0.1, 1 + comfort_penalty)


def graph_for_mode(graph: nx.Graph, mode: str) -> nx.Graph:
    return graph


def nearest_node(graph: nx.Graph, coord: Coordinate) -> str:
    return min(
        graph.nodes,
        key=lambda node_id: haversine_m(
            coord,
            (graph.nodes[node_id]["lat"], graph.nodes[node_id]["lng"]),
        ),
    )


def shortest_path_for_mode(graph: nx.Graph, mode: str, source: str, target: str) -> list[str]:
    mode_graph = graph_for_mode(graph, mode)
    if mode == "노약자":
        return shortest_path_via_shelter(mode_graph, mode, source, target)

    try:
        return nx.shortest_path(
            mode_graph,
            source=source,
            target=target,
            weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return nx.shortest_path(
            graph,
            source=source,
            target=target,
            weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
        )


def shortest_path_via_shelter(graph: nx.Graph, mode: str, source: str, target: str) -> list[str]:
    shelter_nodes = sorted(
        {
            str(attrs["shelter_node"])
            for _source, _target, attrs in graph.edges(data=True)
            if attrs.get("shelter_node") in graph.nodes
        }
    )
    if not shelter_nodes or source in shelter_nodes or target in shelter_nodes:
        return nx.shortest_path(
            graph,
            source=source,
            target=target,
            weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
        )

    best_path = None
    best_weight = None
    for shelter_node in shelter_nodes:
        try:
            first = nx.shortest_path(
                graph,
                source=source,
                target=shelter_node,
                weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
            )
            second = nx.shortest_path(
                graph,
                source=shelter_node,
                target=target,
                weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
            )
        except nx.NetworkXNoPath:
            continue

        candidate = first + second[1:]
        weight = path_weight(graph, mode, candidate)
        if best_weight is None or weight < best_weight:
            best_path = candidate
            best_weight = weight

    if best_path is not None:
        return best_path

    return nx.shortest_path(
        graph,
        source=source,
        target=target,
        weight=lambda _u, _v, attrs: edge_weight(mode, attrs),
    )


def path_weight(graph: nx.Graph, mode: str, path: list[str]) -> float:
    return sum(edge_weight(mode, graph.edges[source, target]) for source, target in pairwise(path))


def pairwise(items: list[str]) -> Iterable[tuple[str, str]]:
    for index in range(len(items) - 1):
        yield items[index], items[index + 1]
