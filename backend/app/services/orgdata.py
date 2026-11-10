"""Everything one organisation owns in the database: for data export and erasure.

A table belongs to the organisation when it has an ``org_id`` column (or is
``organizations`` itself). Tables without one are included through their
foreign keys to rows already collected (for example guideline chunks through
their guideline). Credential material is never exported.
"""
from __future__ import annotations

import base64
import datetime
import decimal
import io
import json
import zipfile
from typing import Dict, List, Set

from sqlalchemy import Table, delete, select
from sqlalchemy.orm import Session

from backend.app.db.base import Base

# Never leaves the server, not even in the organisation's own export.
REDACT = {"password_hash", "salt", "mfa_secret", "token_hash", "key_hash", "secret", "p256dh", "auth"}
# Shared/server tables that are never part of one organisation's data.
SKIP = {"rate_limit_counters", "server_settings"}


def _plan(org_id: str) -> List[tuple]:
    """(table, where-clause builder) in dependency order."""
    return [t for t in Base.metadata.sorted_tables if t.name not in SKIP]


def _jsonable(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return {"bytes": len(bytes(v))}
    return v


def collect_ids(db: Session, org_id: str) -> Dict[str, Set]:
    """Primary keys of every row the organisation owns, per table."""
    owned: Dict[str, Set] = {}
    tables = _plan(org_id)
    for _ in range(3):  # a few passes reach grandchildren (submission -> finding -> ...)
        changed = False
        for t in tables:
            pk = list(t.primary_key.columns)
            if len(pk) != 1:
                continue
            pkc = pk[0]
            conds = []
            if t.name == "organizations":
                conds.append(pkc == org_id)
            elif "org_id" in t.c:
                conds.append(t.c.org_id == org_id)
            else:
                for fk in t.foreign_keys:
                    parent = fk.column.table.name
                    if owned.get(parent):
                        conds.append(fk.parent.in_(list(owned[parent])))
            if not conds:
                continue
            ids = set()
            for c in conds:
                ids |= {r[0] for r in db.execute(select(pkc).where(c))}
            if ids - owned.get(t.name, set()):
                owned.setdefault(t.name, set()).update(ids)
                changed = True
        if not changed:
            break
    return owned


def export_zip(db: Session, org_id: str, include_files: bool = True) -> bytes:
    """A ZIP with data.json (every owned row, secrets removed) and, optionally, uploaded files."""
    owned = collect_ids(db, org_id)
    data: Dict[str, list] = {}
    files: List[tuple] = []
    for t in _plan(org_id):
        ids = owned.get(t.name)
        if not ids:
            continue
        pkc = list(t.primary_key.columns)[0]
        rows = []
        for r in db.execute(select(t).where(pkc.in_(list(ids)))).mappings():
            row = {k: ("[removed]" if k in REDACT and v else _jsonable(v)) for k, v in r.items()}
            if t.name == "stored_files" and include_files and r.get("data") is not None:
                files.append((f"files/{r['id']}", bytes(r["data"])))
                row["file"] = f"files/{r['id']}"
            rows.append(row)
        data[t.name] = rows
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        meta = {"organisation": org_id, "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
                "tables": {k: len(v) for k, v in data.items()},
                "note": "Passwords, two-step secrets, API-key hashes and webhook secrets are never exported."}
        z.writestr("README.json", json.dumps(meta, indent=2))
        z.writestr("data.json", json.dumps(data, indent=1, default=str))
        for name, blob in files:
            z.writestr(name, blob)
    return buf.getvalue()


def counts(db: Session, org_id: str) -> Dict[str, int]:
    return {k: len(v) for k, v in collect_ids(db, org_id).items()}


def erase(db: Session, org_id: str) -> Dict[str, int]:
    """Delete every row the organisation owns (children first). The caller commits."""
    owned = collect_ids(db, org_id)
    removed: Dict[str, int] = {}
    for t in reversed(_plan(org_id)):
        ids = owned.get(t.name)
        if not ids:
            continue
        pkc = list(t.primary_key.columns)[0]
        res = db.execute(delete(t).where(pkc.in_(list(ids))))
        removed[t.name] = res.rowcount or 0
    # Security events and errors may have been written without a foreign key; remove those too.
    for name in ("security_events", "error_events"):
        t: Table = Base.metadata.tables.get(name)  # type: ignore[assignment]
        if t is not None:
            res = db.execute(delete(t).where(t.c.org_id == org_id))
            if res.rowcount:
                removed[name] = removed.get(name, 0) + res.rowcount
    return removed
