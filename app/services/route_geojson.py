from __future__ import annotations

import networkx as nx


def to_feature_collection(graph: nx.Graph, edges: list[tuple[str, str]], edge_attrs: list[dict], mode: str) -> dict:
    features = []
    for (source, target), attrs in zip(edges, edge_attrs):
        coordinates = attrs.get("coordinates") or [
            [graph.nodes[source]["lng"], graph.nodes[source]["lat"]],
            [graph.nodes[target]["lng"], graph.nodes[target]["lat"]],
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "mode": mode,
                    "heat_score": round(float(attrs["heat_score"]), 3),
                    "distance_m": round(float(attrs["distance_m"]), 1),
                    "temperature": round(float(attrs["temperature"]), 2),
                    "uv": round(float(attrs.get("uv", 0.0)), 3),
                    "shade_ratio": round(float(attrs["shade_ratio"]), 3),
                    "wind": round(float(attrs["wind"]), 3),
                    "ground_temp": round(float(attrs["ground_temp"]), 2),
                    "shelter_name": attrs.get("shelter_name"),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def unique_shelters(edge_attrs: list[dict], graph: nx.Graph) -> list[dict]:
    shelters = []
    seen = set()
    for attrs in edge_attrs:
        name = attrs.get("shelter_name")
        node_id = attrs.get("shelter_node")
        if not name or not node_id or name in seen:
            continue
        seen.add(name)
        shelters.append(
            {
                "name": name,
                "lat": graph.nodes[node_id]["lat"],
                "lng": graph.nodes[node_id]["lng"],
                "operating_hours": attrs.get("shelter_operating_hours") or "09:00-18:00",
            }
        )
    return shelters
