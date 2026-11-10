"""
AI Reviewer Intelligence — what human decisions say about the AI and the rules.

Compares AI findings with recorded human decisions to surface governance
patterns: rules reviewers keep approving despite (possible unclear policy or an
unwritten exception), rejections the AI did not anticipate (possible rule gap),
rules reviewers decide differently on (ambiguity), terminology that keeps being
rejected, repeated corrections, turnaround times and queue bottlenecks.

Principles: this analyses policies and patterns, not people. There are no
reviewer rankings, and a high override rate is never treated as poor review.
Patterns need repeated evidence (MIN_EVIDENCE); below that the engine reports
"insufficient data" instead of guessing. It never edits guidelines — an
administrator can turn a suggestion into an unconfirmed draft rule.
"""
from __future__ import annotations

import datetime
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.submission import Submission, Revision
from backend.app.db.eager import SUBMISSION_FULL

MIN_EVIDENCE = 2           # occurrences needed before calling something a pattern
AUTHORITATIVE = ("Approved", "Rejected", "Revision Requested")


def _hours(a: datetime.datetime, b: datetime.datetime) -> float:
    return round((b - a).total_seconds() / 3600, 1)


def analyse(db: Session, org_id: str) -> dict:
    now = datetime.datetime.utcnow()
    subs = db.query(Submission).options(*SUBMISSION_FULL).filter(Submission.org_id == org_id).all()
    decisions = []  # (submission, approval)
    for s in subs:
        for a in s.approvals:
            if a.decision in AUTHORITATIVE:
                decisions.append((s, a))

    # Findings that existed when the decision was taken = findings on the decided
    # version (approvals are version-locked; older records without a version are
    # matched to the current findings).
    def findings_at(s: Submission, a) -> list:
        return [f for f in s.findings if not f.is_applied] if a.submission_version in (None, s.version) else []

    # 1) overridden: approved while open findings existed
    overridden: Dict[str, dict] = {}
    for s, a in decisions:
        if a.decision != "Approved":
            continue
        for f in findings_at(s, a):
            k = f.rule_reference
            o = overridden.setdefault(k, {"rule": k, "category": f.issue_category, "severity": f.severity, "count": 0,
                                          "examples": [], "comments": []})
            o["count"] += 1
            if len(o["examples"]) < 3:
                o["examples"].append({"submission_id": s.id, "title": s.title, "text": f.original_text})
            if a.comments and len(o["comments"]) < 3 and a.comments not in o["comments"]:
                o["comments"].append(a.comments[:200])

    # 2) unanticipated rejections: humans rejected but the AI scored the copy well
    unanticipated = [{"submission_id": s.id, "title": s.title, "score": s.overall_score, "decision": a.decision,
                      "reviewer_comment": (a.comments or "")[:200]}
                     for s, a in decisions if a.decision != "Approved" and s.overall_score >= 80]

    # 3) disagreements: same rule, different outcomes across reviewers
    outcomes: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for s, a in decisions:
        for f in findings_at(s, a):
            outcomes[f.rule_reference][a.decision].add(a.reviewer_name)
    disagreements = []
    for rule, by_dec in outcomes.items():
        if "Approved" in by_dec and len(by_dec) > 1:
            n = sum(len(v) for v in by_dec.values())
            disagreements.append({"rule": rule, "decisions": {d: len(v) for d, v in by_dec.items()}, "reviewers_involved": n})

    # 4) commonly rejected terminology
    rej_terms = Counter()
    for s, a in decisions:
        if a.decision != "Approved":
            for f in findings_at(s, a):
                if f.issue_category == "Terminology":
                    rej_terms[f.original_text.strip().lower()] += 1

    # 5) repeated corrections actually applied by people
    applied = Counter()
    for s in subs:
        for f in s.findings:
            if f.is_applied:
                applied[(f.original_text.strip().lower(), f.suggested_correction.strip())] += 1

    # 6) turnaround: first time content existed -> human decision
    turnaround = []
    for s, a in decisions:
        if a.created_at and s.created_at:
            turnaround.append(_hours(s.created_at, a.created_at))
    waiting = sorted([{"submission_id": s.id, "title": s.title, "status": s.status,
                       "waiting_hours": _hours(s.updated_at or s.created_at, now)}
                      for s in subs if s.status in ("Pending Review", "Analysed")],
                     key=lambda x: -x["waiting_hours"])

    # ---------------------------------------------- recommendations
    recs: List[dict] = []
    for o in sorted(overridden.values(), key=lambda x: -x["count"]):
        if o["count"] >= MIN_EVIDENCE:
            recs.append({
                "kind": "clarify_policy", "title": f"Clarify “{o['rule']}”",
                "detail": f"Reviewers approved content {o['count']} times while this {o['severity'].lower()} finding was open. "
                          "There may be an exception the guideline does not state, or the rule may be broader than intended.",
                "evidence": o["examples"], "reviewer_comments": o["comments"],
                "proposed_rule": f"Clarification needed for “{o['rule']}”: state when it applies and any approved exceptions."})
    for d in disagreements:
        if d["reviewers_involved"] >= MIN_EVIDENCE:
            recs.append({"kind": "align_reviewers", "title": f"Reviewers decide differently on “{d['rule']}”",
                         "detail": "The same finding led to different decisions. Add reviewer guidance with examples of acceptable and "
                                   "unacceptable wording.", "evidence": [d], "reviewer_comments": [],
                         "proposed_rule": f"Reviewer guidance for “{d['rule']}”: acceptable vs unacceptable examples."})
    if len(unanticipated) >= MIN_EVIDENCE:
        recs.append({"kind": "rule_gap", "title": "Reviewers reject content the AI scored highly",
                     "detail": f"{len(unanticipated)} rejection(s) scored 80+ by the AI. Reviewer comments may describe rules not yet in Brand DNA.",
                     "evidence": unanticipated[:3], "reviewer_comments": [u["reviewer_comment"] for u in unanticipated[:3] if u["reviewer_comment"]],
                     "proposed_rule": "Capture the reasons in these reviewer comments as explicit brand rules."})
    for term, n in rej_terms.most_common(3):
        if n >= MIN_EVIDENCE:
            recs.append({"kind": "terminology", "title": f"“{term}” is repeatedly rejected",
                         "detail": f"Present in {n} rejected or returned submissions. Consider guidance for creators before review.",
                         "evidence": [], "reviewer_comments": [],
                         "proposed_rule": f"Creator guidance: avoid “{term}”; use the approved alternative."})

    enough = len(decisions) >= 5
    return {
        "decisions_analysed": len(decisions),
        "data_sufficient": enough,
        "data_note": ("" if enough else
                      f"Only {len(decisions)} human decision(s) are recorded. Patterns need repeated evidence "
                      f"(at least {MIN_EVIDENCE} occurrences, and more decisions overall) before they are reliable."),
        "overridden_findings": sorted(overridden.values(), key=lambda x: -x["count"]),
        "unanticipated_rejections": unanticipated,
        "disagreements": disagreements,
        "rejected_terminology": [{"term": t, "count": n} for t, n in rej_terms.most_common(8)],
        "repeated_corrections": [{"from": k[0], "to": k[1], "count": n} for k, n in applied.most_common(8)],
        "turnaround": {
            "decisions_timed": len(turnaround),
            "median_hours": statistics.median(turnaround) if turnaround else None,
            "max_hours": max(turnaround) if turnaround else None,
        },
        "queue": {"waiting": len(waiting), "oldest": waiting[:8]},
        "recommendations": recs,
        "principles": "Analyses policies and patterns, not people: no reviewer rankings, and overrides are treated as "
                      "signals about the rules, not as reviewer errors. Guidelines are never changed automatically.",
        "generated_at": now.isoformat() + "Z",
    }
