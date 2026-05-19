from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.request


ROUTE_PAYLOAD = {
    "mode": "일반",
    "start": [37.3219, 127.0972],
    "end": [37.3247, 127.1245],
}


def request_json(method: str, url: str, payload: dict | None = None) -> object:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def measure(label: str, method: str, url: str, payload: dict | None, iterations: int) -> dict:
    durations = []
    for _ in range(iterations):
        started = time.perf_counter()
        request_json(method, url, payload)
        durations.append((time.perf_counter() - started) * 1000)

    return {
        "endpoint": label,
        "iterations": iterations,
        "min_ms": round(min(durations), 2),
        "avg_ms": round(statistics.mean(durations), 2),
        "p95_ms": round(sorted(durations)[math.ceil(iterations * 0.95) - 1], 2),
        "max_ms": round(max(durations), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark local Cool Route API endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")

    base_url = args.base_url.rstrip("/")
    endpoints = [
        ("GET /healthcheck", "GET", f"{base_url}/healthcheck", None),
        ("POST /route", "POST", f"{base_url}/route", ROUTE_PAYLOAD),
        ("GET /routes", "GET", f"{base_url}/routes", None),
        ("GET /routes?mode=노약자", "GET", f"{base_url}/routes?mode=%EB%85%B8%EC%95%BD%EC%9E%90", None),
    ]

    # Warm up graph and recommendation caches before measuring steady-state latency.
    for _label, method, url, payload in endpoints:
        request_json(method, url, payload)

    results = [
        measure(label, method, url, payload, args.iterations)
        for label, method, url, payload in endpoints
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
