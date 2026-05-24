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

    assert len(all_routes) == 15
    assert len(elderly_routes) == 15
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
        assert route["geojson"]["type"] == "FeatureCollection"


def test_shelter_routes_have_shelters():
    routes = get_recommended_routes()
    shelter_routes = [r for r in routes if "쉼터 경유" in r["name"]]
    assert len(shelter_routes) > 0
    for r in shelter_routes:
        assert len(r["shelters"]) > 0


def test_elderly_route_includes_shelter_when_available():
    result = shortest_cool_route("노약자", START, END)

    assert isinstance(result["shelters"], list)
