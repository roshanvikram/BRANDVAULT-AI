"""Round 3 · Improvement 3 — ingestion formats, hybrid retrieval, dense embeddings, pgvector,
guideline versions and the Guideline Gap Agent."""
import io
import os
import unittest
import zipfile

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.brand import BrandGuideline, DocumentChunk
from backend.app.models.product import ProductFact
from backend.app.services import embeddings, ingest, rag
from backend.app.services.seed import NOVA_ORG_ID
from backend.main import app
from backend.tests import creative_fixtures as cf
from backend.tests._util import drop_db, make_seeded_db

API = "/api/v1"


def make_docx(paragraphs):
    """[(style or None, text)] -> minimal .docx bytes."""
    from xml.sax.saxutils import escape
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(
        f'<w:p>{f"<w:pPr><w:pStyle w:val=\"{st}\"/></w:pPr>" if st else ""}<w:r><w:t>{escape(t)}</w:t></w:r></w:p>' for st, t in paragraphs)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


def make_xlsx(rows):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    strings, xml_rows = [], []
    for r, row in enumerate(rows, 1):
        cells = []
        for c, val in enumerate(row):
            strings.append(val)
            cells.append(f'<c r="{chr(65 + c)}{r}" t="s"><v>{len(strings) - 1}</v></c>')
        xml_rows.append(f'<row r="{r}">{"".join(cells)}</row>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{ns}">' + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{ns}"><sheetData>{"".join(xml_rows)}</sheetData></worksheet>')
    return buf.getvalue()


class IngestUnitTests(unittest.TestCase):
    def test_docx_sections_follow_headings(self):
        kind, sections, passages, _ = ingest.ingest("g.docx", make_docx([
            ("Heading1", "Logo Usage"), (None, "Keep clear space around the logo equal to the letter N."),
            ("Heading1", "Pricing"), (None, "The official launch price is ₹79,999 for NovaBook AI Pro 16.")]))
        self.assertEqual(kind, "docx")
        self.assertEqual([s["label"] for s in sections], ["Section 1 · Logo Usage", "Section 2 · Pricing"])
        self.assertTrue(all(p["label"].startswith("Section") for p in passages))

    def test_html_ignores_scripts_and_splits_on_headings(self):
        html = b"<html><script>var x=1</script><h1>Voice</h1><p>Calm, precise and confident tone always.</p><h2>Claims</h2><p>Superlatives need an independent benchmark report.</p></html>"
        _, sections, _, _ = ingest.ingest("g.html", html)
        self.assertEqual(len(sections), 2)
        self.assertNotIn("var x", sections[0]["text"])

    def test_spreadsheets_become_rows(self):
        csv_bytes = b"Product,Price,Notes\nNovaBook AI Pro 16,79999,Launch\n"
        _, sections, _, _ = ingest.ingest("prices.csv", csv_bytes)
        self.assertEqual(sections[0]["label"], "Row 2")
        self.assertIn("Price: 79999", sections[0]["text"])
        _, xs, _, _ = ingest.ingest("prices.xlsx", make_xlsx([["Product", "Price"], ["NovaBook AI Pro 16", "79999"]]))
        self.assertIn("Product: NovaBook AI Pro 16", xs[0]["text"])

    def test_long_text_is_split_into_overlapping_passages(self):
        text = " ".join(f"Sentence number {i} explains a brand rule in some detail." for i in range(60))
        _, _, passages, _ = ingest.ingest("g.md", text.encode())
        self.assertGreater(len(passages), 3)
        self.assertTrue(all(len(p["text"]) <= ingest.TARGET_CHARS + 80 for p in passages))

    def test_pdf_pages_and_rejections(self):
        _, sections, _, _ = ingest.ingest("g.pdf", cf.text_pdf([["Page one text about tone and voice."], ["Page two pricing rules."]]))
        self.assertEqual([s["label"] for s in sections], ["Page 1", "Page 2"])
        with self.assertRaises(ingest.IngestError):
            ingest.file_type("virus.exe")
        with self.assertRaises(ingest.IngestError):
            ingest.ingest("bad.docx", b"not a zip")


class RankingUnitTests(unittest.TestCase):
    def test_bm25_prefers_rare_matching_terms(self):
        s = rag.bm25_scores("warranty", ["the warranty lasts two years", "price and price and price", "warranty"])
        self.assertGreater(s[2], 0)
        self.assertEqual(s[1], 0)

    def test_rrf_rewards_agreement(self):
        f = rag._rrf([{"a": 3, "b": 2, "c": 0}, {"b": 5, "a": 1}])
        self.assertGreater(f["b"], f["a"] * 0.99)
        self.assertNotIn("c", f)


class RetrievalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prev = (settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED)
        settings.LLM_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False
        cls.engine, cls.Session, cls.path = make_seeded_db()

        def _override():
            d = cls.Session()
            try:
                yield d
            finally:
                d.close()

        app.dependency_overrides[get_db] = _override
        cls.client = TestClient(app)
        r = cls.client.post(f"{API}/auth/login", json={"email": "admin@novatech.demo", "password": "Admin@2026"})
        cls.admin = {"Authorization": f"Bearer {r.json()['access_token']}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        drop_db(cls.engine, cls.path)
        settings.LLM_ENABLED, settings.RATE_LIMIT_ENABLED = cls._prev

    def _upload(self, name, data, replaces=None):
        form = {"replaces": replaces} if replaces else {}
        r = self.client.post(f"{API}/brand/guidelines/upload", files={"file": (name, data)}, data=form, headers=self.admin)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_docx_upload_is_cited_by_section(self):
        g = self._upload("Visual_Identity.docx", make_docx([("Heading1", "Logo Usage"),
                         (None, "Keep clear space around the NOVA TECH logo equal to the height of the letter N at all times.")]))
        db = self.Session()
        chunks = db.query(DocumentChunk).filter(DocumentChunk.guideline_id == g["id"]).all()
        db.close()
        self.assertEqual(chunks[0].section_label, "Section 1 · Logo Usage")
        hits = self.client.post(f"{API}/rag/search", json={"org_id": NOVA_ORG_ID, "query": "clear space around the logo", "top_k": 3},
                                headers=self.admin).json()
        results = hits["results"] if isinstance(hits, dict) else hits
        self.assertTrue(any("Section 1 · Logo Usage" in h["citation"] for h in results), results)

    def test_price_list_proposes_pending_facts_only(self):
        self._upload("price_list.csv", b"Product,Price\nNovaBook AI Pro 16,76999\nUnknown Gadget,1000\n")
        db = self.Session()
        facts = db.query(ProductFact).filter(ProductFact.org_id == NOVA_ORG_ID, ProductFact.origin == "spreadsheet").all()
        db.close()
        self.assertEqual(len(facts), 1)  # unknown products are skipped, never invented
        self.assertEqual((facts[0].status, facts[0].value_num, facts[0].page_reference), ("pending", 76999.0, 2))

    def test_replacing_a_document_retires_it_and_flags_conflicts(self):
        old = self._upload("Pricing_v1.md", b"# Pricing\nNovaBook AI Pro 16 launch price is \xe2\x82\xb974,999 for all channels.")
        gaps = self.client.get(f"{API}/products/knowledge-gaps", headers=self.admin).json()
        conflict = [i for i in gaps["items"] if i["key"].startswith("guideline_conflict:")]
        self.assertTrue(conflict, "₹74,999 vs the seeded ₹79,999 should be a guideline conflict")
        self._upload("Pricing_v2.md", b"# Pricing\nNovaBook AI Pro 16 launch price is \xe2\x82\xb979,999 for all channels.", replaces=old["id"])
        db = self.Session()
        self.assertEqual(db.get(BrandGuideline, old["id"]).status, "superseded")
        db.close()
        gaps = self.client.get(f"{API}/products/knowledge-gaps", headers=self.admin).json()
        self.assertFalse([i for i in gaps["items"] if i["key"].startswith("guideline_conflict:")])
        hits = self.client.post(f"{API}/rag/search", json={"org_id": NOVA_ORG_ID, "query": "launch price for all channels", "top_k": 5},
                                headers=self.admin).json()
        results = hits["results"] if isinstance(hits, dict) else hits
        self.assertFalse(any(h["filename"] == "Pricing_v1.md" for h in results))

    def test_unrelated_query_returns_nothing(self):
        hits = self.client.post(f"{API}/rag/search", json={"org_id": NOVA_ORG_ID, "query": "favourite pizza topping", "top_k": 3},
                                headers=self.admin).json()
        results = hits["results"] if isinstance(hits, dict) else hits
        self.assertEqual(results, [])

    def test_bad_files_rejected(self):
        r = self.client.post(f"{API}/brand/guidelines/upload", files={"file": ("x.exe", b"MZ")}, headers=self.admin)
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"{API}/brand/guidelines/upload", files={"file": ("x.docx", b"not a docx")}, headers=self.admin)
        self.assertEqual(r.status_code, 422)


class DenseRetrievalTests(unittest.TestCase):
    def setUp(self):
        if not embeddings.status()["available"]:
            self.skipTest("no embedding model available")
        self.engine, self.Session, self.path = make_seeded_db()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        drop_db(self.engine, self.path)

    def test_paraphrase_found_by_meaning_and_vectors_persisted(self):
        from backend.app.models.retrieval import ChunkEmbedding
        r = rag.RagRetriever(self.db)
        r.index_org(NOVA_ORG_ID)
        self.assertGreater(self.db.query(ChunkEmbedding).filter(ChunkEmbedding.org_id == NOVA_ORG_ID).count(), 0)
        hit = r.best(NOVA_ORG_ID, "can we call it the fastest laptop")
        self.assertIn("Advertising Claims", hit["content"])
        self.assertIn("dense", hit["retrieval"])
        self.assertEqual(r._dense_index(NOVA_ORG_ID, self.db.query(DocumentChunk).join(DocumentChunk.guideline)
                                        .filter(BrandGuideline.org_id == NOVA_ORG_ID).all()), 0)  # unchanged chunks are not re-embedded

    @unittest.skipUnless(os.getenv("BV_TEST_DATABASE_URL", "").startswith("postgres"), "PostgreSQL only")
    def test_pgvector_native_search_on_postgres(self):
        from sqlalchemy import text
        r = rag.RagRetriever(self.db)
        r.index_org(NOVA_ORG_ID)
        n = self.db.execute(text("SELECT count(*) FROM chunk_vectors WHERE org_id = :o"), {"o": NOVA_ORG_ID}).scalar()
        self.assertGreater(n, 0)
        prov = embeddings.get_provider()
        res = rag._pgvector_search(self.db, NOVA_ORG_ID, prov.name, embeddings.normalise(prov.embed_query("launch price")))
        self.assertTrue(res and res[0][1] > 0.5)


if __name__ == "__main__":
    unittest.main()
