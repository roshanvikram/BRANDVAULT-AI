"""
BRANDVAULT AI — Complete Product, Feature & Usage Guide PDF Generator
Written in Pure Python (Standard Library + pypdf).
Generates an enterprise-grade, beautifully formatted PDF document.
"""

import os
import pypdf

class SimplePdfBuilder:
    def __init__(self, output_path="BRANDVAULT_AI_PRODUCT_EXPLAINER.pdf"):
        self.output_path = output_path
        self.width = 595.28   # A4 width in pt
        self.height = 841.89  # A4 height in pt
        self.margin_x = 42.0
        self.margin_top = 45.0
        self.margin_bottom = 45.0
        self.content_width = self.width - 2 * self.margin_x
        
        self.pages = []          # List of page stream strings
        self.current_stream = []
        self.y = self.height - self.margin_top
        self.page_number = 1
        
        # Color palette
        self.C_PRIMARY = (0.310, 0.275, 0.898)     # Indigo #4F46E5
        self.C_PRIMARY_BG = (0.933, 0.949, 1.000)  # Indigo-50 #EEF2FF
        self.C_TEXT_MAIN = (0.059, 0.090, 0.165)   # Slate-900 #0F172A
        self.C_TEXT_MUTED = (0.392, 0.455, 0.545)  # Slate-500 #64748B
        self.C_TEXT_LIGHT = (0.580, 0.639, 0.722)  # Slate-400
        self.C_BORDER = (0.886, 0.910, 0.941)      # Slate-200 #E2E8F0
        self.C_EMERALD = (0.063, 0.725, 0.506)     # Emerald #10B981
        self.C_EMERALD_BG = (0.925, 0.992, 0.961)  # Emerald-50
        self.C_ROSE = (0.957, 0.247, 0.369)        # Rose #F43F5E
        self.C_ROSE_BG = (1.000, 0.945, 0.949)     # Rose-50
        self.C_AMBER = (0.961, 0.620, 0.043)       # Amber #F59E0B
        self.C_AMBER_BG = (1.000, 0.984, 0.922)    # Amber-50
        self.C_PURPLE = (0.545, 0.361, 0.965)      # Purple #8B5CF6
        self.C_PURPLE_BG = (0.980, 0.961, 1.000)   # Purple-50
        self.C_SKY = (0.008, 0.518, 0.780)         # Sky #0284C7
        self.C_SKY_BG = (0.941, 0.976, 1.000)      # Sky-50

    def start_new_page(self):
        if self.current_stream:
            self._draw_page_decorations()
            self.pages.append("".join(self.current_stream))
            self.current_stream = []
            self.page_number += 1
        self.y = self.height - self.margin_top - 36.0  # leave room for header

    def _draw_page_decorations(self):
        # Header banner
        # Mini logo box
        self._rect(self.margin_x, self.height - 34, 18, 18, fill=True, stroke=False, fill_color=self.C_PRIMARY)
        self._text("BV", self.margin_x + 3.5, self.height - 29, font="F1", size=8, color=(1, 1, 1))
        self._text("BRANDVAULT AI  //  COMPLETE PRODUCT & FEATURE GUIDE", self.margin_x + 24, self.height - 28, font="F1", size=7.5, color=self.C_PRIMARY)
        self._text("Deal Dynamos · CodeNexus 2026", self.width - self.margin_x - 110, self.height - 28, font="F2", size=7.5, color=self.C_TEXT_MUTED)
        self._line(self.margin_x, self.height - 38, self.width - self.margin_x, self.height - 38, color=self.C_BORDER, width=0.75)
        
        # Footer
        self._line(self.margin_x, self.margin_bottom + 15, self.width - self.margin_x, self.margin_bottom + 15, color=self.C_BORDER, width=0.75)
        self._text("Protect Every Word. Preserve Every Identity. · Enterprise Brand Intelligence", self.margin_x, self.margin_bottom + 4, font="F3", size=7.5, color=self.C_TEXT_MUTED)
        page_str = f"Page {self.page_number}"
        self._text(page_str, self.width - self.margin_x - 30, self.margin_bottom + 4, font="F1", size=7.5, color=self.C_PRIMARY)

    def _set_color(self, r, g, b, stroke=False):
        cmd = "RG" if stroke else "rg"
        self.current_stream.append(f"{r:.3f} {g:.3f} {b:.3f} {cmd}\n")

    def _rect(self, x, y, w, h, fill=True, stroke=False, fill_color=(0.95, 0.95, 0.98), stroke_color=(0.8, 0.8, 0.85), line_width=1.0):
        if fill:
            self._set_color(*fill_color, stroke=False)
        if stroke:
            self._set_color(*stroke_color, stroke=True)
            self.current_stream.append(f"{line_width:.2f} w\n")
        op = "B" if (fill and stroke) else ("f" if fill else "S")
        self.current_stream.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}\n")

    def _line(self, x1, y1, x2, y2, color=(0.8, 0.8, 0.85), width=1.0):
        self._set_color(*color, stroke=True)
        self.current_stream.append(f"{width:.2f} w {x1:.2f} y1 {x2:.2f} {y2:.2f} m l S\n".replace("y1", f"{y1:.2f}"))

    def _text(self, text, x, y, font="F1", size=10, color=(0.1, 0.1, 0.15)):
        self._set_color(*color, stroke=False)
        replacements = {
            "\u2014": " -- ",
            "\u2013": " - ",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2022": "*",
            "\u2713": "[OK]",
            "\u2717": "[X]",
            "\u2715": "[X]",
            "\u20b9": "Rs. ",
            "\xa0": " ",
            "✓": "[OK]",
            "✕": "[X]",
            "•": "*",
            "₹": "Rs. ",
            "→": "->",
            "·": " | ",
            "–": "-",
            "—": "--",
        }
        clean = str(text)
        for k, v in replacements.items():
            clean = clean.replace(k, v)
        clean = clean.encode("ascii", errors="replace").decode("ascii")
        safe_text = clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.current_stream.append(f"BT /{font} {size:.2f} Tf {x:.2f} {y:.2f} Td ({safe_text}) Tj ET\n")

    def ensure_space(self, required_height):
        if (self.y - required_height) < (self.margin_bottom + 25):
            self.start_new_page()

    def add_page_title_block(self, category, title, subtitle):
        self.ensure_space(60)
        # Category badge
        cat_w = len(category) * 4.8 + 12
        self._rect(self.margin_x, self.y - 12, cat_w, 14, fill=True, stroke=True, fill_color=self.C_PRIMARY_BG, stroke_color=self.C_PRIMARY, line_width=0.75)
        self._text(category.upper(), self.margin_x + 6, self.y - 8, font="F1", size=7.0, color=self.C_PRIMARY)
        self.y -= 22
        
        # Title
        self._text(title, self.margin_x, self.y, font="F1", size=16, color=self.C_TEXT_MAIN)
        self.y -= 15
        
        # Subtitle
        self._text(subtitle, self.margin_x, self.y, font="F2", size=9.5, color=self.C_TEXT_MUTED)
        self.y -= 18

    def add_section_header(self, title, tag=None, color=None):
        self.ensure_space(34)
        c = color or self.C_PRIMARY
        # Vertical accent bar
        self._rect(self.margin_x, self.y - 10, 3.5, 14, fill=True, stroke=False, fill_color=c)
        self._text(title, self.margin_x + 10, self.y - 8, font="F1", size=12, color=self.C_TEXT_MAIN)
        if tag:
            tag_w = len(tag) * 4.2 + 8
            self._rect(self.margin_x + 16 + len(title)*6.8, self.y - 9, tag_w, 12, fill=True, stroke=False, fill_color=self.C_PRIMARY_BG)
            self._text(tag, self.margin_x + 20 + len(title)*6.8, self.y - 6.5, font="F1", size=6.5, color=c)
        self.y -= 18

    def wrap_text(self, text, max_chars_per_line=86):
        words = text.split(" ")
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 <= max_chars_per_line:
                cur.append(w)
                cur_len += len(w) + 1
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
        if cur:
            lines.append(" ".join(cur))
        return lines

    def add_paragraph(self, text, size=8.8, color=None, is_bold=False, max_chars=86, line_spacing=11.5):
        font = "F1" if is_bold else "F2"
        col = color or self.C_TEXT_MAIN
        lines = self.wrap_text(text, max_chars_per_line=max_chars)
        self.ensure_space(len(lines) * line_spacing + 4)
        for line in lines:
            self._text(line, self.margin_x, self.y, font=font, size=size, color=col)
            self.y -= line_spacing
        self.y -= 3

    def add_feature_card(self, title, route_tag, summary, how_it_works, why_it_matters, icon_num=None, border_color=None, bg_color=None):
        b_col = border_color or self.C_BORDER
        bg_col = bg_color or (0.99, 0.99, 1.0)
        
        sum_lines = self.wrap_text(summary, max_chars_per_line=78)
        how_lines = self.wrap_text(how_it_works, max_chars_per_line=78)
        why_lines = self.wrap_text(why_it_matters, max_chars_per_line=78)
        
        total_text_lines = len(sum_lines) + len(how_lines) + len(why_lines)
        card_h = 28 + total_text_lines * 10.5 + 24
        
        self.ensure_space(card_h + 8)
        
        top_y = self.y
        card_y = top_y - card_h
        
        # Outer Card Box
        self._rect(self.margin_x, card_y, self.content_width, card_h, fill=True, stroke=True, fill_color=bg_col, stroke_color=b_col, line_width=0.85)
        
        # Header strip inside card
        cur_y = top_y - 16
        if icon_num is not None:
            self._rect(self.margin_x + 10, cur_y - 3, 16, 16, fill=True, stroke=False, fill_color=self.C_PRIMARY)
            self._text(str(icon_num), self.margin_x + 14.5, cur_y + 1.5, font="F1", size=8.5, color=(1, 1, 1))
            self._text(title, self.margin_x + 32, cur_y + 2, font="F1", size=10.5, color=self.C_TEXT_MAIN)
        else:
            self._text(title, self.margin_x + 12, cur_y + 2, font="F1", size=10.5, color=self.C_TEXT_MAIN)
            
        # Route pill on right
        if route_tag:
            pill_w = len(route_tag) * 4.3 + 12
            pill_x = self.margin_x + self.content_width - pill_w - 10
            self._rect(pill_x, cur_y - 2, pill_w, 13, fill=True, stroke=True, fill_color=(1, 1, 1), stroke_color=self.C_BORDER, line_width=0.7)
            self._text(route_tag, pill_x + 6, cur_y + 1.5, font="F4", size=6.8, color=self.C_PRIMARY)
            
        cur_y -= 14
        
        # Summary
        for line in sum_lines:
            self._text(line, self.margin_x + 12, cur_y, font="F2", size=8.2, color=self.C_TEXT_MAIN)
            cur_y -= 10.5
            
        cur_y -= 2
        # How it works
        self._text("How it works:", self.margin_x + 12, cur_y, font="F1", size=7.8, color=self.C_PRIMARY)
        cur_y -= 9.5
        for line in how_lines:
            self._text("•  " + line, self.margin_x + 16, cur_y, font="F2", size=8.0, color=self.C_TEXT_MUTED)
            cur_y -= 10.0
            
        cur_y -= 2
        # Why it matters
        self._text("Why it matters:", self.margin_x + 12, cur_y, font="F1", size=7.8, color=self.C_EMERALD)
        cur_y -= 9.5
        for line in why_lines:
            self._text("✓  " + line, self.margin_x + 16, cur_y, font="F2", size=8.0, color=self.C_TEXT_MUTED)
            cur_y -= 10.0
            
        self.y = card_y - 8

    def add_callout(self, title, message, badge="IMPORTANT", color=None, bg_color=None):
        c = color or self.C_AMBER
        bg = bg_color or self.C_AMBER_BG
        lines = self.wrap_text(message, max_chars_per_line=78)
        box_h = 24 + len(lines) * 11
        self.ensure_space(box_h + 6)
        
        box_y = self.y - box_h
        self._rect(self.margin_x, box_y, self.content_width, box_h, fill=True, stroke=True, fill_color=bg, stroke_color=c, line_width=0.9)
        # Left color band
        self._rect(self.margin_x, box_y, 4, box_h, fill=True, stroke=False, fill_color=c)
        
        cur_y = self.y - 14
        self._text(f"{badge}: {title}", self.margin_x + 12, cur_y, font="F1", size=9, color=self.C_TEXT_MAIN)
        cur_y -= 11.5
        for line in lines:
            self._text(line, self.margin_x + 12, cur_y, font="F2", size=8.2, color=self.C_TEXT_MAIN)
            cur_y -= 11
            
        self.y = box_y - 8

    def add_two_column_comparison(self, left_title, left_points, right_title, right_points):
        col_w = (self.content_width - 12) / 2
        max_pts = max(len(left_points), len(right_points))
        box_h = 24 + max_pts * 19
        self.ensure_space(box_h + 8)
        
        box_y = self.y - box_h
        # Left Box (Danger / Without BrandVault)
        self._rect(self.margin_x, box_y, col_w, box_h, fill=True, stroke=True, fill_color=self.C_ROSE_BG, stroke_color=self.C_ROSE, line_width=0.75)
        self._text(left_title, self.margin_x + 10, self.y - 15, font="F1", size=9.5, color=self.C_ROSE)
        
        ly = self.y - 28
        for pt in left_points:
            self._text("✕ " + pt, self.margin_x + 10, ly, font="F2", size=7.8, color=(0.5, 0.1, 0.15))
            ly -= 18
            
        # Right Box (Success / With BrandVault)
        rx = self.margin_x + col_w + 12
        self._rect(rx, box_y, col_w, box_h, fill=True, stroke=True, fill_color=self.C_EMERALD_BG, stroke_color=self.C_EMERALD, line_width=0.75)
        self._text(right_title, rx + 10, self.y - 15, font="F1", size=9.5, color=self.C_EMERALD)
        
        ry = self.y - 28
        for pt in right_points:
            self._text("✓ " + pt, rx + 10, ry, font="F2", size=7.8, color=(0.05, 0.35, 0.2))
            ry -= 18
            
        self.y = box_y - 10

    def add_table(self, headers, rows, col_widths=None):
        if not col_widths:
            cw = self.content_width / len(headers)
            col_widths = [cw] * len(headers)
            
        row_h = 16
        table_h = (len(rows) + 1) * row_h
        self.ensure_space(table_h + 8)
        
        cur_y = self.y
        # Header row
        self._rect(self.margin_x, cur_y - row_h, self.content_width, row_h, fill=True, stroke=True, fill_color=self.C_PRIMARY_BG, stroke_color=self.C_BORDER, line_width=0.75)
        cx = self.margin_x
        for i, h in enumerate(headers):
            self._text(h, cx + 6, cur_y - 11, font="F1", size=7.8, color=self.C_PRIMARY)
            cx += col_widths[i]
        cur_y -= row_h
        
        # Rows
        for r_idx, r in enumerate(rows):
            bg = (1, 1, 1) if r_idx % 2 == 0 else (0.98, 0.985, 1.0)
            self._rect(self.margin_x, cur_y - row_h, self.content_width, row_h, fill=True, stroke=True, fill_color=bg, stroke_color=self.C_BORDER, line_width=0.5)
            cx = self.margin_x
            for i, val in enumerate(r):
                self._text(str(val), cx + 6, cur_y - 11, font="F2", size=7.5, color=self.C_TEXT_MAIN)
                cx += col_widths[i]
            cur_y -= row_h
            
        self.y = cur_y - 8

    def build(self):
        if self.current_stream:
            self._draw_page_decorations()
            self.pages.append("".join(self.current_stream))
            
        # Objects assembly
        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        
        page_refs = [f"{3 + i * 2} 0 R" for i in range(len(self.pages))]
        objects.append(f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(self.pages)} >>")
        
        for i, stream_content in enumerate(self.pages):
            content_obj_idx = 4 + i * 2
            page_obj = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                f"/Resources << /Font << "
                f"/F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> "
                f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
                f"/F3 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >> "
                f"/F4 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> "
                f"/F5 << /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >> "
                f">> >> "
                f"/Contents {content_obj_idx} 0 R >>"
            )
            objects.append(page_obj)
            
            raw_bytes = stream_content.encode("latin1", errors="replace")
            content_obj = f"<< /Length {len(raw_bytes)} >>\nstream\n{stream_content}\nendstream"
            objects.append(content_obj)
            
        pdf_parts = ["%PDF-1.4\n"]
        xref_offsets = []
        current_offset = len(pdf_parts[0].encode("latin1"))
        
        for i, obj_str in enumerate(objects):
            xref_offsets.append(current_offset)
            header = f"{i + 1} 0 obj\n"
            footer = "\nendobj\n"
            full_obj = header + obj_str + footer
            pdf_parts.append(full_obj)
            current_offset += len(full_obj.encode("latin1"))
            
        xref_start = current_offset
        xref_table = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in xref_offsets:
            xref_table += f"{offset:010d} 00000 n \n"
            
        trailer = (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        )
        pdf_parts.append(xref_table)
        pdf_parts.append(trailer)
        
        full_pdf = "".join(pdf_parts)
        with open(self.output_path, "wb") as f:
            f.write(full_pdf.encode("latin1", errors="replace"))
        return self.output_path, len(self.pages), len(full_pdf)

def build_complete_guide(pdf_path):
    doc = SimplePdfBuilder(pdf_path)
    
    # =========================================================================
    # PAGE 1: WHAT IS BRANDVAULT AI & WHY DO COMPANIES NEED IT?
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Executive Product Overview",
        "BRANDVAULT AI — Complete Product & Feature Guide",
        "Protect Every Word. Preserve Every Identity. · Enterprise Brand Intelligence Platform"
    )
    
    doc.add_section_header("1. What is BrandVault AI in Simple English?", "Plain English Definition")
    doc.add_paragraph(
        "Think of BrandVault AI as an automated, super-intelligent Brand Inspector and Quality Guard for enterprises. "
        "Every company has strict rules: official product names, exact launch prices, legal disclaimers, forbidden words, "
        "approved colors, and protected logos. But marketing teams, creative agencies, and copywriters often publish mistakes "
        "— wrong prices, unproven claims like 'world's fastest', old logos, or distorted translations."
    )
    doc.add_paragraph(
        "BrandVault AI sits between your creative teams and the public. Before any ad, social media post, website copy, "
        "press release, or banner image goes live, BrandVault AI automatically scans every single word, price, claim, and pixel "
        "against your company's official brand guidelines. It highlights every error, shows the exact page where the official rule is written, "
        "provides a one-click compliant correction, and issues a tamper-proof digital Brand Passport once an authorized human approves it."
    )
    
    doc.add_section_header("2. Why Do Businesses Urgently Need It?", "The Multi-Million Dollar Problem")
    doc.add_two_column_comparison(
        "WITHOUT BRANDVAULT (Costly Mistakes)",
        [
            "A writer types ₹69,999 instead of ₹79,999. Thousands buy before it's noticed.",
            "An agency claims '10x faster than everyone' without proof, triggering competitor lawsuits.",
            "Designers stretch logos or use off-brand colors, diluting brand prestige.",
            "Ad translators change 'up to 18 hrs battery' to 'guaranteed 18 hrs', causing false ad fines.",
            "Scammers clone marketing text to sell fake products on fake websites."
        ],
        "WITH BRANDVAULT (Bulletproof Governance)",
        [
            "Instant Price Contradiction check flags ₹69,999 and replaces with ₹79,999.",
            "ClaimDNA catches unproven claims and labels them 'UNSUPPORTED' before launch.",
            "Visual DNA checks pixels, contrast, and logo geometry automatically.",
            "Translation Guard ensures numbers, prices, and qualifiers are never altered.",
            "Brand Fraud Intelligence spots fake websites, look-alike domains, and phishing."
        ]
    )
    
    doc.add_callout(
        "The Golden Rule of BrandVault AI",
        "AGENTS ADVISE, HUMANS DECIDE: AI agents never have the power to approve content, publish ads, or alter company policy on their own. "
        "The AI acts as an infallible, tireless advisor that surfaces facts and evidence; the final governance decision is ALWAYS made by an authorized human reviewer.",
        badge="CORE PRINCIPLE",
        color=doc.C_PRIMARY,
        bg_color=doc.C_PRIMARY_BG
    )
    
    # =========================================================================
    # PAGE 2: HOW IT WORKS — THE 7-STEP WORKFLOW
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Workflow Architecture",
        "How BrandVault Works: The 7-Step Governance Journey",
        "From raw marketing draft to a certified, tamper-evident Brand Passport"
    )
    
    doc.add_section_header("The 7 Steps Every Campaign Follows", "Step-by-Step Flow")
    
    steps = [
        ("Step 1: Upload Guidelines", "/brand-dna", "Admins upload PDF brand books and specification sheets. BrandVault extracts approved rules, facts, prices, and forbidden terms."),
        ("Step 2: Submit Campaign Copy", "/content-intelligence", "Creators paste written marketing copy or upload promotional images and banner creatives into the three-panel workspace."),
        ("Step 3: Multi-Agent Inspection", "/agent-control", "Specialist AI agents run in parallel: Terminology Agent, ClaimDNA Agent, Product Truth Engine, and Visual DNA Inspector."),
        ("Step 4: Evidence-Backed Findings", "/claim-dna", "Issues are flagged with severity (Critical, High, Medium) and linked to exact guideline citations, page numbers, and verbatim excerpts."),
        ("Step 5: One-Click Fixes", "/copy-studio", "Creators review findings and click 'Apply Correction' or use the AI Copy Studio to rewrite the text into 100% compliant copy."),
        ("Step 6: Human Review Gate", "/approval-hub", "Only an authorized human Reviewer or Administrator can approve, reject, or request revision. The decision is logged to the audit trail."),
        ("Step 7: Brand Passport Issued", "/brand-passport", "Upon approval, a cryptographic SHA-256 certificate (e.g. BV-2026-52ED8A) is issued. If a single letter changes, the passport becomes invalid.")
    ]
    
    for s_title, s_route, s_desc in steps:
        doc.ensure_space(28)
        doc._rect(doc.margin_x, doc.y - 18, 18, 18, fill=True, stroke=False, fill_color=doc.C_PRIMARY)
        doc._text(s_title[:6], doc.margin_x + 2, doc.y - 12, font="F1", size=6.5, color=(1, 1, 1))
        doc._text(s_title[8:], doc.margin_x + 24, doc.y - 10, font="F1", size=9.5, color=doc.C_TEXT_MAIN)
        
        # Route pill
        rw = len(s_route) * 4.2 + 8
        doc._rect(doc.width - doc.margin_x - rw, doc.y - 18, rw, 13, fill=True, stroke=True, fill_color=(1, 1, 1), stroke_color=doc.C_BORDER, line_width=0.6)
        doc._text(s_route, doc.width - doc.margin_x - rw + 4, doc.y - 14.5, font="F4", size=6.5, color=doc.C_PRIMARY)
        
        doc.y -= 22
        p_lines = doc.wrap_text(s_desc, max_chars_per_line=82)
        for pl in p_lines:
            doc._text(pl, doc.margin_x + 24, doc.y, font="F2", size=8.0, color=doc.C_TEXT_MUTED)
            doc.y -= 10
        doc.y -= 4

    doc.add_section_header("Understanding the 3 User Roles", "Role-Based Access Control (RBAC)")
    doc.add_table(
        ["Role", "Who Holds It?", "What They Can Do", "What They Cannot Do"],
        [
            ["Creator", "Copywriters, Agencies, Designers", "Submit copy/images, view findings, apply 1-click fixes", "Cannot approve campaigns or issue Passports"],
            ["Reviewer", "Brand Managers, Legal Counsel", "Review evidence, request revisions, approve campaigns", "Cannot edit master Brand DNA rules"],
            ["Administrator", "CMO, VP Brand, Governance Lead", "Upload guidelines, confirm rules, manage API keys & users", "Full access across the entire organization"]
        ],
        col_widths=[65, 120, 190, 130]
    )

    # =========================================================================
    # PAGE 3: CORE INTELLIGENCE ENGINES (PART 1)
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Feature Deep Dive (Part 1)",
        "The 15 Advanced Intelligence Engines & Features",
        "Detailed explanation of core compliance, truth verification, and copy checking"
    )
    
    doc.add_feature_card(
        "1. Command Center & Governance Pulse",
        "/dashboard",
        "Executive dashboard providing a real-time health score (0 to 100) and complete brand governance overview.",
        "Aggregates live statistics across all active campaigns, tracks claim verification distribution, and displays recent audit runs.",
        "Gives CMOs and leadership immediate visibility into brand health, active risks, and campaign pipeline status.",
        icon_num=1
    )
    
    doc.add_feature_card(
        "2. Brand DNA Studio & Knowledge Confirmation",
        "/brand-dna",
        "The central source of truth for the company. Stores all approved rules, verified facts, and forbidden terminology.",
        "Ingests official guideline PDFs, extracts policy items into structured databases, and presents them for administrator confirmation.",
        "Eliminates confusion across teams by maintaining a single, immutable digital Brand Book that everyone is audited against.",
        icon_num=2
    )
    
    doc.add_feature_card(
        "3. Content Intelligence Workspace",
        "/content-intelligence",
        "Professional 3-panel editor where marketing drafts are analyzed and corrected in real time.",
        "Panel 1 holds the content. Panel 2 lists all detected violations with severity badges. Panel 3 displays retrieved evidence and 1-click fixes.",
        "Allows writers to self-correct mistakes in seconds before submitting drafts to legal or management.",
        icon_num=3
    )
    
    doc.add_feature_card(
        "4. ClaimDNA & The 5-Status Truth Model",
        "/claim-dna",
        "Rigorous verification engine for performance, comparative, and financial claims in marketing copy.",
        "Checks claims against verified facts using a 5-tier status model: Supported, Unsupported, Contradicted, Outdated, or Needs Human Review.",
        "Prevents misleading advertising lawsuits by strictly refusing to guess when supporting proof does not exist.",
        icon_num=4
    )
    
    doc.add_feature_card(
        "5. Product Truth Engine",
        "/brand-dna/products",
        "Hardware and product specification guardian that verifies prices, battery life, memory, processor speeds, and weight.",
        "Parses structured product tables and checks copy for numbers and units (e.g. 16GB RAM vs 512GB SSD; 18 hours battery vs 24 hours).",
        "Stops accidental over-promising or specification errors on tech and e-commerce product pages.",
        icon_num=5
    )

    # =========================================================================
    # PAGE 4: CORE INTELLIGENCE ENGINES (PART 2)
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Feature Deep Dive (Part 2)",
        "Visual Inspection, Multilingual Safety, and Governance",
        "From pixel-level color analysis to cryptographic certification"
    )
    
    doc.add_feature_card(
        "6. Visual DNA & Asset Forensics",
        "/visual-dna & /visual-dna/forensics",
        "Direct pixel-level image auditor for marketing creatives, social banners, and advertisements.",
        "Decodes image pixels to measure dominant colors, brand palette fidelity, WCAG accessibility contrast, and logo geometry (stretch/rotation).",
        "Catches stretched logos, outdated visual marks, unreadable text, and forbidden background colors automatically.",
        icon_num=6
    )
    
    doc.add_feature_card(
        "7. Translation Guard",
        "/translation-guard",
        "Multilingual compliance engine for global marketing campaigns running in multiple languages.",
        "Normalizes scripts and numerals across Hindi, Tamil, French, German, Spanish, Japanese, and checks that claims are not exaggerated.",
        "Ensures global campaigns communicate the exact same legal promises regardless of the language spoken.",
        icon_num=7
    )
    
    doc.add_feature_card(
        "8. Approval Hub (Human Governance Gate)",
        "/approval-hub",
        "The authoritative decision point where certified reviewers make the final go/no-go determination.",
        "Presents the full audit report, evidence cards, and reviewer notes. Only authenticated Reviewers or Admins can record an approval.",
        "Guarantees legal accountability: every approval records who reviewed it, when, and with what mandatory rationale comment.",
        icon_num=8
    )
    
    doc.add_feature_card(
        "9. Brand Passport & Fingerprint Verification",
        "/brand-passport & /brand-passport/verify",
        "Cryptographic proof of brand compliance, generating a unique SHA-256 digital passport for every approved campaign.",
        "Computes a tamper-evident hash of the approved text. The verification tool allows anyone to paste published copy to prove it was untouched.",
        "Provides audit-proof evidence for legal compliance and client contracts, proving content was approved before release.",
        icon_num=9
    )
    
    doc.add_feature_card(
        "10. Brand Memory & Continuous Learning",
        "/brand-memory",
        "Continuous intelligence engine that learns from past corrections to make future governance faster and smarter.",
        "Detects recurring mistakes and frequent writer corrections, automatically proposing new terminology rules for administrators to add.",
        "Turns daily review feedback into permanent company knowledge, preventing the same mistakes from recurring.",
        icon_num=10
    )

    # =========================================================================
    # PAGE 5: ADVANCED ENGINES, AI TOOLS & FRAUD SHIELD
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Advanced Capabilities",
        "AI Rewriting, Digital Twins, Risk Radar & Fraud Shield",
        "Proactive brand defense, entity graphs, and AI assistance"
    )
    
    doc.add_feature_card(
        "11. AI Copy Studio (Grounded Rewriter)",
        "/copy-studio",
        "Generative AI assistant that rewrites flagged marketing copy into compliant, polished prose.",
        "Uses Groq LLMs grounded strictly in the company's approved Brand DNA; falls back to deterministic rule rewrites when offline.",
        "Saves creators hours of rewriting time by instantly offering a ready-to-publish, compliant alternative.",
        icon_num=11
    )
    
    doc.add_feature_card(
        "12. Brand Assistant (Digital Twin Q&A)",
        "/assistant",
        "Conversational AI assistant that answers questions about company policies, approved specs, and tone.",
        "Answers only from approved Brand DNA records, always citing source documents. If information is not approved, it honestly says so.",
        "Gives writers and agency partners an instant 24/7 brand expert so they never have to guess company rules.",
        icon_num=12
    )
    
    doc.add_feature_card(
        "13. Brand Fraud & Counterfeit Shield",
        "/risk-radar/fraud",
        "Proactive security scanner that analyzes suspicious links, promotional text, or screenshots for brand impersonation.",
        "Detects look-alike domains (typosquats), unapproved low prices, copied marketing phrases, and phishing triggers.",
        "Protects customers from being scammed by fraudulent websites masquerading under the company's brand name.",
        icon_num=13
    )
    
    doc.add_feature_card(
        "14. Interactive Knowledge Graph",
        "/knowledge-graph",
        "Dynamic visual network map showing how brands, products, guidelines, rules, findings, and passports interconnect.",
        "Renders SVG entity nodes in 9 distinct color categories with click-to-expand exploration and deep link navigation.",
        "Helps administrators understand brand complexity and audit how individual rules impact multiple marketing campaigns.",
        icon_num=14
    )
    
    doc.add_feature_card(
        "15. Campaign Launch Readiness (12-Point Checklist)",
        "/approval-hub/readiness",
        "Comprehensive pre-flight checklist that verifies all 12 compliance dimensions before a campaign launch.",
        "Validates terminology, claim statuses, product truth, translation guard, visual assets, disclaimers, and approval expiration.",
        "Acts as the final flight controller preventing high-risk campaigns from reaching production.",
        icon_num=15
    )

    # =========================================================================
    # PAGE 6: REAL-WORLD EXAMPLE, CORE PRINCIPLES & SUMMARY
    # =========================================================================
    doc.start_new_page()
    doc.add_page_title_block(
        "Practical Demonstration & Principles",
        "Real-World Test Case & Non-Negotiable System Laws",
        "Concrete proof of how BrandVault AI catches real marketing errors"
    )
    
    doc.add_section_header("The NovaBook AI Laptop Launch Test Case", "Real-World Example")
    doc.add_paragraph("Here is the exact test case run during live demonstrations of BrandVault AI:")
    
    doc.add_callout(
        "Submitted Marketing Copy Draft",
        '"Introducing the world\'s fastest AI laptop! 10x faster than every competitor. Now available for only ₹69,999!"',
        badge="DRAFT COPY",
        color=doc.C_ROSE,
        bg_color=doc.C_ROSE_BG
    )
    
    doc.add_table(
        ["Element Flagged", "Finding Category", "Integrity Status", "Official Brand Truth", "System Correction"],
        [
            ["₹69,999", "Pricing Conflict", "CONTRADICTED", "Approved launch price: ₹79,999 (Master Sheet v2.4)", "Replace with approved ₹79,999"],
            ["world's fastest", "Superlative Claim", "UNSUPPORTED", "No lab benchmark proof in approved guidelines", "Remove superlative claim"],
            ["10x faster than competitors", "Comparative Claim", "UNSUPPORTED", "No verified competitor test data stored", "Remove ungrounded claim"],
            ["Product Naming", "Terminology", "SUPPORTED", "'NovaBook AI Pro 16' is approved", "Keep official product name"]
        ],
        col_widths=[85, 80, 85, 135, 120]
    )
    
    doc.add_section_header("The 4 Non-Negotiable BrandVault Laws", "Architectural Commitments")
    doc.add_table(
        ["Principle", "System Law", "Why It Matters"],
        [
            ["1. Humans Decide", "No AI agent may ever approve, reject, or publish content on its own.", "Eliminates rogue AI actions; preserves human legal accountability."],
            ["2. Deterministic First", "Prices, calculations, colors, and hashes use exact math, never fuzzy AI guesses.", "A price of ₹79,999 is checked with exact numbers, not probabilistic text."],
            ["3. Zero Fake Data", "Every citation links to a real document and page. Absence of proof = UNSUPPORTED.", "The system never invents missing facts to satisfy a user request."],
            ["4. Strict Tenant Isolation", "Workspaces, brands, and documents are 100% isolated by organization ID.", "NOVA TECH data can NEVER be retrieved or seen in VORTEXA workspaces."]
        ],
        col_widths=[90, 195, 220]
    )
    
    doc.add_callout(
        "Ready to Protect Your Brand?",
        "BrandVault AI delivers end-to-end brand protection across copy, claims, visuals, and languages. "
        "Explore the live application at http://localhost:3000 or the cloud deployment at https://brandvault-ai-1.onrender.com.",
        badge="GETTING STARTED",
        color=doc.C_PRIMARY,
        bg_color=doc.C_PRIMARY_BG
    )
    
    return doc.build()

if __name__ == "__main__":
    out_file = os.path.abspath("BRANDVAULT_AI_COMPLETE_PRODUCT_GUIDE.pdf")
    path, pages, size = build_complete_guide(out_file)
    print(f"SUCCESS: Generated {pages}-page PDF at {path} ({size} bytes)")
    
    # Also save to submission directory
    sub_dir = os.path.abspath("submission")
    if os.path.exists(sub_dir):
        sub_file = os.path.join(sub_dir, "BRANDVAULT_AI_COMPLETE_PRODUCT_GUIDE.pdf")
        with open(out_file, "rb") as src, open(sub_file, "wb") as dst:
            dst.write(src.read())
        print(f"COPIED TO: {sub_file}")
