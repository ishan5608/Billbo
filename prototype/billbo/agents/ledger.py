"""Ledger Agent: posts bills to the sales and purchase registers."""
import json

from .. import db
from ..util import route_for

AGENT = "Ledger"


def find(owner_id, bill):
    return db.one("SELECT * FROM bills WHERE owner_id=? AND invoice=? AND party_gstin=?",
                  (owner_id, bill["invoice"], bill["party_gstin"]))


def post(owner, bill, problems):
    """Store the bill. Bills with problems wait in the accountant's review queue and are not counted."""
    status = "needs_review" if problems else "posted"
    bill_id = db.run(
        "INSERT INTO bills(owner_id,direction,party,party_gstin,invoice,date,taxable,gst,route,status,"
        "confidence,problems,ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (owner["id"], bill["direction"], bill["party"], bill["party_gstin"], bill["invoice"],
         bill.get("date", ""), bill["taxable"], bill["gst"], route_for(owner["gstin"], bill["party_gstin"]),
         status, bill.get("confidence", 1.0), json.dumps(problems), db.now()))
    db.audit(owner["id"], AGENT, f"{bill['direction']} bill {status}", f"{bill['party']} {bill['invoice']}")
    return db.one("SELECT * FROM bills WHERE id=?", (bill_id,))


def register(owner_id, direction):
    return db.rows("SELECT * FROM bills WHERE owner_id=? AND direction=? ORDER BY date, id",
                   (owner_id, direction))


def review_queue(owner_id):
    return db.rows("SELECT * FROM bills WHERE owner_id=? AND status='needs_review' ORDER BY id", (owner_id,))


def approve(bill_id, gst=None):
    """Called from the accountant dashboard: a human corrects and accepts a bill."""
    b = db.one("SELECT * FROM bills WHERE id=?", (bill_id,))
    if not b:
        return None
    if gst is not None:
        db.run("UPDATE bills SET gst=? WHERE id=?", (gst, bill_id))
    db.run("UPDATE bills SET status='posted', problems='[]' WHERE id=?", (bill_id,))
    db.audit(b["owner_id"], "Accountant", "bill reviewed and accepted", f"{b['party']} {b['invoice']}")
    return db.one("SELECT * FROM bills WHERE id=?", (bill_id,))
