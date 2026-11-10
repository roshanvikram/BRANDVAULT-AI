"""Database-level tenant isolation (PostgreSQL Row-Level Security).

The application already filters every query by organisation. Row-Level Security
adds a second, independent guard inside the database: a policy on every tenant
table only lets a transaction see or write rows whose ``org_id`` matches the
organisation set for that transaction. A query that forgot its filter still
cannot read another organisation's data.

How the organisation is set: after a user (bearer token) or an API key is
authenticated, ``set_tenant`` stores the org on the SQLAlchemy session, and every
transaction that session begins runs ``set_config('app.org_id', <org>, true)``.
The setting is transaction-local, so it never leaks to another request through
the connection pool. Work with no tenant (startup seeding, background jobs,
sign-in itself) runs with the setting empty, which the policy allows.

Policies use FORCE ROW LEVEL SECURITY so they also apply to the table owner
(the usual app role on Neon/Supabase). PostgreSQL superusers always bypass RLS,
so production should connect with a normal (non-superuser) role.
SQLite has no RLS; there the application-level filters remain the guard.
Set RLS_ENABLED=false to skip creating the policies.
"""
from __future__ import annotations

import contextvars
import logging
import os
from typing import List, Optional

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

log = logging.getLogger("brandvault.rls")

SETTING = "app.org_id"
POLICY = "bv_tenant_isolation"
_CTX = "current_setting('app.org_id', true)"
# The organisation of the request being served (for error reports and logs).
current_org: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("bv_current_org", default=None)


def _condition(column: str) -> str:
    return f"(coalesce({_CTX}, '') = '' OR {column} = {_CTX})"


def tenant_tables(engine: Engine) -> List[tuple]:
    """(table, column) pairs to protect: every table with an org_id, plus organizations.id."""
    insp = inspect(engine)
    out = []
    for t in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns(t)}
        if "org_id" in cols:
            out.append((t, "org_id"))
        elif t == "organizations":
            out.append((t, "id"))
    return out


def enable(engine: Engine) -> int:
    """Create or refresh the policies. Returns how many tables are protected (0 if not PostgreSQL)."""
    if engine.dialect.name != "postgresql" or os.getenv("RLS_ENABLED", "true").lower() == "false":
        return 0
    tables = tenant_tables(engine)
    with engine.begin() as conn:
        for table, column in tables:
            q = f'"{table}"'
            cond = _condition(f'"{column}"')
            conn.execute(text(f"ALTER TABLE {q} ENABLE ROW LEVEL SECURITY"))
            conn.execute(text(f"ALTER TABLE {q} FORCE ROW LEVEL SECURITY"))
            conn.execute(text(f"DROP POLICY IF EXISTS {POLICY} ON {q}"))
            conn.execute(text(f"CREATE POLICY {POLICY} ON {q} USING {cond} WITH CHECK {cond}"))
    log.info("Row-Level Security enabled on %d tables", len(tables))
    return len(tables)


def set_tenant(db: Session, org_id: str) -> None:
    """Scope this session's database work to one organisation (no-op on SQLite)."""
    db.info["bv_org"] = org_id
    current_org.set(org_id)
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        db.execute(text("SELECT set_config(:k, :v, true)"), {"k": SETTING, "v": org_id})


@event.listens_for(Session, "after_begin")
def _apply_tenant(session: Session, transaction, connection) -> None:
    org = session.info.get("bv_org")
    if org and connection.dialect.name == "postgresql":
        connection.execute(text("SELECT set_config(:k, :v, true)"), {"k": SETTING, "v": org})
