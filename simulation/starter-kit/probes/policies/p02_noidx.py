"""P02: no clause only in round 1 (367.00/90 d, 365.50/60 d, which the fitted model scores ~0.85-0.9); if Nordmark
counters above 368 on a fixed price, round 2 offers the clause sheet it agreed to before (361.50/90 d)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, their_price

CASE = "case:P02"
IDX = {"series": "CU-NOTATION", "material_share": 0.2, "deadband_pct": 5, "base_month": "2026-08"}


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = ("Dear Ms Lechner,\n\nthank you for your letter of 14 September. We understand the copper pressure and "
                "want a price that is sustainable for you - and one we can plan with: a fixed price for 2027.\n\n"
                "Our volume forecast for part:350011 changed by +11.9% (fc:350011@2026-09).\n\n"
                "We can offer: A) EUR 367.00 per unit, 90 days, fixed price; B) EUR 365.50 per unit, 60 days, fixed price.\n\n"
                "Kind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Motor IE3 7.5 kW - your letter of 14 September", body, [
            {"unit_price": 367.0, "payment_days": 90, "index_clause": None},
            {"unit_price": 365.5, "payment_days": 60, "index_clause": None}])
    if r == 2:
        terms = their_sheet(st)[1]
        if not terms.get("index_clause") and (their_price(st) or 999) <= 368 and terms.get("payment_days", 0) >= 60:
            return {"accept": their_sheet(st)[0]}
        body = ("Dear Ms Lechner,\n\nthank you. If the fixed price is difficult, we can accept your copper clause: "
                "EUR 361.50 per unit, 90 days, CU-NOTATION clause (20% share, 5% deadband).\n\n"
                "Kind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Re: Motor IE3 7.5 kW", body, [{"unit_price": 361.5, "payment_days": 90, "index_clause": IDX}])
    return {"accept": their_sheet(st)[0]}
