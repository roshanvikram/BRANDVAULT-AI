"""
Brand Fraud Intelligence — investigate suspected impersonation.

Analyses content someone reports (a URL, pasted page text, a screenshot or an
ad image) against the organisation's own records:

  domain        lookalike / typosquat / homoglyph / punycode / brand-in-subdomain
                checks against the official domains an administrator registered
  pricing       offers checked with Product Truth (unauthorised discounts)
  records       does the copy match an approved campaign (Brand Passport)?
  phishing      requests for credentials, OTPs, card or bank details
  logo          official logos located in the screenshot (Asset Forensics)

There is no internet-wide monitoring: only what is submitted is analysed.
Fetching a URL from the server is OFF by default (FRAUD_URL_FETCH_ENABLED) to
avoid server-side request forgery; when enabled it only fetches public http(s)
hosts with size and time limits. Results are "suspected" until a person
confirms them, and visual differences are never called a deepfake.
"""
from __future__ import annotations

import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.brand import Organization
from backend.app.models.intelligence import OfficialDomain
from backend.app.models.product import Product
from backend.app.services import product_truth as pt
from backend.app.services import similarity as sim

SUSPICIOUS_TLDS = {"shop", "top", "xyz", "online", "site", "click", "buzz", "live", "store", "icu", "monster", "rest", "cfd"}
LURE_WORDS = {"offer", "offers", "deal", "deals", "sale", "discount", "free", "gift", "promo", "win", "prize", "lucky",
              "official", "support", "help", "verify", "secure", "login", "account", "refund", "claim", "india"}
HOMOGLYPHS = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s"})
PHISHING = [
    (r"\b(password|passcode|pin)\b", "Asks for a password or PIN"),
    (r"\botp\b|one[- ]time password", "Asks for an OTP"),
    (r"\b(card number|cvv|cvc|expiry date|debit card|credit card)\b", "Asks for card details"),
    (r"\b(bank account|ifsc|net ?banking|upi pin)\b", "Asks for bank details"),
    (r"\b(verify|confirm|update) (your )?(account|identity|kyc)\b", "Asks to verify an account or KYC"),
    (r"\b(aadhaar|pan card|passport number)\b", "Asks for identity documents"),
]
URGENCY = re.compile(r"\b(only today|last chance|expires (today|tonight|in \d+ (hours|minutes))|hurry|act now|limited (slots|stock) left|within 24 hours)\b", re.I)


# ----------------------------------------------------------------------------
# Domains
# ----------------------------------------------------------------------------
def host_of(url: str) -> Optional[str]:
    try:
        u = urllib.parse.urlparse(url if "://" in url else f"http://{url}")
        return (u.hostname or "").lower().rstrip(".") or None
    except ValueError:
        return None


def registrable(host: str) -> Tuple[str, str]:
    """(label, tld) of the registrable domain, e.g. shop.vortexa-tech.co.in -> ('vortexa-tech', 'co.in')."""
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov", "ac") and len(parts[-1]) == 2:
        return parts[-3], ".".join(parts[-2:])
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return host, ""


def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


_CYRILLIC = str.maketrans({"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "к": "k", "т": "t",
                           "в": "b", "н": "h", "м": "m", "і": "i", "ј": "j", "ѕ": "s"})


def _ascii_fold(s: str) -> str:
    """Map look-alike letters to Latin: Cyrillic 'о' -> 'o', accented 'ö' -> 'o'."""
    import unicodedata
    s = s.translate(_CYRILLIC)
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def _decode_idna(label: str) -> str:
    try:
        return label.encode("ascii").decode("idna") if label.startswith("xn--") else label
    except Exception:  # noqa: BLE001
        return label


def brand_tokens(db: Session, org_id: str) -> List[str]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    toks = set()
    for name in [org.name if org else ""] + [p.name for p in db.query(Product).filter(Product.org_id == org_id).all()]:
        for w in re.findall(r"[a-z0-9]+", name.lower()):
            if len(w) >= 4 and w not in {"technologies", "tech", "laptop", "inc", "limited", "ltd", "pro"}:
                toks.add(w)
    return sorted(toks)


def analyse_domain(host: str, official: List[str], tokens: List[str]) -> List[dict]:
    out: List[dict] = []
    if not host:
        return out
    try:
        ipaddress.ip_address(host)
        out.append({"type": "ip_host", "severity": "medium", "title": "Link uses a raw IP address",
                    "evidence": host, "confidence": 0.6})
        return out
    except ValueError:
        pass
    off_hosts = {o.lower().lstrip("*.") for o in official}
    if any(host == o or host.endswith("." + o) for o in off_hosts):
        out.append({"type": "official_domain", "severity": "info", "title": "Hosted on a registered official domain",
                    "evidence": host, "confidence": 0.95})
        return out
    label, tld = registrable(host)
    decoded = ".".join(_decode_idna(p) for p in host.split("."))
    if any(p.startswith("xn--") for p in host.split(".")):
        out.append({"type": "punycode", "severity": "high", "title": "Internationalised (punycode) domain",
                    "evidence": f"{host}" + (f" displays as {decoded}" if decoded != host else " (characters outside plain Latin)"),
                    "confidence": 0.8})
    norm = _ascii_fold(_decode_idna(label)).translate(HOMOGLYPHS).replace("rn", "m").replace("vv", "w")
    off_labels = {registrable(o)[0]: o for o in off_hosts}
    for ol, full in off_labels.items():
        d = _lev(norm.replace("-", ""), ol.replace("-", ""))
        if norm != label and norm.replace("-", "") == ol.replace("-", ""):
            out.append({"type": "homoglyph", "severity": "high", "title": f"Look-alike characters imitate {full}",
                        "evidence": f"{label} → reads as {norm}", "confidence": 0.9})
        elif 0 < d <= 2 and len(ol) >= 5:
            out.append({"type": "typosquat", "severity": "high", "title": f"Typo of the official domain {full}",
                        "evidence": f"{label} is {d} character(s) from {ol}", "confidence": 0.85})
        elif label != ol and tld and full.endswith(tld) is False and norm.replace("-", "") == ol.replace("-", ""):
            out.append({"type": "tld_swap", "severity": "high", "title": f"Official name on a different extension ({tld})",
                        "evidence": host, "confidence": 0.8})
    sub_labels = host.split(".")[:-2]
    for t in tokens:
        if t in norm.replace("-", "") and not any(o.startswith(label) for o in off_labels):
            lure = [w for w in LURE_WORDS if w in label]
            out.append({"type": "brand_in_domain", "severity": "high" if lure or tld in SUSPICIOUS_TLDS else "medium",
                        "title": f"Brand name “{t}” used in an unofficial domain" + (f" with lure word(s) {', '.join(lure)}" if lure else ""),
                        "evidence": host, "confidence": 0.75 if lure else 0.6})
            break
        if any(t in s for s in sub_labels):
            out.append({"type": "brand_in_subdomain", "severity": "high", "title": f"Brand name “{t}” placed in a subdomain of another site",
                        "evidence": host, "confidence": 0.8})
            break
    if tld in SUSPICIOUS_TLDS and out:
        out.append({"type": "suspicious_tld", "severity": "low", "title": f"Extension .{tld} is common in scam sites",
                    "evidence": host, "confidence": 0.4})
    if not official:
        out.append({"type": "no_official_domains", "severity": "info", "title": "No official domains registered",
                    "evidence": "Add your real domains so look-alikes can be measured precisely.", "confidence": 0.0})
    return out


# ----------------------------------------------------------------------------
# Safe fetch (disabled by default)
# ----------------------------------------------------------------------------
def _public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def fetch_page(url: str, timeout: float = 6.0, limit: int = 400_000) -> Tuple[Optional[str], str]:
    """Return (text, note). Only public http(s) hosts; no redirects to private IPs."""
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return None, "Only http and https links can be fetched."
    if not _public_host(u.hostname):
        return None, "The host is not a public internet address, so it was not fetched."

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "BrandVault-Investigator/1.0"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read(limit)
    except Exception as e:  # noqa: BLE001
        return None, f"Could not fetch the page ({type(e).__name__})."
    html = raw.decode("utf-8", errors="ignore")
    has_password = bool(re.search(r"<input[^>]+type=[\"']?password", html, re.I))
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    note = "Fetched page text." + (" The page contains a password field." if has_password else "")
    return text[:20000], note


# ----------------------------------------------------------------------------
# Text signals
# ----------------------------------------------------------------------------
def analyse_text(db: Session, org_id: str, text: str, host_official: bool) -> Tuple[List[dict], dict]:
    out: List[dict] = []
    ctx: dict = {}
    low = text.lower()
    toks = brand_tokens(db, org_id)
    ctx["brand_mentioned"] = [t for t in toks if t in low]
    truth = pt.verify_text(db, org_id, text)
    for c in truth["claims"]:
        if c["attribute"] == "price" and c["status"] in ("Contradicted", "Outdated"):
            out.append({"type": "unauthorised_price", "severity": "high",
                        "title": f"Offer price {c['submitted_value']} is not an approved price",
                        "evidence": f"Approved: {c['approved_value']} ({c['source_document']})", "confidence": 0.9})
        elif c["status"] == "Contradicted":
            out.append({"type": "false_spec", "severity": "medium",
                        "title": f"Misrepresents {c['attribute_label'].lower()}: {c['submitted_value']}",
                        "evidence": f"Approved: {c['approved_value']}", "confidence": 0.75})
    match = sim.check_text(db, org_id, text)
    approved = [m for m in match["matches"] if m["kind"] == "passport" and m["label"] in ("Exact duplicate", "Near-duplicate")]
    any_known = [m for m in match["matches"] if m["label"] in ("Exact duplicate", "Near-duplicate")]
    ctx["matches_approved_campaign"] = bool(approved)
    if approved and not host_official:
        out.append({"type": "copied_campaign", "severity": "medium", "title": "Copies an approved campaign on an unofficial source",
                    "evidence": approved[0]["title"], "confidence": 0.7})
    elif ctx["brand_mentioned"] and not approved and not any_known and len(text.split()) > 8:
        out.append({"type": "unknown_campaign", "severity": "medium", "title": "Not found in approved campaign records",
                    "evidence": "No approved or submitted campaign matches this wording.", "confidence": 0.5})
    for rx, label in PHISHING:
        m = re.search(rx, low)
        if m:
            out.append({"type": "phishing_request", "severity": "high", "title": label,
                        "evidence": text[max(0, m.start() - 60):m.end() + 60].strip(), "confidence": 0.85})
    m = URGENCY.search(text)
    if m:
        out.append({"type": "urgency", "severity": "low", "title": "Pressure tactics (urgent deadline)",
                    "evidence": m.group(0), "confidence": 0.4})
    return out, ctx


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
_W = {"high": 3, "medium": 2, "low": 1, "info": 0}


def assess(findings: List[dict], brand_present: bool) -> Tuple[str, float, str, str]:
    real = [f for f in findings if f["severity"] != "info"]
    score = sum(_W[f["severity"]] * f["confidence"] for f in real)
    highs = [f for f in real if f["severity"] == "high"]
    official = any(f["type"] == "official_domain" for f in findings)
    if official and not highs:
        risk = "low"
    elif len(highs) >= 2 or (highs and brand_present):
        risk = "high"
    elif highs or score >= 2:
        risk = "medium"
    else:
        risk = "low"
    conf = round(min(0.95, max([f["confidence"] for f in real] or [0.2]) * (1 + 0.1 * (len(real) - 1))), 2) if real else 0.2
    issue = "; ".join(f["title"] for f in sorted(real, key=lambda f: -_W[f["severity"]])[:3]) or "No impersonation signal found"
    if risk == "high":
        resp = ("Treat as suspected impersonation: preserve the evidence, warn customers through official channels, "
                "and report the domain or page to the registrar / platform after a person confirms it.")
    elif risk == "medium":
        resp = "Review manually: confirm whether the source is an authorised partner and whether the offer is approved."
    else:
        resp = "Low signal. Keep for reference; no action unless more reports arrive."
    return risk, conf, issue, resp
