"""Helpers for probe policies: their latest price, a ladder toward it, and the standard close rules."""


def their_sheet(st):
    sh = (st["last"].get("term_sheets") or [{}])[0]
    return sh.get("term_sheet_id"), sh.get("terms") or {}


def their_price(st):
    return their_sheet(st)[1].get("unit_price")


def our_last_price(st, key=0):
    if not st["history"]:
        return None
    return st["history"][-1][0]["term_sheets"][key]["terms"]["unit_price"]


def should_close(st, target):
    """Accept a final offer / agreement, or a counter at or under the target."""
    status = st["last"].get("status")
    p = their_price(st)
    if status in ("final_offer", "agreed"):
        return True
    return p is not None and target is not None and p <= target


def ladder(st, anchor, share, cap=None):
    """Our next price: the previous offer plus a share of the gap to their latest counter (anchor in round 1)."""
    prev = our_last_price(st)
    if prev is None:
        return anchor
    p = their_price(st)
    nxt = prev + share * (p - prev)
    if cap is not None:
        nxt = min(nxt, cap)
    return round(nxt, 2)


def msg(subject, body, sheets, refs=None):
    m = {"subject": subject, "body": body, "term_sheets": [{"terms": t} for t in sheets]}
    if refs:
        m["refs"] = refs
    return m


def cost_of(case, terms):
    from arena_kit.cost import total_cost
    return total_cost(case, terms)


def hold_policy(case_id, anchor, our_terms, round1_text, later_text, share=0.3, target=None):
    """Hold our structure every round (no switching to theirs), climb `share` of the gap to their standing price,
    accept at final_offer / agreed (or a standing price at or under `target`)."""

    def move(st):
        r = st["round"]
        if r > 1 and should_close(st, target):
            return {"accept": their_sheet(st)[0]}
        p = ladder(st, anchor, share)
        text = round1_text if r == 1 else later_text
        return msg(f"Part {case_id} - our proposal", text.format(p=p), [{**our_terms, "unit_price": p}])

    return move


def hold_close_policy(case_id, anchor, our_terms, round1_text, later_text, close_text, tick, share=0.3, ask_round=3):
    """hold_policy, then from `ask_round` (or once their price stalls) one sign-today ask at their standing price
    minus one tick on OUR structure; accept whatever stands after that."""
    st_ = {"asked": False, "prices": []}

    def move(st):
        r = st["round"]
        last = st["last"]
        if r > 1:
            st_["prices"].append(their_price(st))
        if st_["asked"] or (r > 1 and last.get("status") in ("agreed", "final_offer")):
            return {"accept": their_sheet(st)[0]}
        if r == 1:
            return msg(f"{case_id} - our proposal", round1_text.format(p=anchor), [{**our_terms, "unit_price": anchor}])
        stalled = len(st_["prices"]) >= 2 and st_["prices"][-1] >= st_["prices"][-2]
        if stalled or r >= ask_round:
            p = round(their_price(st) - tick, 2)
            st_["asked"] = True
            return msg(f"{case_id} - we can sign today", close_text.format(p=p), [{**our_terms, "unit_price": p}])
        p = ladder(st, anchor, share)
        return msg(f"{case_id} - our proposal", later_text.format(p=p), [{**our_terms, "unit_price": p}])

    return move
