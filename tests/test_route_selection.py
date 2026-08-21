from app.services.route_service import select_top_k_routes


def make_route(id, heat, dist, shelters_count, shade):
    # build a minimal route dict used by the selector
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[127.0, 37.0], [127.1, 37.1]]},
                "properties": {"shade_ratio": shade, "ground_temp": 28.0, "heat_score": heat, "distance_m": dist},
            }
        ],
    }
    shelters = [{"name": "shelter", "lat": 0.0, "lng": 0.0}] * shelters_count
    return {"id": id, "name": f"r{id}", "mode": "노약자", "heat_score_avg": heat, "distance_m": dist, "geojson": geojson, "shelters": shelters, "is_dummy": True}


def test_select_top_k_returns_three_and_tags(monkeypatch):
    routes = [
        make_route(1, 21.0, 800, 2, 0.55),
        make_route(2, 24.0, 2500, 0, 0.2),
        make_route(3, 22.0, 1200, 1, 0.4),
        make_route(4, 23.5, 4000, 0, 0.1),
        make_route(5, 20.5, 600, 3, 0.6),
    ]

    # monkeypatch the source used by selector
    import app.services.route_service as rs

    monkeypatch.setattr(rs, "get_recommended_routes", lambda mode=None: routes)

    top = select_top_k_routes(preferred_tags=None, k=3, mode=None)

    assert isinstance(top, list)
    assert len(top) == 3
    for r in top:
        assert "tags" in r
        assert "match_score" in r
        assert any(tag.startswith("walk_") for tag in r["tags"])


def test_select_top_k_prefers_given_tag(monkeypatch):
    r_with = make_route(10, 21.0, 800, 2, 0.5)
    r_without = make_route(11, 21.0, 800, 0, 0.2)

    import app.services.route_service as rs
    monkeypatch.setattr(rs, "get_recommended_routes", lambda mode=None: [r_with, r_without])

    top = select_top_k_routes(preferred_tags=["shelter_route"], k=2, mode=None)

    assert len(top) == 2
    # first result should include the preferred tag
    assert "shelter_route" in top[0]["tags"]


def test_select_top_k_respects_mode_filter(monkeypatch):
    # Ensure mode argument is forwarded to get_recommended_routes
    def fake_get(mode=None):
        if mode == "노약자":
            return [make_route(20, 22.0, 1000, 1, 0.4)]
        return []

    import app.services.route_service as rs
    monkeypatch.setattr(rs, "get_recommended_routes", fake_get)

    top = select_top_k_routes(preferred_tags=None, k=3, mode="노약자")
    assert len(top) == 1
