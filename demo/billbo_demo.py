"""Billbo demo: the deterministic core, no AI and no network needed.

Shows three things the agents rely on:
  1. ITC Guard    - match the purchase register against supplier filings (GSTR-2B)
  2. Dispatch     - find sales that need an e-way bill before the truck leaves
  3. Deadlines    - upcoming due dates and what a delay would cost

All numbers come from rules/rule_cards.json, never from a language model.
Data is synthetic. Run:  python demo/billbo_demo.py
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def rule(cards, card_id):
    return next(c for c in cards if c["id"] == card_id)


def itc_guard(purchases, gstr2b):
    """Return (safe_credit, issues). An issue is a purchase whose credit is at risk."""
    filed = {(r["gstin"], r["invoice"]): r for r in gstr2b}
    safe, issues = 0, []
    for p in purchases:
        match = filed.get((p["gstin"], p["invoice"]))
        if match is None:
            issues.append({**p, "reason": "supplier has not reported this invoice", "at_risk": p["gst"]})
        elif match["gst"] != p["gst"]:
            gap = p["gst"] - match["gst"]
            safe += min(p["gst"], match["gst"])
            issues.append({**p, "reason": f"supplier reported GST {match['gst']}, bill says {p['gst']}", "at_risk": max(gap, 0)})
        else:
            safe += p["gst"]
    return safe, issues


def eway_needed(sales, cards, state_card="EWB-INTRA-KA"):
    """Return sales above the applicable limit that have no e-way bill yet."""
    limits = {"inter": rule(cards, "EWB-INTER"), "intra": rule(cards, state_card)}
    out = []
    for s in sales:
        card = limits[s["route"]]
        if s["value"] > card["value"] and not s["eway_bill"]:
            out.append({**s, "rule": card["id"], "limit": card["value"]})
    return out


def deadlines(cards, today):
    """Return (title, due_date, days_left) for this month's filings of last month's period."""
    out = []
    for cid in ("DUE-TDS", "DUE-GSTR1", "GEN-GSTR2B", "DUE-GSTR3B"):
        c = rule(cards, cid)
        due = date(today.year, today.month, c["value"])
        out.append((c["title"], due, (due - today).days))
    return out


def main(today=None):
    today = today or date.today()
    cards = load("rules/rule_cards.json")["cards"]
    purchases, gstr2b, sales = (load(f"demo/data/{n}.json") for n in ("purchases", "gstr2b", "sales"))

    print("=== ITC Guard ===")
    safe, issues = itc_guard(purchases, gstr2b)
    print(f"Credit safe to claim : Rs {safe:,}")
    print(f"Credit at risk       : Rs {sum(i['at_risk'] for i in issues):,}")
    for i in issues:
        print(f"  ! {i['supplier']} {i['invoice']}: {i['reason']} (Rs {i['at_risk']:,} at risk)")
        print(f"    Draft to supplier: 'Namaskara, please report invoice {i['invoice']} correctly in your GSTR-1 so we can claim credit.'")

    print("\n=== Dispatch ===")
    for s in eway_needed(sales, cards):
        print(f"  ! {s['invoice']} to {s['buyer']}: Rs {s['value']:,} is above Rs {s['limit']:,} [{s['rule']}]. E-way bill draft prepared, vehicle number needed.")

    print("\n=== Deadlines ===")
    fee = rule(cards, "LATEFEE-3B")["value"]
    for title, due, left in deadlines(cards, today):
        status = f"in {left} days" if left >= 0 else f"{-left} days ago"
        print(f"  {due:%d %b}: {title} ({status})")
    print(f"  Each day of delay on GSTR-3B costs Rs {fee} in late fee, plus interest. [LATEFEE-3B]")

    print("\nBillbo prepares. You or your accountant file.")


if __name__ == "__main__":
    main()
