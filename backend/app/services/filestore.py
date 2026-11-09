"""Read and write uploaded files through the database.

A stored reference looks like ``db://<id>``. References written by older
versions are plain disk paths; those are still readable while the file exists.
"""
from __future__ import annotations

import hashlib
import os
import uuid

from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.models.storage import StoredFile

PREFIX = "db://"


def put(db: Session, org_id: str, folder: str, data: bytes, mime: str) -> str:
    """Store bytes and return a reference. The caller commits the session."""
    row = StoredFile(id=str(uuid.uuid4()), org_id=org_id, folder=folder, mime=mime, size=len(data),
                     sha256=hashlib.sha256(data).hexdigest(), data=data)
    db.add(row)
    return PREFIX + row.id


def read(db: Session, ref: str | None, org_id: str | None = None) -> bytes:
    """Return the file's bytes. Raises OSError when it is missing (callers skip, never fabricate)."""
    if not ref:
        raise OSError("no file reference")
    if ref.startswith(PREFIX):
        q = db.query(StoredFile).filter(StoredFile.id == ref[len(PREFIX):])
        if org_id:
            q = q.filter(StoredFile.org_id == org_id)
        row = q.first()
        if row is None:
            raise OSError("stored file not found")
        return bytes(row.data)
    if not os.path.isfile(ref):  # legacy disk path
        raise OSError("file not found on disk")
    with open(ref, "rb") as fh:
        return fh.read()


def response(db: Session, ref: str | None, mime: str | None, org_id: str | None = None) -> Response:
    try:
        data = read(db, ref, org_id)
    except OSError:
        raise HTTPException(status_code=404, detail="File not available")
    return Response(content=data, media_type=mime or "application/octet-stream",
                    headers={"Cache-Control": "private, max-age=300"})
