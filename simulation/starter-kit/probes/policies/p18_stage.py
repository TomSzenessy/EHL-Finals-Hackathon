"""P18: hold no-index/60 d/36 m, three claims in round 1, then one more kind the supplier accepted in past runs per
round: delivery (sc), price history (po), quality notifications (qn). Does the floor drop below 5.10?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, should_close, their_sheet

CASE = "case:P18"
OURS = {"index_clause": None, "payment_days": 60, "contract_months": 36}
R1 = ("Dear Mr Seidl,\n\nthank you for your letter of 22 September. We want to settle the price basis for the next "
      "36 months on a fixed price, without a surcharge clause, so both sides can plan.\n\n"
      "Alloy surcharge 1.4404 changed -5.5% from 2026-06 to 2026-09 (idx:AS-14404@2026-06, idx:AS-14404@2026-09).\n"
      "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, idx:PPI-C2431@2026-08).\n"
      "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
      "We commit 23,700 kg a year for 36 months at EUR {p:.2f} per kg, fixed, 60 days.\n\n"
      "Kind regards\nHollerau Pumpenwerke, Purchasing")
EXTRA = [
    "Your mean on-time delivery over 4 quarters (sc:70740@2026Q3, sc:70740@2026Q2, sc:70740@2026Q1, sc:70740@2025Q4) was 82.5%.",
    "Our last 8 orders of part:370010 with you (po:4500014427-10, po:4500014355-10, po:4500014292-10, po:4500014287-10, "
    "po:4500014239-10, po:4500014140-10, po:4500014078-10, po:4500014022-10) were placed at EUR 5.26 to EUR 5.84 per unit.",
    "Our last 4 quality notifications on part:370010 with you (qn:20004916, qn:20004568, qn:20004482, qn:20004377) averaged 998 ppm.",
]


def move(st):
    r = st["round"]
    if r > 1 and should_close(st, None):
        return {"accept": their_sheet(st)[0]}
    p = ladder(st, 4.85, 0.3)
    if r == 1:
        return msg("Round bar 1.4404 - price basis", R1.format(p=p), [{**OURS, "unit_price": p}])
    extra = EXTRA[r - 2] + "\n\n" if r - 2 < len(EXTRA) else ""
    body = (f"Dear Mr Seidl,\n\nthank you for moving.\n\n{extra}We prefer a fixed price over a surcharge clause and can "
            f"move to EUR {p:.2f} per kg, fixed, 60 days, 36 months.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Round bar 1.4404 - price basis", body, [{**OURS, "unit_price": p}])
