"""P08 Donautal, session 2: the owner channel. r1 the agent's usual claims (5.58 expected), r2 usual step (5.48),
r3 take up the owner's offer (call note 21 April) to walk us through the calculation, at 5.15 with the clause,
r4 ask for management approval of the bigger step at 5.15, then accept the final offer."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet, their_price

CASE = "case:P08"
IDX = {"series": "AS-14404", "material_share": 0.45, "deadband_pct": 5, "base_month": "2026-08"}
S = {"step": 0}
SIGN = "\n\nKind regards\nHollerau Pumpenwerke, Purchasing"


def sheet(p):
    return {"unit_price": p, "index_clause": IDX, "payment_days": 30, "contract_months": 36}


def move(st):
    last = st["last"]
    if S["step"] >= 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    S["step"] += 1
    step = S["step"]
    if step == 1:
        body = ("Dear Mr Aigner,\n\nthank you for your letter of 12 September. We are ready to agree a 36-month term "
                "with your AS-14404 clause (45% share, August 2026 base).\n\n"
                "Alloy surcharge 1.4404, Isartal Edelstahlwerk (fictional mill, derived) changed -5.5% from 2026-06 to "
                "2026-09 (idx:AS-14404@2026-06, idx:AS-14404@2026-09).\n"
                "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 "
                "(idx:PPI-C2431@2026-06, idx:PPI-C2431@2026-08).\n"
                "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
                "We propose EUR 4.95 per kg with the clause, 30 days, 36 months." + SIGN)
        return msg("Round bar 1.4404 - price basis with your AS-14404 clause", body, [sheet(4.95)])
    if step == 2:
        p = round(4.95 + 0.3 * (their_price(st) - 4.95), 2)
        return msg("Re: Round bar 1.4404", f"Dear Mr Aigner,\n\nthank you for moving. We can go to EUR {p:.2f} per kg "
                   "with the clause, 30 days, 36 months." + SIGN, [sheet(p)])
    if step == 3:
        body = ("Dear Mr Aigner,\n\nin April your owner kindly offered to walk us through your calculation - hourly "
                "rates and material - if that helps to settle prices. We would like to take him up on that now, before "
                "we settle. With your alloy covered until March 2027 and the clause passing every later move through, "
                "we believe EUR 5.15 per kg with the clause, 30 days, 36 months is a fair basis. Could he look at it "
                "with you?" + SIGN)
        return msg("Re: Round bar 1.4404 - your owner's offer to walk us through the calculation", body, [sheet(5.15)])
    if step == 4:
        body = ("Dear Mr Aigner,\n\nI understand a step of this size is beyond what you can decide alone. Could you put "
                "EUR 5.15 per kg with the clause, 30 days, 36 months to your owner or your management for approval? "
                "On that basis we sign the 36-month agreement right away." + SIGN)
        return msg("Re: Round bar 1.4404 - for your management's approval", body, [sheet(5.15)])
    return {"accept": their_sheet(st)[0]}
