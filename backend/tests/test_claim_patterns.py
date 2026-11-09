"""Unit tests for the claim detectors in app/services/claim_patterns.py."""
import unittest
from types import SimpleNamespace as NS

from backend.app.services import claim_patterns as cp

FACTS = [
    NS(fact_key="NovaCore N10 AI Engine", fact_value="45 TOPS NPU with sustained 3.8 GHz clock speed"),
    NS(fact_key="Standard Battery Endurance", fact_value="Up to 18 hours mixed productivity workload"),
    NS(fact_key="Standard Customer Warranty", fact_value="2-Year On-Site Limited Hardware Warranty"),
]


class PriceTests(unittest.TestCase):
    def kinds(self, text):
        return [(p["value"], p["kind"]) for p in cp.find_prices(text)]

    def test_formats(self):
        self.assertEqual(self.kinds("Rs.74,990/- only"), [("74990", "price")])
        self.assertEqual(self.kinds("NovaBook @ 69999 rs today"), [("69999", "price")])
        self.assertEqual(self.kinds("Priced at ₹79,999.00."), [("79999", "price")])

    def test_rs_without_number_is_not_a_price(self):
        self.assertEqual(cp.find_prices("Hi! NovaBook rs, limited stock"), [])

    def test_emi_and_accessory(self):
        self.assertEqual(self.kinds("No-cost EMI from ₹6,667/month"), [("6667", "instalment")])
        self.assertEqual(self.kinds("NovaSleeve case, ₹2,499, sold separately."), [("2499", "accessory")])
        # A laptop price in the same sentence as an accessory is still the product price.
        self.assertEqual(self.kinds("AI laptop at ₹69,999 with free NovaSleeve."), [("69999", "price")])


class ClaimTests(unittest.TestCase):
    def test_superlatives(self):
        for text in ("The fastest laptop in India.", "India's #1 AI laptop.", "World’s fastest AI laptop",
                     "the most powerful AI laptop ever made", "Best. Deal. Ever!!!"):
            self.assertTrue(cp.find_superlatives(text), text)
        for text in ("Fast, quiet and precise.", "Our best work yet is the keyboard feel."):
            self.assertFalse(cp.find_superlatives(text), text)

    def test_comparatives(self):
        for text in ("2x faster than the MacBook Air", "Beats Dell, HP and Lenovo", "Leaves the competition behind.",
                     "Faster than anything else on the market."):
            self.assertTrue(cp.find_comparatives(text), text)
        self.assertFalse(cp.find_comparatives("Cheaper than you think."))

    def test_spec_conflicts(self):
        wrong = {c["raw"] for t in ("Up to 24 hours of battery life.", "rated at 60 TOPS", "Comes with a 3-year warranty.",
                                    "Includes an 18-month warranty.") for c in cp.find_spec_conflicts(t, FACTS)}
        self.assertEqual(len(wrong), 4)
        for ok in ("Up to 18 hours on a single charge, battery included.", "2-year on-site warranty", "45 TOPS NPU",
                   "Charges to 80% in 1 hour; the battery lasts all day.", "EMI for 12 months on select cards."):
            self.assertEqual(cp.find_spec_conflicts(ok, FACTS), [], ok)

    def test_rule_terms_and_tone(self):
        rule = NS(rule_text="Cite it as 'NovaBook AI Pro 16'. Do not use diminutive terms like 'budget laptop' or 'cheap AI device'.")
        terms = [t for t, _ in cp.rule_forbidden_terms([rule], ["cheap"])]
        self.assertEqual(terms, ["budget laptop"])  # 'cheap AI device' is already covered by 'cheap'
        self.assertTrue(cp.tone_signals("OMG this laptop is INSANE"))
        self.assertTrue(cp.tone_signals("HUGE SALE — LIMITED TIME ONLY"))
        self.assertEqual(cp.tone_signals("NOVA TECH announces the NovaBook with 45 TOPS AI and GST invoice", "NOVA TECH"), [])


if __name__ == "__main__":
    unittest.main()
