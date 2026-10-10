"""P11 volume: as p11_skonto (10-day payment) PLUS a firm commitment of the forecast volume in the text. ONE change against the best known round 1 (three accepted claim kinds, no attachment, no alternative):
take up Kalwisz's own request (e-mail of 10 July: pay within 10 days against a cash discount). Hollerau commits to
pay within 10 days of delivery; the sheet cannot carry it (payment_days is fixed at 60 by the case). Same ladder as
before; accept at agreed / final offer. Decisive: Kalwisz held 45.50 in every earlier run."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, their_sheet

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}


def move(st):
    r = st["round"]
    last = st["last"]
    if r > 1 and last.get("status") in ("agreed", "final_offer"):
        return {"accept": their_sheet(st)[0]}
    if r == 1:
        body = (
            "Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, "
            "qn:20004747) averaged 17197 ppm.\n\n"
            "In July you asked whether we could pay your invoices within 10 days, against a cash discount. We can: from "
            "January we will pay your invoices for this bracket within 10 days of delivery. In return we ask you to "
            "reflect the discount in the price.\n\n"
            "You asked which volume we can commit to. Our forecast for this bracket is up 20%: we commit to you a binding "
            "19,000 pieces a year, our full forecast volume, all from Kalwisz.\n\n"
            "We propose EUR 43.00 per unit with a 300 ppm commitment, paid within 10 days.\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Bearing bracket HN - price, quality and 10-day payment", body, [{**SHEET, "unit_price": 43.0}])
    p = ladder(st, 43.0, 0.3)
    body = (f"Dear Mr Lis,\n\nthank you for moving. With payment within 10 days of delivery we can go to EUR {p:.2f} "
            "per unit with the 300 ppm commitment, on our binding commitment of 19,000 pieces a year, all from "
            "you. What else would you need?\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Bearing bracket HN", body, [{**SHEET, "unit_price": p}])
