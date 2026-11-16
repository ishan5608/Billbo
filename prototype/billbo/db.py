"""SQLite storage. One file, standard library only."""
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("BILLBO_DB", str(ROOT / "billbo.db"))
_lock = threading.RLock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS accountants(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS owners(id INTEGER PRIMARY KEY, name TEXT, business TEXT, gstin TEXT,
    lang TEXT DEFAULT 'en', plan TEXT DEFAULT 'free', accountant_id INTEGER, pending TEXT);
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, name TEXT, alias TEXT, gstin TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, owner_id INTEGER, sender TEXT, kind TEXT,
    text TEXT, agent TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY, owner_id INTEGER, direction TEXT, party TEXT,
    party_gstin TEXT, invoice TEXT, date TEXT, taxable REAL, gst REAL, route TEXT, status TEXT,
    confidence REAL, problems TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS gstr2b(id INTEGER PRIMARY KEY, owner_id INTEGER, gstin TEXT, invoice TEXT,
    taxable REAL, gst REAL);
CREATE TABLE IF NOT EXISTS drafts(id INTEGER PRIMARY KEY, owner_id INTEGER, kind TEXT, payload TEXT,
    status TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL, owner_id INTEGER, agent TEXT,
    action TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS filings(id INTEGER PRIMARY KEY, owner_id INTEGER, period TEXT,
    return_type TEXT, filed_by TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
    return _conn


def close():
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None


def rows(sql, args=()):
    with _lock:
        return [dict(r) for r in conn().execute(sql, args).fetchall()]


def one(sql, args=()):
    r = rows(sql, args)
    return r[0] if r else None


def run(sql, args=()):
    with _lock:
        cur = conn().execute(sql, args)
        conn().commit()
        return cur.lastrowid


def now():
    return time.time()


def audit(owner_id, agent, action, detail=""):
    run("INSERT INTO audit(ts,owner_id,agent,action,detail) VALUES(?,?,?,?,?)",
        (now(), owner_id, agent, action, detail))


def get_pending(owner_id):
    r = one("SELECT pending FROM owners WHERE id=?", (owner_id,))
    return json.loads(r["pending"]) if r and r["pending"] else None


def set_pending(owner_id, state):
    run("UPDATE owners SET pending=? WHERE id=?", (json.dumps(state) if state else None, owner_id))


def meta(key, default=None):
    r = one("SELECT value FROM meta WHERE key=?", (key,))
    return r["value"] if r else default


def reset():
    """Drop everything and load the demo seed data."""
    with _lock:
        c = conn()
        for t in ("accountants", "owners", "customers", "messages", "bills", "gstr2b", "drafts",
                  "audit", "filings", "meta"):
            c.execute(f"DELETE FROM {t}")
        c.commit()
    seed = json.loads((ROOT / "data" / "seed.json").read_text(encoding="utf-8"))
    run("INSERT INTO meta(key,value) VALUES('period',?)", (seed["period"],))
    acc = run("INSERT INTO accountants(name) VALUES(?)", (seed["accountant"]["name"],))
    for c_ in seed["customers"]:
        run("INSERT INTO customers(name,alias,gstin) VALUES(?,?,?)", (c_["name"], c_["alias"], c_["gstin"]))
    first = None
    for o in seed["owners"]:
        oid = run("INSERT INTO owners(name,business,gstin,lang,plan,accountant_id) VALUES(?,?,?,?,?,?)",
                  (o["name"], o["business"], o["gstin"], o["lang"], o["plan"], acc))
        first = first or oid
        run("INSERT INTO messages(owner_id,sender,kind,text,agent,ts) VALUES(?,?,?,?,?,?)",
            (oid, "billbo", "text",
             f"Namaskara {o['name']}! I am Billbo. Send me a bill photo or a voice note and I will "
             "keep your GST paperwork ready. I prepare, you or your accountant file.", "Orchestrator", now()))
    for b in seed["opening_bills"]:
        run("INSERT INTO bills(owner_id,direction,party,party_gstin,invoice,date,taxable,gst,route,status,"
            "confidence,problems,ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (first, b["direction"], b["party"], b["party_gstin"], b["invoice"], b["date"], b["taxable"],
             b["gst"], "intra", "posted", 0.99, "[]", now()))
    for o in rows("SELECT id FROM owners"):
        for g in seed["gstr2b"]:
            run("INSERT INTO gstr2b(owner_id,gstin,invoice,taxable,gst) VALUES(?,?,?,?,?)",
                (o["id"], g["gstin"], g["invoice"], g["taxable"], g["gst"]))
    audit(None, "System", "reset", "demo data loaded")
