import sqlite3

from app.models import db
from scripts.seed_routes import seed_routes


def test_seed_routes_inserts_thirteen_routes(tmp_path, monkeypatch):
    db_path = tmp_path / "cool_routes.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)

    count = seed_routes()

    with sqlite3.connect(db_path) as conn:
        stored_count = conn.execute("SELECT COUNT(*) FROM routes").fetchone()[0]

    assert count == 13
    assert stored_count == 13
