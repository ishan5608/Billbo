"""Returns & Deadlines Agent: drafts return summaries and explains them. Drafting only, never filing."""
from .. import db, rules
from ..util import inr
from . import itc_guard

AGENT = "Returns & Deadlines"


def summary(owner_id):
    sales = db.rows("SELECT * FROM bills WHERE owner_id=? AND direction='sale' AND status='posted'", (owner_id,))
    waiting = db.one("SELECT COUNT(*) n FROM bills WHERE owner_id=? AND status='needs_review'", (owner_id,))["n"]
    rec = itc_guard.reconcile(owner_id)
    out_tax = sum(s["gst"] for s in sales)
    return {"period": db.meta("period", ""), "sales_invoices": len(sales),
            "sales_taxable": sum(s["taxable"] for s in sales), "output_tax": out_tax,
            "itc_safe": rec["safe"], "itc_at_risk": rec["at_risk"],
            "net_payable": max(out_tax - rec["safe"], 0), "bills_waiting_review": waiting,
            "ready_for_accountant": waiting == 0}


def explain(owner_id):
    s = summary(owner_id)
    lines = [f"Here is what you will sign for {s['period']} (draft):",
             f"1. You sold goods worth {inr(s['sales_taxable'])} before tax on {s['sales_invoices']} invoice(s) "
             f"and collected {inr(s['output_tax'])} GST.",
             f"2. You can claim {inr(s['itc_safe'])} credit, because suppliers have reported those bills.",
             f"3. So about {inr(s['net_payable'])} GST is payable."]
    if s["itc_at_risk"]:
        lines.append(f"4. {inr(s['itc_at_risk'])} credit cannot be claimed yet, because suppliers have not "
                     "reported it correctly.")
    if s["bills_waiting_review"]:
        lines.append(f"Note: {s['bills_waiting_review']} bill(s) are waiting for your accountant's check "
                     "and are not counted.")
    lines.append("Your accountant will confirm these numbers and file. I do not file anything.")
    return "\n".join(lines)


def deadline_text(today=None):
    fee = rules.value("LATEFEE-3B")
    lines = ["Due dates this month:"]
    for d in rules.deadlines(today):
        when = f"in {d['days_left']} day(s)" if d["days_left"] >= 0 else f"{-d['days_left']} day(s) ago"
        lines.append(f"{d['label']}: {d['title']} ({when})")
    lines.append(f"A late GSTR-3B costs {inr(fee)} a day in late fee, plus interest.")
    return "\n".join(lines)
