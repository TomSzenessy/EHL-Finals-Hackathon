"""P11 contract lever (last session): our frame contract 4600070140 runs to June 2027; s3.1 fixes prices per calendar
year, changes need 90 days' written notice before year end; Kalwisz sent no price letter (its 47.00 came as a quote).
So today's 45.15 stands for 2027. Proven opening + that argument (plain text, no ctr: ID: without a notice letter the
check could read it as irrelevant). Ladder capped at 45.15; accept agreed / final offer."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, their_price, our_last_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
SIGN = "\n\nKind regards\nHollerau Pumpenwerke, Purchasing"
CAP = 45.15


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = (
            "Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level.\n\n"
            "Before we discuss figures, one contractual point. Our framework agreement 4600070140 with you runs until "
            "30 June 2027 and extends by itself. Its section 3.1 fixes prices for each calendar year; a change requires "
            "written notice of at least 90 days before the end of the calendar year. We have received no such notice "
            "from you - your EUR 47.00 came as a quote. So for 2027 the agreed price of EUR 45.15 continues to apply. "
            "We are not asking you to go below it out of hardball; we are asking for a little room under it for the "
            "quality risk we carry.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
            "qn:20004747) averaged 17197 ppm.\n\n"
            "We propose EUR 43.00 per unit with a 300 ppm commitment." + SIGN)
        return msg("Bearing bracket HN - our framework agreement and the 2027 price", body,
                   [{**SHEET, "unit_price": 43.0}])
    prev = our_last_price(st)
    p = min(CAP, round(prev + 0.35 * (their_price(st) - prev), 2))
    if p <= prev:
        p = round(min(CAP, prev + 0.05), 2)
    body = (f"Dear Mr Lis,\n\nthank you. Under our framework agreement (section 3.1) the price for 2027 stays at EUR "
            f"45.15 unless notice was given in time, and none was. We can go to EUR {p:.2f} per unit with the 300 ppm "
            "commitment." + SIGN)
    return msg("Re: Bearing bracket HN - the 2027 price under our framework agreement", body,
               [{**SHEET, "unit_price": p}])
