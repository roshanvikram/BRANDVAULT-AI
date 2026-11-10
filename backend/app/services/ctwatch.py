"""Look-alike domain watch through public Certificate Transparency logs.

Every publicly trusted HTTPS certificate is recorded in CT logs. A scammer who
sets up ``novatech-offers.shop`` with HTTPS appears there within minutes. This
module searches those logs (through crt.sh) for names that start with the brand's
official domain name or a character-swap spelling of it, keeps the
domains that are not official, scores each one with the same look-alike checks
as Brand Fraud Intelligence, and stores them as watch hits for review.

It finds only domains that obtained a certificate (most phishing sites do) and whose
name starts with the brand (crt.sh does not support "contains" searches), so
"secure-zentrova.com" is missed while "zentrova-offers.shop" is found. It does
not see social-media pages, ads or sites without HTTPS.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.account import DomainWatchHit
from backend.app.models.brand import Organization
from backend.app.models.intelligence import OfficialDomain
from backend.app.services import fraud

log = logging.getLogger("brandvault.ctwatch")
CRT_URL = "https://crt.sh/?q={q}&output=json&exclude=expired"
MAX_ROWS = 3000
state: Dict[str, dict] = {}  # org_id -> {"running", "last_scan", "last_error", "found", "summary"}
_lock = threading.Lock()
session_factory = None  # tests point background scans at their own database

Fetcher = Callable[[str], List[dict]]


_SWAPS = (("o", "0"), ("l", "1"), ("i", "1"), ("e", "3"), ("a", "4"), ("s", "5"))


def queries_for(term: str, max_variants: int = 3) -> List[str]:
    """crt.sh accepts "starts with" searches (term%) but not "contains" (%term%).
    Search the name itself plus a few character-swap spellings (zentr0va, zentrova -> zentr0va)."""
    out = [term]
    for a, b in _SWAPS:
        if a in term and len(out) <= max_variants:
            out.append(term.replace(a, b, 1))
    return out


def _fetch_crtsh(query: str, attempts: int = 2) -> List[dict]:
    """One crt.sh search. The service is free and often slow, so allow 90 s and retry once."""
    url = CRT_URL.format(q=urllib.parse.quote(f"{query}%"))
    req = urllib.request.Request(url, headers={"User-Agent": "BrandVault-DomainWatch/1.0", "Accept": "application/json"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read(25_000_000)
            data = json.loads(raw.decode("utf-8") or "[]")
            return data[:MAX_ROWS] if isinstance(data, list) else []
        except Exception:  # noqa: BLE001
            if attempt == attempts - 1:
                raise
            time.sleep(3)
    return []


def start_scan(org_id: str) -> bool:
    """Run scan() in a background thread (a search can take minutes). False if one is already running."""
    with _lock:
        cur = state.get(org_id, {})
        if cur.get("running"):
            return False
        state[org_id] = {**cur, "running": True, "started": datetime.datetime.utcnow().isoformat() + "Z"}

    def _work():
        from backend.app.db.session import SessionLocal
        db = (session_factory or SessionLocal)()
        try:
            scan(db, org_id)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            state[org_id] = {**state.get(org_id, {}), "last_error": f"Search failed ({type(exc).__name__})"}
        finally:
            db.close()
            state[org_id] = {**state.get(org_id, {}), "running": False}

    threading.Thread(target=_work, daemon=True).start()
    return True


def search_terms(db: Session, org_id: str) -> Tuple[List[str], List[str]]:
    """(terms to search, official domains). Terms are the names of the official domains
    (zentrova.com -> "zentrova"). Generic company words are not searched: "verify" or
    "foods" would match hundreds of thousands of unrelated certificates."""
    official = [d.domain.lower() for d in db.query(OfficialDomain).filter(OfficialDomain.org_id == org_id).all()]
    terms = {fraud.registrable(o)[0] for o in official}
    return sorted(t for t in terms if t and len(t) >= 5), official


def _parse_date(s: Optional[str]) -> Optional[datetime.datetime]:
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", ""))
    except ValueError:
        return None


def scan(db: Session, org_id: str, fetch: Optional[Fetcher] = None) -> dict:
    """Search the CT logs for this organisation and store new look-alikes. Returns a summary."""
    fetch = fetch or _fetch_crtsh
    terms, official = search_terms(db, org_id)
    # The official names count as brand words too, so "brandvault.evil.com" is caught as a subdomain lure.
    tokens = sorted(set(fraud.brand_tokens(db, org_id)) | set(terms))
    summary = {"terms": terms, "certificates": 0, "domains_checked": 0, "new_hits": 0, "errors": []}
    if not terms:
        summary["errors"].append("No official domains to watch yet. Add them under Brand Fraud Intelligence → Official domains.")
        state[org_id] = {**state.get(org_id, {}), "last_scan": datetime.datetime.utcnow().isoformat() + "Z",
                         "last_error": summary["errors"][0], "found": 0, "summary": summary}
        return summary
    known = {h.host for h in db.query(DomainWatchHit.host).filter(DomainWatchHit.org_id == org_id)}
    seen: Dict[str, dict] = {}
    for i, (term, query) in enumerate([(t, q) for t in terms for q in queries_for(t)]):
        if i and fetch is _fetch_crtsh:
            time.sleep(2)  # crt.sh refuses rapid back-to-back searches
        try:
            rows = fetch(query)
        except Exception as exc:  # noqa: BLE001 - crt.sh is often slow; report, never invent
            summary["errors"].append(f"{query}: certificate log search failed ({type(exc).__name__})")
            continue
        summary["certificates"] += len(rows)
        for r in rows:
            for name in str(r.get("name_value", "")).lower().split("\n"):
                host = name.strip().lstrip("*.").strip(".")
                if not host or " " in host or "@" in host or host in seen:
                    continue
                if not re.match(r"^[a-z0-9.-]+\.[a-z0-9-]{2,}$", host):
                    continue
                seen[host] = {"term": term, "issuer": str(r.get("issuer_name", ""))[:300],
                              "cert_id": r.get("id"), "not_before": _parse_date(r.get("not_before"))}
    summary["domains_checked"] = len(seen)
    for host, meta in seen.items():
        if host in known:
            continue
        findings = [f for f in fraud.analyse_domain(host, official, tokens)
                    if f["type"] not in ("no_official_domains",)]
        if not findings or any(f["type"] == "official_domain" for f in findings):
            continue
        sev = {f["severity"] for f in findings}
        risk = "high" if "high" in sev else "medium" if "medium" in sev else "low"
        db.add(DomainWatchHit(org_id=org_id, host=host[:255], matched_term=meta["term"], issuer=meta["issuer"],
                              cert_id=meta["cert_id"] if isinstance(meta["cert_id"], int) else None,
                              not_before=meta["not_before"], findings=findings, risk=risk))
        summary["new_hits"] += 1
    db.commit()
    state[org_id] = {**state.get(org_id, {}), "last_scan": datetime.datetime.utcnow().isoformat() + "Z",
                     "last_error": "; ".join(summary["errors"]) or None, "found": summary["new_hits"], "summary": summary}
    return summary


def _scan_all() -> None:
    from backend.app.db.session import SessionLocal
    from backend.app.services.analytics import DEMO_ORGS
    db = SessionLocal()
    try:
        orgs = [o.id for o in db.query(Organization).all() if o.id not in DEMO_ORGS]
        for oid in orgs:
            if not db.query(OfficialDomain).filter(OfficialDomain.org_id == oid).count():
                continue  # nothing precise to watch yet
            try:
                scan(db, oid)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                log.warning("CT scan failed for %s: %s", oid, exc)
    finally:
        db.close()


async def _loop() -> None:
    await asyncio.sleep(120)  # let startup finish first
    while True:
        try:
            await asyncio.to_thread(_scan_all)
        except Exception as exc:  # noqa: BLE001
            log.warning("CT watch round failed: %s", exc)
        await asyncio.sleep(max(1, settings.CT_MONITOR_HOURS) * 3600)


def start() -> Optional[asyncio.Task]:
    """Daily background scan for every company workspace with official domains registered."""
    if not settings.CT_MONITOR_ENABLED or settings.ENVIRONMENT.lower() != "production":
        return None
    return asyncio.get_event_loop().create_task(_loop())
