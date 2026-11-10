"""Portable backup and restore of the whole BrandVault database.

Works the same on SQLite and PostgreSQL, so a backup can move between them.

    python -m backend.scripts.backup create  backups/brandvault-2026-11-10.json.gz
    python -m backend.scripts.backup verify  backups/brandvault-2026-11-10.json.gz
    python -m backend.scripts.backup restore backups/brandvault-2026-11-10.json.gz   # empty database only

The database comes from DATABASE_URL (or --url). Binary columns (uploaded files)
are stored as base64. Restore refuses to write into a database that already has
users, so it can never overwrite live data by mistake.

On Neon, point-in-time restore is also available in the Neon console; this file
is an extra copy you control (keep it encrypted and off the server).
"""
from __future__ import annotations

import argparse
import base64
import datetime
import decimal
import gzip
import hashlib
import json
import os
import sys

from sqlalchemy import create_engine, insert, select, text

FORMAT = "brandvault-backup/1"


def _enc(v):
    if isinstance(v, (bytes, bytearray, memoryview)):
        return {"$b64": base64.b64encode(bytes(v)).decode("ascii")}
    if isinstance(v, datetime.datetime):
        return {"$dt": v.isoformat()}
    if isinstance(v, datetime.date):
        return {"$d": v.isoformat()}
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def _dec(v):
    if isinstance(v, dict) and len(v) == 1:
        k = next(iter(v))
        if k == "$b64":
            return base64.b64decode(v[k])
        if k == "$dt":
            return datetime.datetime.fromisoformat(v[k])
        if k == "$d":
            return datetime.date.fromisoformat(v[k])
    return v


def _metadata():
    import backend.app.models  # noqa: F401 - registers every table
    from backend.app.db.base import Base
    return Base.metadata


def create(url: str, path: str) -> dict:
    md = _metadata()
    eng = create_engine(url)
    counts = {}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with eng.connect() as conn, gzip.open(path, "wt", encoding="utf-8") as out:
        out.write(json.dumps({"format": FORMAT, "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                              "dialect": eng.dialect.name}) + "\n")
        for t in md.sorted_tables:
            try:
                rows = conn.execute(select(t)).mappings()
            except Exception:  # table missing in this database
                conn.rollback()
                continue
            n = 0
            for r in rows:
                out.write(json.dumps({"t": t.name, "r": {k: _enc(v) for k, v in r.items()}}, default=str) + "\n")
                n += 1
            counts[t.name] = n
        out.write(json.dumps({"end": True, "counts": counts}) + "\n")
    return counts


def verify(path: str) -> dict:
    counts, seen, ended = {}, {}, None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        head = json.loads(f.readline())
        if head.get("format") != FORMAT:
            raise SystemExit(f"Not a BrandVault backup: {path}")
        for line in f:
            rec = json.loads(line)
            if rec.get("end"):
                ended = rec["counts"]
                break
            seen[rec["t"]] = seen.get(rec["t"], 0) + 1
    if ended is None:
        raise SystemExit("Backup is incomplete (no end marker).")
    for k, v in ended.items():
        if v and seen.get(k, 0) != v:
            raise SystemExit(f"Table {k}: expected {v} rows, found {seen.get(k, 0)}.")
    counts.update(ended)
    return counts


def restore(url: str, path: str) -> dict:
    verify(path)
    md = _metadata()
    eng = create_engine(url)
    md.create_all(eng)
    with eng.connect() as conn:
        if conn.execute(text("SELECT COUNT(*) FROM users")).scalar():
            raise SystemExit("This database already has users. Restore only into an empty database.")
    tables = {t.name: t for t in md.sorted_tables}
    batch: dict = {}
    counts: dict = {}
    order = [t.name for t in md.sorted_tables]
    with gzip.open(path, "rt", encoding="utf-8") as f:
        f.readline()
        for line in f:
            rec = json.loads(line)
            if rec.get("end"):
                break
            if rec["t"] in tables:
                cols = set(tables[rec["t"]].c.keys())
                batch.setdefault(rec["t"], []).append({k: _dec(v) for k, v in rec["r"].items() if k in cols})
    with eng.begin() as conn:
        for name in order:
            rows = batch.get(name)
            if rows:
                conn.execute(insert(tables[name]), rows)
                counts[name] = len(rows)
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["create", "verify", "restore"])
    ap.add_argument("path")
    ap.add_argument("--url", default=os.getenv("DATABASE_URL", "sqlite:///./brandvault.db"))
    a = ap.parse_args(argv)
    if a.url.startswith("postgres://"):
        a.url = "postgresql://" + a.url[len("postgres://"):]
    if a.url.startswith("postgresql://"):
        a.url = "postgresql+psycopg://" + a.url[len("postgresql://"):]
    if a.command == "create":
        counts = create(a.url, a.path)
    elif a.command == "verify":
        counts = verify(a.path)
    else:
        counts = restore(a.url, a.path)
    digest = hashlib.sha256(open(a.path, "rb").read()).hexdigest()[:16]
    print(f"{a.command}: {sum(counts.values())} rows in {len([c for c in counts.values() if c])} tables  (file sha256 {digest}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
