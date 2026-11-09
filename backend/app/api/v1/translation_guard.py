"""Translation Guard API — multilingual claim consistency."""
import datetime
import re
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, resolve_org
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.brand import Organization, ApprovedFact, TerminologyRule
from backend.app.models.multilingual import MultilingualCampaign, CampaignTranslation
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.models.user import User
from backend.app.services import translation_guard as tg
from backend.app.services.llm import get_llm_provider

router = APIRouter(prefix="/translation-guard", tags=["Translation Guard"])

MAX_TEXT = 5000
MAX_TRANSLATIONS = 8


class TranslationIn(BaseModel):
    label: Optional[str] = Field(default=None, max_length=60)
    text: str = Field(min_length=1, max_length=MAX_TEXT)


class AnalyzeRequest(BaseModel):
    title: str = Field(default="Multilingual campaign", min_length=1, max_length=255)
    source_text: str = Field(min_length=1, max_length=MAX_TEXT)
    translations: List[TranslationIn] = Field(min_length=1, max_length=MAX_TRANSLATIONS)
    use_ai: bool = True
    org_id: Optional[str] = None


_PRICE_NUM = re.compile(r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*)", re.IGNORECASE)


def brand_context(db: Session, org_id: str) -> tuple[tg.BrandContext, str]:
    """Approved product names, prohibited terms and prices for this org, plus a
    short brief for the AI pass. Everything comes from stored Brand DNA."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id, TerminologyRule.is_active == True).all()  # noqa: E712

    names: List[str] = []
    prices: List[tuple] = []
    for f in facts:
        key = f.fact_key.strip()
        if "product name" in key.lower():
            names.append(f.fact_value.strip())
        if (f.category or "").lower() == "pricing":
            base = re.sub(r"\s*(launch\s+)?price\s*$", "", key, flags=re.IGNORECASE).strip()
            if base and base.lower() != key.lower():
                names.append(base)
            m = _PRICE_NUM.search(f.fact_value)
            if m:
                prices.append((float(m.group(1).replace(",", "")), key, f.verification_source))
    names = sorted({n for n in names if len(n) >= 3}, key=len, reverse=True)
    ctx = tg.BrandContext(product_names=names,
                          prohibited=[(t.prohibited_term, t.preferred_term) for t in terms],
                          approved_prices=prices)
    brief_lines = [f"BRAND: {org.name if org else ''}", "APPROVED FACTS:"]
    brief_lines += [f"- {f.fact_key}: {f.fact_value}" for f in facts] or ["- (none)"]
    brief_lines.append("PRODUCT NAMES (keep exactly): " + (", ".join(names) or "(none)"))
    return ctx, "\n".join(brief_lines)


def _summary(c: MultilingualCampaign) -> dict:
    return {
        "id": c.id, "title": c.title, "source_lang": c.source_lang,
        "source_language": tg.LANG_NAMES.get(c.source_lang, c.source_lang),
        "overall_score": c.overall_score, "verdict": c.verdict, "engine": c.engine,
        "created_by": c.created_by_name, "created_at": c.created_at.isoformat() if c.created_at else None,
        "languages": [t.detected_lang for t in c.translations],
    }


def _detail(c: MultilingualCampaign) -> dict:
    out = _summary(c)
    out["source_text"] = c.source_text
    out["translations"] = [
        {"id": t.id, "label": t.label, "text": t.text, "detected_lang": t.detected_lang,
         "overall_score": t.overall_score, "verdict": t.verdict, **(t.result or {})}
        for t in c.translations
    ]
    return out


@router.get("/languages")
def languages():
    """What the deterministic checks support, so the UI can be honest about it."""
    return {
        "detected": [{"code": k, "name": v} for k, v in tg.LANG_NAMES.items() if k != "und"],
        "qualifier_and_negation_checks": [{"code": k, "name": tg.LANG_NAMES[k]} for k in tg._QUALIFIERS],
        "ai_available": get_llm_provider(settings).available,
    }


@router.post("/analyze", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    org_id = resolve_org(payload.org_id, current)
    started = time.perf_counter()
    ctx, brief = brand_context(db, org_id)
    provider = get_llm_provider(settings) if payload.use_ai else None
    if provider is not None and not provider.available:
        provider = None

    src_lang = str(tg.detect_language(payload.source_text)["code"])
    campaign = MultilingualCampaign(
        id=str(uuid.uuid4()), org_id=org_id, title=payload.title.strip(), source_lang=src_lang,
        source_text=payload.source_text, created_by=current.id, created_by_name=current.full_name,
        created_at=datetime.datetime.utcnow(),
    )
    engines = set()
    scores = []
    verdicts = []
    for i, tr in enumerate(payload.translations):
        r = tg.analyze_pair(payload.source_text, src_lang, tr.text, ctx, provider=provider, brand_brief=brief,
                            language_hint=tr.label)
        engines.add(r["engine"])
        scores.append(r["overall_score"])
        verdicts.append(r["verdict"])
        result = {k: v for k, v in r.items() if k not in ("overall_score", "verdict")}
        campaign.translations.append(CampaignTranslation(
            id=str(uuid.uuid4()), position=i, label=(tr.label or None), text=tr.text,
            detected_lang=str(r["language"]["code"]), overall_score=r["overall_score"], verdict=r["verdict"],
            result=result,
        ))
    campaign.overall_score = min(scores)
    campaign.verdict = ("Needs revision" if "Needs revision" in verdicts
                        else "Review recommended" if "Review recommended" in verdicts else "Consistent")
    campaign.engine = "deterministic+llm" if any("llm" in e for e in engines) else "deterministic"

    elapsed = time.perf_counter() - started
    n_find = sum(len(t.result.get("findings", [])) for t in campaign.translations)
    db.add(campaign)
    db.add(AgentRun(
        id=str(uuid.uuid4()), org_id=org_id, agent_name="Translation Guard Agent",
        task_name=f"Compare {len(payload.translations)} translation(s) against the {tg.LANG_NAMES.get(src_lang, src_lang)} source",
        status="COMPLETED", execution_time_ms=round(elapsed * 1000), execution_time_us=max(1, round(elapsed * 1_000_000)),
        tokens_used=0, input_preview=payload.source_text[:120],
        output_preview=f"{n_find} findings; verdict: {campaign.verdict}; lowest score {campaign.overall_score}/100.",
        event_details={"languages": [t.detected_lang for t in campaign.translations], "engine": campaign.engine},
        created_at=datetime.datetime.utcnow(),
    ))
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action="TRANSLATION_GUARD_RUN",
                    actor=f"{current.full_name} ({current.role})",
                    details=f"'{campaign.title}': {len(payload.translations)} translation(s), verdict {campaign.verdict}."))
    db.commit()
    db.refresh(campaign)
    return _detail(campaign)


@router.get("/campaigns")
def list_campaigns(limit: int = 20, org_id: Optional[str] = None, db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    rows = (db.query(MultilingualCampaign).filter(MultilingualCampaign.org_id == org_id)
            .order_by(MultilingualCampaign.created_at.desc()).limit(max(1, min(limit, 100))).all())
    return [_summary(c) for c in rows]


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    c = db.query(MultilingualCampaign).filter(MultilingualCampaign.id == campaign_id).first()
    if c is None or c.org_id != current.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return _detail(c)
