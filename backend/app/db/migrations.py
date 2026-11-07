"""
Lightweight, idempotent schema migrations for the SQLite persistence layer.

SQLAlchemy's `create_all` creates *missing tables* but never alters existing
ones, so new columns added to a model are invisible on a database that was
created by an earlier version. This helper performs additive `ALTER TABLE ...
ADD COLUMN` statements guarded by a PRAGMA check, which is safe to run on every
startup. It is intentionally minimal — for a production Postgres target this is
replaced by Alembic (see IMPLEMENTATION_ROADMAP.md, Milestone G).
"""
import re
from sqlalchemy import text
from sqlalchemy.engine import Engine

# (table, column, column definition) tuples to ensure exist.
_ADDITIVE_COLUMNS = [
    ("approved_facts", "valid_until", "DATETIME"),
    ("approved_facts", "superseded_by", "TEXT"),
    ("agent_runs", "execution_time_us", "INTEGER"),
    ("findings", "analysis_engine", "TEXT DEFAULT 'heuristic'"),
    ("users", "auth_provider", "TEXT DEFAULT 'password'"),
    ("users", "google_sub", "TEXT"),
    # Phase 1a — tenant-scoped agent runs + version-locked approvals.
    ("agent_runs", "org_id", "VARCHAR(36)"),
    ("approval_records", "submission_version", "INTEGER"),
    ("approval_records", "content_hash", "VARCHAR(64)"),
]


def _existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return {r[1] for r in rows}


_PAGE_MARKER = re.compile(r"---\s*Page\s+(\d+)\s*---")


def fix_chunk_page_numbers(engine: Engine) -> int:
    """Data fix: older uploads stored a chunk's page as (paragraph index // 3) + 1.
    Where the chunk text carries its real "--- Page N ---" marker, use that.
    Idempotent; returns the number of rows corrected."""
    fixed = 0
    with engine.begin() as conn:
        try:
            rows = conn.execute(text("SELECT id, page_number, content FROM document_chunks")).fetchall()
        except Exception:  # table not created yet
            return 0
        for cid, page, content in rows:
            m = _PAGE_MARKER.search(content or "")
            if m and int(m.group(1)) != page:
                conn.execute(text("UPDATE document_chunks SET page_number = :p WHERE id = :i"),
                             {"p": int(m.group(1)), "i": cid})
                fixed += 1
    return fixed


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
