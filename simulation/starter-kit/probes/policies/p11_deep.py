"""P11: round-1 claims on the deepest valid index windows (PPI-D351 -17.1%, PPI-C241 -5.0%) plus forecast;
hold 300 ppm / no chargeback; same ladder shape as the agent."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import hold_policy

CASE = "case:P11"
R1 = ("Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level.\n\n"
      "Producer prices DE: electric power generation, transmission and distribution changed -17.1% from 2025-02 to 2026-02 "
      "(idx:PPI-D351@2025-02, idx:PPI-D351@2026-02).\n"
      "Producer prices DE: casting of metals changed -5.0% from 2024-09 to 2025-09 (idx:PPI-C241@2024-09, idx:PPI-C241@2025-09).\n"
      "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n\n"
      "We propose EUR {p:.2f} per unit with a 300 ppm commitment.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
LATER = ("Dear Mr Lis,\n\nthank you for moving. We can go to EUR {p:.2f} per unit with the 300 ppm commitment and "
         "place the order this week.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
move = hold_policy(CASE, 38.5, {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}, R1, LATER, share=0.3)
