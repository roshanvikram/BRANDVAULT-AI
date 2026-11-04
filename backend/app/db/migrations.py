"""
Lightweight, idempotent schema migrations for the SQLite persistence layer.

SQLAlchemy's `create_all` creates *missing tables* but never alters existing
ones, so new columns added to a model are invisible on a database that was
created by an earlier version. This helper performs additive `ALTER TABLE ...
ADD COLUMN` statements guarded by a PRAGMA check, which is safe to run on every
startup. It is intentionally minimal — for a production Postgres target this is
replaced by Alembic (see IMPLEMENTATION_ROADMAP.md, Milestone G).
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# (table, column, column definition) tuples to ensure exist.
_ADDITIVE_COLUMNS = [
    ("approved_facts", "valid_until", "DATETIME"),
    ("approved_facts", "superseded_by", "TEXT"),
    ("agent_runs", "execution_time_us", "INTEGER"),
]


def _existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return {r[1] for r in rows}


def run_light_migrations(engine: Engine) -> list[str]:
    """Apply additive column migrations. Returns a list of applied changes."""
    applied: list[str] = []
    # Only SQLite needs this shim; real engines use Alembic migrations.
    if not engine.url.get_backend_name().startswith("sqlite"):
        return applied

    with engine.begin() as conn:
        for table, column, coltype in _ADDITIVE_COLUMNS:
            # Skip if the table itself does not exist yet (create_all handles it).
            table_exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                {"t": table},
            ).first()
            if not table_exists:
                continue
            if column not in _existing_columns(conn, table):
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {coltype}'))
                applied.append(f"{table}.{column}")
    return applied
