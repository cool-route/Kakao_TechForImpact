from app.main import healthcheck
from app.api.routes import create_route, list_routes
from app.schemas.routes import RouteRequest


def test_healthcheck():
    assert healthcheck() == {"status": "ok"}


def test_post_route_handler():
    result = create_route(
        RouteRequest(
            mode="노약자",
            start=(37.3219, 127.0972),
            end=(37.3247, 127.1245),
        )
    )

    assert result["path"]["type"] == "FeatureCollection"
    assert result["distance_m"] > 0


def test_get_routes_handler_returns_five():
    routes = list_routes(mode=None)

    assert len(routes) == 14
    assert all(route["mode"] == "노약자" for route in routes)
