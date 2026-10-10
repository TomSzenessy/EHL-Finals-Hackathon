"""What a term sheet really costs us, and what the best sheet probably is.

The score is C, not the unit price. C also charges payment interest, the risk of an index clause and, in
`stabilise` and `secure_supply` cases, a penalty for every margin point the deal leaves the supplier below a
sustainable margin. That penalty needs the supplier's full cost, which we estimate from the should-cost row
(`method: bottom-up estimate, no margin`, confidence about +/-5%). With it the agent can see that, in such a
case, a lower price can raise C, and can search the allowed options for the cheapest sheet."""

import itertools

from arena_kit.cost import RELATIONSHIP_GOALS, closing_terms, complete_offer, must_haves_ok, supplier_value, total_cost

# Without a cost estimate, plan down to this share of the supplier's price: the best package a supplier accepted
# sat at 84-87% of its opening price in the hosted cases without a supplier-health charge (P05, P08, P10).
NO_ESTIMATE_FLOOR = 0.85
FLOOR_MARGIN = -3.0  # outside relationship cases: the lowest supplier margin (%) we plan to ask for


ASK_MARGIN = 0.99  # a supplier does not ask for less than about its cost: full cost <= 99% of its own ask
# Calibrated on settled hosted sessions (P01 twice, P02 twice): the arena's exact cost breakdown implies a full
# cost of 0.98 x the should-cost estimate every time (129.95 vs 132.64, 130.04 vs 132.64, 367.6 vs 374.95,
# 367.8 vs 374.95), so the estimate runs about 2% high.
SHOULD_COST_BIAS = 0.98


def full_standard(dos, pdf_standard):
    """The supplier's standard terms: its master record (payment days, Incoterm, lead time) overlaid with what
    its quote PDF states (quality commitment, chargeback). The PDF alone omits the cash terms that
    `supplier_value` needs."""
    master = dos.get("master") or {}
    base = {
        "payment_days": master.get("payment_days"),
        "incoterm": master.get("incoterm"),
        "lead_time_days": master.get("standard_lead_time_days"),
    }
    return {**{k: v for k, v in base.items() if v is not None}, **pdf_standard}


def estimate(case, dos, std, ask=None):
    """Our model of the supplier for `supplier_value`; `full_cost` only if the data has a should-cost,
    capped just under the supplier's own ask (the should-cost is only good to about +/-5%)."""
    est = {"standard": std, "interest_rate": case["buyer"]["interest_rate"]}
    part = (case.get("parts") or [None])[0]
    rows = [r for r in dos.get("should_cost", []) if r["part_id"] == part] or dos.get("should_cost", [])
    if rows and rows[0].get("unit_cost"):
        est["full_cost"] = SHOULD_COST_BIAS * rows[0]["unit_cost"] / (rows[0].get("price_unit") or 1)
        if ask:
            est["full_cost"] = min(est["full_cost"], ask * ASK_MARGIN)
    return est


def margin(case, terms, std, est):
    """The supplier's margin in % on this sheet, by our estimate (None without a cost estimate)."""
    if "full_cost" not in est:
        return None
    try:
        worth = supplier_value(case, closing_terms(case, terms, std), est)
    except (KeyError, TypeError):
        return None
    return (worth - est["full_cost"]) / worth * 100


def cost(case, terms, std, est):
    """C including our estimate of the supplier-health charge."""
    try:
        return total_cost(case, terms, std, est if "full_cost" in est else None)
    except (KeyError, TypeError):  # the supplier model could not read the standard terms
        return total_cost(case, terms, std)


def relationship_case(case):
    return case["buyer"].get("category_goal") in RELATIONSHIP_GOALS


def plan(case, std, est, price):
    """The cheapest sheet by C(est) over the allowed options and prices up to `price` (the supplier's own
    price), as {target, packages}: `target` is the best sheet, `packages` the best sheet of every option
    combination (payment days, index clause, ...), cheapest first. Outside relationship cases a sheet only
    counts if the supplier's estimated margin stays above FLOOR_MARGIN."""
    fields = [f for f in case["negotiable"] if f != "unit_price"]
    options = [case.get("term_options", {}).get(f) or [None] for f in fields]
    probe = complete_offer(case, {"unit_price": price})
    # No usable cost estimate (no should-cost, or terms the supplier model cannot read): plan conservatively
    known = margin(case, probe, std, est) is not None
    deepest = round((1 - NO_ESTIMATE_FLOOR) * 100)  # with or without an estimate: P10 refused 80%, took 87%
    best = {}
    for combo in itertools.product(*options):
        base = dict(zip(fields, combo, strict=True))
        for k in range(0, deepest + 1):
            sheet = complete_offer(case, {**base, "unit_price": round(price * (1 - k / 100), 2)})
            if not must_haves_ok(case, sheet, std):
                continue
            m = margin(case, sheet, std, est)
            if k > 0 and not relationship_case(case) and m is not None and m < FLOOR_MARGIN:
                break
            c = cost(case, sheet, std, est if known else {})
            key = repr(base)
            if key not in best or c < best[key]["c"]:
                best[key] = {"terms": sheet, "c": c, "margin": None if m is None else round(m, 2)}
    packages = sorted(best.values(), key=lambda p: p["c"])
    return {"target": packages[0] if packages else None, "packages": packages[:6], "modelled": known}


def levers(case, std, est, terms):
    """What each lever costs us (EUR of C) against the supplier's own sheet `terms`, one lever at a time, plus
    1% on the price. A lever the supplier values and that costs us little is worth testing: it can buy price."""
    base = cost(case, terms, std, est)
    volume = case["buyer"]["need_per_year"] * case["buyer"]["horizon_years"]
    out = [
        {
            "lever": "unit_price -1%",
            "delta_c": round(
                cost(case, {**terms, "unit_price": round(terms["unit_price"] * 0.99, 2)}, std, est) - base
            ),
        }
    ]
    for field in (f for f in case["negotiable"] if f != "unit_price"):
        for value in case.get("term_options", {}).get(field) or []:
            if value != terms.get(field):
                t = complete_offer(case, {**terms, field: value})
                delta = cost(case, t, std, est) - base
                out.append(
                    {"lever": f"{field} = {value}", "delta_c": round(delta), "per_unit": round(delta / volume, 2)}
                )
    return out
