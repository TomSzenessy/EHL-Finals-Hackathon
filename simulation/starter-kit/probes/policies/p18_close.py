"""P18: hold no-index / 36 m / 60 d every round, the three accepted round-1 claims, volume framing."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import hold_close_policy

CASE = "case:P18"
R1 = ("Dear Mr Seidl,\n\nthank you for your letter of 22 September. We want to settle the price basis for the next "
      "36 months on a fixed price, without a surcharge clause, so both sides can plan.\n\n"
      "Alloy surcharge 1.4404 changed -5.5% from 2026-06 to 2026-09 (idx:AS-14404@2026-06, idx:AS-14404@2026-09).\n"
      "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, idx:PPI-C2431@2026-08).\n"
      "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
      "We commit 23,700 kg a year for 36 months at EUR {p:.2f} per kg, fixed, 60 days.\n\n"
      "Kind regards\nHollerau Pumpenwerke, Purchasing")
LATER = ("Dear Mr Seidl,\n\nthank you. We commit 23,700 kg a year, binding for 36 months. We prefer a fixed price over a "
         "surcharge clause and can move to EUR {p:.2f} per kg, fixed, 60 days, 36 months.\n\n"
         "Kind regards\nHollerau Pumpenwerke, Purchasing")
CLOSE = ("Dear Sir,\n\nwe are very close. If you can do EUR {p:.2f} per kg, fixed price without a clause, 60 days, 36 months, we sign today and place the first call-off this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
move = hold_close_policy(CASE, 4.85, {"index_clause": None, "payment_days": 60, "contract_months": 36}, R1, LATER, CLOSE, 0.1 if CASE == 'case:P18' else 0.05)
