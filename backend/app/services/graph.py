"""
Brand Knowledge Graph builder (Round 2 / R2-2).

Assembles a graph purely from REAL persisted records — no fabricated nodes or
relationships. The structure is:

    Brand
      ├─ Guidelines ─ Guideline ─ Evidence (document chunk, by page)
      ├─ Brand Rules ─ Rule
      ├─ Approved Facts ─ Fact
      ├─ Terminology ─ Term
      └─ Campaigns ─ Campaign (submission)
                       ├─ Finding  ──references──▶ Rule   (when the finding's
                       │                                    rule_reference matches
                       │                                    a real rule title)
                       ├─ Claim
                       └─ Brand Passport

Every node carries real fields in `meta` and an `href` into the owning module,
so clicking a node opens its genuine detail. `references` edges are only added
when they resolve against real data; nothing is invented.
"""
from __future__ import annotations

import datetime
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.brand import (
    Organization, BrandGuideline, DocumentChunk, BrandRule, ApprovedFact, TerminologyRule,
)
from backend.app.models.submission import Submission
from backend.app.db.eager import SUBMISSION_FULL


def _node(nid: str, ntype: str, label: str, parent: Optional[str] = None,
          count: Optional[int] = None, meta: Optional[dict] = None, href: Optional[str] = None) -> dict:
    n: dict = {"id": nid, "type": ntype, "label": label, "parent": parent}
    if count is not None:
        n["count"] = count
    if href:
        n["href"] = href
    n["meta"] = meta or {}
    return n


def build_brand_graph(db: Session, org_id: str) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    nodes: list[dict] = []
    edges: list[dict] = []

    def link(a: str, b: str, kind: str = "contains") -> None:
        edges.append({"source": a, "target": b, "kind": kind})

    BRAND = "brand"
    nodes.append(_node(BRAND, "brand", org.name, href="/brand-dna", meta={"slug": org.slug}))

    guidelines = db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).all()
    rules = db.query(BrandRule).filter(BrandRule.org_id == org_id).all()
    facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()
    subs = (
        db.query(Submission)
        .options(*SUBMISSION_FULL)
        .filter(Submission.org_id == org_id)
        .order_by(Submission.created_at.desc())
        .all()
    )

    categories = [
        ("cat-guidelines", "Guidelines", len(guidelines), "/brand-dna"),
        ("cat-rules", "Brand Rules", len(rules), "/brand-dna"),
        ("cat-facts", "Approved Facts", len(facts), "/claim-dna"),
        ("cat-terms", "Terminology", len(terms), "/brand-dna"),
        ("cat-campaigns", "Campaigns", len(subs), "/content-intelligence"),
    ]
    for cid, label, count, href in categories:
        nodes.append(_node(cid, "category", label, parent=BRAND, count=count, href=href))
        link(BRAND, cid)

    # Guidelines + their evidence chunks.
    for g in guidelines:
        gid = f"guideline-{g.id}"
        nodes.append(_node(gid, "guideline", g.filename, parent="cat-guidelines", href="/brand-dna",
                           meta={"pages": g.total_pages, "status": g.status, "fileType": g.file_type}))
        link("cat-guidelines", gid)
        for c in db.query(DocumentChunk).filter(DocumentChunk.guideline_id == g.id).all():
            eid = f"evidence-{c.id}"
            nodes.append(_node(eid, "evidence", f"Page {c.page_number}", parent=gid,
                               meta={"page": c.page_number, "content": c.content[:400]}))
            link(gid, eid)

    # Rules (index by title for finding->rule cross-links).
    rule_by_title: dict[str, str] = {}
    for r in rules:
        rid = f"rule-{r.id}"
        if r.title:
            rule_by_title[r.title.lower()] = rid
        nodes.append(_node(rid, "rule", r.title, parent="cat-rules", href="/brand-dna",
                           meta={"category": r.category, "severity": r.severity, "text": r.rule_text,
                                 "source": r.source_document, "page": r.page_reference, "confirmed": r.is_confirmed}))
        link("cat-rules", rid)

    # Approved facts.
    now = datetime.datetime.utcnow()
    for f in facts:
        fid = f"fact-{f.id}"
        outdated = bool(f.valid_until and f.valid_until < now)
        nodes.append(_node(fid, "fact", f.fact_key, parent="cat-facts", href="/claim-dna",
                           meta={"category": f.category, "value": f.fact_value, "source": f.verification_source,
                                 "outdated": outdated, "supersededBy": f.superseded_by}))
        link("cat-facts", fid)

    # Terminology.
    for t in terms:
        tid = f"term-{t.id}"
        nodes.append(_node(tid, "term", t.prohibited_term, parent="cat-terms", href="/brand-dna",
                           meta={"preferred": t.preferred_term, "explanation": t.explanation}))
        link("cat-terms", tid)

    # Campaigns (submissions) + findings, claims, passport.
    for s in subs:
        sid = f"campaign-{s.id}"
        nodes.append(_node(sid, "campaign", s.title, parent="cat-campaigns", href="/content-intelligence",
                           meta={"status": s.status, "score": s.overall_score, "author": s.author_name,
                                 "content": s.content[:300]}))
        link("cat-campaigns", sid)

        for fd in s.findings:
            fdid = f"finding-{fd.id}"
            nodes.append(_node(fdid, "finding", fd.issue_category, parent=sid,
                               meta={"severity": fd.severity, "text": fd.original_text,
                                     "ruleReference": fd.rule_reference, "evidence": fd.evidence_source,
                                     "engine": fd.analysis_engine}))
            link(sid, fdid)
            # Real cross-link: finding -> rule when its rule_reference resolves to a rule title.
            rr = (fd.rule_reference or "").lower()
            if rr:
                for title_l, rnid in rule_by_title.items():
                    if len(title_l) > 6 and (title_l in rr or rr in title_l):
                        link(fdid, rnid, kind="references")
                        break

        for cv in s.claim_verifications:
            cvid = f"claim-{cv.id}"
            label = (cv.claim_text or "")[:60] + ("…" if cv.claim_text and len(cv.claim_text) > 60 else "")
            nodes.append(_node(cvid, "claim", label or "Claim", parent=sid,
                               meta={"status": cv.status, "category": cv.category, "explanation": cv.explanation,
                                     "evidence": cv.evidence_text, "source": cv.source_reference}))
            link(sid, cvid)

        if s.passport:
            pp = s.passport
            pid = f"passport-{pp.id}"
            nodes.append(_node(pid, "passport", pp.passport_number, parent=sid, href="/brand-passport",
                               meta={"status": pp.verification_status, "score": pp.final_score, "auditor": pp.audited_by}))
            link(sid, pid)

    stats = {
        "guidelines": len(guidelines), "rules": len(rules), "facts": len(facts),
        "terms": len(terms), "campaigns": len(subs),
        "nodes": len(nodes), "edges": len(edges),
    }
    return {"brand": {"id": org.id, "name": org.name}, "nodes": nodes, "edges": edges, "stats": stats}
