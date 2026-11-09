"""Phase 3 APIs: campaign stress testing, content similarity, brand fraud
intelligence and reputation early warning."""
import datetime
import hashlib
import os
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles, ensure_same_org
from backend.app.api.v1 import assets as assets_api
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.asset import BrandAsset, AssetInvestigation
from backend.app.models.intelligence import (
    SimulationRun, SimilarityDismissal, OfficialDomain, FraudIncident, FeedbackRecord, INCIDENT_STATUSES,
)
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.models.product import Product
from backend.app.models.submission import Submission
from backend.app.models.user import User, ROLE_ADMIN, ROLE_REVIEWER
from backend.app.services import filestore
from backend.app.services import forensics as fx, fraud, reputation, similarity, simulation

router = APIRouter(tags=["Advanced Intelligence"])
AI_LIMIT = [Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))]


def _audit(db, org_id, action, user, details):
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action=action, actor=f"{user.full_name} ({user.role})", details=details))


def _agent(db, org_id, name, task, started, inp, out, details=None):
    el = time.perf_counter() - started
    db.add(AgentRun(id=str(uuid.uuid4()), org_id=org_id, agent_name=name, task_name=task, status="COMPLETED",
                    execution_time_ms=round(el * 1000), execution_time_us=max(1, round(el * 1_000_000)), tokens_used=0,
                    input_preview=inp[:120], output_preview=out[:240], event_details=details or {},
                    created_at=datetime.datetime.utcnow()))


def _own_sub(db: Session, sid: str, user: User) -> Submission:
    s = db.query(Submission).filter(Submission.id == sid).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_same_org(user, s.org_id)
    return s


# =============================================================== simulation
@router.get("/simulation/scenarios")
def scenarios():
    return {"scenarios": [{"key": k, "label": v} for k, v in simulation.SCENARIOS.items()]}


class SimIn(BaseModel):
    submission_id: str
    scenario: str
    params: dict = Field(default_factory=dict)


@router.post("/simulation/run", dependencies=AI_LIMIT)
def run_simulation(payload: SimIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    sub = _own_sub(db, payload.submission_id, current)
    if payload.scenario not in simulation.SCENARIOS:
        raise HTTPException(status_code=400, detail="Unknown scenario")
    t0 = time.perf_counter()
    try:
        result = simulation.simulate(db, sub, payload.scenario, payload.params)
    except simulation.SimulationUnavailable as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = SimulationRun(id=str(uuid.uuid4()), org_id=sub.org_id, submission_id=sub.id, submission_version=sub.version,
                        scenario=payload.scenario, params=payload.params, result=result,
                        created_by=f"{current.full_name} ({current.role})")
    db.add(row)
    _agent(db, sub.org_id, "Stress Test Agent", f"Hypothetical: {result['scenario_label']}", t0, sub.title,
           f"+{len(result['introduced'])} / -{len(result['resolved'])} findings; score Δ {result['score_delta']}")
    db.commit()
    return {"id": row.id, **result}


@router.get("/simulation/runs")
def simulation_runs(submission_id: Optional[str] = None, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    q = db.query(SimulationRun).filter(SimulationRun.org_id == current.org_id)
    if submission_id:
        q = q.filter(SimulationRun.submission_id == submission_id)
    return [{"id": r.id, "submission_id": r.submission_id, "scenario": r.scenario, "params": r.params,
             "score_delta": (r.result or {}).get("score_delta"), "introduced": len((r.result or {}).get("introduced", [])),
             "resolved": len((r.result or {}).get("resolved", [])), "created_by": r.created_by,
             "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in q.order_by(SimulationRun.created_at.desc()).limit(20).all()]


# =============================================================== similarity
class SimilarityIn(BaseModel):
    text: Optional[str] = Field(default=None, max_length=20000)
    submission_id: Optional[str] = None
    include_dismissed: bool = False


@router.post("/similarity/check")
def similarity_check(payload: SimilarityIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    t0 = time.perf_counter()
    exclude, self_key = set(), None
    if payload.submission_id:
        sub = _own_sub(db, payload.submission_id, current)
        text = sub.content
        self_key = f"submission:{sub.id}"
        exclude = {self_key}
        if sub.passport:
            exclude.add(f"passport:{sub.passport.id}")
    elif (payload.text or "").strip():
        text = payload.text
    else:
        raise HTTPException(status_code=400, detail="Provide text or a submission.")
    r = similarity.check_text(db, current.org_id, text, exclude=exclude, self_key=self_key,
                              include_dismissed=payload.include_dismissed)
    _agent(db, current.org_id, "Similarity Agent", "Compare content with existing campaigns", t0, text,
           f"{len(r['matches'])} similar item(s) out of {r['compared']}")
    db.commit()
    return r


@router.get("/similarity/clusters")
def similarity_clusters(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return {"clusters": similarity.clusters(db, current.org_id)}


class DismissIn(BaseModel):
    pair_key: str = Field(min_length=5, max_length=200)
    reason: str = Field(min_length=3, max_length=1000)


@router.post("/similarity/dismiss")
def similarity_dismiss(payload: DismissIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if db.query(SimilarityDismissal).filter(SimilarityDismissal.org_id == current.org_id,
                                            SimilarityDismissal.pair_key == payload.pair_key).first():
        return {"dismissed": True, "already": True}
    db.add(SimilarityDismissal(id=str(uuid.uuid4()), org_id=current.org_id, pair_key=payload.pair_key,
                               reason=payload.reason.strip(), dismissed_by=f"{current.full_name} ({current.role})"))
    _audit(db, current.org_id, "SIMILARITY_DISMISSED", current, f"{payload.pair_key}: {payload.reason[:200]}")
    db.commit()
    return {"dismissed": True}


@router.post("/similarity/restore")
def similarity_restore(payload: DismissIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    row = db.query(SimilarityDismissal).filter(SimilarityDismissal.org_id == current.org_id,
                                               SimilarityDismissal.pair_key == payload.pair_key).first()
    if row:
        db.delete(row)
        _audit(db, current.org_id, "SIMILARITY_RESTORED", current, f"{payload.pair_key}: {payload.reason[:200]}")
        db.commit()
    return {"restored": bool(row)}


@router.post("/similarity/image", dependencies=AI_LIMIT)
async def similarity_image(file: UploadFile = File(...), db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    data = await assets_api._read_image(file)
    try:
        fp = fx.fingerprints(data)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))
    out = []
    refs = [("asset", a.id, f"{a.name} {a.version_label}", a.sha256, a.phash, a.dhash, a.created_at)
            for a in db.query(BrandAsset).filter(BrandAsset.org_id == current.org_id).all()]
    for inv in db.query(AssetInvestigation).filter(AssetInvestigation.org_id == current.org_id).all():
        try:
            dh = fx.dhash(fx.load_image(filestore.read(db, inv.file_path, current.org_id))[0])
        except (OSError, ValueError):
            continue
        refs.append(("investigation", inv.id, inv.file_name, inv.sha256, inv.phash, dh, inv.created_at))
    for kind, rid, title, sha, ph, dh, when in refs:
        dp, dd = fx.hamming(fp["phash"], ph), fx.hamming(fp["dhash"], dh)
        label = "Identical file" if sha == fp["sha256"] else "Near-duplicate image" if dp <= 10 and dd <= 14 else \
            "Visually similar" if dp <= 18 else None
        if label:
            out.append({"kind": kind, "id": rid, "title": title, "label": label, "phash_distance": dp, "dhash_distance": dd,
                        "similarity": round(1 - (dp + dd) / 128, 3), "date": when.isoformat() if when else None})
    out.sort(key=lambda m: (m["phash_distance"] + m["dhash_distance"]))
    return {"sha256": fp["sha256"], "matches": out, "compared": len(refs),
            "note": "Perceptual hashes compare overall appearance; similarity is not proof of copying."}


# =============================================================== fraud
@router.get("/fraud/domains")
def list_domains(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return [{"id": d.id, "domain": d.domain, "added_by": d.added_by}
            for d in db.query(OfficialDomain).filter(OfficialDomain.org_id == current.org_id).order_by(OfficialDomain.domain).all()]


class DomainIn(BaseModel):
    domain: str = Field(min_length=3, max_length=255)


@router.post("/fraud/domains")
def add_domain(payload: DomainIn, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    host = fraud.host_of(payload.domain.strip())
    if not host or "." not in host:
        raise HTTPException(status_code=400, detail="Enter a domain such as example.com")
    if not db.query(OfficialDomain).filter(OfficialDomain.org_id == current.org_id, OfficialDomain.domain == host).first():
        db.add(OfficialDomain(id=str(uuid.uuid4()), org_id=current.org_id, domain=host, added_by=current.full_name))
        _audit(db, current.org_id, "OFFICIAL_DOMAIN_ADDED", current, host)
        db.commit()
    return list_domains(db, current)


@router.delete("/fraud/domains/{domain_id}")
def remove_domain(domain_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    d = db.query(OfficialDomain).filter(OfficialDomain.id == domain_id, OfficialDomain.org_id == current.org_id).first()
    if d is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    _audit(db, current.org_id, "OFFICIAL_DOMAIN_REMOVED", current, d.domain)
    db.delete(d)
    db.commit()
    return list_domains(db, current)


def _incident_out(i: FraudIncident, full: bool = True) -> dict:
    out = {"id": i.id, "number": i.number, "source_url": i.source_url, "source_kind": i.source_kind,
           "detected_issue": i.detected_issue, "confidence": i.confidence, "risk": i.risk, "status": i.status,
           "recommended_response": i.recommended_response, "has_evidence_file": bool(i.evidence_path),
           "created_by": i.created_by, "created_at": i.created_at.isoformat() if i.created_at else None,
           "updated_at": i.updated_at.isoformat() if i.updated_at else None}
    if full:
        out.update({"findings": i.findings, "text_excerpt": i.text_excerpt, "history": i.history,
                    "evidence_sha256": i.evidence_sha256})
    return out


@router.post("/fraud/investigate", dependencies=AI_LIMIT)
async def investigate(url: Optional[str] = Form(default=None), text: Optional[str] = Form(default=None),
                      file: Optional[UploadFile] = File(default=None), db: Session = Depends(get_db),
                      current: User = Depends(get_current_user)):
    url = (url or "").strip() or None
    text = (text or "").strip()
    data = None
    if file is not None and file.filename:
        data = await assets_api._read_image(file)
    if not (url or text or data):
        raise HTTPException(status_code=400, detail="Provide a URL, page text or a screenshot.")
    t0 = time.perf_counter()
    findings: List[dict] = []
    official = [d.domain for d in db.query(OfficialDomain).filter(OfficialDomain.org_id == current.org_id).all()]
    toks = fraud.brand_tokens(db, current.org_id)
    host = fraud.host_of(url) if url else None
    if url:
        findings += fraud.analyse_domain(host, official, toks)
        if settings.FRAUD_URL_FETCH_ENABLED and not text:
            fetched, note = fraud.fetch_page(url)
            findings.append({"type": "fetch", "severity": "info", "title": note, "evidence": url, "confidence": 0.0})
            if fetched:
                text = fetched
                if "password field" in note:
                    findings.append({"type": "password_form", "severity": "high", "title": "Page asks for a password",
                                     "evidence": url, "confidence": 0.8})
        elif not text:
            findings.append({"type": "fetch", "severity": "info",
                             "title": "Page content was not fetched (server fetching is disabled). Paste the page text or attach a screenshot for a full check.",
                             "evidence": url, "confidence": 0.0})
    host_official = any(f["type"] == "official_domain" for f in findings)
    ctx = {}
    if text:
        tf, ctx = fraud.analyse_text(db, current.org_id, text, host_official)
        findings += tf
    path = mime = sha = None
    if data is not None:
        try:
            fp = fx.fingerprints(data)
        except ValueError as e:
            raise HTTPException(status_code=415, detail=str(e))
        path = assets_api._save(db, current.org_id, "incidents", data, fp["mime"])
        mime, sha = fp["mime"], fp["sha256"]
        now = datetime.datetime.utcnow()
        refs = []
        for a in db.query(BrandAsset).filter(BrandAsset.org_id == current.org_id).all():
            try:
                rgb, _, alpha = fx.load_image(filestore.read(db, a.file_path, current.org_id))
            except (OSError, ValueError):
                continue
            refs.append({"id": a.id, "name": a.name, "kind": a.kind, "version_label": a.version_label, "status": a.status,
                         "current": assets_api._is_current(a, now), "rgb": rgb, "alpha": alpha, "sha256": a.sha256,
                         "phash": a.phash, "dhash": a.dhash, "replacement": None})
        if refs:
            res = fx.investigate(data, refs)
            for m in res["matches"]:
                for f in m["findings"]:
                    if m["asset_kind"] == "logo" and f["type"] in ("official_logo", "stretched", "rotated", "cropped", "recoloured", "outdated_logo"):
                        sev = "info" if host_official else ("high" if f["type"] != "official_logo" else "medium")
                        findings.append({"type": "logo_use", "severity": sev,
                                         "title": f"{m['asset_name']} {m['version_label']} found — {f['title'].lower()}"
                                                  + ("" if host_official else " on a source that is not an official domain"),
                                         "evidence": f["measurement"], "confidence": round(f["confidence"], 2)})
        else:
            findings.append({"type": "no_assets", "severity": "info", "title": "No official assets in the library to compare the screenshot with",
                             "evidence": "Upload logos in Asset Forensics", "confidence": 0.0})
    risk, conf, issue, resp = fraud.assess(findings, bool(ctx.get("brand_mentioned")) or any(f["type"].startswith("brand_in") for f in findings))
    now = datetime.datetime.utcnow()
    inc = FraudIncident(id=str(uuid.uuid4()), number=f"BV-INC-{uuid.uuid4().hex[:6].upper()}", org_id=current.org_id,
                        source_url=url, source_kind="mixed" if sum(bool(x) for x in (url, text, data)) > 1 else
                        ("url" if url else "image" if data else "text"),
                        evidence_path=path, evidence_mime=mime, evidence_sha256=sha, text_excerpt=text[:3000] if text else None,
                        detected_issue=issue, findings=findings, confidence=conf, risk=risk, status="Under Investigation",
                        recommended_response=resp, created_by=f"{current.full_name} ({current.role})",
                        history=[{"status": "Under Investigation", "by": f"{current.full_name} ({current.role})",
                                  "note": "Incident opened", "at": now.isoformat() + "Z"}], created_at=now, updated_at=now)
    db.add(inc)
    _agent(db, current.org_id, "Brand Fraud Agent", "Investigate suspected impersonation", t0, url or text or file.filename,
           f"{inc.number}: {risk} risk — {issue}")
    db.commit()
    from backend.app.services import events
    events.emit(db, current.org_id, "incident.opened", {"incident": inc.number, "risk": risk, "source_url": url},
                title=f"{inc.number}: {risk} risk suspected impersonation", body=issue, link="/risk-radar/fraud")
    return _incident_out(inc)


@router.get("/fraud/incidents")
def list_incidents(status: Optional[str] = None, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    q = db.query(FraudIncident).filter(FraudIncident.org_id == current.org_id)
    if status:
        q = q.filter(FraudIncident.status == status)
    return [_incident_out(i, full=False) for i in q.order_by(FraudIncident.created_at.desc()).limit(50).all()]


def _own_incident(db: Session, iid: str, user: User) -> FraudIncident:
    i = db.query(FraudIncident).filter(FraudIncident.id == iid).first()
    if i is None or i.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Incident not found")
    return i


@router.get("/fraud/incidents/{iid}")
def get_incident(iid: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _incident_out(_own_incident(db, iid, current))


@router.get("/fraud/incidents/{iid}/evidence")
def incident_evidence(iid: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    i = _own_incident(db, iid, current)
    if not i.evidence_path:
        raise HTTPException(status_code=404, detail="No evidence file")
    return filestore.response(db, i.evidence_path, i.evidence_mime, current.org_id)


class StatusIn(BaseModel):
    status: str
    note: str = Field(default="", max_length=1000)


@router.post("/fraud/incidents/{iid}/status")
def set_incident_status(iid: str, payload: StatusIn, db: Session = Depends(get_db),
                        current: User = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER))):
    if payload.status not in INCIDENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {', '.join(INCIDENT_STATUSES)}")
    i = _own_incident(db, iid, current)
    i.status = payload.status
    i.updated_at = datetime.datetime.utcnow()
    i.history = list(i.history or []) + [{"status": payload.status, "by": f"{current.full_name} ({current.role})",
                                          "note": payload.note.strip(), "at": i.updated_at.isoformat() + "Z"}]
    _audit(db, i.org_id, "INCIDENT_STATUS", current, f"{i.number} → {payload.status}")
    db.commit()
    return _incident_out(i)


# =============================================================== reputation
def _product_of(text: str, names: List[str], given: Optional[str]) -> Optional[str]:
    if given:
        return given
    low = text.lower()
    return next((n for n in names if n.lower() in low), None)


def _store(db: Session, org_id: str, rows: List[dict], source: str, user: User) -> tuple:
    from backend.app.services.product_truth import bootstrap_products
    bootstrap_products(db, org_id)  # make sure approved product names are known
    names = [p.name for p in db.query(Product).filter(Product.org_id == org_id).all()]
    batch = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    for r in rows:
        label, score, engine = reputation.score_sentiment(r["text"], r.get("rating"))
        db.add(FeedbackRecord(id=str(uuid.uuid4()), org_id=org_id, batch_id=batch, source=source[:255],
                              channel=r.get("channel"), text=r["text"], rating=r.get("rating"),
                              feedback_date=r.get("date") or now, product=_product_of(r["text"], names, r.get("product")),
                              sentiment=label, sentiment_score=score, sentiment_engine=engine,
                              categories=reputation.categorise(r["text"]), uploaded_by=user.full_name))
    return batch, len(rows)


@router.post("/reputation/upload")
async def upload_feedback(file: UploadFile = File(...), db: Session = Depends(get_db),
                          current: User = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER))):
    name = file.filename or "upload"
    if not name.lower().endswith((".csv", ".json")):
        raise HTTPException(status_code=400, detail="Upload a .csv or .json export.")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB.")
    rows, problems = reputation.parse_upload(name, data)
    if not rows:
        raise HTTPException(status_code=400, detail="No usable feedback rows. " + "; ".join(problems[:5]))
    rows = rows[:5000]
    batch, n = _store(db, current.org_id, rows, name, current)
    _audit(db, current.org_id, "FEEDBACK_UPLOADED", current, f"{name}: {n} records (batch {batch[:8]})")
    db.commit()
    return {"batch_id": batch, "imported": n, "skipped": len(problems), "problems": problems[:20]}


class FeedbackIn(BaseModel):
    text: str = Field(min_length=3, max_length=4000)
    rating: Optional[float] = Field(default=None, ge=1, le=5)
    date: Optional[datetime.datetime] = None
    channel: Optional[str] = Field(default=None, max_length=100)
    product: Optional[str] = Field(default=None, max_length=255)


@router.post("/reputation/feedback")
def add_feedback(payload: FeedbackIn, db: Session = Depends(get_db),
                 current: User = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER))):
    batch, _ = _store(db, current.org_id, [payload.model_dump()], "manual", current)
    db.commit()
    return {"batch_id": batch, "imported": 1}


@router.get("/reputation/overview")
def reputation_overview(days: int = 90, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    recs = db.query(FeedbackRecord).filter(FeedbackRecord.org_id == current.org_id).all()
    camps = [(s.id, s.title, s.content) for s in db.query(Submission).filter(Submission.org_id == current.org_id).all()]
    out = reputation.overview(recs, camps, days=max(0, min(days, 3650)))
    out["batches"] = [{"batch_id": b, "source": src, "records": n} for (b, src), n in
                      __import__("collections").Counter((r.batch_id, r.source) for r in recs).items()]
    return out


@router.get("/reputation/feedback")
def list_feedback(limit: int = 50, sentiment: Optional[str] = None, db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    q = db.query(FeedbackRecord).filter(FeedbackRecord.org_id == current.org_id)
    if sentiment:
        q = q.filter(FeedbackRecord.sentiment == sentiment)
    return [{"id": r.id, "text": r.text, "rating": r.rating, "sentiment": r.sentiment, "score": r.sentiment_score,
             "engine": r.sentiment_engine, "categories": r.categories, "product": r.product, "channel": r.channel,
             "source": r.source, "date": r.feedback_date.isoformat() if r.feedback_date else None}
            for r in q.order_by(FeedbackRecord.feedback_date.desc()).limit(max(1, min(limit, 500))).all()]


@router.delete("/reputation/batches/{batch_id}")
def delete_batch(batch_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    q = db.query(FeedbackRecord).filter(FeedbackRecord.org_id == current.org_id, FeedbackRecord.batch_id == batch_id)
    n = q.count()
    if not n:
        raise HTTPException(status_code=404, detail="Batch not found")
    q.delete(synchronize_session=False)
    _audit(db, current.org_id, "FEEDBACK_BATCH_REMOVED", current, f"batch {batch_id[:8]}: {n} records")
    db.commit()
    return {"removed": n}
