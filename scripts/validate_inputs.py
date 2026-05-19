from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.services.geojson_loader import load_graph_from_geojson, load_shelters
from app.services.routing import load_route_specs


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate backend input files without DB.")
    parser.add_argument("--nodes", default="data/sample/nodes_with_score.geojson")
    parser.add_argument("--shelters", default="data/sample/shelters.json")
    parser.add_argument("--routes", default="data/route_specs.json")
    args = parser.parse_args()

    graph = load_graph_from_geojson(Path(args.nodes))
    shelters = load_shelters(Path(args.shelters))
    route_specs = load_route_specs(Path(args.routes))

    print(f"nodes: {graph.number_of_nodes()}")
    print(f"edges: {graph.number_of_edges()}")
    print(f"shelters: {len(shelters)}")
    print(f"route_specs: {len(route_specs)}")
    print("validation: ok")


if __name__ == "__main__":
    main()
