from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.models.db import get_connection, init_db
from app.services.routing import get_recommended_routes


def seed_routes() -> int:
    init_db()
    routes = get_recommended_routes()
    with get_connection() as conn:
        conn.execute("DELETE FROM routes")
        conn.executemany(
            """
            INSERT INTO routes (name, mode, heat_score_avg, distance_m, geojson)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    route["name"],
                    route["mode"],
                    route["heat_score_avg"],
                    route["distance_m"],
                    json.dumps(route["geojson"], ensure_ascii=False),
                )
                for route in routes
            ],
        )
    return len(routes)


def main() -> None:
    count = seed_routes()
    print(f"seeded routes: {count}")


if __name__ == "__main__":
    main()
