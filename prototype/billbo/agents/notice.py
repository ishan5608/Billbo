"""Notice Helper Agent: explains a notice in plain language and prepares a checklist for the accountant."""
import json

from .. import db, rules

AGENT = "Notice Helper"


def handle(owner, form, plus):
    info = rules.notice(form)
    if not info:
        db.audit(owner["id"], AGENT, "unknown notice sent to accountant", form)
        return ("I could not recognise this notice. I have sent the photo to your accountant. "
                "Please call him today.")
    payload = {"form": form, "title": info["title"], "reply_days": info["reply_days"], "papers": info["papers"]}
    db.run("INSERT INTO drafts(owner_id,kind,payload,status,ts) VALUES(?,?,?,?,?)",
           (owner["id"], "notice_pack", json.dumps(payload), "sent_to_accountant", db.now()))
    db.audit(owner["id"], AGENT, "notice checklist sent to accountant", form)
    head = (f"This is a GST notice, form {form}. It normally needs a reply within {info['reply_days']} days, "
            "so please do not ignore it. I have alerted your accountant.")
    if not plus:
        return head
    papers = "\n".join(f"- {p}" for p in info["papers"])
    return (f"{head}\n\nWhat it means: {info['meaning']}\nWhat to do: {info['what_to_do']}\n"
            f"Papers your accountant will need:\n{papers}\n\nI have not replied to the notice. "
            "Your accountant will.")
