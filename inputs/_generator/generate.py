"""Build the BrandVault test-input library: one folder per feature, 50+ files each.

Run from the repository root:
    backend/venv/Scripts/python inputs/_generator/generate.py

Output is deterministic (fixed random seed). Each folder gets a manifest.csv that
says what every file should trigger, derived from how the file was built.
"""
import csv
import io
import json
import os
import random
import shutil
import sys
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "inputs")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402

from backend.tests import creative_fixtures as cf  # noqa: E402
from backend.tests import forensics_fixtures as ff  # noqa: E402
import bank  # noqa: E402

RND = random.Random(2026)


# --------------------------------------------------------------------------- #
#  helpers
# --------------------------------------------------------------------------- #
def folder(name):
    path = os.path.join(OUT, name)
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def write(path, data):
    mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
    with open(path, mode, **({} if mode == "wb" else {"encoding": "utf-8", "newline": "\n"})) as fh:
        fh.write(data)


def manifest(path, header, rows):
    with open(os.path.join(path, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def tags_text(tags):
    return "clean" if not tags else ";".join(sorted(set(tags)))


def compose_copy(n_violations, channel=None, rnd=RND):
    """A realistic multi-sentence copy with known issue tags."""
    channel = channel or rnd.choice(list(bank.CHANNEL_OPENERS))
    sentences, tags = [], []
    clean = rnd.sample(bank.CLEAN, k=rnd.randint(1, 3))
    groups = rnd.sample(list(bank.VIOLATIONS), k=n_violations)
    for g in groups:
        s, t = rnd.choice(bank.VIOLATIONS[g])
        sentences.append(bank.fill(s, rnd))
        tags += t
    for s, _ in clean:
        sentences.insert(rnd.randint(0, len(sentences)), bank.fill(s, rnd))
    text = bank.CHANNEL_OPENERS[channel] + " ".join(sentences)
    if channel == "email":
        text += "\n\nWarm regards,\nTeam NovaTech"
    return channel, text, tags


def wrap(text, width=78):
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


def latin(text):
    """PDF Helvetica text is Latin-1: swap the few characters it cannot show."""
    for a, b in (("₹", "Rs. "), ("—", "-"), ("–", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("→", "->")):
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def fit(lines, size, font_size):
    """Wrap banner lines so none runs off the canvas (first line is the larger headline)."""
    out = []
    for i, line in enumerate(lines):
        px = font_size if i == 0 else font_size * 0.72
        out += wrap(line, max(12, int((size[0] - 120) / (px * 0.6))))
    return out


def pdf_from_sections(title, sections):
    lines = [latin(title), ""]
    for head, paras in sections:
        lines += ["", latin(head.upper())]
        for p in paras:
            lines += wrap(latin(p), 80)
    pages = [lines[i:i + 28] for i in range(0, len(lines), 28)]
    return cf.text_pdf(pages)


def docx_from_sections(title, sections):
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    def para(text, style=None):
        ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
        return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

    body = para(title, "Title") + "".join(para(h, "Heading1") + "".join(para(p) for p in ps) for h, ps in sections)
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}"><w:body>{body}'
           f'<w:sectPr/></w:body></w:document>')
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W}">'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
              '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>'
              '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="30"/></w:rPr></w:style>'
              '</w:styles>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                   '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                   '</Relationships>')
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   '</Relationships>')
        z.writestr("word/document.xml", doc)
        z.writestr("word/styles.xml", styles)
    return buf.getvalue()


def xlsx_from_rows(rows):
    def col(i):
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    xml_rows = []
    for ri, row in enumerate(rows, start=1):
        cells = []
        for ci, v in enumerate(row):
            ref = f"{col(ci)}{ri}"
            if isinstance(v, (int, float)):
                cells.append(f'<c r="{ref}"><v>{v}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>')
        xml_rows.append(f'<row r="{ri}">{"".join(cells)}</row>')
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + "".join(xml_rows) + '</sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   '<sheet name="Price list" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '</Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
#  01 Content Intelligence — marketing copy
# --------------------------------------------------------------------------- #
def content_intelligence():
    path = folder("01_content_intelligence")
    rows = []
    for name in ("realworld_dataset.json", "realworld_holdout.json"):
        with open(os.path.join(ROOT, "backend", "eval", name), encoding="utf-8") as fh:
            for c in json.load(fh)["cases"]:
                fname = f"{c['id']}_{c['channel'].replace(' ', '_')}.txt"
                write(os.path.join(path, fname), c["content"] + "\n")
                rows.append([fname, c["channel"], tags_text(set(c["expected"]) - {"clean"}), "from labelled eval set"])
    for i in range(1, 41):
        channel, text, tags = compose_copy(RND.choice([0, 1, 1, 2, 2, 3]))
        fname = f"m{i:02d}_{channel.replace(' ', '_')}.txt"
        write(os.path.join(path, fname), text + "\n")
        rows.append([fname, channel, tags_text(tags), "multi-sentence copy"])
    return manifest(path, ["file", "channel", "expected_issues", "notes"], rows)


# --------------------------------------------------------------------------- #
#  02 ClaimDNA — single factual claims
# --------------------------------------------------------------------------- #
def claim_dna():
    path = folder("02_claim_dna")
    claims = []
    for s in ["The NovaBook AI Pro 16 costs ₹79,999.", "Launch price: Rs. 79,999 including GST.",
              "Available for INR 79999 at authorised stores.", "MRP ₹79,999.00 across India.",
              "Priced at ₹79,999 for every buyer.", "Yours for 79,999 rupees."]:
        claims.append(("price", s, "Supported", "matches approved price ₹79,999"))
    for p in bank.PRICES_WRONG:
        claims.append(("price", f"Now available at ₹{p}.", "Contradicted", "approved price is ₹79,999"))
    for p in ["70,000", "73,990"]:
        claims.append(("price", f"Rs.{p}/- final offer price.", "Contradicted", "approved price is ₹79,999"))
    for s in ["Up to 18 hours of battery on mixed workloads.", "Battery rated for up to 18 hours.",
              "An 18-hour battery for long days.", "Up to 18 hours on a single charge, battery permitting."]:
        claims.append(("battery", s, "Supported", "approved: up to 18 hours"))
    for h in [10, 12, 20, 22, 24, 30, 36, 48]:
        claims.append(("battery", f"Up to {h} hours of battery life.", "Contradicted", "approved: up to 18 hours"))
    for s in ["The NovaCore N10 delivers 45 TOPS.", "45 TOPS of on-device AI.", "A 45 TOPS NPU for local AI.",
              "Sustained 45 TOPS AI performance."]:
        claims.append(("tops", s, "Supported", "approved: 45 TOPS"))
    for t in [30, 40, 48, 50, 60, 100]:
        claims.append(("tops", f"Rated at {t} TOPS of AI performance.", "Contradicted", "approved: 45 TOPS"))
    for s in ["Includes a 2-year on-site warranty.", "Two-year limited hardware warranty included.",
              "Covered by a 2-Year On-Site Limited Hardware Warranty.", "Warranty: 24 months on-site."]:
        claims.append(("warranty", s, "Supported", "approved: 2-year warranty"))
    for s in ["Comes with a 1-year warranty.", "3-year warranty as standard.", "Five-year warranty included.",
              "An 18-month warranty is included.", "Warranty: 36 months.", "Includes a 4-year warranty."]:
        claims.append(("warranty", s, "Contradicted", "approved: 2-year warranty"))
    for s, _ in bank.VIOLATIONS["superlative"]:
        claims.append(("superlative", s, "Unsupported", "no approved benchmark"))
    for s, _ in bank.VIOLATIONS["outdated"]:
        claims.append(("promotion", s, "Outdated", "pre-order bonus expired 31 Dec 2024"))
    for s in ["A game-changing machine.", "Industry-leading build quality.", "Next-generation thermals.",
              "Cutting-edge AI for everyone."]:
        claims.append(("ambiguous", s, "Needs Human Review", "vague claim a reviewer must judge"))
    rows = []
    for i, (kind, text, status, why) in enumerate(claims, start=1):
        fname = f"claim_{i:03d}_{kind}.txt"
        write(os.path.join(path, fname), text + "\n")
        rows.append([fname, kind, status, why])
    return manifest(path, ["file", "claim_type", "expected_status", "reason"], rows)


# --------------------------------------------------------------------------- #
#  03 Creative Inspection — banners, PDF decks, short videos
# --------------------------------------------------------------------------- #
def creative_inspection():
    path = folder("03_creative_inspection")
    rows = []
    sizes = [(1200, 628), (1080, 1080), (1080, 1350), (728, 300)]
    bgs = [((255, 255, 255), (15, 23, 42)), ((15, 23, 42), (255, 255, 255)), ((238, 242, 255), (30, 27, 75)),
           ((250, 250, 250), (17, 17, 17))]

    def lines_for(n_viol):
        out, tags = ["NovaBook AI Pro 16"], []
        for g in RND.sample([g for g in bank.VIOLATIONS if g not in ("tone", "fact_conflict")], k=n_viol):
            s, t = RND.choice(bank.VIOLATIONS[g])
            out.append(bank.fill(s, RND))
            tags += t
        if len(out) < 3:
            out.append(bank.fill(RND.choice(bank.CLEAN[:4])[0], RND))
        return out, tags

    fmts = [("png", "PNG"), ("jpg", "JPEG"), ("webp", "WEBP")]
    for i in range(1, 37):
        ext, fmt = fmts[i % 3]
        lines, tags = lines_for(RND.choice([0, 1, 1, 2]))
        size, (bg, fg) = sizes[i % 4], bgs[i % 4]
        fs = 46 if size[0] >= 1000 else 30
        lines = fit(lines, size, fs)
        size = (size[0], max(size[1], 70 + int(fs * 1.6) * len(lines) + 40))  # tall enough for every line
        data = cf.banner(lines, size=size, bg=bg, fg=fg, font_size=fs, variant=i % 3, fmt=fmt)
        fname = f"banner_{i:02d}.{ext}"
        write(os.path.join(path, fname), data)
        rows.append([fname, f"image {size[0]}x{size[1]}", tags_text(tags), " | ".join(lines)])
    for i in range(1, 15):
        pages, tags = [], []
        for _ in range(RND.randint(2, 4)):
            lines, t = lines_for(RND.choice([0, 0, 1]))
            pages.append([latin(l) for l in lines])
            tags += t
        fname = f"deck_{i:02d}.pdf"
        write(os.path.join(path, fname), cf.text_pdf(pages))
        rows.append([fname, f"PDF deck, {len(pages)} pages", tags_text(tags), " / ".join(" | ".join(p) for p in pages)])
    for i in range(1, 11):
        frames, tags = [], []
        for _ in range(3):
            lines, t = lines_for(RND.choice([0, 1]))
            frames.append(fit(lines, (960, 540), 40)[:6])
            tags += t
        fname = f"video_{i:02d}.mp4"
        write(os.path.join(path, fname), cf.video(frames, seconds_each=1.0))
        rows.append([fname, "MP4 video, 3 scenes", tags_text(tags), " / ".join(" | ".join(f) for f in frames)])
    return manifest(path, ["file", "format", "expected_issues", "text_in_creative"], rows)


# --------------------------------------------------------------------------- #
#  04 Visual DNA — colour and contrast
# --------------------------------------------------------------------------- #
def visual_dna():
    path = folder("04_visual_dna")
    rows = []
    mono = [(10, 10, 10), (23, 23, 23), (64, 64, 64), (120, 120, 120), (200, 200, 200), (245, 245, 245), (255, 255, 255)]
    colours = [(79, 70, 229), (16, 185, 129), (239, 68, 68), (245, 158, 11), (14, 165, 233), (236, 72, 153), (132, 204, 22)]
    fmts = [("png", "PNG"), ("jpg", "JPEG"), ("webp", "WEBP"), ("bmp", "BMP")]
    for i in range(1, 61):
        kind = ["mono_high", "mono_low", "colour_high", "colour_low", "colour_accent"][i % 5]
        w, h = RND.choice([(1200, 628), (1080, 1080), (800, 800), (1600, 900)])
        if kind.startswith("mono"):
            bg = RND.choice(mono[:2] + mono[-2:]) if kind == "mono_high" else (130, 130, 130)
            fg = (255, 255, 255) if sum(bg) < 300 else (10, 10, 10)
            if kind == "mono_low":
                fg = (150, 150, 150)
        elif kind == "colour_accent":
            bg, fg = (250, 250, 250), (10, 10, 10)
        else:
            bg = RND.choice(colours)
            fg = (255, 255, 255) if kind == "colour_high" else tuple(min(255, c + 25) for c in bg)
        img = Image.new("RGB", (w, h), bg)
        d = ImageDraw.Draw(img)
        d.rectangle([w * 0.08, h * 0.6, w * 0.92, h * 0.85], fill=fg)
        d.text((w * 0.08, h * 0.15), "NovaBook AI Pro 16", fill=fg, font=cf.font(int(h * 0.08)))
        d.text((w * 0.08, h * 0.32), "Built for long working days.", fill=fg, font=cf.font(int(h * 0.05)))
        if kind == "colour_accent":
            d.rectangle([w * 0.08, h * 0.48, w * 0.2, h * 0.52], fill=RND.choice(colours))  # small accent (<10%)
        ext, fmt = fmts[i % 4]
        if fmt == "BMP":  # uncompressed: keep it small
            img = img.resize((400, int(400 * h / w)))
        buf = io.BytesIO()
        img.save(buf, fmt, **({"optimize": True} if fmt == "PNG" else {}))
        fname = f"visual_{i:02d}_{kind}.{ext}"
        write(os.path.join(path, fname), buf.getvalue())
        expected = {
            "mono_high": "on-palette (monochrome); contrast OK",
            "mono_low": "on-palette; LOW contrast flagged",
            "colour_high": "OFF-palette colour flagged (>10% colour; needs a confirmed monochrome palette rule)",
            "colour_low": "OFF-palette colour flagged (needs monochrome palette rule); LOW contrast flagged",
            "colour_accent": "on-palette (colour accent under 10%); contrast OK",
        }[kind]
        rows.append([fname, f"{w}x{h} {ext}", kind, expected])
    return manifest(path, ["file", "size_format", "design", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  05 Brand DNA — guideline documents and price lists
# --------------------------------------------------------------------------- #
GUIDE_KINDS = [
    ("Brand Guidelines 2026", [
        ("Brand Voice", ["The NOVA TECH voice is calm, precise and confident. Avoid hype, slang and exclamation marks."]),
        ("Pricing", ["The authorised launch price of the NovaBook AI Pro 16 is ₹79,999 inclusive of taxes."]),
        ("Specifications", ["The NovaCore N10 AI Engine delivers 45 TOPS.",
                            "Battery is rated for up to 18 hours of mixed productivity workload.",
                            "Every unit includes a 2-Year On-Site Limited Hardware Warranty."]),
        ("Claims", ["Superlatives such as fastest or number one require an independent benchmark report."]),
    ], "consistent with approved facts"),
    ("Social Media Policy", [
        ("Posting rules", ["Posts on X must stay under 280 characters with at most two hashtags.",
                           "Do not use the words 'cheap' or 'budget laptop' in any post."]),
        ("Tone", ["Never use more than one exclamation mark. Avoid slang such as OMG or insane."]),
        ("Disclosure", ["Paid creator posts must be labelled #ad."]),
    ], "adds terminology and tone rules"),
    ("Retail Partner Playbook", [
        ("Pricing", ["Partners must display the authorised price of ₹79,999. Discounts need a written approval."]),
        ("In-store displays", ["Show the full product name NovaBook AI Pro 16 on every shelf card."]),
        ("Promotions", ["The NovaSleeve pre-order bonus ended on 31 December 2024 and must not be advertised."]),
    ], "consistent; reinforces expired promotion"),
    ("Influencer Collaboration Guidelines", [
        ("Claims", ["Influencers must not compare the product with named competitors.",
                    "Do not describe the product as the world's fastest."]),
        ("Disclosure", ["Every sponsored post must include #ad in the first line."]),
    ], "adds comparative-claim rule"),
    ("Press and PR Guidelines", [
        ("Facts", ["Quote only approved figures: 45 TOPS, up to 18 hours of battery, 2-year warranty, ₹79,999."]),
        ("Spokespeople", ["Only the Brand Office may comment on pricing or competitors."]),
    ], "consistent with approved facts"),
    ("Accessibility Standards", [
        ("Contrast", ["Body text must meet a contrast ratio of at least 4.5 to 1."]),
        ("Alt text", ["Every image needs alt text that describes the product shown."]),
    ], "visual/accessibility rules"),
    ("Legal Disclaimers India", [
        ("EMI", ["EMI offers must state subject to bank approval and any processing fee."]),
        ("Battery claims", ["Battery claims must say up to and name the test workload."]),
    ], "disclaimer rules"),
    ("Email Marketing Standards", [
        ("Subject lines", ["Email subject lines must be under 60 characters and must not use capitals for emphasis."]),
        ("Unsubscribe", ["Every email must include an unsubscribe link."]),
    ], "channel rules"),
    ("Festival Campaign Rules 2026", [
        ("Offers", ["Festival offers require a separate approved offer record. The base price stays ₹79,999."]),
        ("Tone", ["Festive greetings are welcome; hype words such as dhamaka are not."]),
    ], "consistent; offer governance"),
    ("Product Fact Sheet NovaBook AI Pro 16", [
        ("Key facts", ["Price ₹79,999.", "NovaCore N10 AI Engine with 45 TOPS.", "Up to 18 hours of battery.",
                       "2-Year On-Site Limited Hardware Warranty."]),
    ], "consistent product facts"),
    ("Regional Pricing Memo (unapproved draft)", [
        ("South region", ["Draft: the NovaBook AI Pro 16 will be priced at ₹74,999 in the south region."]),
    ], "CONFLICT: ₹74,999 disagrees with approved ₹79,999"),
    ("Brand Guidelines 2024 (superseded)", [
        ("Promotions", ["Every pre-order includes a complimentary NovaSleeve accessory."]),
        ("Battery", ["The NovaBook AI Pro 16 offers up to 20 hours of battery."]),
    ], "OUTDATED/CONFLICT: 20 hours disagrees with approved 18 hours"),
    ("Campus Program Guidelines", [
        ("Student offers", ["Student pricing must be verified through the campus portal. Never call the product cheap."]),
    ], "adds terminology rule"),
    ("Spec Sheet Draft from Agency", [
        ("Performance", ["The NovaCore N10 delivers 50 TOPS.", "Warranty: 3 years."]),
    ], "CONFLICT: 50 TOPS and 3-year warranty disagree with approved facts"),
    ("Customer Support Style Guide", [
        ("Voice", ["Support replies are calm and precise. Never promise refunds outside the policy."]),
        ("Warranty answers", ["Every NovaBook AI Pro 16 includes a 2-year on-site warranty."]),
    ], "consistent"),
]

REGIONS = ["India", "North", "South", "West", "East", "Online", "Enterprise", "Retail", "Campus", "Export"]


def brand_dna():
    path = folder("05_brand_dna_guidelines")
    rows = []
    fmts = ["docx", "pdf", "md", "txt", "html"]
    n = 0
    for k, (title, sections, expect) in enumerate(GUIDE_KINDS):
        for j, ext in enumerate(RND.sample(fmts, k=4)):
            n += 1
            region = REGIONS[(k + j) % len(REGIONS)]
            full_title = f"NOVA TECH {title} — {region} edition"
            secs = [(h, list(ps)) for h, ps in sections]
            secs.append(("Document control", [f"Owner: NOVA TECH Brand Office ({region}). Version {j + 1}.{k}. "
                                              f"Applies to all {region.lower()} marketing material."]))
            base = f"guide_{n:02d}_{title.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{region.lower()}"
            fname = f"{base}.{ext}"
            if ext == "docx":
                data = docx_from_sections(full_title, secs)
            elif ext == "pdf":
                data = pdf_from_sections(full_title, secs)
            elif ext == "md":
                data = f"# {full_title}\n\n" + "\n".join(f"## {h}\n\n" + "\n\n".join(ps) + "\n" for h, ps in secs)
            elif ext == "txt":
                data = full_title + "\n\n" + "\n".join(f"{h.upper()}\n" + "\n".join(ps) + "\n" for h, ps in secs)
            else:
                data = (f"<!doctype html><html><head><meta charset=\"utf-8\"><title>{escape(full_title)}</title></head><body>"
                        f"<h1>{escape(full_title)}</h1>"
                        + "".join(f"<h2>{escape(h)}</h2>" + "".join(f"<p>{escape(p)}</p>" for p in ps) for h, ps in secs)
                        + "</body></html>")
            write(os.path.join(path, fname), data)
            rows.append([fname, ext, title, expect])
    # Price lists (CSV and Excel)
    header = ["Product", "Configuration", "Price (INR)", "Region", "Channel", "Effective from", "Status"]
    for i in range(1, 11):
        good = i % 3 != 0
        price = 79999 if good else int(RND.choice(bank.PRICES_WRONG).replace(",", ""))
        region = REGIONS[i % len(REGIONS)]
        data_rows = [header,
                     ["NovaBook AI Pro 16", "32 GB / 1 TB", price, region, "All", "2026-01-01", "Approved" if good else "Draft"],
                     ["NovaSleeve 16", "Sleeve", 2499, region, "All", "2026-01-01", "Approved"],
                     ["NovaCare Plus", "Extended cover, 1 year", 4999, region, "Online", "2026-01-01", "Approved"],
                     ["NovaDock USB-C", "Dock", 8999, region, "Retail", "2026-02-01", "Approved"]]
        ext = "csv" if i % 2 else "xlsx"
        fname = f"pricelist_{i:02d}_{region.lower()}.{ext}"
        if ext == "csv":
            buf = io.StringIO()
            csv.writer(buf, lineterminator="\n").writerows(data_rows)
            data = buf.getvalue()
        else:
            data = xlsx_from_rows(data_rows)
        write(os.path.join(path, fname), data)
        rows.append([fname, ext, "Price list", "consistent: laptop at ₹79,999" if good
                     else f"CONFLICT: laptop listed at ₹{price:,} (draft) vs approved ₹79,999"])
    return manifest(path, ["file", "format", "document_type", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  06 Translation Guard — source + translations
# --------------------------------------------------------------------------- #
SOURCES = {
    "price": ("The NovaBook AI Pro 16 is priced at ₹79,999.", {
        "hi": "NovaBook AI Pro 16 की कीमत ₹79,999 है।",
        "fr": "Le NovaBook AI Pro 16 est proposé à ₹79,999.",
        "es": "El NovaBook AI Pro 16 tiene un precio de ₹79,999.",
        "de": "Das NovaBook AI Pro 16 kostet ₹79,999.",
        "ta": "NovaBook AI Pro 16 இன் விலை ₹79,999.",
    }),
    "battery": ("Up to 18 hours of battery life.", {
        "hi": "18 घंटे तक की बैटरी लाइफ।",
        "fr": "Jusqu'à 18 heures d'autonomie.",
        "es": "Hasta 18 horas de batería.",
        "de": "Bis zu 18 Stunden Akkulaufzeit.",
        "ta": "18 மணிநேரம் வரை பேட்டரி ஆயுள்.",
    }),
    "tops": ("The NovaCore N10 delivers 45 TOPS.", {
        "hi": "NovaCore N10 45 TOPS प्रदान करता है।",
        "fr": "Le NovaCore N10 offre 45 TOPS.",
        "es": "El NovaCore N10 ofrece 45 TOPS.",
        "de": "Der NovaCore N10 liefert 45 TOPS.",
        "ta": "NovaCore N10 45 TOPS வழங்குகிறது.",
    }),
    "warranty": ("Includes a 2-year on-site warranty.", {
        "hi": "2 साल की ऑन-साइट वारंटी शामिल है।",
        "fr": "Comprend une garantie sur site de 2 ans.",
        "es": "Incluye una garantía in situ de 2 años.",
        "de": "Inklusive 2 Jahre Vor-Ort-Garantie.",
        "ta": "2 ஆண்டு ஆன்-சைட் உத்தரவாதம் அடங்கும்.",
    }),
    "no_fee": ("No processing fee on EMI.", {
        "hi": "EMI पर कोई प्रोसेसिंग शुल्क नहीं।",
        "fr": "Pas de frais de dossier sur l'EMI.",
        "es": "Sin comisión de apertura en la EMI.",
        "de": "Keine Bearbeitungsgebühr bei EMI.",
        "ta": "EMI க்கு செயலாக்கக் கட்டணம் இல்லை.",
    }),
}

CORRUPT = {
    "price": [("number_changed", lambda t: t.replace("79,999", "69,999"), "price changed 79,999 → 69,999")],
    "battery": [("number_changed", lambda t: t.replace("18", "24"), "hours changed 18 → 24"),
                ("qualifier_dropped", None, "'up to' dropped")],
    "tops": [("number_changed", lambda t: t.replace("45", "54"), "TOPS changed 45 → 54"),
             ("product_name_changed", lambda t: t.replace("NovaCore N10", "Nova Core N1"), "product name altered")],
    "warranty": [("number_changed", lambda t: t.replace("2", "3", 1), "warranty 2 → 3 years")],
    "no_fee": [("negation_dropped", None, "'no' dropped: claim reversed")],
}

DROP_QUALIFIER = {"hi": "18 घंटे की बैटरी लाइफ।", "fr": "18 heures d'autonomie.", "es": "18 horas de batería.",
                  "de": "18 Stunden Akkulaufzeit.", "ta": "18 மணிநேரம் பேட்டரி ஆயுள்."}
DROP_NEGATION = {"hi": "EMI पर प्रोसेसिंग शुल्क लागू है।", "fr": "Frais de dossier sur l'EMI.",
                 "es": "Comisión de apertura en la EMI.", "de": "Bearbeitungsgebühr bei EMI.",
                 "ta": "EMI க்கு செயலாக்கக் கட்டணம் உண்டு."}


def translation_guard():
    path = folder("06_translation_guard")
    rows = []
    n = 0
    langs = ["hi", "fr", "es", "de", "ta"]
    for key, (src, trans) in SOURCES.items():
        # clean: all languages correct
        n += 1
        body = {"title": f"{key} — all languages", "source_text": src,
                "translations": [{"label": l, "text": trans[l]} for l in langs]}
        fname = f"tg_{n:02d}_{key}_clean.json"
        write(os.path.join(path, fname), json.dumps(body, ensure_ascii=False, indent=2))
        rows.append([fname, key, ",".join(langs), "all translations consistent", "clean"])
        for lang in langs:
            n += 1
            body = {"title": f"{key} — {lang}", "source_text": src, "translations": [{"label": lang, "text": trans[lang]}]}
            fname = f"tg_{n:02d}_{key}_{lang}_clean.json"
            write(os.path.join(path, fname), json.dumps(body, ensure_ascii=False, indent=2))
            rows.append([fname, key, lang, "consistent", "clean"])
        for lang in langs:
            for kind, fn, why in CORRUPT[key]:
                n += 1
                if kind == "qualifier_dropped":
                    bad = DROP_QUALIFIER[lang]
                elif kind == "negation_dropped":
                    bad = DROP_NEGATION[lang]
                else:
                    bad = fn(trans[lang])
                others = [l for l in langs if l != lang][:1]
                body = {"title": f"{key} — {lang} {kind}", "source_text": src,
                        "translations": [{"label": lang, "text": bad}] + [{"label": o, "text": trans[o]} for o in others]}
                fname = f"tg_{n:02d}_{key}_{lang}_{kind}.json"
                write(os.path.join(path, fname), json.dumps(body, ensure_ascii=False, indent=2))
                rows.append([fname, key, ",".join([lang] + others), f"{lang}: {why}; {others[0]} clean", kind])
    # longer paragraph cases
    para_src = "The NovaBook AI Pro 16 is priced at ₹79,999. Up to 18 hours of battery life. Includes a 2-year on-site warranty."
    for lang in langs:
        good = " ".join([SOURCES["price"][1][lang], SOURCES["battery"][1][lang], SOURCES["warranty"][1][lang]])
        for variant, text, why in [("clean", good, "consistent"),
                                   ("price_changed", good.replace("79,999", "74,999"), "price changed 79,999 → 74,999")]:
            n += 1
            body = {"title": f"paragraph — {lang} {variant}", "source_text": para_src,
                    "translations": [{"label": lang, "text": text}]}
            fname = f"tg_{n:02d}_paragraph_{lang}_{variant}.json"
            write(os.path.join(path, fname), json.dumps(body, ensure_ascii=False, indent=2))
            rows.append([fname, "paragraph", lang, why, variant])
    return manifest(path, ["file", "claim", "languages", "expected_result", "case_type"], rows)


# --------------------------------------------------------------------------- #
#  07 AI Copy Studio — off-brand copy to rewrite
# --------------------------------------------------------------------------- #
def copy_studio():
    path = folder("07_copy_studio")
    rows = []
    for i in range(1, 61):
        channel, text, tags = compose_copy(RND.choice([1, 2, 2, 3]))
        fname = f"rewrite_{i:02d}_{channel.replace(' ', '_')}.txt"
        write(os.path.join(path, fname), text + "\n")
        rows.append([fname, channel, tags_text(tags), "rewrite should remove these issues and keep the message"])
    return manifest(path, ["file", "channel", "issues_to_fix", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  08 Brand Assistant — questions
# --------------------------------------------------------------------------- #
QUESTIONS = [
    ("What is the launch price of the NovaBook AI Pro 16?", "₹79,999"),
    ("How long does the battery last?", "up to 18 hours (mixed productivity workload)"),
    ("How many TOPS does the NovaCore N10 deliver?", "45 TOPS"),
    ("What warranty comes with the laptop?", "2-Year On-Site Limited Hardware Warranty"),
    ("Can we still advertise the NovaSleeve pre-order bonus?", "No — it expired on 31 Dec 2024"),
    ("Can I say it is the world's fastest AI laptop?", "No — prohibited without independent benchmark"),
    ("Is 'cheap' allowed in our copy?", "No — prohibited term"),
    ("Can we say 10x faster than every competitor?", "No — prohibited comparative claim"),
    ("What tone should our marketing use?", "calm, precise, understated"),
    ("Are exclamation marks allowed?", "avoid them"),
    ("Is ₹69,999 an approved price?", "No — not approved"),
    ("What should I use instead of 'cheap'?", "exceptional enterprise value / highly accessible"),
    ("How should the product name be written?", "NovaBook AI Pro 16 or NovaBook AI Pro"),
    ("Can I call it a budget laptop?", "No — naming rule forbids it"),
    ("Who approved the launch price?", "Pricing Policy Master Document 2026"),
    ("Where does the battery figure come from?", "Lab Battery Benchmark Test 2026-B8"),
    ("What clock speed does the NovaCore N10 sustain?", "3.8 GHz"),
    ("Does the warranty include accidental damage?", "Year 1 accidental damage protection (fact note)"),
    ("Can we compare ourselves with MacBook?", "comparative claims need cited methodology"),
    ("Is 'industry-leading' allowed?", "needs human review"),
]
UNANSWERABLE = [
    "What is the CEO's personal phone number?", "What will the price be in 2028?",
    "How many units did we sell last quarter?", "What is the weather in Mumbai today?",
    "Which competitor is planning a launch next month?", "What is the employee salary band for designers?",
    "Can you write me a poem about cricket?", "What is the stock price of NOVA TECH?",
    "Does the NovaBook support 5G?", "What colour options will launch next year?",
]


def brand_assistant():
    path = folder("08_brand_assistant")
    rows = []
    phrasings = ["{q}", "Quick check: {q}", "Hi, {q_lower}", "{q} Please cite the source."]
    n = 0
    for q, a in QUESTIONS:
        for p in RND.sample(phrasings, k=2):
            n += 1
            text = p.format(q=q, q_lower=q[0].lower() + q[1:])
            fname = f"q{n:02d}.txt"
            write(os.path.join(path, fname), text + "\n")
            rows.append([fname, "answerable", a])
    for q in UNANSWERABLE:
        for p in RND.sample(phrasings, k=2):
            n += 1
            text = p.format(q=q, q_lower=q[0].lower() + q[1:])
            fname = f"q{n:02d}.txt"
            write(os.path.join(path, fname), text + "\n")
            rows.append([fname, "not in brand data", "should say it is not in approved data (no invented answer)"])
    return manifest(path, ["file", "type", "expected_answer"], rows)


# --------------------------------------------------------------------------- #
#  09 Reputation — customer feedback exports
# --------------------------------------------------------------------------- #
FEEDBACK = {
    "positive": [
        "Battery easily lasts my whole workday. Very happy.", "Delivery was quick and the packaging was solid.",
        "The keyboard is excellent for long typing sessions.", "Runs my AI tools locally without any lag.",
        "Display colours are accurate, great for photo work.", "Support team sorted my query in one call.",
        "Quiet fans even under load. Love it.", "Worth every rupee for the performance.",
        "Setup was simple and the build feels premium.", "On-site warranty visit was prompt and professional.",
    ],
    "negative": [
        "Battery drains in 6 hours, nowhere near what was advertised.", "Delivery was delayed by a week with no updates.",
        "It gets hot on my lap during video calls.", "Customer support kept me on hold for 40 minutes.",
        "The store charged me more than the website price.", "Trackpad stopped working after two weeks.",
        "Ad said 24 hours battery, that is misleading.", "Fan noise is loud when exporting video.",
        "Warranty claim was rejected without explanation.", "Received a scratched unit, very disappointing.",
    ],
    "neutral": [
        "Does it support two external monitors?", "Received the laptop today, will update after a week.",
        "Is there a student discount?", "Average experience overall.", "The charger is a bit bulky.",
        "Comparable to my previous laptop.", "Which service centre is nearest to Pune?",
    ],
}
SOURCES_FB = ["amazon_reviews", "flipkart_reviews", "support_tickets", "twitter_mentions", "nps_survey",
              "retail_store_feedback", "instagram_comments", "email_inbox", "google_reviews", "dealer_reports", "app_store"]


def reputation():
    path = folder("09_reputation_feedback")
    rows = []
    for i in range(1, 56):
        src = SOURCES_FB[i % len(SOURCES_FB)]
        n = RND.randint(25, 120)
        mix = RND.choice([(0.7, 0.2), (0.4, 0.45), (0.2, 0.7), (0.55, 0.3)])
        records, counts = [], {"positive": 0, "negative": 0, "neutral": 0}
        for r in range(n):
            x = RND.random()
            label = "positive" if x < mix[0] else "negative" if x < mix[0] + mix[1] else "neutral"
            counts[label] += 1
            rating = {"positive": RND.choice([4, 5]), "negative": RND.choice([1, 2]), "neutral": 3}[label]
            day = 1 + (r * 3 + i) % 28
            month = 1 + (r + i) % 10
            records.append({"date": f"2026-{month:02d}-{day:02d}", "channel": src.replace("_", " "),
                            "rating": rating, "review": RND.choice(FEEDBACK[label]), "product": "NovaBook AI Pro 16"})
        broken = 0
        if i % 7 == 0:  # a couple of unusable rows to test skipping
            records += [{"date": "2026-03-01", "channel": src, "rating": 3, "review": "", "product": ""}] * 2
            broken = 2
        if i % 3 == 0:
            fname = f"feedback_{i:02d}_{src}.json"
            write(os.path.join(path, fname), json.dumps(records, ensure_ascii=False, indent=1))
        else:
            fname = f"feedback_{i:02d}_{src}.csv"
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=["date", "channel", "rating", "review", "product"], lineterminator="\n")
            w.writeheader()
            w.writerows(records)
            write(os.path.join(path, fname), buf.getvalue())
        rows.append([fname, src, n, broken, counts["positive"], counts["negative"], counts["neutral"]])
    return manifest(path, ["file", "source", "usable_rows", "rows_to_skip", "positive", "negative", "neutral"], rows)


# --------------------------------------------------------------------------- #
#  10 Fraud Intelligence — reported URLs and messages
# --------------------------------------------------------------------------- #
FRAUD = [
    ("https://novatech.example/novabook-ai-pro-16", "The NovaBook AI Pro 16 is available at ₹79,999 with a 2-year warranty.", "legitimate (official domain, approved price)"),
    ("https://n0vatech.shop/offer", "NovaTech official sale! NovaBook AI Pro 16 for ₹29,999. Pay now to reserve.", "SUSPECTED: lookalike domain (0→o), suspicious TLD, unauthorised price"),
    ("https://novatech-offers.xyz/claim", "Congratulations! You won a NovaBook AI Pro 16. Share your OTP to claim the prize.", "SUSPECTED: lure domain, OTP request (phishing)"),
    ("https://novatech.example.secure-login.top/verify", "Your NovaTech account is locked. Enter your card number and CVV to verify.", "SUSPECTED: brand in subdomain, card/CVV request"),
    ("https://novateck.in/sale", "Diwali dhamaka: NovaBook AI Pro 16 only ₹39,999. Limited stock.", "SUSPECTED: typosquat domain, unauthorised price"),
    ("https://nova-tech.click/refund", "Refund pending. Log in with your NovaTech password to receive ₹5,000.", "SUSPECTED: lookalike, credential request"),
    ("https://shop.novatech.example/accessories", "NovaSleeve 16 protective sleeve, ₹2,499.", "legitimate (official subdomain)"),
    ("https://novatechindia.online/emi", "Get NovaBook AI Pro 16 on 0% EMI, just send your Aadhaar and bank details on WhatsApp.", "SUSPECTED: brand+lure domain, bank detail request"),
    ("https://novatech.example/support", "Book a warranty visit online. We never ask for your OTP.", "legitimate"),
    ("https://n0vabook-pro.store/buy", "NovaBook AI Pro 16 world's fastest laptop, ₹19,999 only today!!", "SUSPECTED: lookalike, unauthorised price, banned claim"),
]


def fraud():
    path = folder("10_fraud_intelligence")
    rows = []
    channels = ["WhatsApp forward", "SMS", "Instagram ad", "Facebook post", "Email", "Telegram channel"]
    n = 0
    for k in range(6):
        for url, msg, expect in FRAUD:
            n += 1
            ch = channels[(n + k) % len(channels)]
            text = msg if k == 0 else (RND.choice(["Hi, ", "Dear customer, ", "", "URGENT: ", "Sir, "]) + msg)
            if "URGENT" in text and "legitimate" in expect:
                text = msg  # keep legitimate messages free of pressure words
            fname = f"report_{n:02d}.txt"
            write(os.path.join(path, fname), f"Reported via: {ch}\nURL: {url}\n\nMessage:\n{text}\n")
            rows.append([fname, ch, url, expect])
    return manifest(path, ["file", "reported_via", "url", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  11 Channel check — copy + channel + image size
# --------------------------------------------------------------------------- #
CHANNEL_LIMITS = {"x": 280, "instagram": 2200, "linkedin": 3000, "google_ads": 30, "email": 60, "web_banner": 120}
RATIOS = {"x": [(1600, 900), (1080, 1080)], "instagram": [(1080, 1080), (1080, 1350)], "linkedin": [(1200, 628), (1080, 1080)],
          "web_banner": [(728, 90), (300, 250)]}
BAD_SIZES = [(1080, 1920), (800, 600), (500, 500 * 3)]


def channel_check():
    path = folder("11_channel_check")
    rows = []
    texts_short = ["NovaBook AI Pro 16 — ₹79,999", "Up to 18 hrs battery", "Meet NovaBook AI Pro 16",
                   "45 TOPS on-device AI", "Now shipping across India"]
    for i in range(1, 61):
        ch = list(CHANNEL_LIMITS)[i % len(CHANNEL_LIMITS)]
        limit = CHANNEL_LIMITS[ch]
        over = i % 3 == 0
        if limit <= 60:
            text = RND.choice(texts_short)
            if over:
                text = text + " — " + bank.fill(RND.choice(bank.CLEAN)[0], RND)
        else:
            parts = [bank.fill(s, RND) for s, _ in RND.sample(bank.CLEAN, k=4)]
            text = " ".join(parts)
            while over and len(text) <= limit:
                text += " " + bank.fill(RND.choice(bank.CLEAN)[0], RND)
            if not over:
                text = text[:limit - 1].rsplit(" ", 1)[0]
        body = {"text": text, "channels": [ch], "region": "IN"}
        size_note = "no image"
        if ch in RATIOS:
            w, h = RND.choice(RATIOS[ch]) if i % 4 else RND.choice(BAD_SIZES)
            body.update(width=w, height=h)
            size_note = f"{w}x{h} " + ("allowed ratio" if i % 4 else "WRONG aspect ratio")
        fname = f"channel_{i:02d}_{ch}.json"
        write(os.path.join(path, fname), json.dumps(body, ensure_ascii=False, indent=2))
        n = len(text)
        rows.append([fname, ch, n, limit, "OVER limit" if n > limit else "within limit", size_note])
    return manifest(path, ["file", "channel", "chars", "max_chars", "length_result", "image_result"], rows)


# --------------------------------------------------------------------------- #
#  12 Asset Forensics — logo placements and edits
# --------------------------------------------------------------------------- #
def asset_forensics():
    path = folder("12_asset_forensics")
    rows = []
    official = ff.make_logo("v2")
    write(os.path.join(path, "00_official_logo_REGISTER_FIRST.png"), ff.png_bytes(official))
    rows.append(["00_official_logo_REGISTER_FIRST.png", "official logo", "register this as the official asset first"])
    old = ff.make_logo("v1")
    write(os.path.join(path, "00_old_logo_2024.png"), ff.png_bytes(old))
    rows.append(["00_old_logo_2024.png", "old logo version", "register as a retired/old version if you want version checks"])
    cases = []
    for i in range(1, 54):
        kind = ["placed", "scaled", "rotated", "recoloured", "jpeg_recompressed", "old_version", "no_logo"][i % 7]
        scene_seed = i
        if kind == "no_logo":
            img = ff.scene(seed=scene_seed)
            expect = "no official logo found"
        elif kind == "recoloured":
            img = ff.compose(ff.recolour(official), at=(RND.randint(50, 500), RND.randint(50, 400)))
            expect = "logo found but RECOLOURED (altered)"
        elif kind == "old_version":
            img = ff.compose(old, at=(RND.randint(50, 500), RND.randint(50, 400)))
            expect = "old 2024 logo version (outdated asset)"
        elif kind == "rotated":
            img = ff.compose(official, at=(300, 220), rotate=RND.choice([8, 15, 30]))
            expect = "logo found, ROTATED (guideline: never rotate)"
        elif kind == "scaled":
            s = RND.choice([0.5, 0.7, 1.4])
            img = ff.compose(official, at=(RND.randint(50, 400), RND.randint(50, 300)), size=(int(360 * s), int(160 * s)))
            expect = f"logo found, scaled x{s}"
        else:
            img = ff.compose(official, at=(RND.randint(50, 550), RND.randint(50, 450)))
            expect = "official logo found (unchanged)"
        if kind == "jpeg_recompressed":
            data, ext = ff.jpeg_bytes(img, q=RND.choice([45, 60, 75])), "jpg"
            expect = "official logo found (JPEG recompressed)"
        elif i % 10 == 0:
            data, ext = ff.png_bytes(img), "png"
        else:
            data, ext = ff.jpeg_bytes(img.convert("RGB"), q=92), "jpg"  # photo-like scenes: JPEG keeps files small
        fname = f"asset_{i:02d}_{kind}.{ext}"
        write(os.path.join(path, fname), data)
        rows.append([fname, kind, expect])
    return manifest(path, ["file", "case", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  13 Brand Passport verification — approved copy vs tampered copy
# --------------------------------------------------------------------------- #
APPROVED = ("Meet NovaBook AI Pro 16. The NovaCore N10 AI Engine delivers up to 45 TOPS sustained AI processing performance, "
            "with up to 18 hours mixed productivity workload on a single charge. Available at ₹79,999 with a "
            "2-Year On-Site Limited Hardware Warranty.")
TAMPER = [
    ("price_changed", lambda t: t.replace("₹79,999", "₹69,999")),
    ("hours_changed", lambda t: t.replace("18 hours", "24 hours")),
    ("tops_changed", lambda t: t.replace("45 TOPS", "50 TOPS")),
    ("warranty_changed", lambda t: t.replace("2-Year", "3-Year")),
    ("sentence_added", lambda t: t + " Now the world's fastest AI laptop."),
    ("sentence_removed", lambda t: t.split(". ", 1)[1]),
    ("word_swapped", lambda t: t.replace("Meet", "Discover")),
    ("qualifier_removed", lambda t: t.replace("up to 18", "18")),
    ("typo", lambda t: t.replace("Engine", "Engin")),
    ("product_renamed", lambda t: t.replace("NovaBook AI Pro 16", "NovaBook Pro")),
]


def passport_verify():
    path = folder("13_brand_passport_verify")
    rows = []
    n = 0
    for k in range(5):
        n += 1
        fname = f"verify_{n:02d}_exact_approved.txt"
        write(os.path.join(path, fname), APPROVED)
        rows.append([fname, "exact approved copy", "VERIFIED: matches the passport for 'Product Page Hero'"])
        for name, fn in TAMPER:
            n += 1
            fname = f"verify_{n:02d}_{name}.txt"
            write(os.path.join(path, fname), fn(APPROVED))
            rows.append([fname, name, "NOT verified: content differs from the approved version"])
    return manifest(path, ["file", "change", "expected_result"], rows)


# --------------------------------------------------------------------------- #
#  14 Similarity — near-duplicates of existing campaigns
# --------------------------------------------------------------------------- #
def similarity():
    path = folder("14_similarity")
    rows = []
    from backend.app.services.demo_content import CAMPAIGNS
    n = 0
    edits = [
        ("near_copy", lambda t: t.replace("NovaBook AI Pro 16", "the NovaBook AI Pro 16", 1)),
        ("reordered", lambda t: " ".join(reversed([s for s in t.split(". ") if s]))),
        ("light_rewrite", lambda t: t.replace("Introducing", "Say hello to").replace("grab", "pick up").replace("Meet", "Discover")),
        ("trimmed", lambda t: t.split(". ")[0] + "."),
        ("extended", lambda t: t + " Visit a NovaTech store near you."),
        ("case_and_punctuation", lambda t: t.upper().replace("!", ".")),
    ]
    for title, _, _, copy, _ in CAMPAIGNS:
        for name, fn in edits:
            n += 1
            fname = f"sim_{n:02d}_{name}.txt"
            write(os.path.join(path, fname), fn(copy) + "\n")
            strength = "high" if name in ("near_copy", "case_and_punctuation", "extended") else "medium"
            rows.append([fname, name, title, f"{strength} similarity to '{title}'"])
    for i in range(1, 11):
        n += 1
        fname = f"sim_{n:02d}_unrelated.txt"
        text = RND.choice([
            "Our offices will be closed on Monday for the public holiday.",
            "Join our webinar on data privacy best practices next Thursday.",
            "The quarterly town hall moves to the main auditorium.",
            "Reminder: submit travel claims before the 25th.",
            "Our recycling programme now accepts old chargers and cables.",
        ]) + f" Ref {1000 + i}."
        write(os.path.join(path, fname), text + "\n")
        rows.append([fname, "unrelated", "-", "no meaningful similarity"])
    return manifest(path, ["file", "edit", "source_campaign", "expected_result"], rows)


BUILDERS = [content_intelligence, claim_dna, creative_inspection, visual_dna, brand_dna, translation_guard,
            copy_studio, brand_assistant, reputation, fraud, channel_check, asset_forensics, passport_verify, similarity]

if __name__ == "__main__":
    total = 0
    for b in BUILDERS:
        count = b()
        total += count
        print(f"{b.__name__:<22} {count:>4} files")
    print(f"{'TOTAL':<22} {total:>4} files")
