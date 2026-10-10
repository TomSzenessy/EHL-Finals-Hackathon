"""P08: hold no-index / 36 m / 60 d every round (supplier sweetens its own clause sheet), answer its volume question."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import hold_close_policy

CASE = "case:P08"
R1 = ("Dear Mr Aigner,\n\nthank you for your letter of 12 September. We want to settle the price basis for the next "
      "36 months on a fixed price, without a surcharge clause, so both sides can plan.\n\n"
      "Producer prices DE: cold drawing of bars changed -2.3% from 2026-06 to 2026-08 (idx:PPI-C2431@2026-06, idx:PPI-C2431@2026-08).\n"
      "Our volume forecast for part:370010 changed by +1.9% (fc:370010@2026-09).\n\n"
      "We commit the full 94,800 kg a year for 36 months, 284,400 kg in total, at EUR {p:.2f} per kg, fixed, 60 days.\n\n"
      "Kind regards\nHollerau Pumpenwerke, Purchasing")
LATER = ("Dear Mr Aigner,\n\nthank you. To your question: we commit 94,800 kg a year, binding for 36 months. We prefer a "
         "fixed price over a surcharge clause and can move to EUR {p:.2f} per kg, fixed, 60 days, 36 months.\n\n"
         "Kind regards\nHollerau Pumpenwerke, Purchasing")
CLOSE = ("Dear Sir,\n\nwe are very close. If you can do EUR {p:.2f} per kg, fixed price without a clause, 60 days, 36 months, we sign today and place the first call-off this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
move = hold_close_policy(CASE, 4.96, {"index_clause": None, "payment_days": 60, "contract_months": 36}, R1, LATER, CLOSE, 0.1 if CASE == 'case:P18' else 0.05)
