"""
Lightweight, idempotent schema migrations (SQLite for local use, PostgreSQL in production).

SQLAlchemy's `create_all` creates *missing tables* but never alters existing
ones, so new columns added to a model are invisible on a database that was
created by an earlier version. This helper performs additive `ALTER TABLE ...
ADD COLUMN` statements guarded by an inspector check, which is safe to run on
every startup for both SQLite and PostgreSQL.
"""
import re
from sqlalchemy import inspect, text
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
    # Phase 2 — department analytics.
    ("submissions", "department", "VARCHAR(100)"),
    # Round 3 — section citations and guideline version history.
    ("document_chunks", "section_label", "VARCHAR(120)"),
    ("brand_guidelines", "superseded_by_id", "VARCHAR(36)"),
    ("brand_guidelines", "superseded_at", "DATETIME"),
]


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
    """Apply additive column migrations on SQLite and PostgreSQL. Returns the applied changes.

    Only ever ADDs missing columns, so it is safe to run on every startup and never
    touches existing data. New tables are created by ``Base.metadata.create_all``.
    """
    applied: list[str] = []
    is_sqlite = engine.url.get_backend_name().startswith("sqlite")
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, coltype in _ADDITIVE_COLUMNS:
            if table not in tables:
                continue  # create_all builds it with every column
            existing = {c["name"] for c in insp.get_columns(table)}
            if column in existing:
                continue
            ddl = coltype if is_sqlite else coltype.replace("DATETIME", "TIMESTAMP")
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {ddl}'))
            applied.append(f"{table}.{column}")
    return applied
