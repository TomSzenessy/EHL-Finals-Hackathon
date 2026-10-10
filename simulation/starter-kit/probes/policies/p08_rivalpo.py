"""P08 probe: the rival's (Werdenfels) lower order prices for the same part as a round-1 claim, plus PPI 3-month
fall and forecast. Same ladder as p08_hedge (anchor 4.95, 30% of the gap) for comparison."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, should_close, their_sheet

CASE = "case:P08"
IDX = {"series": "AS-14404", "material_share": 0.45, "deadband_pct": 5, "base_month": "2026-08"}
TARGET = 5.12


def sheet(p):
    return {"unit_price": p, "index_clause": IDX, "payment_days": 30, "contract_months": 36}


def move(st):
    r = st["round"]
    if r > 1 and should_close(st, TARGET):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = (
            "Dear Mr Aigner,\n\n"
            "thank you for your letter of 12 September. We are ready to agree a 36-month term with your AS-14404 clause "
            "(45% share, August 2026 base).\n\n"
            "We also buy this bar from a second source: our orders of part:370010 (po:4500014022-10, po:4500014078-10) "
            "were placed at EUR 5.26 per kg.\n"
            "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, "
            "idx:PPI-C2431@2026-08).\n"
            "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
            "On this basis we propose EUR 4.95 per kg with the clause, 30 days, 36 months.\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing"
        )
        return msg("Round bar 1.4404 - price basis with your AS-14404 clause", body, [sheet(4.95)])
    p = ladder(st, 4.95, 0.3)
    body = (
        "Dear Mr Aigner,\n\nthank you for moving. Our second source supplies the same bar at EUR 5.26. "
        f"We can move to EUR {p:.2f} per kg with the clause, 30 days, 36 months.\n\n"
        "Kind regards\nHollerau Pumpenwerke, Purchasing"
    )
    return msg("Re: Round bar 1.4404 - price basis", body, [sheet(p)])
