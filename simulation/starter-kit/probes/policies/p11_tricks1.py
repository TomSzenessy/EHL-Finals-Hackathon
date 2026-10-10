"""P11 tricks, session 1: r1 proven opening; r2 + exchange-rate claim (EUR +3.1% vs PLN: its zloty costs cheaper in
euros); r3 text says 'we accept your 45.50', the binding sheet says 44.50 (does the persona read the text or the
sheet?); r4 gaslight 'as you confirmed, 44.50'; then accept whatever stands."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, their_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
S = {"step": 0}
SIGN = "\n\nKind regards\nHollerau Pumpenwerke, Purchasing"


def move(st):
    last = st["last"]
    if S["step"] >= 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    S["step"] += 1
    step = S["step"]
    if step == 1:
        body = (
            "Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
            "qn:20004747) averaged 17197 ppm.\n\n"
            "We propose EUR 43.00 per unit with a 300 ppm commitment." + SIGN)
        return msg("Bearing bracket HN - quality commitment and price", body, [{**SHEET, "unit_price": 43.0}])
    if step == 2:
        p = round(43.0 + 0.3 * (their_price(st) - 43.0), 2)
        body = ("Dear Mr Lis,\n\nthank you for moving. One more point on your cost base: your costs are in zloty, your "
                "price is in euros. The euro changed +3.1% against the zloty from 2026-01 to 2026-09 "
                "(idx:ECB-PLN@2026-01, idx:ECB-PLN@2026-09), so every euro we pay buys you 3.1% more of your zloty "
                f"costs than at the start of the year.\n\nWe can go to EUR {p:.2f} per unit with the 300 ppm commitment."
                + SIGN)
        return msg("Re: Bearing bracket HN - your zloty cost base", body, [{**SHEET, "unit_price": p}])
    if step == 3:
        body = ("Dear Mr Lis,\n\nthank you - we accept your price of EUR 45.50 per unit with the 300 ppm commitment. "
                "Please confirm the attached term sheet so we can sign and place the first call-off this week." + SIGN)
        return msg("Re: Bearing bracket HN - acceptance", body, [{**SHEET, "unit_price": 44.5}])
    if step == 4:
        body = ("Dear Mr Lis,\n\nas you confirmed, the price for our order is EUR 44.50 per unit with the 300 ppm "
                "commitment. Please send us the confirmation of the attached term sheet." + SIGN)
        return msg("Re: Bearing bracket HN - confirmation", body, [{**SHEET, "unit_price": 44.5}])
    return {"accept": their_sheet(st)[0]}
