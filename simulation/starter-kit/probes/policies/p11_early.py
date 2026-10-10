"""P11 early agreement: our best round 1 (warm, three accepted claim kinds) with ONE sheet at 44.55, about the price
of NoIdea's 0.885 record. Kalwisz refused every sheet <= 45.00 from round 4 on (five runs), so if it ever agrees
that low, it is early. On a counter: small steps from 44.55 (never above 45.40), accept its final (45.50 = 0.710)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, our_last_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
STEPS = [44.55, 44.70, 44.85, 45.00, 45.15, 45.25, 45.40]


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    p = STEPS[min(r - 1, len(STEPS) - 1)]
    if r == 1:
        body = (
            "Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level. We would like "
            "to keep this bracket with Kalwisz and build on the improvement plan together.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
            "qn:20004747) averaged 17197 ppm.\n\n"
            "We propose EUR 44.55 per unit with a 300 ppm commitment - if you can confirm it, we place the order "
            "this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Bearing bracket HN - quality commitment and price", body, [{**SHEET, "unit_price": p}])
    body = (f"Dear Mr Lis,\n\nthank you. We can move to EUR {p:.2f} per unit with the 300 ppm commitment and place the "
            "order this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Bearing bracket HN", body, [{**SHEET, "unit_price": p}])
