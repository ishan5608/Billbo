import re

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$")
VEHICLE_RE = re.compile(r"\b([A-Z]{2})[\s-]?(\d{1,2})[\s-]?([A-Z]{1,3})[\s-]?(\d{4})\b", re.I)


def inr(n):
    """Format a number the Indian way: 123456 -> ₹1,23,456."""
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + "₹" + s


def route_for(owner_gstin, party_gstin):
    """Same first two digits (state code) means movement within the state."""
    return "intra" if owner_gstin[:2] == party_gstin[:2] else "inter"


def find_amount(text):
    """Largest number of 1000 or more mentioned in a message, or None."""
    nums = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", text)]
    nums = [n for n in nums if n >= 1000]
    return max(nums) if nums else None


def find_vehicle(text):
    m = VEHICLE_RE.search(text)
    return "".join(m.groups()).upper() if m else None
