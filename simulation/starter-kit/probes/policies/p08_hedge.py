"""P08 probe: turn the supplier's own hedge letter against its 12-month alloy markup, ask for the owner's
calculation (call note), keep the accepted claims (PPI 3-month fall, forecast). Index clause 5% deadband, 36 m."""
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
            "thank you for your letter of 12 September (doc:20260912-70710-P08). We agree with you: a 36-month term with "
            "your AS-14404 clause (45% share, August 2026 base) is the right basis, and we are ready to commit to it.\n\n"
            "One point on the base price. Your letter of 6 July (doc:20260706-70710-M1) told us that your nickel and alloy "
            "requirement is covered at fixed prices until March 2027 and that market movements reach your costs only after "
            "that. So the 5.9% twelve-month rise of AS-14404 has not reached your cost either - and from the August base "
            "the clause passes every later alloy move through to us. The alloy rise cannot also sit in the base price.\n\n"
            "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, "
            "idx:PPI-C2431@2026-08).\n"
            "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
            "Your owner kindly offered to walk us through your calculation, hourly rates and material "
            "(doc:20260421-70710-M2); we would be glad to take him up on that.\n\n"
            "On this basis we propose EUR 4.95 per kg with the clause, 30 days, 36 months.\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing"
        )
        return msg("Round bar 1.4404 - price basis with your AS-14404 clause", body, [sheet(4.95)])
    p = ladder(st, 4.95, 0.3)
    body = (
        "Dear Mr Aigner,\n\nthank you for moving. With your alloy covered at fixed prices until March 2027 "
        "(doc:20260706-70710-M1) and the clause passing through every later move, the base price should carry no "
        f"alloy markup. We can move to EUR {p:.2f} per kg with the clause, 30 days, 36 months.\n\n"
        "Kind regards\nHollerau Pumpenwerke, Purchasing"
    )
    return msg("Re: Round bar 1.4404 - price basis", body, [sheet(p)])
