"""Rule engine. Every rate, limit, due date and price comes from rule cards, never from an AI model."""
import json
from datetime import date
from pathlib import Path

CARDS_PATH = Path(__file__).resolve().parent.parent.parent / "rules" / "rule_cards.json"
_cache = {"mtime": None, "data": None}


def _load():
    m = CARDS_PATH.stat().st_mtime
    if _cache["mtime"] != m:
        _cache["data"] = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
        _cache["mtime"] = m
    return _cache["data"]


def card(card_id):
    for c in _load()["cards"]:
        if c["id"] == card_id:
            return c
    raise KeyError(card_id)


def value(card_id):
    return card(card_id)["value"]


def all_cards():
    return _load()["cards"]


def notice(form):
    return _load().get("notices", {}).get(form)


def eway_limit(route):
    """Return (limit, card id) for 'inter' or 'intra' state movement."""
    cid = "EWB-INTER" if route == "inter" else "EWB-INTRA-KA"
    return value(cid), cid


def deadlines(today=None):
    """This month's due dates for last month's period: list of dicts sorted by date."""
    today = today or date.today()
    out = []
    for cid in ("DUE-TDS", "DUE-GSTR1", "GEN-GSTR2B", "DUE-GSTR3B"):
        c = card(cid)
        due = date(today.year, today.month, c["value"])
        out.append({"id": cid, "title": c["title"], "date": due.isoformat(),
                    "label": due.strftime("%d %b"), "days_left": (due - today).days})
    return out


def rate_ok(taxable, gst):
    """True if gst/taxable matches a rate on the GST-RATES card (within 1 rupee)."""
    if taxable <= 0:
        return False
    return any(abs(taxable * r / 100 - gst) <= 1 for r in value("GST-RATES"))
