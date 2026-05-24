from __future__ import annotations

from typing import Iterable

import networkx as nx

from app.services.geo import Coordinate, haversine_m


def edge_weight(attrs: dict) -> float:
    heat = float(attrs["heat_score"])
    distance = float(attrs["distance_m"])
    shade = float(attrs["shade_ratio"])
    shelter_bonus = 2.0 if attrs.get("shelter_name") else 0.0

    # heat_score ~16-29, shade 0-1
    comfort_penalty = heat * 0.5 - shade * 8.0 - shelter_bonus
    return distance * max(0.1, 1 + comfort_penalty)


def nearest_node(graph: nx.Graph, coord: Coordinate) -> str:
    return min(
        graph.nodes,
        key=lambda node_id: haversine_m(
            coord,
            (graph.nodes[node_id]["lat"], graph.nodes[node_id]["lng"]),
        ),
    )


def shortest_path_for_mode(graph: nx.Graph, mode: str, source: str, target: str) -> list[str]:
    return shortest_path_via_shelter(graph, source, target)


def shortest_path_via_shelter(graph: nx.Graph, source: str, target: str) -> list[str]:
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
            weight=lambda _u, _v, attrs: edge_weight(attrs),
        )

    best_path = None
    best_weight = None
    for shelter_node in shelter_nodes:
        try:
            first = nx.shortest_path(
                graph,
                source=source,
                target=shelter_node,
                weight=lambda _u, _v, attrs: edge_weight(attrs),
            )
            second = nx.shortest_path(
                graph,
                source=shelter_node,
                target=target,
                weight=lambda _u, _v, attrs: edge_weight(attrs),
            )
        except nx.NetworkXNoPath:
            continue

        candidate = first + second[1:]
        weight = path_weight(graph, candidate)
        if best_weight is None or weight < best_weight:
            best_path = candidate
            best_weight = weight

    if best_path is not None:
        return best_path

    return nx.shortest_path(
        graph,
        source=source,
        target=target,
        weight=lambda _u, _v, attrs: edge_weight(attrs),
    )


def path_weight(graph: nx.Graph, path: list[str]) -> float:
    return sum(edge_weight(graph.edges[source, target]) for source, target in pairwise(path))


def pairwise(items: list[str]) -> Iterable[tuple[str, str]]:
    for index in range(len(items) - 1):
        yield items[index], items[index + 1]
