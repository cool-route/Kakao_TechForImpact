import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve().parents[1]


def _free_local_port() -> int:
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except OSError as exc:
        pytest.skip(f"localhost sockets are not available in this environment: {exc}")


@pytest.fixture(scope="module")
def api_base_url():
    port = _free_local_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"

    try:
        deadline = time.time() + 10
        last_error = None
        while time.time() < deadline:
            try:
                _request_json("GET", f"{base_url}/healthcheck")
                break
            except (OSError, urllib.error.URLError) as exc:
                last_error = exc
                time.sleep(0.2)
        else:
            pytest.skip(f"API server did not become reachable: {last_error}")

        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def _request_json(method: str, url: str, payload: dict | None = None) -> tuple[int, dict | list]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_healthcheck_http(api_base_url):
    status, body = _request_json("GET", f"{api_base_url}/healthcheck")

    assert status == 200
    assert body == {"status": "ok"}


def test_post_route_http(api_base_url):
    status, body = _request_json(
        "POST",
        f"{api_base_url}/route",
        {
            "mode": "일반",
            "start": [37.3219, 127.0972],
            "end": [37.3247, 127.1245],
        },
    )

    assert status == 200
    assert body["path"]["type"] == "FeatureCollection"
    assert body["heat_score_avg"] > 0
    assert body["distance_m"] > 0
    assert "is_dummy" in body


def test_get_routes_http(api_base_url):
    status, body = _request_json("GET", f"{api_base_url}/routes")

    assert status == 200
    assert len(body) == 13
    assert {"id", "name", "mode", "heat_score_avg", "distance_m", "geojson", "shelters", "is_dummy"} <= set(body[0])


def test_get_routes_by_mode_http(api_base_url):
    status, body = _request_json("GET", f"{api_base_url}/routes?mode=%EB%85%B8%EC%95%BD%EC%9E%90")

    assert status == 200
    assert len(body) == 5
    assert all(route["mode"] == "노약자" for route in body)
