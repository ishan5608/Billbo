"""Run: python -m unittest demo/test_billbo.py"""
import sys, unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import billbo_demo as b


class BillboTests(unittest.TestCase):
    def setUp(self):
        self.cards = b.load("rules/rule_cards.json")["cards"]

    def test_itc_guard_totals(self):
        safe, issues = b.itc_guard(b.load("demo/data/purchases.json"), b.load("demo/data/gstr2b.json"))
        self.assertEqual(safe, 7560 + 3330 + 3000)
        self.assertEqual(sum(i["at_risk"] for i in issues), 6120 + 2160 + 1500)
        self.assertEqual(len(issues), 3)

    def test_eway_only_flags_missing_above_limit(self):
        flagged = b.eway_needed(b.load("demo/data/sales.json"), self.cards)
        self.assertEqual([s["invoice"] for s in flagged], ["INV-502"])

    def test_rule_change_is_one_card(self):
        cards = [dict(c) for c in self.cards]
        b.rule(cards, "EWB-INTRA-KA")["value"] = 30000
        flagged = b.eway_needed(b.load("demo/data/sales.json"), cards)
        self.assertEqual([s["invoice"] for s in flagged], ["INV-501", "INV-502"])

    def test_deadlines_order(self):
        days = [d.day for _, d, _ in b.deadlines(self.cards, date(2026, 12, 1))]
        self.assertEqual(days, [7, 11, 14, 20])


if __name__ == "__main__":
    unittest.main()
