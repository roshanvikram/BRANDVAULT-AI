"""
Channel Adapter and Regulatory Disclaimer agents (Round 3 · Improvement 2).

Both are deterministic and read their rules from the organisation's settings
(Settings → Channels / Disclaimers), so administrators control them:

- Channel Adapter: character limits, required elements and image aspect ratios
  per publishing channel.
- Disclaimer agent: when a trigger pattern appears (e.g. a price or an EMI
  offer), at least one approved disclaimer wording must be present.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional


def _ratio(spec: str) -> Optional[float]:
    try:
        a, b = spec.split(":")
        return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return None


def check_channels(text: str, channels: Dict[str, Dict], selected: List[str],
                   width: Optional[int] = None, height: Optional[int] = None) -> List[Dict]:
    out = []
    n = len(text or "")
    for key in selected:
        cfg = channels.get(key)
        if not cfg:
            out.append({"channel": key, "label": key, "ok": False, "issues": [f"Unknown channel '{key}'."]})
            continue
        issues = []
        limit = int(cfg.get("max_chars") or 0)
        if limit and n > limit:
            issues.append(f"{n} characters; {cfg['label']} allows {limit} ({n - limit} over).")
        for req in cfg.get("required") or []:
            if req and req.lower() not in (text or "").lower():
                issues.append(f"Missing required element: “{req}”.")
        ratios = [r for r in (cfg.get("aspect_ratios") or []) if _ratio(r)]
        aspect = None
        if width and height and ratios:
            aspect = width / height
            if not any(abs(aspect - _ratio(r)) / _ratio(r) <= 0.03 for r in ratios):
                issues.append(f"Image is {width}×{height} ({aspect:.2f}:1); {cfg['label']} expects {', '.join(ratios)}.")
        out.append({"channel": key, "label": cfg.get("label", key), "chars": n, "max_chars": limit or None,
                    "aspect": round(aspect, 3) if aspect else None, "ok": not issues, "issues": issues})
    return out


def check_disclaimers(text: str, rules: List[Dict], region: Optional[str] = None) -> List[Dict]:
    out = []
    low = (text or "").lower()
    for rule in rules:
        if region and rule.get("region") not in ("*", None, "", region):
            continue
        try:
            triggered = re.search(rule.get("trigger", ""), text or "", re.I) is not None
        except re.error:
            out.append({"id": rule.get("id"), "label": rule.get("label"), "triggered": False, "ok": False,
                        "issue": "This rule's trigger pattern is invalid; an administrator should fix it in Settings."})
            continue
        if not triggered:
            continue
        options = [o for o in rule.get("required_any") or [] if o]
        present = [o for o in options if o.lower() in low]
        out.append({"id": rule.get("id"), "label": rule.get("label"), "region": rule.get("region"), "triggered": True,
                    "ok": bool(present), "present": present, "required_any": options,
                    "issue": None if present else f"Add one of: {', '.join(repr(o) for o in options)}."})
    return out
