# Performance

## What Is Cached

- Routing graph: loaded once from real GeoJSON files, then reused in memory.
- Recommended routes: `GET /routes` and `GET /routes?mode=...` results are cached by mode after the first calculation.

The first request after server startup may be slower because it loads files and builds the graph. Later requests measure steady-state API latency.

## Local Benchmark

Start the API:

```bash
python3 run_server.py
```

Run the benchmark:

```bash
python3 scripts/benchmark_api.py --base-url http://127.0.0.1:8000 --iterations 20
```

The script measures:

- `GET /healthcheck`
- `POST /route`
- `GET /routes`
- `GET /routes?mode=노약자`

## Result Format

The benchmark prints JSON:

```json
[
  {
    "endpoint": "GET /routes",
    "iterations": 20,
    "min_ms": 0.0,
    "avg_ms": 0.0,
    "p95_ms": 0.0,
    "max_ms": 0.0
  }
]
```

Replace the sample values with measured results when sharing final performance numbers.

## Local Sample Result

Measured with:

```bash
python3 scripts/benchmark_api.py --base-url http://127.0.0.1:8765 --iterations 5
```

Sample result from the current development environment:

```json
[
  {"endpoint": "GET /healthcheck", "iterations": 5, "min_ms": 0.7, "avg_ms": 0.76, "p95_ms": 0.81, "max_ms": 0.82},
  {"endpoint": "POST /route", "iterations": 5, "min_ms": 5.18, "avg_ms": 5.23, "p95_ms": 5.24, "max_ms": 5.26},
  {"endpoint": "GET /routes", "iterations": 5, "min_ms": 6.62, "avg_ms": 9.57, "p95_ms": 6.78, "max_ms": 20.89},
  {"endpoint": "GET /routes?mode=노약자", "iterations": 5, "min_ms": 3.21, "avg_ms": 3.26, "p95_ms": 3.31, "max_ms": 3.33}
]
```
