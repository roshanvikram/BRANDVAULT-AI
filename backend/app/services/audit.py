"""Security audit trail (who did what, from where). Writing never breaks the caller."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.models.account import SecurityEvent

log = logging.getLogger("brandvault.audit")


def client_ip(request: Optional[Request]) -> str:
    if request is None or request.client is None:
        return ""
    return request.client.host or ""


def record(db: Session, action: str, *, org_id: Optional[str], actor: str = "", target: str = "",
           detail: Optional[dict] = None, request: Optional[Request] = None, commit: bool = True) -> None:
    try:
        db.add(SecurityEvent(org_id=org_id, actor=actor or "", action=action, target=target or "",
                             detail=detail or {}, ip=client_ip(request)))
        if commit:
            db.commit()
    except Exception as exc:  # noqa: BLE001 - auditing must not take the request down
        log.warning("audit write failed (%s): %s", action, exc)
        db.rollback()
