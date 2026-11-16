"""ITC Guard Agent: matches the purchase register against what suppliers reported (mock GSTR-2B)."""
from .. import db

AGENT = "ITC Guard"


def reconcile(owner_id):
    """Return credit that is safe to claim, credit at risk, and the invoices causing the risk."""
    filed = {(r["gstin"], r["invoice"]): r for r in
             db.rows("SELECT * FROM gstr2b WHERE owner_id=?", (owner_id,))}
    safe, issues = 0, []
    for p in db.rows("SELECT * FROM bills WHERE owner_id=? AND direction='purchase' AND status='posted' "
                     "ORDER BY id", (owner_id,)):
        match = filed.get((p["party_gstin"], p["invoice"]))
        if match is None:
            issues.append({"bill_id": p["id"], "supplier": p["party"], "gstin": p["party_gstin"],
                           "invoice": p["invoice"], "at_risk": p["gst"],
                           "reason": "supplier has not reported this invoice"})
        elif abs(match["gst"] - p["gst"]) > 1:
            safe += min(p["gst"], match["gst"])
            issues.append({"bill_id": p["id"], "supplier": p["party"], "gstin": p["party_gstin"],
                           "invoice": p["invoice"], "at_risk": max(p["gst"] - match["gst"], 0),
                           "reason": f"supplier reported GST {int(match['gst'])}, the bill says {int(p['gst'])}"})
        else:
            safe += p["gst"]
    return {"safe": safe, "at_risk": sum(i["at_risk"] for i in issues), "issues": issues}


def scorecard(owner_id):
    """Per supplier: how many of the owner's invoices they reported correctly."""
    risk = {i["bill_id"]: i["at_risk"] for i in reconcile(owner_id)["issues"]}
    out = {}
    for p in db.rows("SELECT * FROM bills WHERE owner_id=? AND direction='purchase' AND status='posted'",
                     (owner_id,)):
        s = out.setdefault(p["party_gstin"], {"supplier": p["party"], "gstin": p["party_gstin"],
                                              "invoices": 0, "reported_ok": 0, "at_risk": 0})
        s["invoices"] += 1
        if p["id"] in risk:
            s["at_risk"] += risk[p["id"]]
        else:
            s["reported_ok"] += 1
    for s in out.values():
        s["score"] = round(100 * s["reported_ok"] / s["invoices"])
    return sorted(out.values(), key=lambda s: s["score"])


def supplier_issues(owner_id, gstin):
    return [i for i in reconcile(owner_id)["issues"] if i["gstin"] == gstin]


def reminder_text(owner, issues):
    invoices = ", ".join(i["invoice"] for i in issues)
    return (f"Namaskara, this is {owner['name']} from {owner['business']} (GSTIN {owner['gstin']}). "
            f"Our records show invoice(s) {invoices} are not correctly reported in your GSTR-1, so we "
            "cannot claim input credit. Please report or correct them before your next filing. Thank you.")
