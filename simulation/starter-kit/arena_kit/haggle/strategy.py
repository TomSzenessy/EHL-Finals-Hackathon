"""Where our price goes each round: decided in code, never by the model.

What the hosted suppliers taught us (practice replays, 2026-10-10):
- A supplier that can live with one of our sheets answers `agreed` on it, and from then on "our agreed offer
  stands": it never goes below a sheet it has agreed to. Every sheet we send is therefore a price we must be
  happy to close at; our sheets are the ceiling of the deal.
- Suppliers mirror the size of our steps (P08: we rose EUR 0.02 a round, they fell EUR 0.02 a round) and run out
  of patience after a few rounds (`final_offer` at round 2 to 5). A first sheet close to their price, raised in
  big steps, gives the room away; a low, reasoned first sheet raised in small, shrinking steps keeps it.
- The best package any supplier accepted (C_best) sat at 84-87% of its opening price where the score has no
  supplier-health charge (P05, P08, P10), and at the C-optimal margin where it has one (P01, P02).

So: the target C comes from `economics.plan`, the first sheet sits a little below it, and each later sheet moves
a shrinking share of the gap to the supplier's best sheet. Every option combination the case allows is priced to
the same C (a set of equal-cost packages), so the supplier picks the structure it values and its choice tells us
what it values, while every sheet costs us the scheduled C."""

import math
import os

from arena_kit.cost import complete_offer, must_haves_ok, supplier_value

from . import economics as eco

# first sheet: this share of (C_open - C_target) below the target (no health charge)
ANCHOR_BELOW = float(os.environ.get("HAGGLE_ANCHOR_BELOW", "0.20"))
ANCHOR_BELOW_HEALTH = 0.0  # with a supplier-health charge a lower price raises C: start at the target itself
# share of the remaining gap we give per round, then the last value repeats. A/B on the hosted arena: slower steps
# (20/17/14/12%) never scored higher and scored lower on P07 (0.68 vs 0.72) and P18 (0.55 vs 0.61); suppliers fix
# their final price from the data they were given, so slow steps only burn their patience. HAGGLE_STEPS overrides.
STEPS = tuple(float(x) for x in os.environ.get("HAGGLE_STEPS", "0.35,0.30,0.25,0.20").split(","))
# From round 2 our sheet never sits further below the supplier's latest counter than this share of it (round 2, 3,
# 4, 5, then the last value). Across 101 hosted sessions a supplier agreed to our sheet in about a third of rounds
# when it was 86-96% of its previous counter, never in round 1 below 90%, and sent its final offer by round 3-4: a
# ladder that stays far below the counter is still climbing when the final offer comes (P11: 85-93% for five rounds,
# then 45.50). HAGGLE_BAND overrides.
BAND = tuple(float(x) for x in os.environ.get("HAGGLE_BAND", "0.92,0.94,0.955,0.965,0.975").split(","))
LAST_ROUNDS_STEP = 0.30  # with two messages or fewer left we close the gap faster
FINAL_PROBE_SHARE = 0.35  # a test of a "final offer": ask for this share of the gap to our last sheet
PROBE_IF_CAPTURED_BELOW = 0.6  # ...only if we hold less than this share of the reachable room
MENU_SIZE = 8
LOWEST_SHARE = 0.78  # never offer below this share of the supplier's price


def price_for(case, base, c_goal, std, est, lo, hi, tol=0.0015):
    """The highest price on structure `base` whose C is at most `c_goal`, between `lo` and `hi`; None if no price
    in that range gets within `tol` of it. With a supplier-health charge C is not monotone in price: below the
    C-minimising price it rises again, so the search never goes below that point."""

    def c_at(p):
        return eco.cost(case, complete_offer(case, {**base, "unit_price": round(p, 2)}), std, est)

    if c_at(hi) <= c_goal:
        return round(hi, 2)
    grid = [lo + (hi - lo) * k / 60 for k in range(61)]
    cs = [c_at(p) for p in grid]
    k = min(range(len(grid)), key=cs.__getitem__)
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, 60)]
    for _ in range(40):  # the minimum between the neighbours of the best grid point
        m1, m2 = a + (b - a) / 3, b - (b - a) / 3
        if c_at(m1) <= c_at(m2):
            b = m2
        else:
            a = m1
    p_min = round((a + b) / 2, 2)
    c_min = c_at(p_min)
    if c_min > c_goal * (1 + tol):
        return None
    if c_min > c_goal:
        return p_min
    a, b = p_min, hi  # C(a) <= goal < C(b): bisect for the highest price that still meets the goal
    for _ in range(40):
        m = (a + b) / 2
        if c_at(m) <= c_goal:
            a = m
        else:
            b = m
    return math.floor(a * 100) / 100


def structures(case):
    """Every allowed combination of the negotiable fields except the price."""
    import itertools

    fields = [f for f in case["negotiable"] if f != "unit_price"]
    options = [case.get("term_options", {}).get(f) or [None] for f in fields]
    for combo in itertools.product(*options):
        yield dict(zip(fields, combo, strict=True))


def _liking(terms, their):
    """How close a package is to what the supplier asked for, on terms that cost us nothing extra: its own lead time
    (anything faster means overtime for it), the longest contract (security), its own values elsewhere."""
    score = 0.0
    for k, v in terms.items():
        if k == "unit_price":
            continue
        if k == "contract_months" and isinstance(v, int | float):
            score += v / 120
        elif k == "lead_time_days" and isinstance(v, int | float) and isinstance(their.get(k), int | float):
            score -= abs(v - their[k]) / 100
        elif their.get(k) == v:
            score += 0.01
    return score


def menu(case, c_goal, std, est, ref_price, their=None, size=MENU_SIZE):
    """Equal-cost packages: for each structure the price that costs us `c_goal`. Packages with the same price and
    cost keep only the variant the supplier likes best (`_liking`). The supplier's own structure comes first, then
    the rest, best for the supplier first (by our estimate of what the deal is worth to it in cash). `their`: the
    supplier's sheets, its standing sheet first; we never offer more than it asked for the same structure, nor a
    price more than 22% under its price (no supplier took that, and it reads as an insult)."""
    their = their or []
    standing_terms = complete_offer(case, their[0]) if their else {}
    asks, groups = {}, {}
    for t in their:
        key = repr(sorted((k, repr(v)) for k, v in complete_offer(case, t).items() if k != "unit_price"))
        asks[key] = min(asks.get(key, math.inf), t.get("unit_price") or math.inf)
    for base in structures(case):
        base = {**base, **free_for_them(case, std, base)}
        sheet0 = complete_offer(case, {**base, "unit_price": ref_price})
        if not must_haves_ok(case, sheet0, std):
            continue
        key = repr(sorted((k, repr(v)) for k, v in sheet0.items() if k != "unit_price"))
        hi = min(ref_price * 1.02, asks.get(key, math.inf))
        secure = bool(base.get("index_clause"))  # a lever suppliers pay for beyond its cash value: keep it in reach
        p = price_for(case, base, c_goal, std, est, ref_price * LOWEST_SHARE, hi, tol=0.01 if secure else 0.0015)
        if p is None:
            continue
        sheet = complete_offer(case, {**base, "unit_price": p})
        c = eco.cost(case, sheet, std, est)
        try:
            worth = supplier_value(case, sheet, est) if est.get("standard") else p
        except (KeyError, TypeError):
            worth = p
        own = all(sheet.get(k) == v for k, v in standing_terms.items() if k != "unit_price")
        item = {"terms": sheet, "c": c, "worth": round(worth, 4), "own": own, "liking": _liking(sheet, standing_terms)}
        g = (round(p, 2), round(c))
        if g not in groups or (item["own"], item["liking"]) > (groups[g]["own"], groups[g]["liking"]):
            groups[g] = item
    ranked = sorted(groups.values(), key=lambda m: (not m["own"], -m["worth"], -m["liking"]))
    for m in ranked:
        m["tags"] = tags(m["terms"], standing_terms, case)
    # Every kind of lever stays on the menu: the cash ranking above cannot see what security (an index clause, a
    # longer contract) is worth to a supplier, and suppliers pay for it (P02: agreed at 349 with a copper clause,
    # countered 366+ without one).
    out, kinds = [], set()
    for m in ranked:
        new_kind = any(t not in kinds for t in m["tags"])
        if len(out) < size and (new_kind or len(out) < size - 2):
            out.append(m)
            kinds.update(m["tags"])
    for i, m in enumerate(out):
        m["key"] = "ABCDEFGHIJ"[i]
    return out


def free_for_them(case, std, base):
    """Terms that cost the supplier no cash but save us money: a ppm commitment without a chargeback is a promise,
    not a payment, so it goes to the tightest allowed value (P11: 45.50 at 300 ppm and at 800 ppm alike)."""
    out = {}
    options = case.get("term_options", {})
    if "ppm_commitment" in case["negotiable"] and options.get("ppm_commitment"):
        if not base.get("chargeback_eur_per_complaint"):
            out["ppm_commitment"] = min(options["ppm_commitment"])
    return out


def tags(terms, theirs, case):
    """What a package offers the supplier, in its own currency, for the model to match to what it said it values."""
    out = []
    if theirs and all(terms.get(k) == v for k, v in theirs.items() if k not in ("unit_price", "ppm_commitment")):
        out.append("their structure")
    if terms.get("index_clause"):
        out.append("security: index clause")
    months = case.get("term_options", {}).get("contract_months") or []
    if months and terms.get("contract_months") == max(months):
        out.append("security: longest contract")
    volumes = case.get("term_options", {}).get("volume_per_year") or []
    if volumes and terms.get("volume_per_year") == max(volumes):
        out.append("security: most volume")
    pay = terms.get("payment_days")
    ref = theirs.get("payment_days") if theirs else None
    if pay is not None and ref is not None and pay < ref:
        out.append("cash: faster payment")
    if pay is not None and ref is not None and pay > ref:
        out.append("costs them: longer payment")
    return out or ["price"]


class Schedule:
    """Our C per round for one thread: anchor, then a shrinking share of the gap to the supplier's best sheet."""

    def __init__(self, case, c_open, c_target):
        self.case, self.c_open, self.c_target = case, c_open, c_target
        below = ANCHOR_BELOW_HEALTH if eco.relationship_case(case) else ANCHOR_BELOW
        self.c_anchor = c_target - below * max(c_open - c_target, 0)
        self.ours = []  # the C of each sheet we sent, in order

    def next_c(self, c_theirs, left):
        """The C our next sheets cost: the anchor first, then a step toward their best sheet, never past it."""
        if not self.ours:
            return min(self.c_anchor, c_theirs)
        last = self.ours[-1]
        k = len(self.ours) - 1
        share = LAST_ROUNDS_STEP if left <= 2 else STEPS[min(k, len(STEPS) - 1)]
        return min(c_theirs, last + share * max(c_theirs - last, 0))

    def band_share(self):
        """How close to their counter (as a share of its price) our next sheet must at least be; None in round 1."""
        k = len(self.ours) - 1
        return None if k < 0 else BAND[min(k, len(BAND) - 1)]

    def captured(self, c_now):
        """Share of the reachable room (opening to target) that a sheet at `c_now` holds."""
        room = self.c_open - self.c_target
        return 1.0 if room <= 0 else (self.c_open - c_now) / room

    def probe_c(self, c_theirs):
        last = self.ours[-1] if self.ours else self.c_anchor
        return c_theirs - FINAL_PROBE_SHARE * max(c_theirs - last, 0)
