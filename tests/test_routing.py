from app.services.route_service import get_recommended_routes, shortest_cool_route


START = (37.3219, 127.0972)
END = (37.3247, 127.1245)


def test_shortest_cool_route_returns_geojson():
    result = shortest_cool_route("노약자", START, END)

    assert result["path"]["type"] == "FeatureCollection"
    assert result["path"]["features"]
    assert result["heat_score_avg"] > 0
    assert result["distance_m"] > 0


def test_recommended_routes_count_and_filtering():
    all_routes = get_recommended_routes()
    elderly_routes = get_recommended_routes("노약자")

    assert len(all_routes) == 80
    assert len(elderly_routes) == 80
    assert all(route["mode"] == "노약자" for route in elderly_routes)


def test_recommended_routes_have_required_fields():
    routes = get_recommended_routes()
    for route in routes:
        assert "id" in route
        assert "name" in route
        assert "mode" in route
        assert "heat_score_avg" in route
        assert "distance_m" in route
        assert "geojson" in route
        assert "shelters" in route
        assert "tags" in route
        assert route["geojson"]["type"] == "FeatureCollection"
        assert any(tag.startswith("walk_") for tag in route["tags"])
        assert any(tag in {"pungdeokcheon_1", "pungdeokcheon_2", "sinbong", "seongbok", "dongcheon", "sanghyeon_1", "sanghyeon_2", "sanghyeon_3", "jukjeon_1", "jukjeon_2", "jukjeon_3"} for tag in route["tags"])


def test_recommended_routes_have_id_tags():
    routes = get_recommended_routes()
    for route in routes:
        assert all(not tag.startswith(" ") for tag in route["tags"])
        assert all(isinstance(tag, str) for tag in route["tags"])
        assert "with_elder" in route["tags"]
        assert any(tag in {"cool_path", "shelter_route", "shelter_rich", "low_tmrt", "shady_path", "green_path", "flat_path", "quiet_path", "low_surface_temp", "low_heat_island", "mobility_support"} for tag in route["tags"])


def test_elderly_route_includes_shelter_when_available():
    result = shortest_cool_route("노약자", START, END)

    assert isinstance(result["shelters"], list)
