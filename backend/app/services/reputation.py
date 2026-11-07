"""
Brand Reputation Early Warning.

Works on feedback the organisation is authorised to use: uploaded CSV/JSON
exports (reviews, support tickets, surveys) or records added manually. There is
no scraping and no live social integration yet — the overview says so.

Per record (deterministic, explainable):
  sentiment     lexicon with negation and intensifier handling; a star rating,
                when present, takes precedence (1-2 negative, 3 neutral, 4-5 positive)
  categories    keyword taxonomy (battery, performance, price, delivery, ...)
  product       approved product names mentioned
Aggregates: sentiment overview, complaint categories, recurring phrases,
affected products, campaign-related feedback (claims customers dispute),
negative trend and emerging themes — trends only when enough data exists.

Model-derived sentiment is a signal, not confirmed customer opinion.
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

POS = set("""good great excellent amazing love loved awesome fantastic fast smooth reliable recommend happy perfect
superb brilliant impressed impressive solid worth premium beautiful sharp crisp helpful quick satisfied best nice""".split())
NEG = set("""bad poor terrible awful horrible hate hated slow broken defective faulty disappointed disappointing worst
useless overpriced expensive refund return returned crash crashes crashed lag laggy overheating overheats hot noisy
fake misleading lie lied scam cheated delay delayed late rude unhelpful issue issues problem problems drain drains
dies died dead cracked flicker flickering bug bugs buggy waste regret annoying""".split())
NEGATORS = {"not", "no", "never", "isn't", "wasn't", "don't", "doesn't", "didn't", "hardly", "barely", "without", "cannot", "can't", "won't"}
INTENSIFIERS = {"very", "really", "extremely", "so", "super", "totally", "absolutely"}

CATEGORIES: Dict[str, List[str]] = {
    "Battery": ["battery", "charge", "charging", "backup", "drain", "hours"],
    "Performance": ["slow", "lag", "laggy", "performance", "speed", "fast", "hang", "freez", "overheat", "hot", "fan"],
    "Price & billing": ["price", "overpriced", "expensive", "cost", "billing", "charged", "emi", "discount", "₹"],
    "Delivery": ["delivery", "delivered", "shipping", "courier", "late", "delay", "arrived"],
    "Support": ["support", "service", "customer care", "agent", "helpline", "rude", "response"],
    "Quality & defects": ["broken", "defect", "defective", "faulty", "crack", "dead pixel", "build quality", "damaged"],
    "Display": ["screen", "display", "flicker", "brightness", "pixel"],
    "Software": ["software", "update", "bug", "crash", "driver", "windows", "app"],
    "Warranty & returns": ["warranty", "refund", "return", "replacement", "repair"],
    "Advertising claims": ["advertised", "claimed", "claims", "promised", "misleading", "fake", "false", "ad said", "as shown"],
}
# Complaints that carry no single negative word ("lasts 5 hours, not 18 as advertised").
COMPLAINT_PATTERNS = re.compile(
    r"\bnot\b[^.!?]{0,40}\bas (advertised|claimed|promised|shown|described)\b"
    r"|\b(doesn'?t|does not|did not|didn'?t|stopped|isn'?t|is not|not) (work|working|charge|charging|turn on|boot)\b"
    r"|\bonly lasts\b|\blasts only\b|\bnever (arrived|came|works?)\b|\bwant(ed)? (a|my) refund\b",
    re.I)
MIN_FOR_TREND = 6           # records per period before a trend is reported
_WORD = re.compile(r"[a-z₹'][a-z0-9₹']*")


def score_sentiment(text: str, rating: Optional[float]) -> Tuple[str, float, str]:
    if rating is not None:
        if rating <= 2:
            return "negative", round(-1 + (rating - 1) * 0.25, 2), "rating"
        if rating >= 4:
            return "positive", round(0.5 + (rating - 4) * 0.5, 2), "rating"
        return "neutral", 0.0, "rating"
    words = _WORD.findall(text.lower())
    total = 0.0
    for i, w in enumerate(words):
        val = 1.0 if w in POS else -1.0 if w in NEG else 0.0
        if not val:
            continue
        window = words[max(0, i - 3):i]
        if any(x in NEGATORS for x in window):
            val = -val * 0.8
        if any(x in INTENSIFIERS for x in window):
            val *= 1.5
        total += val
    total -= 1.5 * len(COMPLAINT_PATTERNS.findall(text))
    norm = max(-1.0, min(1.0, total / 3))
    label = "positive" if norm >= 0.2 else "negative" if norm <= -0.2 else "neutral"
    return label, round(norm, 2), "lexicon"


def categorise(text: str) -> List[str]:
    low = text.lower()
    return [c for c, kws in CATEGORIES.items() if any(k in low for k in kws)]


# ----------------------------------------------------------------------------
# Parsing uploads
# ----------------------------------------------------------------------------
_TEXT_COLS = ("text", "review", "feedback", "comment", "message", "body", "content")
_DATE_COLS = ("date", "created_at", "timestamp", "review_date", "time")


def _parse_date(v) -> Optional[datetime.datetime]:
    if not v:
        return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(s[:19], fmt)
        except ValueError:
            continue
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", ""))
    except ValueError:
        return None


def parse_upload(name: str, data: bytes) -> Tuple[List[dict], List[str]]:
    """Return (rows, problems). Rows: text, rating, date, channel, product."""
    problems: List[str] = []
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], ["File is not UTF-8 text."]
    if name.lower().endswith(".json"):
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            return [], [f"Invalid JSON: {e}"]
        if isinstance(items, dict):
            items = items.get("feedback") or items.get("items") or []
        if not isinstance(items, list):
            return [], ["JSON must be a list of feedback objects."]
    else:
        items = list(csv.DictReader(io.StringIO(raw)))
    rows = []
    for n, it in enumerate(items, 1):
        if not isinstance(it, dict):
            problems.append(f"Row {n}: not an object")
            continue
        lower = {str(k).strip().lower(): v for k, v in it.items()}
        text = next((str(lower[c]).strip() for c in _TEXT_COLS if lower.get(c)), "")
        if len(text) < 3:
            problems.append(f"Row {n}: no feedback text")
            continue
        rating = None
        for c in ("rating", "stars", "score"):
            if lower.get(c) not in (None, ""):
                try:
                    rating = max(1.0, min(5.0, float(lower[c])))
                except (TypeError, ValueError):
                    problems.append(f"Row {n}: rating '{lower[c]}' ignored")
                break
        date = next((_parse_date(lower[c]) for c in _DATE_COLS if lower.get(c)), None)
        rows.append({"text": text[:4000], "rating": rating, "date": date,
                     "channel": (str(lower.get("channel") or lower.get("source") or "")[:100] or None),
                     "product": (str(lower.get("product") or "")[:255] or None)})
    return rows, problems


# ----------------------------------------------------------------------------
# Overview
# ----------------------------------------------------------------------------
def _bigrams(text: str) -> List[str]:
    w = [x for x in _WORD.findall(text.lower()) if len(x) > 2 and x not in {"the", "and", "for", "was", "but", "this", "with", "very", "after"}]
    return [f"{a} {b}" for a, b in zip(w, w[1:])]


def overview(records: list, campaigns: List[Tuple[str, str, str]], days: int = 90) -> dict:
    """records: FeedbackRecord rows; campaigns: (id, title, content)."""
    now = datetime.datetime.utcnow()
    recs = [r for r in records if r.feedback_date >= now - datetime.timedelta(days=days)] if days else list(records)
    n = len(recs)
    sent = Counter(r.sentiment for r in recs)
    neg = [r for r in recs if r.sentiment == "negative"]

    cat_all, cat_neg = Counter(), Counter()
    for r in recs:
        for c in r.categories or []:
            cat_all[c] += 1
            if r.sentiment == "negative":
                cat_neg[c] += 1
    categories = [{"category": c, "mentions": cat_all[c], "negative": cat_neg[c],
                   "negative_share": round(100 * cat_neg[c] / cat_all[c]) if cat_all[c] else 0,
                   "samples": [r.text[:220] for r in neg if c in (r.categories or [])][:3]}
                  for c in sorted(cat_all, key=lambda c: (-cat_neg[c], -cat_all[c]))]

    phrases = Counter()
    for r in neg:
        phrases.update(set(_bigrams(r.text)))
    recurring = [{"phrase": p, "count": k} for p, k in phrases.most_common(10) if k >= 2]

    prod = defaultdict(lambda: Counter())
    for r in recs:
        prod[r.product or "Not specified"][r.sentiment] += 1
    products = [{"product": p, "total": sum(c.values()), "negative": c["negative"], "positive": c["positive"],
                 "negative_share": round(100 * c["negative"] / sum(c.values()))} for p, c in prod.items()]
    products.sort(key=lambda x: -x["negative"])

    # campaign-related: negative feedback disputing a figure or claim a campaign made
    camp_links = []
    for cid, title, content in campaigns:
        figures = set(re.findall(r"\d+\s*(?:hours?|hrs?|tops|gb|x)\b|₹\s?[\d,]+", content.lower()))
        phrases_c = {p for p in ("fastest", "10x", "all-day", "all day", "lightest", "best") if p in content.lower()}
        hits = [r for r in neg if (figures and any(f.replace(" ", "") in r.text.lower().replace(" ", "") for f in figures))
                or any(p in r.text.lower() for p in phrases_c)]
        if hits:
            camp_links.append({"submission_id": cid, "title": title, "negative_mentions": len(hits),
                               "disputed": sorted(figures | phrases_c)[:6], "samples": [h.text[:220] for h in hits[:3]]})
    camp_links.sort(key=lambda x: -x["negative_mentions"])

    # trends: weekly negative share, only with enough records
    weeks = defaultdict(lambda: Counter())
    for r in recs:
        wk = (r.feedback_date - datetime.timedelta(days=r.feedback_date.weekday())).strftime("%Y-%m-%d")
        weeks[wk][r.sentiment] += 1
    trend = [{"week": w, "total": sum(c.values()), "negative": c["negative"],
              "negative_share": round(100 * c["negative"] / sum(c.values()))} for w, c in sorted(weeks.items())]
    trend_note, rising = None, False
    usable = [t for t in trend if t["total"] >= MIN_FOR_TREND]
    if len(usable) >= 2:
        rising = usable[-1]["negative_share"] - usable[-2]["negative_share"] >= 10
    else:
        trend_note = f"Insufficient data for a trend: needs at least two weeks with {MIN_FOR_TREND}+ records."

    # emerging themes: category mentions in the last 14 days vs the 14 before
    cut1, cut2 = now - datetime.timedelta(days=14), now - datetime.timedelta(days=28)
    recent, before = Counter(), Counter()
    for r in neg:
        for c in r.categories or []:
            if r.feedback_date >= cut1:
                recent[c] += 1
            elif r.feedback_date >= cut2:
                before[c] += 1
    emerging = [{"category": c, "last_14_days": recent[c], "previous_14_days": before[c]}
                for c in recent if recent[c] >= 3 and recent[c] >= 2 * max(1, before[c])]

    risks = []
    for c in categories:
        if c["negative"] >= 3 and c["negative_share"] >= 50:
            level = "high" if c["category"] in ("Advertising claims", "Quality & defects") or c["negative"] >= 8 else "medium"
            risks.append({"theme": c["category"], "level": level,
                          "why": f"{c['negative']} negative mentions ({c['negative_share']}% of mentions in this theme).",
                          "investigate": _investigate(c["category"])})
    for e in emerging:
        if not any(r["theme"] == e["category"] for r in risks):
            risks.append({"theme": e["category"], "level": "medium",
                          "why": f"Rising: {e['last_14_days']} negative mentions in 14 days vs {e['previous_14_days']} before.",
                          "investigate": _investigate(e["category"])})
    for cl in camp_links:
        risks.append({"theme": f"Campaign: {cl['title']}", "level": "high" if cl["negative_mentions"] >= 3 else "medium",
                      "why": f"{cl['negative_mentions']} negative mention(s) dispute what the campaign claimed ({', '.join(cl['disputed'])}).",
                      "investigate": "Compare the campaign's claims with Product Truth and review it in the Approval Hub."})

    return {
        "window_days": days, "records": n,
        "sentiment": {"positive": sent["positive"], "neutral": sent["neutral"], "negative": sent["negative"],
                      "negative_share": round(100 * sent["negative"] / n) if n else None},
        "engines": dict(Counter(r.sentiment_engine for r in recs)),
        "categories": categories, "recurring_phrases": recurring, "products": products,
        "campaign_related": camp_links, "trend": trend, "trend_note": trend_note, "negative_rising": rising,
        "emerging": emerging, "risks": risks,
        "sources": dict(Counter(r.source for r in recs)),
        "note": ("Sentiment is an automated estimate (rating when provided, otherwise a word list), not confirmed customer "
                 "opinion. Only uploaded or manually added feedback is analysed; no social platform is connected."),
    }


def _investigate(category: str) -> str:
    return {
        "Battery": "Check the battery claims in live campaigns against the approved battery specification.",
        "Advertising claims": "Customers dispute advertised claims. Re-verify live campaigns with ClaimDNA and Product Truth.",
        "Quality & defects": "Share samples with quality engineering; check whether a batch or model is affected.",
        "Price & billing": "Confirm the prices customers saw were approved offers (Product Truth / Brand Fraud Intelligence).",
        "Support": "Review support response times and scripts for the affected channel.",
        "Delivery": "Check with logistics partners for the affected period.",
    }.get(category, "Review the sample feedback and decide whether a campaign or product change is needed.")
