"""End-to-end tests of the agents and the business model. Run from the prototype folder:
    python -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

os.environ["BILLBO_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from billbo import db, plans, rules, server  # noqa: E402
from billbo.agents import itc_guard, orchestrator as orch, returns  # noqa: E402

RAMESH, FATHIMA = 1, 2  # Ramesh is on Plus, Fathima on Free


def texts(replies):
    return " | ".join(r["text"] for r in replies)


class FlowTests(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_clean_bill_is_saved_and_credit_is_safe(self):
        out = texts(orch.handle(RAMESH, "bill", sample_id="b1"))
        self.assertIn("Saved. Sri Lakshmi Traders, ₹21,830", out)
        self.assertEqual(itc_guard.reconcile(RAMESH)["at_risk"], 0)

    def test_unreported_bill_offers_reminder_and_owner_must_approve(self):
        out = texts(orch.handle(RAMESH, "bill", sample_id="b2"))
        self.assertIn("₹6,120 of your credit is at risk", out)
        self.assertEqual(db.rows("SELECT * FROM drafts WHERE kind='supplier_reminder'"), [])
        out = texts(orch.handle(RAMESH, "text", "yes"))
        self.assertIn("Forward it to Mahadev Plastics yourself", out)
        self.assertEqual(len(db.rows("SELECT * FROM drafts WHERE kind='supplier_reminder'")), 1)

    def test_blurry_bill_asks_before_posting(self):
        out = texts(orch.handle(RAMESH, "bill", sample_id="b3"))
        self.assertIn("not clear", out)
        self.assertEqual(db.one("SELECT COUNT(*) n FROM bills WHERE invoice='MP-2260'")["n"], 0)
        orch.handle(RAMESH, "text", "2160")
        self.assertEqual(db.one("SELECT gst FROM bills WHERE invoice='MP-2260'")["gst"], 2160)

    def test_wrong_arithmetic_goes_to_review_and_is_not_counted(self):
        out = texts(orch.handle(RAMESH, "bill", sample_id="b5"))
        self.assertIn("not a known GST rate", out)
        self.assertEqual(returns.summary(RAMESH)["bills_waiting_review"], 1)
        self.assertFalse(returns.summary(RAMESH)["ready_for_accountant"])

    def test_duplicate_bill_is_not_added_twice(self):
        orch.handle(RAMESH, "bill", sample_id="b1")
        self.assertIn("already have", texts(orch.handle(RAMESH, "bill", sample_id="b1")))

    def test_eway_draft_needs_vehicle_and_is_never_generated_by_billbo(self):
        out = texts(orch.handle(RAMESH, "voice", "74,500 rupees order going to Pune Polymers tomorrow"))
        self.assertIn("needs an e-way bill", out)
        self.assertEqual(db.one("SELECT status FROM drafts WHERE kind='eway'")["status"], "needs_vehicle")
        orch.handle(RAMESH, "text", "KA 19 AB 1234")
        d = db.one("SELECT * FROM drafts WHERE kind='eway'")
        self.assertEqual(d["status"], "ready")
        self.assertEqual(json.loads(d["payload"])["vehicle"], "KA19AB1234")

    def test_small_order_needs_no_eway_bill(self):
        out = texts(orch.handle(RAMESH, "voice", "sold 38,000 to Hubli Hardware"))
        self.assertIn("No e-way bill needed", out)

    def test_rule_change_is_one_card(self):
        self.assertEqual(rules.eway_limit("inter"), (50000, "EWB-INTER"))
        card = rules.card("EWB-INTRA-KA")
        old, card["value"] = card["value"], 30000
        try:
            self.assertIn("needs an e-way bill", texts(orch.handle(RAMESH, "voice", "sold 38,000 to Hubli Hardware")))
        finally:
            card["value"] = old

    def test_free_plan_holds_back_paid_features_but_still_warns(self):
        out = texts(orch.handle(FATHIMA, "bill", sample_id="b2"))
        self.assertIn("Saved.", out)
        self.assertIn("Billbo Plus", out)
        self.assertNotIn("Shall I draft a reminder", out)
        out = texts(orch.handle(FATHIMA, "voice", "74,500 order going to Pune Polymers"))
        self.assertIn("above the e-way bill limit", out)
        self.assertEqual(db.rows("SELECT * FROM drafts WHERE owner_id=?", (FATHIMA,)), [])
        out = texts(orch.handle(FATHIMA, "notice", sample_id="n1"))
        self.assertIn("within 7 days", out)
        self.assertNotIn("What it means", out)

    def test_upgrade_unlocks_plus(self):
        orch.handle(FATHIMA, "text", "upgrade")
        self.assertIn("at risk", texts(orch.handle(FATHIMA, "bill", sample_id="b2")))
        self.assertIn("Shall I draft a reminder", db.rows("SELECT text FROM messages ORDER BY id DESC LIMIT 1")[0]["text"])

    def test_billing_follows_the_business_model(self):
        b = plans.billing(1)
        self.assertEqual((b["clients"], b["plus_clients"]), (3, 1))
        self.assertEqual(b["total"], 3 * rules.value("PRICE-ACCOUNTANT") + 1 * rules.value("PRICE-PLUS"))

    def test_supplier_reporting_makes_credit_safe(self):
        orch.handle(RAMESH, "bill", sample_id="b2")
        bill = db.one("SELECT id FROM bills WHERE invoice='MP-2231'")
        msg = orch.supplier_reported(RAMESH, bill["id"])
        self.assertIn("credit is safe", msg["text"])
        self.assertEqual(itc_guard.reconcile(RAMESH)["at_risk"], 0)

    def test_return_summary_numbers(self):
        for s in ("b1", "b4", "s1", "s2"):
            orch.handle(RAMESH, "bill", sample_id=s)
        s = returns.summary(RAMESH)
        self.assertEqual(s["output_tax"], 5400 + 9000)
        self.assertEqual(s["itc_safe"], 7560 + 3330 + 3000)
        self.assertEqual(s["itc_at_risk"], 1500)
        self.assertEqual(s["net_payable"], 14400 - 13890)

    def test_language_switch(self):
        orch.handle(RAMESH, "text", "hindi")
        self.assertIn("सेव हो गया", texts(orch.handle(RAMESH, "bill", sample_id="b1")))

    def test_no_agent_code_files_a_return(self):
        for s in ("b1", "b2", "s1"):
            orch.handle(RAMESH, "bill", sample_id=s)
        orch.handle(RAMESH, "text", "summary")
        self.assertEqual(db.rows("SELECT * FROM filings"), [])
        agents_dir = Path(__file__).resolve().parent.parent / "billbo" / "agents"
        for f in agents_dir.glob("*.py"):
            self.assertNotIn("INSERT INTO filings", f.read_text(encoding="utf-8"), f.name)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.reset()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def call(self, path, body=None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if "json" in r.headers["Content-Type"] else raw

    def test_pages_and_api(self):
        for page in ("/", "/chat", "/dashboard", "/portal"):
            self.assertIn("Billbo", self.call(page))
        r = self.call("/api/send", {"owner_id": 1, "kind": "bill", "sample_id": "b5"})
        self.assertIn("accountant", r["replies"][0]["text"])
        d = self.call("/api/client?owner_id=1")
        self.assertEqual(len(d["review"]), 1)
        self.call("/api/review", {"bill_id": d["review"][0]["id"], "gst": 1800})
        self.assertEqual(self.call("/api/client?owner_id=1")["review"], [])
        self.assertIn("PURCHASE REGISTER", self.call("/api/pack.csv?owner_id=1"))
        self.assertEqual(self.call("/api/dashboard")["billing"]["clients"], 3)
        self.call("/api/portal/file", {"owner_id": 1, "return_type": "GSTR-3B", "filed_by": "Suresh"})
        self.assertEqual(len(self.call("/api/client?owner_id=1")["filings"]), 1)


if __name__ == "__main__":
    unittest.main()
