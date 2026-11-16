"""Orchestrator: routes every owner message to the right agent, keeps an audit trail, and applies
the plan (Free or Plus). Nothing here files a return or generates a real e-way bill."""
import json
import re

from .. import db, plans
from ..i18n import t
from ..util import find_amount, find_vehicle, inr, route_for
from . import dispatch, intake, itc_guard, ledger, notice, returns

AGENT = "Orchestrator"
HELP = ("You can send me: a bill photo, a notice photo, or a voice note. Or type: 'credit' (is my input "
        "credit safe), 'suppliers' (scorecard), 'due' (due dates), 'summary' (what am I signing), "
        "'hindi' / 'kannada' / 'english', 'plan', 'upgrade'.")


def owner_row(owner_id):
    return db.one("SELECT * FROM owners WHERE id=?", (owner_id,))


def say(owner_id, text, agent=AGENT):
    db.run("INSERT INTO messages(owner_id,sender,kind,text,agent,ts) VALUES(?,?,?,?,?,?)",
           (owner_id, "billbo", "text", text, agent, db.now()))
    return {"text": text, "agent": agent}


def handle(owner_id, kind, text="", sample_id=None):
    """Entry point for every incoming message. Returns the list of replies Billbo sent."""
    owner = owner_row(owner_id)
    if not owner:
        raise ValueError("unknown owner")
    label = text
    if kind == "bill":
        b = intake.read_photo(sample_id)
        label = "Photo: " + (b["label"] if b else "unknown bill")
    elif kind == "notice":
        n = next((x for x in intake.samples()["notices"] if x["id"] == sample_id), None)
        label = n["label"] if n else "Notice photo"
    elif kind == "voice":
        label = "Voice note (transcript): " + text
    db.run("INSERT INTO messages(owner_id,sender,kind,text,agent,ts) VALUES(?,?,?,?,?,?)",
           (owner_id, "owner", kind, label, None, db.now()))
    db.audit(owner_id, AGENT, f"received {kind}", label[:120])

    if kind == "bill":
        return _on_bill_photo(owner, sample_id)
    if kind == "notice":
        n = next((x for x in intake.samples()["notices"] if x["id"] == sample_id), None)
        return [say(owner_id, notice.handle(owner, n["form"] if n else "?", plans.is_plus(owner)), notice.AGENT)]
    replies = _resolve_pending(owner, text)
    if replies is None:
        replies = _on_text(owner, text)
    return replies


# ---------- bills ----------

def _on_bill_photo(owner, sample_id):
    bill = intake.read_photo(sample_id)
    if not bill:
        return [say(owner["id"], "I could not read that photo. Please send it again.", intake.AGENT)]
    db.audit(owner["id"], intake.AGENT, "bill read", f"{bill['party']} {bill['invoice']} conf {bill['confidence']}")
    if bill["confidence"] < intake.MIN_CONFIDENCE and bill["unclear"]:
        db.set_pending(owner["id"], {"type": "clarify", "bill": bill, "field": bill["unclear"]})
        return [say(owner["id"], f"The photo is not clear. I read the GST amount on {bill['invoice']} from "
                    f"{bill['party']} as {inr(bill['gst'])}. Is that right? Reply yes, or send the correct amount.",
                    intake.AGENT)]
    return _post_bill(owner, bill)


def _post_bill(owner, bill):
    oid = owner["id"]
    if ledger.find(oid, bill):
        return [say(oid, f"I already have {bill['invoice']} from {bill['party']}. Not added again.", ledger.AGENT)]
    problems = intake.validate(bill)
    row = ledger.post(owner, bill, problems)
    total = inr(bill["taxable"] + bill["gst"])
    if problems:
        return [say(oid, f"I saved {bill['invoice']} from {bill['party']} ({total}), but something does not add "
                    f"up: {'; '.join(problems)}. I have sent it to your accountant to check. It is not counted yet.",
                    intake.AGENT)]
    out = [say(oid, t(owner["lang"], "saved", party=bill["party"], total=total), ledger.AGENT)]
    if bill["direction"] == "purchase":
        out += _credit_follow_up(owner, row)
    else:
        out += _dispatch_check(owner, bill["party"], bill["party_gstin"], bill["taxable"] + bill["gst"],
                               row["route"], bill["invoice"])
    return out


def _credit_follow_up(owner, row):
    oid = owner["id"]
    mine = [i for i in itc_guard.supplier_issues(oid, row["party_gstin"])]
    if not any(i["bill_id"] == row["id"] for i in mine):
        return []
    if not plans.is_plus(owner):
        return [say(oid, "I found input credit at risk on this bill. " + plans.upsell_line(), itc_guard.AGENT)]
    amount = inr(sum(i["at_risk"] for i in mine))
    if db.get_pending(oid):
        return [say(oid, f"Note: {row['party']} has not reported this invoice correctly. {amount} of credit is "
                    "at risk. Type 'credit' for details.", itc_guard.AGENT)]
    db.set_pending(oid, {"type": "reminder", "gstin": row["party_gstin"], "supplier": row["party"]})
    return [say(oid, t(owner["lang"], "itc_risk", supplier=row["party"], n=len(mine), amount=amount),
                itc_guard.AGENT)]


# ---------- dispatch ----------

def _dispatch_check(owner, buyer, buyer_gstin, value, route, invoice=None):
    oid = owner["id"]
    needed, limit, _ = dispatch.needs_eway(value, route)
    if not needed:
        return []
    if not plans.is_plus(owner):
        return [say(oid, f"Careful: {inr(value)} is above the e-way bill limit of {inr(limit)}. Generate an "
                    "e-way bill before the goods leave. " + plans.upsell_line(), dispatch.AGENT)]
    draft_id = dispatch.create_draft(oid, buyer, buyer_gstin, value, route, invoice)
    db.set_pending(oid, {"type": "vehicle", "draft_id": draft_id})
    return [say(oid, t(owner["lang"], "eway_needed", value=inr(value), limit=inr(limit)), dispatch.AGENT)]


def _on_dispatch_text(owner, text, amount):
    low = text.lower()
    cust = next((c for c in db.rows("SELECT * FROM customers")
                 if c["name"].lower() in low or c["alias"] in low), None)
    if not cust:
        db.set_pending(owner["id"], {"type": "buyer_state", "value": amount})
        return [say(owner["id"], f"Noted, an order of {inr(amount)}. Is the buyer in Karnataka or in another "
                    "state? (reply 'karnataka' or 'other')", dispatch.AGENT)]
    route = route_for(owner["gstin"], cust["gstin"])
    out = _dispatch_check(owner, cust["name"], cust["gstin"], amount, route)
    if not out:
        out = [say(owner["id"], f"An order of {inr(amount)} to {cust['name']} is below the e-way bill limit. "
                   "No e-way bill needed.", dispatch.AGENT)]
    out.append(say(owner["id"], "Send me the invoice photo when it is ready, so I can add it to your sales "
                   "register.", ledger.AGENT))
    return out


# ---------- waiting for an answer ----------

def _resolve_pending(owner, text):
    oid, state = owner["id"], db.get_pending(owner["id"])
    if not state:
        return None
    low = text.strip().lower()
    yes = low in ("yes", "y", "ok", "haan", "ha", "houdu", "correct", "right")
    no = low in ("no", "n", "nahi", "beda")
    if state["type"] == "clarify":
        bill = state["bill"]
        amount = re.fullmatch(r"[₹\s]*([\d,]+)", text.strip())
        if yes or amount:
            if amount:
                bill[state["field"]] = int(amount.group(1).replace(",", ""))
            bill["confidence"] = 1.0
            db.set_pending(oid, None)
            db.audit(oid, intake.AGENT, "owner confirmed unclear field", bill["invoice"])
            return _post_bill(owner, bill)
        return None
    if state["type"] == "vehicle":
        vehicle = find_vehicle(text)
        if vehicle:
            dispatch.set_vehicle(state["draft_id"], vehicle)
            db.set_pending(oid, None)
            return [say(oid, t(owner["lang"], "eway_ready", vehicle=vehicle), dispatch.AGENT)]
        return None
    if state["type"] == "reminder":
        if yes:
            issues = itc_guard.supplier_issues(oid, state["gstin"])
            msg = itc_guard.reminder_text(owner, issues)
            db.run("INSERT INTO drafts(owner_id,kind,payload,status,ts) VALUES(?,?,?,?,?)",
                   (oid, "supplier_reminder", json.dumps({"supplier": state["supplier"], "text": msg}),
                    "approved_by_owner", db.now()))
            db.audit(oid, itc_guard.AGENT, "supplier reminder drafted", state["supplier"])
            db.set_pending(oid, None)
            return [say(oid, f"Here is the reminder. Forward it to {state['supplier']} yourself, I do not send "
                        f"messages to others:\n\n{msg}", itc_guard.AGENT)]
        if no:
            db.set_pending(oid, None)
            return [say(oid, "Okay, no reminder. Type 'credit' any time to see the list.", itc_guard.AGENT)]
        return None
    if state["type"] == "buyer_state":
        if any(w in low for w in ("karnataka", "same", "inside", "local")):
            route = "intra"
        elif any(w in low for w in ("other", "outside", "another")):
            route = "inter"
        else:
            return None
        db.set_pending(oid, None)
        out = _dispatch_check(owner, "Buyer (name to confirm)", "", state["value"], route)
        return out or [say(oid, f"An order of {inr(state['value'])} is below the e-way bill limit. No e-way "
                           "bill needed.", dispatch.AGENT)]
    return None


# ---------- typed or spoken messages ----------

def _on_text(owner, text):
    oid, low = owner["id"], text.lower()
    for word, lang, reply in (("hindi", "hi", "ठीक है, अब मैं हिंदी में जवाब दूँगा।"),
                              ("kannada", "kn", "ಸರಿ, ಈಗ ನಾನು ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸುತ್ತೇನೆ."),
                              ("english", "en", "Okay, I will reply in English.")):
        if low.strip() == word:
            db.run("UPDATE owners SET lang=? WHERE id=?", (lang, oid))
            return [say(oid, reply + " (Only my most common replies are translated in this prototype.)")]
    if "upgrade" in low:
        plans.set_plan(oid, "plus")
        return [say(oid, "Billbo Plus is on (demo, no payment taken). You now get " +
                    ", ".join(plans.PLUS_FEATURES) + ".", "Plans")]
    if "downgrade" in low or "free plan" in low:
        plans.set_plan(oid, "free")
        return [say(oid, "You are back on the Free plan: bill capture, registers and due-date reminders.", "Plans")]
    if low.strip() == "plan":
        return [say(oid, "You are on " + ("Billbo Plus." if plans.is_plus(owner) else "the Free plan. ") +
                    ("" if plans.is_plus(owner) else plans.upsell_line()), "Plans")]
    parsed = intake.parse_text(text)
    if parsed:
        return _post_bill(owner, parsed)
    vehicle = find_vehicle(text)
    if vehicle and dispatch.open_draft(oid):
        dispatch.set_vehicle(dispatch.open_draft(oid)["id"], vehicle)
        return [say(oid, t(owner["lang"], "eway_ready", vehicle=vehicle), dispatch.AGENT)]
    amount = find_amount(text)
    if amount and re.search(r"order|going|sold|sale|dispatch|send|ship|deliver", low):
        return _on_dispatch_text(owner, text, amount)
    if re.search(r"credit|itc|safe", low):
        return [_credit_status(owner)]
    if re.search(r"supplier|scorecard", low):
        return [_scorecard(owner)]
    if re.search(r"\bdue\b|deadline|last date|dates", low):
        return [say(oid, returns.deadline_text(), returns.AGENT)]
    if re.search(r"sign|summary|return", low):
        return [say(oid, returns.explain(oid), returns.AGENT)]
    return [say(oid, HELP)]


def _credit_status(owner):
    oid, rec = owner["id"], itc_guard.reconcile(owner["id"])
    if not plans.is_plus(owner):
        extra = (f" I can see {len(rec['issues'])} bill(s) with credit at risk. " if rec["issues"] else " ")
        return say(oid, f"Credit reported by your suppliers so far: {inr(rec['safe'])}.{extra}" +
                   plans.upsell_line(), itc_guard.AGENT)
    lines = [f"Credit safe to claim: {inr(rec['safe'])}", f"Credit at risk: {inr(rec['at_risk'])}"]
    lines += [f"- {i['supplier']} {i['invoice']}: {i['reason']} ({inr(i['at_risk'])})" for i in rec["issues"]]
    if not rec["issues"]:
        lines.append("All your purchase bills match what suppliers reported.")
    return say(oid, "\n".join(lines), itc_guard.AGENT)


def _scorecard(owner):
    oid = owner["id"]
    if not plans.is_plus(owner):
        return say(oid, plans.upsell_line(), itc_guard.AGENT)
    cards = itc_guard.scorecard(oid)
    if not cards:
        return say(oid, "No purchase bills yet, so no scorecard.", itc_guard.AGENT)
    lines = ["Supplier scorecard (bills reported correctly):"]
    lines += [f"- {c['supplier']}: {c['reported_ok']} of {c['invoices']} ({c['score']}%)" for c in cards]
    return say(oid, "\n".join(lines), itc_guard.AGENT)


# ---------- events from the mock portal ----------

def supplier_reported(owner_id, bill_id):
    """A supplier has now reported an invoice on the (mock) portal. Tell the owner the credit is safe."""
    b = db.one("SELECT * FROM bills WHERE id=? AND owner_id=?", (bill_id, owner_id))
    if not b:
        return None
    db.run("DELETE FROM gstr2b WHERE owner_id=? AND gstin=? AND invoice=?", (owner_id, b["party_gstin"], b["invoice"]))
    db.run("INSERT INTO gstr2b(owner_id,gstin,invoice,taxable,gst) VALUES(?,?,?,?,?)",
           (owner_id, b["party_gstin"], b["invoice"], b["taxable"], b["gst"]))
    db.audit(owner_id, "Mock GST portal", "supplier reported invoice", f"{b['party']} {b['invoice']}")
    owner = owner_row(owner_id)
    if plans.is_plus(owner):
        return say(owner_id, t(owner["lang"], "credit_safe", supplier=b["party"], invoice=b["invoice"],
                               amount=inr(b["gst"])), itc_guard.AGENT)
    return None
