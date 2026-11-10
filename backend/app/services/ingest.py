"""
Guideline ingestion (Round 3 · Improvement 3).

Turns an uploaded guideline into citable sections, then into retrieval-sized
passages:

- PDF        — one section per page ("Page N")
- DOCX       — sections start at headings ("Section N · Heading")
- HTML       — sections start at <h1>–<h3>; scripts/styles/nav are ignored
- Markdown / text — sections start at "#" headings
- CSV / XLSX — rows become "Row N: column: value | …" passages (price lists, spec sheets)

Passages are sentence-aligned windows of about 600 characters with one
sentence of overlap, so a citation points at the paragraph that matters rather
than a whole page. Each passage keeps the number and label of its section.
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from html.parser import HTMLParser
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

SUPPORTED = (".pdf", ".docx", ".html", ".htm", ".md", ".txt", ".csv", ".xlsx")
TARGET_CHARS = 600
MAX_PASSAGES = 400
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9“\"(₹])")
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class IngestError(ValueError):
    pass


def file_type(name: str) -> str:
    n = (name or "").lower()
    for ext in SUPPORTED:
        if n.endswith(ext):
            return {".htm": "html"}.get(ext, ext[1:])
    raise IngestError(f"Unsupported file type. Allowed: {', '.join(SUPPORTED)}")


# ------------------------------------------------------------------ readers --
def _pdf(data: bytes) -> List[Dict]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return [{"n": i + 1, "label": f"Page {i + 1}", "text": (p.extract_text() or "").strip()} for i, p in enumerate(reader.pages)]


def _docx(data: bytes) -> List[Dict]:
    try:
        xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml")
        root = ET.fromstring(xml)
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise IngestError("This .docx file could not be read.")
    sections: List[Dict] = [{"n": 1, "label": "Section 1", "text": ""}]
    for p in root.iter(f"{_W}p"):
        style = p.find(f"{_W}pPr/{_W}pStyle")
        text = "".join(t.text or "" for t in p.iter(f"{_W}t")).strip()
        if not text:
            continue
        style_name = (style.get(f"{_W}val") or "").lower() if style is not None else ""
        is_heading = "heading" in style_name or style_name == "title"
        if is_heading:
            n = len(sections) + (0 if not sections[-1]["text"] else 1)
            if sections[-1]["text"]:
                sections.append({"n": n, "label": f"Section {n} · {text[:60]}", "text": ""})
            else:
                sections[-1].update(label=f"Section {sections[-1]['n']} · {text[:60]}")
            sections[-1]["text"] += text + ".\n"
        else:
            sections[-1]["text"] += text + "\n"
    return [s for s in sections if s["text"].strip()]


class _HTML(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.sections: List[Dict] = [{"n": 1, "label": "Section 1", "text": ""}]
        self._skip = 0
        self._heading = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag in ("h1", "h2", "h3"):
            self._heading = True
            if self.sections[-1]["text"].strip():
                n = len(self.sections) + 1
                self.sections.append({"n": n, "label": f"Section {n}", "text": ""})
        elif tag in ("p", "li", "br", "tr", "div"):
            self.sections[-1]["text"] += "\n"

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag in ("h1", "h2", "h3"):
            self._heading = False
            self.sections[-1]["text"] += ".\n"

    def handle_data(self, data):
        if self._skip or not data.strip():
            return
        s = self.sections[-1]
        if self._heading and s["label"] == f"Section {s['n']}":
            s["label"] = f"Section {s['n']} · {data.strip()[:60]}"
        s["text"] += data.strip() + " "


def _html(data: bytes) -> List[Dict]:
    parser = _HTML()
    parser.feed(data.decode("utf-8", errors="ignore"))
    return [s for s in parser.sections if s["text"].strip()]


def _markdown(data: bytes) -> List[Dict]:
    sections: List[Dict] = [{"n": 1, "label": "Section 1", "text": ""}]
    for line in data.decode("utf-8", errors="ignore").splitlines():
        page = re.match(r"^\s*---\s*Page\s+(\d+)\s*---\s*$", line)  # text exported from a PDF keeps its pages
        if page:
            n = int(page.group(1))
            if sections[-1]["text"].strip():
                sections.append({"n": n, "label": f"Page {n}", "text": ""})
            else:
                sections[-1].update(n=n, label=f"Page {n}")
            continue
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            if sections[-1]["text"].strip():
                n = len(sections) + 1
                sections.append({"n": n, "label": f"Section {n} · {m.group(1)[:60]}", "text": m.group(1) + ".\n"})
            else:
                sections[-1]["label"] = f"Section {sections[-1]['n']} · {m.group(1)[:60]}"
                sections[-1]["text"] += m.group(1) + ".\n"
        else:
            sections[-1]["text"] += line + "\n"
    return [s for s in sections if s["text"].strip()]


def _rows_to_sections(rows: List[List[str]]) -> List[Dict]:
    rows = [[(c or "").strip() for c in r] for r in rows if any((c or "").strip() for c in r)]
    if len(rows) < 2:
        raise IngestError("The spreadsheet needs a header row and at least one data row.")
    header = [h or f"Column {i + 1}" for i, h in enumerate(rows[0])]
    out = []
    for i, r in enumerate(rows[1:], start=2):
        cells = [f"{header[j]}: {v}" for j, v in enumerate(r) if j < len(header) and v]
        if cells:
            out.append({"n": i, "label": f"Row {i}", "text": f"Row {i}: " + " | ".join(cells) + "."})
    return out


def _csv(data: bytes) -> List[Dict]:
    text = data.decode("utf-8-sig", errors="ignore")
    return _rows_to_sections(list(csv.reader(io.StringIO(text))))


def _xlsx(data: bytes) -> List[Dict]:
    """First worksheet of an .xlsx (shared strings + inline values), no extra dependency."""
    return _rows_to_sections(xlsx_rows(data))


def xlsx_rows(data: bytes) -> List[List[str]]:
    """Cell values of the first worksheet, row by row."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{ns}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{ns}t")))
        sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
        rows = []
        for row in ET.fromstring(z.read(sheet)).iter(f"{ns}row"):
            vals: Dict[int, str] = {}
            for c in row.iter(f"{ns}c"):
                ref = re.match(r"([A-Z]+)", c.get("r", "A"))
                col = 0
                for ch in ref.group(1):
                    col = col * 26 + (ord(ch) - 64)
                v = c.find(f"{ns}v")
                if c.get("t") == "s" and v is not None:
                    val = shared[int(v.text)]
                elif c.get("t") == "inlineStr":
                    val = "".join(t.text or "" for t in c.iter(f"{ns}t"))
                else:
                    val = v.text if v is not None else ""
                vals[col - 1] = val or ""
            if vals:
                rows.append([vals.get(i, "") for i in range(max(vals) + 1)])
    except (zipfile.BadZipFile, KeyError, IndexError, ET.ParseError):
        raise IngestError("This .xlsx file could not be read.")
    return rows


READERS = {"pdf": _pdf, "docx": _docx, "html": _html, "md": _markdown, "txt": _markdown, "csv": _csv, "xlsx": _xlsx}


# ----------------------------------------------------------------- chunking --
def passages(sections: List[Dict]) -> List[Dict]:
    """Sentence-aligned ~600-character passages, one sentence of overlap, per section."""
    out: List[Dict] = []
    for s in sections:
        text = re.sub(r"[ \t]+", " ", s["text"]).strip()
        if len(text) < 25:
            continue
        sentences = [x.strip() for x in _SENT.split(re.sub(r"\s*\n\s*", " ", text)) if x.strip()]
        window: List[str] = []
        for sent in sentences:
            if window and len(" ".join(window)) + len(sent) > TARGET_CHARS:
                out.append({"n": s["n"], "label": s["label"], "text": " ".join(window)})
                window = window[-1:]  # overlap
            window.append(sent)
        if window and (not out or out[-1]["text"] != " ".join(window) or out[-1]["n"] != s["n"]):
            out.append({"n": s["n"], "label": s["label"], "text": " ".join(window)})
    return out[:MAX_PASSAGES]


def ingest(filename: str, data: bytes) -> Tuple[str, List[Dict], List[Dict], str]:
    """Return (file_type, sections, passages, raw_text)."""
    kind = file_type(filename)
    sections = READERS[kind](data)
    if not sections:
        raise IngestError("No readable text was found in this file.")
    raw = "\n".join(f"\n--- {s['label']} ---\n{s['text']}" for s in sections)
    return kind, sections, passages(sections), raw
