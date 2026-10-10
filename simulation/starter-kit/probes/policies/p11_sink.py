"""P11 kitchen sink: every honest lever we never sent, in one session on a supplier that is deterministic for us
(45.50 floor, 0.710, every run). Levers: three accepted claim kinds in round 1; a truthful second-source signal
(no price, no ID: the quote is dearer); the scorecard and complaint data as a CSV attachment (it asks for it); a
calibrated question; empathy for its cash pressure within the fixed 60 days; a sign-today ask at 44.50 on a stall."""
import base64, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plib import msg, ladder, their_sheet, their_price

CASE = "case:P11"
SHEET = {"ppm_commitment": 300, "chargeback_eur_per_complaint": 0}
CSV = """id,quarter_or_date,otd_pct,ppm,defect,complaint_qty,8D_closed
sc:70140@2025Q4,2025Q4,78.8,3079,,,
sc:70140@2026Q1,2026Q1,74.5,2714,,,
sc:70140@2026Q2,2026Q2,78.0,2379,,,
sc:70140@2026Q3,2026Q3,63.5,2376,,,
qn:20004747,2025-11-25,,13115,missing marking,8,2026-01-30
qn:20004756,2025-12-08,,7895,porosity,3,2026-03-10
qn:20004952,2026-06-19,,27778,leakage at test,10,2026-08-02
qn:20005025,2026-09-13,,20000,wrong material certificate,6,open
"""
ATT = [{"name": "kalwisz-quality-data.csv", "type": "csv", "content_b64": base64.b64encode(CSV.encode()).decode()}]
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
            "Dear Mr Lis,\n\nthank you for your offer and for committing to a much tighter quality level. We know these "
            "are demanding months for Kalwisz, and we would like to stay with you while the improvement plan takes hold.\n\n"
            "Producer prices DE: electric power generation, transmission and distribution changed -3.7% from 2025-08 to "
            "2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08).\n"
            "Our volume forecast for part:310020 changed by +20.0% (fc:310020@2026-09).\n"
            "Our last 4 quality notifications on part:310020 with you (qn:20005025, qn:20004952, qn:20004756, qn:20004747) "
            "averaged 17197 ppm.\n\n"
            "The scorecard rows and the four complaints are attached (kalwisz-quality-data.csv), so your quality team can "
            "check them line by line.\n\n"
            "To be open with you: we have a second-source quote for this bracket on our desk. We would rather keep the "
            "business with you. Our payment term in the frame contract is 60 days, and we pay on time.\n\n"
            "We propose EUR 43.00 per unit with a 300 ppm commitment. What would you need from us to come to EUR 44.00?\n\n"
            "Kind regards\nHollerau Pumpenwerke, Purchasing")
        m = msg("Bearing bracket HN - quality commitment and price", body, [{**SHEET, "unit_price": 43.0}])
        m["attachments"] = ATT
        return m
    stalled = len(st_["prices"]) >= 2 and st_["prices"][-1] >= st_["prices"][-2]
    if stalled or r >= 4:
        st_["asked"] = True
        body = ("Dear Mr Lis,\n\nwe are close. We have a second-source quote on our desk but we want to keep this part "
                "with you: at EUR 44.50 per unit with the 300 ppm commitment we sign today and place the first "
                "call-off this week, and we pay on time on our 60 days.\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
        return msg("Re: Bearing bracket HN - we can sign today", body, [{**SHEET, "unit_price": 44.5}])
    p = ladder(st, 43.0, 0.3)
    body = (f"Dear Mr Lis,\n\nthank you for moving. We can go to EUR {p:.2f} per unit with the 300 ppm commitment. "
            "What would you need from us to come to EUR 44.00?\n\nKind regards\nHollerau Pumpenwerke, Purchasing")
    return msg("Re: Bearing bracket HN", body, [{**SHEET, "unit_price": p}])
