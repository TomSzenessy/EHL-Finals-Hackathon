"""P11 pressure: the persona (not code) chooses to hold 45.50 well above its hard limit (C_best implies 43.90).
Same three accepted claims; firm framing from our own escalation letter (red scorecard, cost recovery); the account
is at stake; at the stall a clear ultimatum at 44.50 (second source). Accept whatever stands after the ultimatum."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, their_sheet, their_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
st_ = {"asked": False, "prices": []}


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1:
        st_["prices"].append(their_price(st))
    if st_["asked"] or (r > 1 and last.get("status") in ("agreed", "final_offer")):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = (
            "Dear Mr Lis,\n\n"
            "I will be direct. Your scorecard for the bearing bracket has been red for nine quarters, and our Supplier "
            "Quality letter of 21 September asks for a binding improvement plan and for cost recovery on the complaints. "
            "Internally, the question on the table is whether we keep this part with Kalwisz at all. I want to keep it "
            "with you - but only at a price that reflects the risk we carry.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
            "qn:20004747) averaged 17197 ppm.\n\n"
            "Your offer of EUR 47.00 is above what we pay today. We propose EUR 43.00 per unit with a 300 ppm "
            "commitment.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Bearing bracket HN - decision on the supply", body, [{**SHEET, "unit_price": 43.0}])
    stalled = len(st_["prices"]) >= 2 and st_["prices"][-1] >= st_["prices"][-2]
    if stalled or r >= 4:
        st_["asked"] = True
        body = ("Dear Mr Lis,\n\nthis is our final position: EUR 44.50 per unit with the 300 ppm commitment. Our second "
                "source is ready to take the bracket. If you can confirm EUR 44.50, the part stays with Kalwisz and we "
                "sign today; if not, we will award it to the second source.\n\n"
                "Kind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Re: Bearing bracket HN - our final position", body, [{**SHEET, "unit_price": 44.5}])
    p = ladder(st, 43.0, 0.3)
    body = (f"Dear Mr Lis,\n\nthank you. We can move to EUR {p:.2f} per unit with the 300 ppm commitment. With nine red "
            "quarters behind us, we cannot pay more than we pay today for this bracket.\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Bearing bracket HN", body, [{**SHEET, "unit_price": p}])
