"""P11: the agent's round-1 claims; ladder; once their price stops falling (or from round 4), offer exactly one tick
(EUR 0.50) under their standing price with a sign-today close. Accept whatever comes back after that."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, their_sheet, their_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
state = {"asked": False, "prices": []}


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1:
        state["prices"].append(their_price(st))
    if state["asked"] or (r > 1 and last.get("status") in ("agreed", "final_offer")):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = ("Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level.\n\n"
                "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 "
                "to 2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
                "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
                "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
                "qn:20004747) averaged 17197 ppm.\n\n"
                "We propose EUR {p:.2f} per unit with a 300 ppm commitment.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Bearing bracket HN - quality commitment and price", body.format(p=38.5), [{**SHEET, "unit_price": 38.5}])
    stalled = len(state["prices"]) >= 2 and state["prices"][-1] >= state["prices"][-2]
    if stalled or r >= 4:
        p = round(their_price(st) - 0.5, 2)
        state["asked"] = True
        body = (f"Dear Mr Lis,\n\nwe are very close. If you can do EUR {p:.2f} per unit with the 300 ppm commitment, "
                "we sign today and place the first call-off this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Re: Bearing bracket HN - we can sign today", body, [{**SHEET, "unit_price": p}])
    p = ladder(st, 38.5, 0.3)
    body = (f"Dear Mr Lis,\n\nthank you for moving. We can go to EUR {p:.2f} per unit with the 300 ppm commitment.\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Bearing bracket HN", body, [{**SHEET, "unit_price": p}])
