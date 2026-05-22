from app.services.route_service import get_recommended_routes, load_route_specs, shortest_cool_route


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

    assert len(all_routes) == 5
    assert len(elderly_routes) == 5
    assert all(route["mode"] == "노약자" for route in elderly_routes)


def test_route_specs_are_five_elderly_routes():
    specs = load_route_specs()

    assert len(specs) == 5
    assert [spec["id"] for spec in specs] == list(range(1, 6))
    assert all(spec["mode"] == "노약자" for spec in specs)


def test_elderly_route_includes_shelter_when_available():
    result = shortest_cool_route("노약자", START, END)

    assert isinstance(result["shelters"], list)
    assert len(result["shelters"]) > 0
