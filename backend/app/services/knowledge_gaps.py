"""
Brand Knowledge Gap Detector.

Inspects an organisation's stored Brand DNA and reports what reliable brand
governance still needs: missing product facts, missing policy areas, conflicts
between sources, claims with no evidence, weakly-sourced facts and stale
records. Everything is computed from database records; nothing is filled in.
"""
from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.brand import Organization, BrandGuideline, DocumentChunk, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.product import Product, ProductFact, PRODUCT_ATTRIBUTES, FACT_APPROVED, FACT_PENDING
from backend.app.models.submission import ClaimVerification, Submission
from backend.app.services import product_truth as pt

OK, MISSING, CONFLICT, WEAK, STALE = "ok", "missing", "conflict", "weak", "stale"
HIGH, MEDIUM, LOW = "high", "medium", "low"
_WEIGHT = {HIGH: 3, MEDIUM: 2, LOW: 1}

# Product attributes governance needs to verify typical marketing claims.
REQUIRED_PRODUCT_ATTRS = [
    ("price", HIGH), ("battery", HIGH), ("processor", MEDIUM), ("memory", MEDIUM), ("storage", MEDIUM),
    ("display", MEDIUM), ("warranty", HIGH), ("performance_claim", MEDIUM), ("availability", LOW),
]

_PRODUCTS_HREF = "/brand-dna/products"
_UPLOAD_HREF = "/brand-dna"


def _lc(label: str) -> str:
    """'Memory (RAM)' -> 'memory (RAM)'; keeps acronyms readable."""
    return label[:1].lower() + label[1:]


def _corpus(db: Session, org_id: str) -> List[tuple]:
    """(text, source label, page) for confirmed rules and guideline chunks."""
    out = []
    for r in db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_confirmed == True).all():  # noqa: E712
        out.append((f"{r.title}. {r.rule_text}", r.source_document or f"Rule: {r.title}", r.page_reference))
    rows = (db.query(DocumentChunk, BrandGuideline).join(BrandGuideline, DocumentChunk.guideline_id == BrandGuideline.id)
            .filter(BrandGuideline.org_id == org_id, BrandGuideline.status != "superseded").all())
    for ch, g in rows:
        out.append((ch.content, g.filename, ch.page_number))
    return out


def _find(corpus: List[tuple], pattern: str) -> Optional[tuple]:
    rx = re.compile(pattern, re.IGNORECASE)
    for text, src, page in corpus:
        m = rx.search(text)
        if m:
            s = max(0, m.start() - 60)
            return (src, page, ("…" if s else "") + text[s:m.end() + 80].strip() + "…")
    return None


def _item(key, label, status, priority, detail, recommendation="", evidence=None, action=None, group="Policy"):
    return {"key": key, "label": label, "status": status, "priority": priority, "group": group, "detail": detail,
            "recommendation": recommendation,
            "evidence": ({"source": evidence[0], "page": evidence[1], "excerpt": evidence[2]} if evidence else None),
            "action": action}


def detect_gaps(db: Session, org_id: str) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        return None
    pt.bootstrap_products(db, org_id)
    now = datetime.datetime.utcnow()
    corpus = _corpus(db, org_id)
    items: List[dict] = []
    product_matrix = []

    # ------------------------------------------------------------ products
    products = db.query(Product).filter(Product.org_id == org_id).all()
    if not products:
        items.append(_item("product_names", "Official product names", MISSING, HIGH,
                           "No products are defined, so product claims cannot be verified.",
                           "Add each product with its official name and model number.",
                           action={"label": "Add a product", "href": _PRODUCTS_HREF}, group="Products"))
    for p in products:
        facts = [f for f in p.facts]
        current = {f.attribute: f for f in facts if f.status == FACT_APPROVED and (f.valid_until is None or f.valid_until > now)}
        pending = {f.attribute for f in facts if f.status == FACT_PENDING}
        row = {"product": p.name, "product_id": p.id, "attributes": []}
        for attr, prio in REQUIRED_PRODUCT_ATTRS:
            label = PRODUCT_ATTRIBUTES[attr]
            f = current.get(attr)
            if f is None:
                expired = [x for x in facts if x.attribute == attr and x.status == FACT_APPROVED and x.valid_until and x.valid_until <= now]
                st = STALE if expired else MISSING
                row["attributes"].append({"attribute": attr, "label": label, "status": st, "pending": attr in pending})
                items.append(_item(
                    f"product:{p.id}:{attr}", f"{p.name} — {label}", st, prio,
                    (f"The approved value for {_lc(label)} expired on {expired[0].valid_until:%d %b %Y}." if expired
                     else f"Nothing approved is on record for {_lc(label)}.")
                    + (" An AI-extracted proposal is waiting for approval." if attr in pending else ""),
                    f"Upload the source document or add the approved value for {_lc(label)} with its reference.",
                    action={"label": "Review pending facts" if attr in pending else "Add fact", "href": _PRODUCTS_HREF},
                    group="Products"))
            else:
                weak = not f.evidence_excerpt
                row["attributes"].append({"attribute": attr, "label": label, "status": WEAK if weak else OK,
                                          "value": f.value_text, "pending": False})
                items.append(_item(f"product:{p.id}:{attr}", f"{p.name} — {label}", OK, prio,
                                   f"Approved: {f.value_text}", group="Products",
                                   evidence=(f.source_document, f.page_reference, f.evidence_excerpt) if f.evidence_excerpt else None))
                if weak:
                    items.append(_item(
                        f"source:{f.id}", f"{p.name} — {label} has no document evidence", WEAK, LOW,
                        f"“{f.value_text}” is approved (source: {f.source_document or 'unknown'}) but the value was "
                        "not found in any uploaded guideline, so findings cannot quote it.",
                        "Upload the referenced document so its passage can be cited.",
                        action={"label": "Upload document", "href": _UPLOAD_HREF}, group="Sources"))
        if not p.model_number:
            row["attributes"].append({"attribute": "model_number", "label": "Model number", "status": MISSING, "pending": False})
            items.append(_item(f"product:{p.id}:model_number", f"{p.name} — Model number", MISSING, LOW,
                               "No model number is recorded, so wrong model numbers in copy cannot be detected.",
                               "Add the official model number.", action={"label": "Edit product", "href": _PRODUCTS_HREF},
                               group="Products"))
        product_matrix.append(row)

        # conflicts: guideline text stating a different launch price
        price = current.get("price")
        if price and price.value_num:
            rx = re.compile(r"(?:launch|official|approved)\s+price[^.₹]{0,40}₹\s*([\d,]+)", re.IGNORECASE)
            for text, src, page in corpus:
                for m in rx.finditer(text):
                    v = float(m.group(1).replace(",", ""))
                    if abs(v - price.value_num) > 0.5 and p.name.split()[0].lower() in text.lower():
                        items.append(_item(
                            f"conflict:price:{p.id}:{src}:{page}", f"{p.name} — conflicting price", CONFLICT, HIGH,
                            f"The approved price is {price.value_text} but “{src}” states ₹{v:,.0f}.",
                            "Confirm which price is current and supersede the other source.",
                            evidence=(src, page, text[max(0, m.start() - 40):m.end() + 40].strip()),
                            action={"label": "Review product facts", "href": _PRODUCTS_HREF}, group="Conflicts"))

    # legacy ApprovedFact vs ProductFact disagreement
    for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id, ApprovedFact.category.ilike("pricing")).all():
        m = re.search(r"₹\s*([\d,]+)", f.fact_value)
        if not m:
            continue
        v = float(m.group(1).replace(",", ""))
        for p in products:
            if p.name.lower() in f.fact_key.lower():
                cur = [x for x in p.facts if x.attribute == "price" and x.status == FACT_APPROVED and x.value_num]
                if cur and abs(cur[0].value_num - v) > 0.5:
                    items.append(_item(f"conflict:fact:{f.id}", f"{p.name} — Brand DNA and Product Truth disagree", CONFLICT, HIGH,
                                       f"Approved fact “{f.fact_key}” says {f.fact_value}; Product Truth says {cur[0].value_text}.",
                                       "Update or retire the outdated record.", group="Conflicts",
                                       action={"label": "Review product facts", "href": _PRODUCTS_HREF}))

    # ------------------------------------------------------------ policy areas
    def policy(key, label, pattern, prio, recommendation, missing_detail):
        ev = _find(corpus, pattern)
        if ev:
            items.append(_item(key, label, OK, prio, "Covered in your Brand DNA.", evidence=ev))
        else:
            items.append(_item(key, label, MISSING, prio, missing_detail, recommendation,
                               action={"label": "Upload guideline", "href": _UPLOAD_HREF}))

    policy("visual_colours", "Brand colour palette", r"\b(colou?r palette|brand colou?rs?|#[0-9a-f]{6}|hex\b|pantone)", HIGH,
           "Upload the visual identity guideline with approved HEX values.",
           "No approved brand colours were found, so colour compliance cannot be checked.")
    policy("visual_logo", "Logo usage rules", r"\blogo\b", HIGH,
           "Upload logo usage rules (clear space, minimum size, backgrounds).",
           "No logo usage rules were found.")
    policy("typography", "Typography standards", r"\b(typeface|typography|font)\b", MEDIUM,
           "Add approved fonts, weights and hierarchy.", "No typography standard was found.")
    policy("disclaimers", "Disclaimer requirements", r"\b(disclaimer|terms (and|&) conditions apply|t&c|\*conditions)\b", HIGH,
           "Add which claims need disclaimers and the exact wording.",
           "No disclaimer requirements were found, so missing disclaimers cannot be detected.")
    policy("regional", "Regional guidelines", r"\b(region(al)?|market-specific|state-wise|country|locali[sz])\b", LOW,
           "Add region- or market-specific rules if you advertise in several regions.",
           "No regional or market-specific guidance was found.")
    policy("competitor", "Approved competitor comparisons", r"\b(competitor|comparative|compared (to|with))\b", MEDIUM,
           "Record which comparisons are approved and their benchmark source.",
           "No guidance on competitor comparisons was found.")
    policy("benchmark", "Official performance benchmarks", r"\b(benchmark|tested by|lab test|certified test)\b", MEDIUM,
           "Upload the benchmark or test report that substantiates performance claims.",
           "No benchmark source was found for performance claims.")

    n_terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id, TerminologyRule.is_active == True).count()  # noqa: E712
    items.append(_item("terminology", "Prohibited terminology", OK if n_terms else MISSING, MEDIUM,
                       f"{n_terms} active terminology rule(s)." if n_terms else "No prohibited terms are defined.",
                       "" if n_terms else "Add terms the brand must avoid and their approved replacements.",
                       action=None if n_terms else {"label": "Open Brand DNA", "href": _UPLOAD_HREF}))

    # approved logos (Brand Asset Library) — only if the library exists
    try:
        from backend.app.models.asset import BrandAsset
        n_logos = db.query(BrandAsset).filter(BrandAsset.org_id == org_id, BrandAsset.kind == "logo",
                                              BrandAsset.status.in_(["approved", "active"])).count()
        items.append(_item("assets_logo", "Approved logo files", OK if n_logos else MISSING, HIGH,
                           f"{n_logos} approved logo(s) in the Asset Library." if n_logos
                           else "No approved logo file is stored, so logo misuse cannot be detected.",
                           "" if n_logos else "Upload the official logo files to the Brand Asset Library.",
                           action=None if n_logos else {"label": "Open Asset Library", "href": "/visual-dna"}, group="Assets"))
    except ImportError:
        pass

    # ------------------------------------------------------------ claims evidence
    unsupported = (db.query(ClaimVerification.claim_text, func.count(ClaimVerification.id))
                   .join(Submission, ClaimVerification.submission_id == Submission.id)
                   .filter(Submission.org_id == org_id, ClaimVerification.status.in_(["Unsupported", "Needs Human Review"]))
                   .group_by(ClaimVerification.claim_text).order_by(func.count(ClaimVerification.id).desc()).limit(5).all())
    for text, n in unsupported:
        if n >= 2:
            items.append(_item(f"claim:{text[:40]}", f"Recurring claim without evidence: “{text[:60]}”", MISSING, MEDIUM,
                               f"Flagged as unsupported in {n} reviews.",
                               "Add substantiating evidence as an approved claim, or add it to prohibited terminology.",
                               action={"label": "Open ClaimDNA", "href": "/claim-dna"}, group="Claims"))

    # ------------------------------------------------------------ governance hygiene
    pending_rules = db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_confirmed == False).count()  # noqa: E712
    if pending_rules:
        items.append(_item("unconfirmed_rules", "Unconfirmed extracted rules", WEAK, MEDIUM,
                           f"{pending_rules} rule(s) extracted from documents are not confirmed, so they are not enforced.",
                           "Review and confirm or discard them.", action={"label": "Review rules", "href": _UPLOAD_HREF},
                           group="Sources"))
    items.append(_item("ownership", "Policy ownership", MISSING, LOW,
                       "Rules do not record an owner, so nobody is accountable for keeping them current.",
                       "Assign an owner to each policy area (feature not yet available in BrandVault).", group="Sources"))
    eff = _find(corpus, r"\beffective (date|from)\b")
    items.append(_item("effective_dates", "Effective dates on guidelines", OK if eff else MISSING, MEDIUM,
                       "Guideline states an effective date." if eff else "No effective date was found in uploaded guidelines.",
                       "" if eff else "Add the effective date and version to each guideline.", evidence=eff, group="Sources"))
    old_docs = [g for g in db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).all()
                if g.created_at and (now - g.created_at).days > 365]
    for g in old_docs:
        items.append(_item(f"stale_doc:{g.id}", f"Old source document: {g.filename}", STALE, MEDIUM,
                           f"Uploaded {g.created_at:%d %b %Y}, over a year ago.", "Confirm it is still current or upload the new version.",
                           group="Sources"))
    expired_facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id, ApprovedFact.valid_until != None,  # noqa: E711
                                                  ApprovedFact.valid_until <= now).all()
    for f in expired_facts:
        items.append(_item(f"expired_fact:{f.id}", f"Expired fact still on record: {f.fact_key}", STALE, LOW,
                           f"Expired on {f.valid_until:%d %b %Y}{'; superseded by ' + f.superseded_by if f.superseded_by else ''}.",
                           "Keep it for history, and make sure campaigns no longer use it.", group="Sources"))
    # Guideline Gap Agent: product values that disagree across the current documents.
    for c in guideline_conflicts(db, org_id):
        a, b = c["values"][0], c["values"][1]
        items.append(_item(f"guideline_conflict:{c['product']}:{c['attribute']}",
                           f"Guidelines disagree: {c['product']} {c['attribute_label']}", CONFLICT, HIGH,
                           f"{a['text']} ({a['source']}, {a['where']}) vs {b['text']} ({b['source']}, {b['where']})"
                           + (f" and {len(c['values']) - 2} more" if len(c["values"]) > 2 else "") + ".",
                           "Decide which value is correct, fix the other document, and re-upload it.",
                           evidence=(a["source"], a["page"], a["sentence"]), action={"label": "Open Brand DNA", "href": _UPLOAD_HREF},
                           group="Sources"))
    # Facts and rules whose source document has been replaced by a newer version.
    replaced = {g.filename: g for g in db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id,
                                                                     BrandGuideline.status == "superseded").all()}
    if replaced:
        for f in db.query(ProductFact).filter(ProductFact.org_id == org_id, ProductFact.status == FACT_APPROVED,
                                              ProductFact.source_document.in_(list(replaced))).all():
            items.append(_item(f"replaced_source:{f.id}", f"Fact from a replaced document: {f.product.name} {f.attribute}",
                               WEAK, MEDIUM, f"“{f.value_text}” came from {f.source_document}, which has been replaced by a newer version.",
                               "Confirm the value against the new document.", action={"label": "Open Product Truth", "href": "/brand-dna/products"},
                               group="Sources"))
        for r in db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_active == True,  # noqa: E712
                                            BrandRule.source_document.in_(list(replaced))).all():
            items.append(_item(f"replaced_rule:{r.id}", f"Rule from a replaced document: {r.title}", WEAK, LOW,
                               f"Taken from {r.source_document}, which has been replaced.", "Re-confirm or retire this rule.",
                               action={"label": "Review rules", "href": _UPLOAD_HREF}, group="Sources"))
    if not db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).count():
        items.append(_item("no_documents", "Brand guideline documents", MISSING, HIGH, "No guideline has been uploaded.",
                           "Upload your brand guideline PDF.", action={"label": "Upload guideline", "href": _UPLOAD_HREF},
                           group="Sources"))

    # ------------------------------------------------------------ scoring
    scored = [i for i in items if i["status"] in (OK, MISSING, CONFLICT, STALE)]
    total = sum(_WEIGHT[i["priority"]] for i in scored)
    good = sum(_WEIGHT[i["priority"]] for i in scored if i["status"] == OK)
    order = {CONFLICT: 0, MISSING: 1, STALE: 2, WEAK: 3, OK: 4}
    prio = {HIGH: 0, MEDIUM: 1, LOW: 2}
    items.sort(key=lambda i: (order[i["status"]], prio[i["priority"]]))
    counts = {s: sum(1 for i in items if i["status"] == s) for s in (OK, MISSING, CONFLICT, STALE, WEAK)}

    docs: List[str] = []
    keys = {i["key"].split(":")[0] if i["status"] != OK else "" for i in items}
    def want(cond, doc):
        if cond and doc not in docs:
            docs.append(doc)
    want(any(i["status"] != OK and i["group"] == "Products" for i in items), "Product specification sheet for each product")
    want("visual_colours" in keys or "visual_logo" in keys or "assets_logo" in keys, "Visual identity guideline (logo, colours, clear space)")
    want("typography" in keys, "Typography standard")
    want("disclaimers" in keys, "Legal disclaimer policy")
    want("benchmark" in keys or "competitor" in keys or "claim" in keys, "Claims substantiation file / benchmark reports")
    want("regional" in keys, "Regional marketing guidelines")

    return {
        "org": {"id": org.id, "name": org.name},
        "completeness": round(100 * good / total) if total else 0,
        "counts": counts,
        "items": items,
        "products": product_matrix,
        "recommended_documents": docs,
        "basis": "Computed from stored Brand DNA records. Gaps are never filled automatically.",
        "generated_at": now.isoformat() + "Z",
    }


_SENTENCES = re.compile(r"(?<=[.!?])\s+")
_NEGATED = re.compile(r"\b(not|never|no longer|prohibited|forbidden|incorrect|wrong|instead of|must not|do not|don't|contradict\w*)\b", re.I)
_ATTR_LABELS = {"price": "price", "battery": "battery life", "ai_performance": "AI performance", "processor": "clock speed",
                "storage": "storage", "display": "display size", "display_refresh": "refresh rate", "weight": "weight",
                "warranty": "warranty"}


def guideline_conflicts(db: Session, org_id: str) -> List[dict]:
    """Guideline Gap Agent: the same product attribute stated with different values in current documents.

    Values come from the same deterministic parser Product Truth uses. A conflict is
    reported only when two passages that both name the product give values that differ
    by more than 1%, so wording differences alone never count.
    """
    products = [p.name for p in db.query(Product).filter(Product.org_id == org_id).all() if p.name]
    if not products:
        return []
    rows = (db.query(DocumentChunk, BrandGuideline).join(BrandGuideline, DocumentChunk.guideline_id == BrandGuideline.id)
            .filter(BrandGuideline.org_id == org_id, BrandGuideline.status != "superseded").all())
    seen: Dict[tuple, List[dict]] = {}
    for ch, g in rows:
        low = (ch.content or "").lower()
        named = [p for p in products if p.lower() in low]
        if len(named) != 1:  # ambiguous or no product: do not guess which product a number belongs to
            continue
        for sentence in _SENTENCES.split(ch.content or ""):
            if _NEGATED.search(sentence):  # "never advertise ₹69,999" states a forbidden value, not a fact
                continue
            for v in pt.parse_values(sentence):
                if v.qualifier == "min" or v.attribute not in _ATTR_LABELS:
                    continue
                seen.setdefault((named[0], v.attribute), []).append(
                    {"value": v.value, "unit": v.unit, "text": v.text.strip(), "source": g.filename, "page": ch.page_number,
                     "where": ch.section_label or f"page {ch.page_number}", "sentence": sentence.strip()[:240]})
    out = []
    for (product, attr), vals in seen.items():
        distinct: List[dict] = []
        for v in vals:
            if not any(abs(v["value"] - d["value"]) <= 0.01 * max(abs(d["value"]), 1e-9) for d in distinct):
                distinct.append(v)
        # Only documents contradicting *each other* count; one document is assumed internally consistent.
        if len(distinct) > 1 and len({d["source"] for d in distinct}) > 1:
            out.append({"product": product, "attribute": attr, "attribute_label": _ATTR_LABELS[attr], "values": distinct})
    return out
