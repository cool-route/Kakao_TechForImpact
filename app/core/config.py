from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

MODES = ("노약자",)
NODES_PATH = DATA_DIR / "nodes_with_score.geojson"
EDGES_PATH = DATA_DIR / "sujiku_edges.geojson"
SHELTERS_PATH = DATA_DIR / "shelters.json"
LEGACY_GRAPH_PATH = DATA_DIR / "geojson/nodes_with_score.geojson"
ROUTE_SPECS_PATH = DATA_DIR / "route_specs.json"
