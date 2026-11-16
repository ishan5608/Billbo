"""The business model in code: Free for owners, Accountant plan per client, Billbo Plus for owners."""
from . import db, rules

PLUS_FEATURES = ("credit alerts", "supplier scorecard", "e-way bill drafts", "notice explanations")


def is_plus(owner):
    return owner["plan"] == "plus"


def set_plan(owner_id, plan):
    assert plan in ("free", "plus")
    db.run("UPDATE owners SET plan=? WHERE id=?", (plan, owner_id))
    db.audit(owner_id, "Plans", "plan changed", plan)


def upsell_line():
    return (f"Billbo Plus ({rules.value('PRICE-PLUS')} rupees a month, target price) adds "
            + ", ".join(PLUS_FEATURES) + ". Type 'upgrade' to switch it on in this demo (no payment).")


def billing(accountant_id):
    """Monthly revenue Billbo would earn from one accountant and his clients, at target prices."""
    owners = db.rows("SELECT plan FROM owners WHERE accountant_id=?", (accountant_id,))
    clients = len(owners)
    plus = sum(1 for o in owners if o["plan"] == "plus")
    pa, pp = rules.value("PRICE-ACCOUNTANT"), rules.value("PRICE-PLUS")
    return {"clients": clients, "plus_clients": plus, "price_accountant": pa, "price_plus": pp,
            "accountant_fee": clients * pa, "plus_revenue": plus * pp, "total": clients * pa + plus * pp}
