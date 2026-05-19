from pathlib import Path

import pytest

from app.services.geojson_loader import load_graph_from_geojson, load_shelters


BASE_DIR = Path(__file__).resolve().parents[1]


def test_load_graph_from_geojson_sample():
    graph = load_graph_from_geojson(BASE_DIR / "data/sample/nodes_with_score.geojson")

    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 3
    assert graph.nodes["library"]["lat"] == 37.3232
    assert graph.edges["suji_office", "library"]["heat_score"] == 0.32
    assert graph.edges["suji_office", "library"]["distance_m"] > 0


def test_load_shelters_sample():
    shelters = load_shelters(BASE_DIR / "data/sample/shelters.json")

    assert len(shelters) == 2
    assert shelters[0]["name"] == "수지도서관"
    assert shelters[0]["lat"] == 37.3232


def test_load_graph_rejects_missing_required_properties(tmp_path):
    invalid_geojson = tmp_path / "invalid.geojson"
    invalid_geojson.write_text(
        """
        {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "geometry": {
                "type": "LineString",
                "coordinates": [[127.0972, 37.3219], [127.101, 37.3232]]
              },
              "properties": {
                "source": "a",
                "target": "b"
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required properties"):
        load_graph_from_geojson(invalid_geojson)
