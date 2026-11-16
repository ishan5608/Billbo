"""HTTP server: owner chat, accountant dashboard and mock GST portal. Standard library only."""
import csv
import io
import json
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import db, plans, rules
from .agents import intake, itc_guard, ledger, orchestrator, returns

WEB = Path(__file__).resolve().parent.parent / "web"
PAGES = {"/": "index.html", "/chat": "chat.html", "/dashboard": "dashboard.html", "/portal": "portal.html",
         "/style.css": "style.css", "/common.js": "common.js"}
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}


def drafts_for(owner_id):
    out = db.rows("SELECT * FROM drafts WHERE owner_id=? ORDER BY id DESC", (owner_id,))
    for d in out:
        d["payload"] = json.loads(d["payload"])
    return out


def client_detail(owner_id):
    owner = orchestrator.owner_row(owner_id)
    if not owner:
        return None
    return {"owner": owner, "purchases": ledger.register(owner_id, "purchase"),
            "sales": ledger.register(owner_id, "sale"), "review": ledger.review_queue(owner_id),
            "credit": itc_guard.reconcile(owner_id), "scorecard": itc_guard.scorecard(owner_id),
            "drafts": drafts_for(owner_id), "summary": returns.summary(owner_id),
            "reported": db.rows("SELECT * FROM gstr2b WHERE owner_id=? ORDER BY id", (owner_id,)),
            "filings": db.rows("SELECT * FROM filings WHERE owner_id=? ORDER BY id", (owner_id,)),
            "audit": db.rows("SELECT * FROM audit WHERE owner_id=? ORDER BY id DESC LIMIT 40", (owner_id,))}


def dashboard():
    acc = db.one("SELECT * FROM accountants ORDER BY id LIMIT 1")
    clients = []
    for o in db.rows("SELECT * FROM owners WHERE accountant_id=? ORDER BY id", (acc["id"],)):
        s, rec = returns.summary(o["id"]), itc_guard.reconcile(o["id"])
        n = db.one("SELECT COUNT(*) n FROM bills WHERE owner_id=?", (o["id"],))["n"]
        open_drafts = db.one("SELECT COUNT(*) n FROM drafts WHERE owner_id=? AND status IN "
                             "('needs_vehicle','ready','sent_to_accountant')", (o["id"],))["n"]
        clients.append({"id": o["id"], "name": o["name"], "business": o["business"], "plan": o["plan"],
                        "bills": n, "review": s["bills_waiting_review"], "at_risk": rec["at_risk"],
                        "open_items": open_drafts, "ready": s["ready_for_accountant"] and n > 0})
    return {"accountant": acc, "period": db.meta("period", ""), "clients": clients,
            "billing": plans.billing(acc["id"]), "deadlines": rules.deadlines()}


def pack_csv(owner_id):
    d = client_detail(owner_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([f"Billbo filing-ready pack (DRAFT) for {d['owner']['business']}", d["summary"]["period"]])
    w.writerow(["Prepared by Billbo. Not filed. To be checked and filed by the owner or accountant."])
    for title, key in (("PURCHASE REGISTER", "purchases"), ("SALES REGISTER", "sales")):
        w.writerow([])
        w.writerow([title])
        w.writerow(["Date", "Party", "GSTIN", "Invoice", "Taxable", "GST", "Route", "Status"])
        for b in d[key]:
            w.writerow([b["date"], b["party"], b["party_gstin"], b["invoice"], b["taxable"], b["gst"],
                        b["route"], b["status"]])
    w.writerow([])
    w.writerow(["INPUT CREDIT CHECK"])
    w.writerow(["Safe to claim", d["credit"]["safe"]])
    w.writerow(["At risk", d["credit"]["at_risk"]])
    for i in d["credit"]["issues"]:
        w.writerow([i["supplier"], i["invoice"], i["reason"], i["at_risk"]])
    w.writerow([])
    w.writerow(["DRAFT RETURN SUMMARY"])
    for k, v in d["summary"].items():
        w.writerow([k, v])
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = "Billbo/0.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in PAGES:
                f = WEB / PAGES[u.path]
                return self._send(200, f.read_bytes(), TYPES[f.suffix])
            oid = int(q.get("owner_id", 0) or 0)
            if u.path == "/api/owners":
                return self._json(db.rows("SELECT id,name,business,plan,lang FROM owners ORDER BY id"))
            if u.path == "/api/samples":
                return self._json(intake.samples())
            if u.path == "/api/messages":
                return self._json({"owner": orchestrator.owner_row(oid), "messages": db.rows(
                    "SELECT * FROM messages WHERE owner_id=? AND id>? ORDER BY id", (oid, int(q.get("after", 0))))})
            if u.path == "/api/dashboard":
                return self._json(dashboard())
            if u.path == "/api/client":
                d = client_detail(oid)
                return self._json(d) if d else self._json({"error": "unknown client"}, 404)
            if u.path == "/api/rules":
                return self._json(rules.all_cards())
            if u.path == "/api/pack.csv":
                return self._send(200, pack_csv(oid), "text/csv",
                                  {"Content-Disposition": f'attachment; filename="billbo_pack_{oid}.csv"'})
            self._json({"error": "not found"}, 404)
        except Exception as e:  # keep the demo server alive and show the reason
            self._json({"error": str(e)}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            oid = int(body.get("owner_id", 0) or 0)
            if u.path == "/api/send":
                kind = body.get("kind", "text")
                if kind not in ("text", "voice", "bill", "notice"):
                    return self._json({"error": "bad kind"}, 400)
                return self._json({"replies": orchestrator.handle(oid, kind, str(body.get("text", ""))[:500],
                                                                 body.get("sample_id"))})
            if u.path == "/api/owner":
                if body.get("plan") in ("free", "plus"):
                    plans.set_plan(oid, body["plan"])
                if body.get("lang") in ("en", "hi", "kn"):
                    db.run("UPDATE owners SET lang=? WHERE id=?", (body["lang"], oid))
                return self._json(orchestrator.owner_row(oid))
            if u.path == "/api/review":
                gst = body.get("gst")
                return self._json(ledger.approve(int(body["bill_id"]), float(gst) if gst not in (None, "") else None))
            if u.path == "/api/portal/supplier_report":
                r = orchestrator.supplier_reported(oid, int(body["bill_id"]))
                return self._json({"ok": True, "message": r})
            if u.path == "/api/portal/eway":
                d = db.one("SELECT * FROM drafts WHERE id=? AND kind='eway' AND status='ready'", (int(body["draft_id"]),))
                if not d:
                    return self._json({"error": "draft is not ready"}, 400)
                p = json.loads(d["payload"])
                p["simulated_number"] = "SIM-" + str(random.randint(10**11, 10**12 - 1))
                db.run("UPDATE drafts SET payload=?, status='generated_simulated' WHERE id=?", (json.dumps(p), d["id"]))
                db.audit(d["owner_id"], "Human on mock portal", "e-way bill generated (simulated)", p["simulated_number"])
                return self._json(p)
            if u.path == "/api/portal/file":
                who = str(body.get("filed_by", "")).strip()[:60]
                if not who or body.get("return_type") not in ("GSTR-1", "GSTR-3B"):
                    return self._json({"error": "a person's name and a return type are required"}, 400)
                db.run("INSERT INTO filings(owner_id,period,return_type,filed_by,ts) VALUES(?,?,?,?,?)",
                       (oid, db.meta("period", ""), body["return_type"], who, db.now()))
                db.audit(oid, "Human on mock portal", f"{body['return_type']} filed (simulated)", who)
                return self._json({"ok": True})
            if u.path == "/api/reset":
                db.reset()
                return self._json({"ok": True})
            self._json({"error": "not found"}, 404)
        except Exception as e:
            self._json({"error": str(e)}, 500)


def serve(port=8000, host="127.0.0.1"):
    if not db.one("SELECT id FROM owners LIMIT 1"):
        db.reset()
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Billbo prototype running: http://{host}:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
