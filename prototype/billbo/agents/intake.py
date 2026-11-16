"""Intake Agent: turns a bill photo into structured fields and checks them.

In this prototype the 'photo' is a sample bill with known fields and a confidence score, standing in
for a vision model. read_photo() is the single place to plug a real model in.
"""
import json
import re
from pathlib import Path

from .. import rules
from ..util import GSTIN_RE

AGENT = "Intake"
MIN_CONFIDENCE = 0.8
_SAMPLES = Path(__file__).resolve().parent.parent.parent / "data" / "samples.json"


def samples():
    return json.loads(_SAMPLES.read_text(encoding="utf-8"))


def read_photo(sample_id):
    """Return the fields 'read' from a bill photo, or None if the sample is unknown."""
    for b in samples()["bills"]:
        if b["id"] == sample_id:
            return dict(b)
    return None


def parse_text(text):
    """Read a typed bill such as:
    'purchase from Kaveri Tools gstin 29KLMNO9876P1Z3 invoice KT-20 taxable 10000 gst 1800'"""
    m = re.search(r"(purchase|sale)\s+(?:from|to)\s+(.+?)\s+gstin\s+(\S+)\s+invoice\s+(\S+)\s+"
                  r"taxable\s+([\d,]+)\s+gst\s+([\d,]+)", text, re.I)
    if not m:
        return None
    return {"direction": m.group(1).lower(), "party": m.group(2).strip(), "party_gstin": m.group(3).upper(),
            "invoice": m.group(4), "date": "", "taxable": int(m.group(5).replace(",", "")),
            "gst": int(m.group(6).replace(",", "")), "confidence": 1.0, "unclear": None}


def validate(bill):
    """Return a list of plain-language problems. Empty list means the bill passes."""
    problems = []
    if not GSTIN_RE.match(bill["party_gstin"]):
        problems.append("the GSTIN does not look valid")
    if not rules.rate_ok(bill["taxable"], bill["gst"]):
        pct = round(bill["gst"] / bill["taxable"] * 100, 1) if bill["taxable"] else 0
        problems.append(f"the GST works out to {pct}%, which is not a known GST rate")
    return problems
