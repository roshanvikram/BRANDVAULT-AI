"""Turn uploaded files into a list of pieces of copy to check in one go.

* CSV / XLSX: one row per piece. The copy column is found by its header
  (content, copy, text, body, message, caption, description); the title from
  title, name, campaign, headline or subject; the team from department, team or channel.
* TXT / MD: pieces separated by a line containing only --- (or one piece per file).
* DOCX / PDF / HTML: the whole document is one piece.
"""
from __future__ import annotations

import csv
import io
import os
import re
from typing import Dict, List

from backend.app.services import ingest

MAX_ITEMS = 200
MAX_CHARS = 20_000

_CONTENT = ("content", "copy", "text", "body", "message", "caption", "description", "ad copy", "post")
_TITLE = ("title", "name", "campaign", "headline", "subject")
_DEPT = ("department", "team", "channel")
_SEP = re.compile(r"^\s*(-{3,}|={3,})\s*$", re.M)


class BulkError(ValueError):
    pass


def _col(header: List[str], names) -> int:
    h = [c.strip().lower() for c in header]
    for n in names:
        if n in h:
            return h.index(n)
    for i, c in enumerate(h):
        if any(n in c for n in names):
            return i
    return -1


def _title_from(text: str, fallback: str) -> str:
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    first = re.sub(r"^(subject|title|headline)\s*:\s*", "", first, flags=re.I)
    return (first[:80] + ("…" if len(first) > 80 else "")) if first else fallback


def from_rows(rows: List[List[str]], source: str) -> List[Dict]:
    rows = [[(c or "").strip() for c in r] for r in rows if any((c or "").strip() for c in r)]
    if len(rows) < 2:
        raise BulkError(f"{source}: needs a header row and at least one row of copy.")
    header = rows[0]
    ci, ti, di = _col(header, _CONTENT), _col(header, _TITLE), _col(header, _DEPT)
    if ci < 0:
        raise BulkError(f"{source}: no copy column found. Name one column Content, Copy or Text.")
    out = []
    for n, r in enumerate(rows[1:], start=2):
        text = r[ci] if ci < len(r) else ""
        if not text:
            continue
        title = (r[ti] if 0 <= ti < len(r) else "") or _title_from(text, f"{source} row {n}")
        out.append({"title": title[:200], "content": text, "department": (r[di] if 0 <= di < len(r) else "")[:100],
                    "source": f"{source} row {n}"})
    return out


def from_text(text: str, source: str) -> List[Dict]:
    parts = [p.strip() for p in _SEP.split(text) if p and p.strip() and not _SEP.fullmatch(p)]
    parts = [p for p in parts if not re.fullmatch(r"-{3,}|={3,}", p)]
    many = len(parts) > 1
    return [{"title": _title_from(p, f"{source} #{i + 1}" if many else source), "content": p, "department": "",
             "source": f"{source} #{i + 1}" if many else source} for i, p in enumerate(parts)]


def parse_file(filename: str, data: bytes) -> List[Dict]:
    name = os.path.basename(filename or "file")
    try:
        kind = ingest.file_type(name)
    except ingest.IngestError as e:
        raise BulkError(f"{name}: {e}")
    if kind == "csv":
        return from_rows(list(csv.reader(io.StringIO(data.decode("utf-8-sig", errors="ignore")))), name)
    if kind == "xlsx":
        try:
            return from_rows(ingest.xlsx_rows(data), name)
        except ingest.IngestError as e:
            raise BulkError(f"{name}: {e}")
    if kind in ("txt", "md"):
        return from_text(data.decode("utf-8-sig", errors="ignore"), os.path.splitext(name)[0])
    try:
        sections = ingest.READERS[kind](data)
    except ingest.IngestError as e:
        raise BulkError(f"{name}: {e}")
    text = "\n".join(s["text"] for s in sections).strip()
    if not text:
        raise BulkError(f"{name}: no readable text.")
    return [{"title": _title_from(text, os.path.splitext(name)[0]), "content": text, "department": "", "source": name}]


def clean(items: List[Dict]) -> List[Dict]:
    """Validate and trim a batch. Raises BulkError with a plain reason."""
    out = []
    for it in items:
        content = (it.get("content") or "").strip()
        if not content:
            continue
        if len(content) > MAX_CHARS:
            raise BulkError(f"“{(it.get('title') or '')[:60]}” is longer than {MAX_CHARS:,} characters. Split it up.")
        out.append({"title": ((it.get("title") or "").strip() or _title_from(content, "Untitled"))[:200],
                    "content": content, "department": (it.get("department") or "").strip()[:100]})
    if not out:
        raise BulkError("Nothing to check: every item is empty.")
    if len(out) > MAX_ITEMS:
        raise BulkError(f"At most {MAX_ITEMS} pieces per batch (you sent {len(out)}). Split the file.")
    return out
