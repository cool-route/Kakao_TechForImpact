from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from app.services.geo import haversine_m


REQUIRED_EDGE_PROPERTIES = {
    "source",
    "target",
    "heat_score",
    "temperature",
    "shade_ratio",
    "wind",
    "ground_temp",
}


def load_graph_from_nodes_and_edges(
    nodes_path: str | Path,
    edges_path: str | Path,
    shelters_path: str | Path | None = None,
) -> nx.Graph:
    nodes_data = load_json(nodes_path)
    edges_data = load_json(edges_path)

    node_map: dict[str, dict] = {}
    for feature in nodes_data["features"]:
        props = feature.get("properties") or {}
        osmid = str(props["osmid"])
        lng, lat = feature["geometry"]["coordinates"]
        node_map[osmid] = {
            "lat": float(lat),
            "lng": float(lng),
            "score": float(props["score"]),
            "utci": float(props["utci"]),
            "heat": float(props["heat"]),
            "shade": float(props["shade"]),
            "wind": float(props["wind"]),
        }

    graph = nx.Graph()
    for osmid, attrs in node_map.items():
        graph.add_node(osmid, lat=attrs["lat"], lng=attrs["lng"])

    for feature in edges_data["features"]:
        props = feature.get("properties") or {}
        u = str(props["u"])
        v = str(props["v"])
        if u not in node_map or v not in node_map:
            continue

        u_node = node_map[u]
        v_node = node_map[v]
        coords = feature["geometry"]["coordinates"]

        graph.add_edge(
            u,
            v,
            distance_m=float(props.get("length") or haversine_m(
                (u_node["lat"], u_node["lng"]),
                (v_node["lat"], v_node["lng"]),
            )),
            heat_score=(u_node["score"] + v_node["score"]) / 2,
            temperature=(u_node["utci"] + v_node["utci"]) / 2,
            ground_temp=(u_node["heat"] + v_node["heat"]) / 2,
            shade_ratio=(u_node["shade"] + v_node["shade"]) / 2,
            wind=(u_node["wind"] + v_node["wind"]) / 2,
            coordinates=coords,
        )

    if shelters_path and Path(shelters_path).exists():
        shelters = load_shelters(shelters_path)
        _attach_shelters(graph, shelters)

    return graph


def _attach_shelters(graph: nx.Graph, shelters: list[dict]) -> None:
    for shelter in shelters:
        nearest = min(
            graph.nodes,
            key=lambda n: haversine_m(
                (shelter["lat"], shelter["lng"]),
                (graph.nodes[n]["lat"], graph.nodes[n]["lng"]),
            ),
        )
        for neighbor in list(graph.neighbors(nearest)):
            attrs = graph.edges[nearest, neighbor]
            if not attrs.get("shelter_name"):
                attrs["shelter_name"] = shelter["name"]
                attrs["shelter_node"] = nearest
                attrs["shelter_operating_hours"] = shelter.get("operating_hours", "")


def load_graph_from_geojson(path: str | Path) -> nx.Graph:
    data = load_json(path)
    validate_feature_collection(data, path)

    graph = nx.Graph()
    for feature in data["features"]:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        validate_edge_feature(geometry, properties)

        source = str(properties["source"])
        target = str(properties["target"])
        coordinates = geometry["coordinates"]
        start_lng, start_lat = coordinates[0]
        end_lng, end_lat = coordinates[-1]

        graph.add_node(source, lat=float(start_lat), lng=float(start_lng))
        graph.add_node(target, lat=float(end_lat), lng=float(end_lng))
        graph.add_edge(
            source,
            target,
            distance_m=float(properties.get("distance_m") or haversine_m((start_lat, start_lng), (end_lat, end_lng))),
            heat_score=float(properties["heat_score"]),
            temperature=float(properties["temperature"]),
            uv=float(properties.get("uv") or 0.0),
            shade_ratio=float(properties["shade_ratio"]),
            wind=float(properties["wind"]),
            ground_temp=float(properties["ground_temp"]),
            shelter_name=properties.get("shelter_name"),
            shelter_node=properties.get("shelter_node"),
        )

    return graph


def load_shelters(path: str | Path) -> list[dict[str, Any]]:
    shelters = load_json(path)
    if not isinstance(shelters, list):
        raise ValueError("shelters.json must be a JSON array")

    required = {"name", "lat", "lng"}
    for shelter in shelters:
        missing = required - set(shelter)
        if missing:
            raise ValueError(f"shelter is missing required fields: {sorted(missing)}")
        shelter["lat"] = float(shelter["lat"])
        shelter["lng"] = float(shelter["lng"])
    return shelters


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def validate_feature_collection(data: Any, path: str | Path) -> None:
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError(f"{path} must be a GeoJSON FeatureCollection")
    if not isinstance(data.get("features"), list):
        raise ValueError(f"{path} must include a features array")


def validate_edge_feature(geometry: dict, properties: dict) -> None:
    if geometry.get("type") != "LineString":
        raise ValueError("each route segment must be a LineString feature")
    if len(geometry.get("coordinates", [])) < 2:
        raise ValueError("each LineString feature must include at least two coordinates")

    missing = REQUIRED_EDGE_PROPERTIES - set(properties)
    if missing:
        raise ValueError(f"route segment is missing required properties: {sorted(missing)}")
