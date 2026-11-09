"""Per-organisation settings with documented defaults.

Only keys listed in DEFAULTS can be stored; values are validated by type so a
bad payload can never break an engine that reads them.
"""
from __future__ import annotations

import copy
import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.app.models.creative import OrgSetting

DEFAULTS: Dict[str, Any] = {
    # Improvement 1 — logo clear space: required empty margin around a logo, as a
    # fraction of the logo's shorter side (0.25 = a quarter of the logo height).
    "logo_clear_space_ratio": 0.25,
    # Improvement 2 — channel rules used by the Channel Adapter agent.
    "channels": {
        "x": {"label": "X (Twitter)", "max_chars": 280, "aspect_ratios": ["16:9", "1:1"], "required": []},
        "instagram": {"label": "Instagram post", "max_chars": 2200, "aspect_ratios": ["1:1", "4:5"], "required": []},
        "linkedin": {"label": "LinkedIn post", "max_chars": 3000, "aspect_ratios": ["1.91:1", "1:1"], "required": []},
        "google_ads": {"label": "Google search ad headline", "max_chars": 30, "aspect_ratios": [], "required": []},
        "email": {"label": "Email subject line", "max_chars": 60, "aspect_ratios": [], "required": []},
        "web_banner": {"label": "Web banner", "max_chars": 120, "aspect_ratios": ["728:90", "300:250"], "required": []},
    },
    # Improvement 2 — mandatory disclaimers by category / region (regex trigger -> required text).
    "disclaimers": [
        {"id": "price-tc", "label": "Prices need terms", "trigger": r"(₹|rs\.?|inr)\s*\d", "region": "IN",
         "required_any": ["T&C apply", "terms and conditions apply", "*conditions apply"]},
        {"id": "emi-interest", "label": "EMI offers need an interest disclosure", "trigger": r"\bemi\b|no[- ]cost emi", "region": "IN",
         "required_any": ["subject to bank approval", "interest", "processing fee"]},
        {"id": "battery-conditions", "label": "Battery claims need test conditions", "trigger": r"\b\d+\s*(hours?|hrs?)\b.*battery|battery.*\b\d+\s*(hours?|hrs?)\b",
         "region": "*", "required_any": ["up to", "under test conditions", "varies with use", "mixed productivity workload"]},
    ],
    # Improvement 2 — notifications.
    "notifications": {"email": "", "slack_webhook_url": "", "events": ["review_requested", "approved", "revision_requested", "passport_superseded"]},
}


def get(db: Session, org_id: str) -> Dict[str, Any]:
    row = db.query(OrgSetting).filter(OrgSetting.org_id == org_id).first()
    merged = copy.deepcopy(DEFAULTS)
    if row and isinstance(row.data, dict):
        for k, v in row.data.items():
            if k in merged:
                merged[k] = v
    return merged


def _check(key: str, value: Any) -> Any:
    default = DEFAULTS[key]
    if key == "logo_clear_space_ratio":
        v = float(value)
        if not 0 <= v <= 2:
            raise ValueError("logo_clear_space_ratio must be between 0 and 2.")
        return round(v, 3)
    if not isinstance(value, type(default)):
        raise ValueError(f"{key} must be a {type(default).__name__}.")
    return value


def update(db: Session, org_id: str, changes: Dict[str, Any], actor: str) -> Dict[str, Any]:
    unknown = [k for k in changes if k not in DEFAULTS]
    if unknown:
        raise ValueError(f"Unknown setting(s): {', '.join(unknown)}")
    row = db.query(OrgSetting).filter(OrgSetting.org_id == org_id).first()
    if row is None:
        row = OrgSetting(org_id=org_id, data={})
        db.add(row)
    data = dict(row.data or {})
    for k, v in changes.items():
        data[k] = _check(k, v)
    row.data = data
    row.updated_by = actor
    row.updated_at = datetime.datetime.utcnow()
    db.commit()
    return get(db, org_id)
