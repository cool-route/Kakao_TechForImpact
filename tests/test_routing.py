from app.services.routing import get_recommended_routes, load_route_specs, shortest_cool_route


START = (37.3219, 127.0972)
END = (37.3247, 127.1245)


def coordinates(result):
    return [
        tuple(coord)
        for feature in result["path"]["features"]
        for coord in feature["geometry"]["coordinates"]
    ]


def test_shortest_cool_route_returns_geojson():
    result = shortest_cool_route("일반", START, END)

    assert result["path"]["type"] == "FeatureCollection"
    assert result["path"]["features"]
    assert result["heat_score_avg"] > 0
    assert result["distance_m"] > 0


def test_modes_can_return_different_paths():
    elderly = coordinates(shortest_cool_route("노약자", START, END))
    pet = coordinates(shortest_cool_route("반려동물", START, END))
    general = coordinates(shortest_cool_route("일반", START, END))

    assert len({tuple(elderly), tuple(pet), tuple(general)}) >= 2


def test_recommended_routes_count_and_filtering():
    all_routes = get_recommended_routes()
    elderly_routes = get_recommended_routes("노약자")

    assert len(all_routes) == 13
    assert len(elderly_routes) == 5
    assert all(route["mode"] == "노약자" for route in elderly_routes)


def test_route_specs_are_fixed_to_thirteen_routes():
    specs = load_route_specs()

    assert len(specs) == 13
    assert [spec["id"] for spec in specs] == list(range(1, 14))
    assert sum(1 for spec in specs if spec["mode"] == "노약자") == 5
    assert sum(1 for spec in specs if spec["mode"] == "반려동물") == 5
    assert sum(1 for spec in specs if spec["mode"] == "일반") == 3


def test_elderly_route_includes_shelter_when_available():
    result = shortest_cool_route("노약자", START, END)

    assert isinstance(result["shelters"], list)
    assert len(result["shelters"]) > 0


def test_pet_route_avoids_hot_ground_segments_when_possible():
    result = shortest_cool_route("반려동물", START, END)

    ground_temps = [
        feature["properties"]["ground_temp"]
        for feature in result["path"]["features"]
    ]
    # 실데이터에서 고온 세그먼트 전부 회피 불가 시 fallback 허용
    avg_ground_temp = sum(ground_temps) / len(ground_temps)
    assert avg_ground_temp < 40.0
