"""P02: round-1 sheets that the C model (fitted to the arena's relationship charge) scores far higher than the
358.20/45 d/index sheet Nordmark always agrees to: no index at 363.5/60 d and 365.5/90 d, index at 361.5/90 d."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, their_price, our_last_price

CASE = "case:P02"
IDX = {"series": "CU-NOTATION", "material_share": 0.2, "deadband_pct": 5, "base_month": "2026-08"}


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = ("Dear Ms Lechner,\n\nthank you for your letter of 14 September. We understand the copper pressure and "
                "want a basis that is sustainable for you.\n\n"
                "Our volume forecast for part:350011 changed by +11.9% (fc:350011@2026-09).\n\n"
                "We can offer: A) EUR 363.50 per unit, 60 days, fixed price without a clause; B) EUR 365.50, 90 days, "
                "fixed price; C) EUR 361.50, 90 days, with your CU-NOTATION clause (20% share, 5% deadband).\n\n"
                "Kind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Motor IE3 7.5 kW - your letter of 14 September", body, [
            {"unit_price": 363.5, "payment_days": 60, "index_clause": None},
            {"unit_price": 365.5, "payment_days": 90, "index_clause": None},
            {"unit_price": 361.5, "payment_days": 90, "index_clause": IDX}])
    prev = our_last_price(st)
    p = round(prev + 0.3 * (their_price(st) - prev), 2)
    body = (f"Dear Ms Lechner,\n\nthank you. We can move to EUR {p:.2f}, 60 days, fixed price; or keep EUR 361.50, "
            "90 days with your clause.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Motor IE3 7.5 kW", body, [{"unit_price": p, "payment_days": 60, "index_clause": None},
                                             {"unit_price": 361.5, "payment_days": 90, "index_clause": IDX}])
