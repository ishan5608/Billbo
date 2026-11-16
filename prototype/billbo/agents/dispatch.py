"""Dispatch Agent: prepares e-way bill drafts before goods leave. It never generates the real bill."""
import json

from .. import db, rules

AGENT = "Dispatch"


def needs_eway(value, route):
    limit, card_id = rules.eway_limit(route)
    return value > limit, limit, card_id


def create_draft(owner_id, buyer, buyer_gstin, value, route, invoice=None):
    _, limit, card_id = needs_eway(value, route)
    payload = {"buyer": buyer, "buyer_gstin": buyer_gstin, "value": value, "route": route,
               "invoice": invoice, "vehicle": None, "limit": limit, "rule": card_id}
    draft_id = db.run("INSERT INTO drafts(owner_id,kind,payload,status,ts) VALUES(?,?,?,?,?)",
                      (owner_id, "eway", json.dumps(payload), "needs_vehicle", db.now()))
    db.audit(owner_id, AGENT, "e-way draft prepared", f"{buyer} value {int(value)} rule {card_id}")
    return draft_id


def open_draft(owner_id):
    return db.one("SELECT * FROM drafts WHERE owner_id=? AND kind='eway' AND status='needs_vehicle' "
                  "ORDER BY id DESC", (owner_id,))


def set_vehicle(draft_id, vehicle):
    d = db.one("SELECT * FROM drafts WHERE id=?", (draft_id,))
    payload = json.loads(d["payload"])
    payload["vehicle"] = vehicle
    db.run("UPDATE drafts SET payload=?, status='ready' WHERE id=?", (json.dumps(payload), draft_id))
    db.audit(d["owner_id"], AGENT, "e-way draft completed", f"vehicle {vehicle}")
    return payload
