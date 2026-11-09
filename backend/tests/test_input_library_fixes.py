"""Regression tests for problems found by running the input library (inputs/) through the API."""
import unittest
from types import SimpleNamespace as NS

from backend.app.services import claim_patterns as cp
from backend.app.services import ocr
from backend.app.services import translation_guard as tg


class OcrDigitTests(unittest.TestCase):
    def test_letters_inside_numbers(self):
        self.assertEqual(ocr.fix_digits("1ox faster than every competitor")[0], "10x faster than every competitor")
        self.assertEqual(ocr.fix_digits("alert: 75,0o0 today")[0], "alert: 75,000 today")
        for keep in ("NovaCore N10 delivers 45 TOPS", "Ill be there", "The 16GB model", "hello lol"):
            self.assertEqual(ocr.fix_digits(keep)[0], keep)

    def test_dropped_rupee_after_alert(self):
        self.assertIn("₹74,999", ocr.restore_currency("Price drop alert:74,999thisweekend.", "₹")[0])


class TranslationTests(unittest.TestCase):
    def test_hindi_negation_whole_words(self):
        self.assertEqual(tg.count_negations("NovaBook AI Pro 16 की कीमत ₹79,999 है।", "hi"), 0)  # कीमत contains मत
        self.assertEqual(tg.count_negations("NovaCore N10 45 TOPS प्रदान करता है।", "hi"), 0)
        self.assertEqual(tg.count_negations("EMI पर कोई प्रोसेसिंग शुल्क नहीं।", "hi"), 1)

    def test_label_sets_language(self):
        self.assertEqual(tg.language_from_label("French (France)"), "fr")
        self.assertEqual(tg.language_from_label("fr-FR"), "fr")
        self.assertIsNone(tg.language_from_label("Version B"))
        ctx = tg.BrandContext()
        r = tg.analyze_pair("No processing fee on EMI.", "en", "Pas de frais de dossier sur l'EMI.", ctx, language_hint="fr")
        self.assertEqual(r["language"]["code"], "fr")
        self.assertEqual(r["findings"], [])

    def test_trademark_names_must_survive(self):
        r = tg.analyze_pair("The NovaCore N10 delivers 45 TOPS.", "en", "Le Nova Core N1 offre 45 TOPS.", tg.BrandContext(),
                            language_hint="fr")
        self.assertIn("brand_term_changed", [f["type"] for f in r["findings"]])


class AccessoryTests(unittest.TestCase):
    def test_accessory_sentence(self):
        self.assertTrue(cp.is_accessory_sentence("NovaSleeve 16 protective sleeve, ₹2,499."))
        self.assertFalse(cp.is_accessory_sentence("AI laptop at ₹69,999 with free NovaSleeve."))
        self.assertFalse(cp.is_accessory_sentence("NovaBook AI Pro 16 with a sleeve, ₹79,999."))

    def test_superlative_tail_included(self):
        self.assertEqual(cp.find_superlatives("The best laptop money can buy."), ["best laptop money can buy"])
        self.assertEqual(cp.find_superlatives("India's #1 AI laptop."), ["India's #1 AI laptop"])


class CopyStudioTests(unittest.TestCase):
    def test_rules_based_rewrite_clears_issues(self):
        from backend.app.services.copystudio import _heuristic_rewrite
        facts = [NS(category="Pricing", fact_key="NovaBook AI Pro 16 Launch Price", fact_value="₹79,999",
                    verification_source="Pricing doc", valid_until=None),
                 NS(category="Product Specification", fact_key="Standard Battery Endurance",
                    fact_value="Up to 18 hours mixed productivity workload", verification_source="Lab", valid_until=None)]
        terms = [NS(prohibited_term="cheap", preferred_term="exceptional enterprise value / highly accessible", explanation="")]
        out = _heuristic_rewrite("OMG it's INSANE!! Cheaper than ever, 3x faster than Apple. Up to 24 hours of battery "
                                 "life at Rs.69,999/- only.", facts, terms, provider_available=False)["rewritten"]
        self.assertIn("₹79,999", out)
        self.assertIn("18 hours", out)
        for gone in ("OMG", "INSANE", "!", "Apple", "Cheaper", "24 hours"):
            self.assertNotIn(gone, out)
        self.assertEqual(cp.find_comparatives(out), [])


if __name__ == "__main__":
    unittest.main()
