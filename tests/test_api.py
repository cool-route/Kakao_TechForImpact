from app.main import healthcheck
from app.routers.route import RouteRequest, create_route, list_routes


def test_healthcheck():
    assert healthcheck() == {"status": "ok"}


def test_post_route_handler():
    result = create_route(
        RouteRequest(
            mode="일반",
            start=(37.3219, 127.0972),
            end=(37.3247, 127.1245),
        )
    )

    assert result["path"]["type"] == "FeatureCollection"
    assert result["distance_m"] > 0


def test_get_routes_by_mode_handler():
    routes = list_routes(mode="반려동물")

    assert len(routes) == 5
    assert all(route["mode"] == "반려동물" for route in routes)
