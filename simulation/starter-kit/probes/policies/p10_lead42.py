"""P10: the supplier gives its final offer in round 1 and always picks the 56-day sheet (EUR 33.6k of lateness
for us, = EUR 0.72 a unit). Offer only the 42-day sheet; same claims as the agent (should-cost accepted, forecast).
Break-even vs today's 31.70/56 d: a 42-day price up to 32.41."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, their_sheet

CASE = "case:P10"


def move(st):
    if st["round"] > 1:
        return {"accept": their_sheet(st)[0]}
    body = ("Dear Monika,\n\nI understand that very high capacity utilisation means you must prioritise customers with "
            "firm, long-term commitments.\n\n"
            "Our bottom-up estimate of your unit cost for part:340010 is EUR 24.31 (cost:340010), before any margin.\n"
            "Our volume forecast for part:340010 changed by +10.1% (fc:340010@2026-09). We make our full requirement a "
            "firm annual commitment: 23,400 pcs a year for 36 months.\n\n"
            "Our production plan needs a 42-day lead time. On that basis we can confirm EUR 27.37 per unit, 42-day lead "
            "time, 23,400 pcs a year, 36 months.\n\nBest regards,\nHollerau Pumpenwerke, Purchasing")
    return msg("Mechanical seal 24 mm - firm 36-month commitment", body,
               [{"unit_price": 27.37, "volume_per_year": 23400, "contract_months": 36, "lead_time_days": 42}])
