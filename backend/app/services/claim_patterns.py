"""Deterministic claim detectors used by the content analyzer.

Each function is pure (text in, matches out) so it can be tested on its own.
Widened after measuring the analyzer on 50 held-out real-world inputs
(backend/eval/realworld_dataset.json): the earlier fixed phrase lists missed
reworded superlatives, competitor comparisons and wrong specifications.
"""
import re
from typing import Dict, Iterable, List, Optional, Tuple

_APOS = str.maketrans({"’": "'", "‘": "'", "`": "'"})


def normalise(text: str) -> str:
    """Same-length copy with curly apostrophes made straight, so offsets still line up."""
    return text.translate(_APOS)


def _merged(text: str, patterns: Iterable[re.Pattern]) -> List[str]:
    spans: List[Tuple[int, int]] = []
    for pat in patterns:
        spans += [m.span() for m in pat.finditer(text)]
    spans.sort()
    out: List[Tuple[int, int]] = []
    for s, e in spans:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return [text[s:e].strip() for s, e in out]


# --------------------------------------------------------------------------- #
#  Superlatives and competitor comparisons
# --------------------------------------------------------------------------- #
_PRODUCT = r"(?:AI\s+)?(?:laptops?|notebooks?|computers?|pcs?|devices?|machines?|workstations?)"
_RIVALS = r"(?:apple|macbooks?|dell|hp|lenovo|asus|acer|samsung|microsoft|surface|msi|razer)"

SUPERLATIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (
    r"\bworld'?s\s+(?:fastest|best|most\s+powerful|first|thinnest|lightest)\b",
    r"\b(?:fastest|most\s+powerful|best|strongest|thinnest|lightest|smartest)\s+" + _PRODUCT + r"\b",
    r"(?:#\s?1|\bno\.?\s?1|\bnumber\s+one)\s+" + _PRODUCT + r"\b",
    r"\bunbeatable(?:\s+(?!and\b|or\b)\w+)?",
    r"\bbest\b(?:\W+\w+){0,3}?\W+ever\b",
    r"\b(?:most\s+\w+|best|fastest)\b[^.!?]{0,40}?\bever\s+(?:made|built|created)\b",
)]

COMPARATIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (
    r"\b\d+(?:\.\d+)?\s*[x×]\s+(?:faster|better|quicker|smarter|more\s+powerful)\b(?:\s+than\s+(?:every|any|all|the)?\s*\w+)?",
    r"\b(?:faster|better|quicker|quieter|lighter|thinner|smarter|more\s+powerful)\s+than\s+(?:any(?:thing|one)?(?:\s+else)?|every(?:thing|one)?(?:\s+else)?|all|the\s+competition|(?:its\s+|their\s+)?(?:competitors?|rivals?)|(?:the\s+)?" + _RIVALS + r")\b(?:\s+(?:rival|competitor|other)s?\b)?",
    r"\b(?:outperforms?|outpaces?|beats?|crushes|destroys|trounces)\s+(?:every|all|any|the\s+competition|competitors?|rivals?|" + _RIVALS + r")\b",
    r"\bleaves?\s+(?:the\s+|its\s+)?(?:competition|competitors|rivals)\s+(?:behind|in\s+the\s+dust)\b",
)]


def find_superlatives(text: str) -> List[str]:
    return _merged(normalise(text), SUPERLATIVE_PATTERNS)


def find_comparatives(text: str) -> List[str]:
    return _merged(normalise(text), COMPARATIVE_PATTERNS)


# --------------------------------------------------------------------------- #
#  Prices
# --------------------------------------------------------------------------- #
_PRICE_PREFIX = re.compile(r"(?:₹|\bRs\.?|\bINR)\s*(\d[\d,]*)(?:\.\d{1,2})?(?:\s*/-)?", re.IGNORECASE)
_PRICE_SUFFIX = re.compile(r"\b(\d[\d,]{3,})(?:\.\d{1,2})?\s*(?:/-\s*)?(?:rs\b\.?|rupees\b|inr\b)", re.IGNORECASE)
_INSTALMENT_AFTER = re.compile(r"^\s*(?:/\s*(?:month|mo|mth)\b|per\s+month\b|a\s+month\b|p\.?\s?m\.?\b|monthly\b)", re.IGNORECASE)
_INSTALMENT_BEFORE = re.compile(r"\b(?:emi|instal?ments?)\b[^.!?]{0,25}$", re.IGNORECASE)
_ACCESSORY = re.compile(
    r"\b(?:sleeve|case|charger|adapter|bag|backpack|mouse|keyboard|stand|dock|stylus|cable|skin|novacare|novasleeve|accessor(?:y|ies))\b",
    re.IGNORECASE)
_PRODUCT_WORD = re.compile(r"\b(?:laptops?|notebooks?)\b", re.IGNORECASE)
_SENTENCE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)")


def _sentence_at(text: str, pos: int) -> str:
    for m in _SENTENCE.finditer(text):
        if m.start() <= pos < m.end():
            return m.group(0)
    return text


def find_prices(text: str, product_hint: str = "novabook") -> List[Dict[str, str]]:
    """Return price mentions as {raw, value, kind}.

    kind is "price" (compare with the approved price), "instalment" (an EMI or
    monthly amount: a financing term a person must review) or "accessory" (the
    price of something other than the product, so not compared).
    """
    found, taken = [], []
    for pat in (_PRICE_PREFIX, _PRICE_SUFFIX):
        for m in pat.finditer(text):
            if any(s < m.end() and m.start() < e for s, e in taken):
                continue
            value = m.group(1).replace(",", "")
            if not value.isdigit():
                continue
            taken.append(m.span())
            after, before = text[m.end():m.end() + 20], text[max(0, m.start() - 40):m.start()]
            sentence = _sentence_at(text, m.start()).lower()
            if _INSTALMENT_AFTER.search(after) or _INSTALMENT_BEFORE.search(before):
                kind = "instalment"
            elif _ACCESSORY.search(sentence) and not _PRODUCT_WORD.search(sentence) and product_hint not in sentence:
                kind = "accessory"
            else:
                kind = "price"
            found.append({"raw": m.group(0).strip(), "value": value, "kind": kind, "start": m.start()})
    found.sort(key=lambda f: f["start"])
    return found


# --------------------------------------------------------------------------- #
#  Specification numbers (battery hours, TOPS, warranty length)
# --------------------------------------------------------------------------- #
_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "ten": 10, "twelve": 12}
_NUM = r"\b(\d+(?:\.\d+)?|one|two|three|four|five|six|ten|twelve)"

# unit -> (pattern for a stated value, words the sentence must contain, words the fact must contain)
_SPECS = {
    "TOPS": (re.compile(_NUM + r"\s*TOPS\b", re.IGNORECASE), None, ("tops",)),
    "hours": (re.compile(r"(?<!\bin\s)(?<!\bwithin\s)" + _NUM + r"[\s-]*(?:hours?|hrs?)\b", re.IGNORECASE),
              re.compile(r"\b(?:battery|charge|unplugged)\b", re.IGNORECASE), ("battery",)),
    "warranty_months": (re.compile(_NUM + r"[\s-]*(years?|yrs?|months?)\b", re.IGNORECASE),
                        re.compile(r"\bwarranty\b", re.IGNORECASE), ("warranty",)),
}


def _num(tok: str) -> float:
    tok = tok.lower()
    return float(_WORD_NUM.get(tok, tok))


def _approved_spec(unit: str, value_text: str) -> Optional[float]:
    pat = _SPECS[unit][0]
    m = pat.search(value_text)
    if not m:
        return None
    n = _num(m.group(1))
    if unit == "warranty_months" and m.group(2).lower().startswith("y"):
        n *= 12
    return n


def find_spec_conflicts(text: str, facts) -> List[Dict]:
    """Numbers in the text that disagree with an approved specification fact.

    `facts` are objects with fact_key / fact_value. Returns {raw, fact, stated, approved}.
    """
    out = []
    for unit, (pat, sentence_words, fact_words) in _SPECS.items():
        fact = next((f for f in facts
                     if all(w in f"{f.fact_key} {f.fact_value}".lower() for w in fact_words)
                     and _approved_spec(unit, f.fact_value) is not None), None)
        if fact is None:
            continue
        approved = _approved_spec(unit, fact.fact_value)
        for m in pat.finditer(text):
            if sentence_words is not None and not sentence_words.search(_sentence_at(text, m.start())):
                continue
            stated = _num(m.group(1))
            if unit == "warranty_months" and m.group(2).lower().startswith("y"):
                stated *= 12
            if stated != approved:
                out.append({"raw": m.group(0).strip(), "fact": fact, "stated": stated, "approved": approved})
    return out


# --------------------------------------------------------------------------- #
#  Terms forbidden inside written brand rules ("Do not use ... 'budget laptop'")
# --------------------------------------------------------------------------- #
_FORBID = re.compile(r"\b(?:do\s+not\s+use|don't\s+use|never\s+use|must\s+not\s+use|avoid(?:\s+using)?)\b([^.]*)", re.IGNORECASE)
_QUOTED = re.compile(r"['‘\"“]([^'’\"”]{3,40})['’\"”]")


def rule_forbidden_terms(rules, register_terms: Iterable[str]) -> List[Tuple[str, object]]:
    """Quoted terms a rule tells writers not to use, minus ones the register already covers."""
    known = [t.lower() for t in register_terms]
    out, seen = [], set()
    for rule in rules:
        for m in _FORBID.finditer(normalise(rule.rule_text or "")):
            for q in _QUOTED.findall(m.group(1)):
                term = q.strip().lower()
                if term in seen or any(k in term for k in known):
                    continue
                seen.add(term)
                out.append((term, rule))
    return out


# --------------------------------------------------------------------------- #
#  Tone: shouting and hype slang (exclamation marks are counted by the analyzer)
# --------------------------------------------------------------------------- #
_HYPE = re.compile(r"\b(?:omg|insane|crazy|mind[\s-]?blowing|epic|lit|killer|dhamaka)\b|[\U0001F525\U0001F92F\U0001F4A5\U0001F631]", re.IGNORECASE)
_ACRONYMS = {"AI", "TOPS", "GST", "NPU", "MRP", "EMI", "INR", "HP", "USB", "SSD", "RAM", "CPU", "GPU", "OLED", "LCD",
             "HDMI", "FAQ", "CEO", "CMO", "ISO", "MSI", "LTE", "PDF", "USA", "UK", "SKU", "OS", "TB", "GB", "GHZ"}
_CAPS_WORD = re.compile(r"\b[A-Z]{3,}\b")


def tone_signals(text: str, org_name: str = "") -> List[str]:
    reasons = []
    hype = sorted({m.group(0) for m in _HYPE.finditer(text)})
    if hype:
        reasons.append("hype language: " + ", ".join(hype))
    brand = {w.upper() for w in re.findall(r"[A-Za-z]+", org_name or "")}
    shouted = [m for m in _CAPS_WORD.finditer(text) if m.group(0) not in _ACRONYMS and m.group(0) not in brand]
    if len(shouted) >= 2 or (shouted and hype):
        reasons.append("shouting in capitals: " + " ".join(m.group(0) for m in shouted[:4]))
    return reasons
