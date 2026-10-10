# ruff: noqa: E501
"""What the agent knows about a supplier, from the data package alone.

`dossier` is the supplier's record (shown on the Suppliers tab and injected into the model).
`claims` are arguments the arena will check, already worded and computed from facts.json, so the
model only chooses which to use: a figure it writes itself could be wrong, and a wrong one costs trust."""

import json
import re
import threading

DB_LOCK = threading.RLock()  # one sqlite connection is shared by every supplier thread
SUPPLIER_ID = re.compile(r"^sup:\d+$")
SECTIONS = {
    "master": ("SELECT * FROM suppliers WHERE id = ?", 1),
    "intel": ("SELECT * FROM supplier_intel WHERE supplier_id = ?", 1),
    "scorecards": (
        "SELECT id, quarter, otd_pct, otd_confirmed_pct, ppm, qn_count, open_8d_overdue, score, class, colour "
        "FROM scorecards WHERE supplier_id = ? ORDER BY quarter DESC",
        12,
    ),
    "news": ("SELECT id, date, topic, headline, body, source FROM news WHERE supplier_id = ? ORDER BY date DESC", 20),
    "history": (
        "SELECT date, part_id, type, asked_pct, settled_pct, note FROM negotiation_history "
        "WHERE supplier_id = ? ORDER BY date DESC",
        30,
    ),
    "documents": (
        "SELECT id, date, kind, subject, author, asked_pct, asked_price, effective_date, notice_days, file "
        "FROM documents WHERE supplier_id = ? ORDER BY date DESC",
        40,
    ),
    "contracts": (
        "SELECT id, type, valid_from, valid_to, payment_days, incoterm, notice_days, price_basis, file "
        "FROM contracts WHERE supplier_id = ?",
        10,
    ),
    "prices": (
        "SELECT part_id, valid_from, valid_to, price, price_unit, basis FROM price_conditions "
        "WHERE supplier_id = ? ORDER BY valid_from DESC",
        30,
    ),
    "quotes": (
        "SELECT id, part_id, quote_date, unit_price, lead_time_days, payment_days, incoterm, validity_days, "
        "awarded, remarks FROM quotes WHERE supplier_id = ? ORDER BY quote_date DESC",
        20,
    ),
    "should_cost": (
        "SELECT id, part_id, estimate_date, unit_cost, material_eur, conversion_eur, overhead_eur, confidence_pct, "
        "method FROM should_cost WHERE supplier_id = ?",
        10,
    ),
    "sourcing": ("SELECT part_id, status, quota_pct, approved_since FROM sourcing WHERE supplier_id = ?", 10),
    "spend": (
        "SELECT fiscal_year, category, spend_eur FROM spend_cube WHERE supplier_id = ? "
        "ORDER BY fiscal_year DESC, spend_eur DESC",
        10,
    ),
    "quality": (
        "SELECT qn_date, part_id, defect, complaint_qty, supplier_caused, cost_recharged_eur "
        "FROM quality_notifications WHERE supplier_id = ? ORDER BY qn_date DESC",
        15,
    ),
}


def _rows(pkg, sql, *params, limit=50):
    if not (pkg and pkg.db):
        return []
    with DB_LOCK:
        return pkg.query(sql, params, limit=limit)


def dossier(pkg, sup, case=None):
    """The supplier's record. A section is a list of rows (master and intel: one row or null)."""
    if not SUPPLIER_ID.match(sup):
        raise ValueError(f"not a supplier id: {sup}")
    out = {"supplier_id": sup}
    for name, (sql, limit) in SECTIONS.items():
        rows = _rows(pkg, sql, sup, limit=limit)
        out[name] = (rows[0] if rows else None) if limit == 1 else rows
    out["orders"] = (
        _rows(
            pkg,
            "SELECT count(*) AS lines, round(sum(qty * price / price_unit), 0) AS value_eur, "
            "max(order_date) AS last_order FROM po_lines WHERE supplier_id = ?",
            sup,
            limit=1,
        )
        or [None]
    )[0]
    parts = list((case or {}).get("parts", [])) or [r["part_id"] for r in out["prices"][:3]]
    out["parts"] = [r for p in parts for r in _rows(pkg, "SELECT * FROM parts WHERE id = ?", p, limit=1)]
    out["cost_drivers"] = [r for p in parts for r in _rows(pkg, "SELECT * FROM cost_drivers WHERE part_id = ?", p)]
    out["clauses"] = [
        r
        for c in out["contracts"]
        for r in _rows(pkg, "SELECT * FROM contract_clauses WHERE contract_id = ?", c["id"], limit=60)
    ]
    return out


def names(pkg, ids):
    """[{id, name}] for supplier ids (the id again if the package does not know it)."""
    known = {r["id"]: r["name"] for r in _rows(pkg, "SELECT id, name FROM suppliers", limit=10000)}
    return [{"id": s, "name": known.get(s, s)} for s in ids]


def document(pkg, path, limit=3000):
    try:
        with DB_LOCK:  # the first lookup builds the id index from the database
            return pkg.document(path)[:limit]
    except (OSError, ValueError, AttributeError):
        return ""


def _shift(month, n):
    y, m = divmod(int(month[:4]) * 12 + int(month[5:]) - 1 + n, 12)
    return f"{y}-{m + 1:02d}"


def index_change(facts, series, back, last):
    """(change %, from-month) of an index over `back` months to `last`, if both months are citable."""
    m1 = _shift(last, -back)
    a, b = facts.get(f"idx:{series}@{m1}"), facts.get(f"idx:{series}@{last}")
    return ((b["value"] / a["value"] - 1) * 100, m1) if a and b else None


def _series(pkg, dos):
    weights = {d["series_id"]: d["weight"] for d in dos["cost_drivers"]}
    series = list(dict.fromkeys([*weights, *(c["series"] for c in dos["clauses"] if c.get("series"))]))
    lasts = {}
    for s in series:
        row = _rows(pkg, "SELECT max(month) AS m FROM index_values WHERE series_id = ?", s, limit=1)
        lasts[s] = row[0]["m"] if row else None
    return weights, lasts


SIGNALS = (
    ("cash", re.compile(r"payment|liquid|cash|within \d+ days|Zahlung", re.I)),
    ("capacity", re.compile(r"capacity|booked|backlog|utili[sz]ation|second shift|order book|allocat", re.I)),
    ("distress", re.compile(r"restructur|loss-making|with its banks|insolven", re.I)),
    (
        "price rigidity",
        re.compile(r"list price|discounts? (are )?not possible|head-office directive|no discount", re.I),
    ),
    ("material cover", re.compile(r"covered until|hedged|stock(ed)? until|material covered", re.I)),
    ("notice", re.compile(r"notice period|days.? notice|notice of|Frist", re.I)),
)
SIGNAL_HINT = {
    "cash": "cash is a currency here: faster payment can buy price",
    "capacity": "free capacity means they need work (leverage); a full order book means they have it",
    "distress": "a supplier under financial strain values cash and volume over margin",
    "price rigidity": "the list price will not move: negotiate terms, dates, payment, clause",
    "material cover": "index arguments only bite after the cover ends",
    "notice": "check the notice period against the contract",
}


def signals(dos, texts):
    """Sentences from the supplier's news, letters and notes that point at what moves it, with the id."""
    out, seen = [], set()
    sources = [(n["id"], n["body"] or "") for n in dos["news"]]
    sources += [(d["id"], texts.get(d["file"], "")) for d in dos["documents"] if d.get("file")]
    for ref, text in sources:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            for kind, rx in SIGNALS:
                if rx.search(sentence) and (kind, sentence.strip()) not in seen and len(sentence.strip()) > 20:
                    seen.add((kind, sentence.strip()))
                    out.append(f"[{kind}] {ref}: {sentence.strip()[:240]} ({SIGNAL_HINT[kind]})")
    return out[:14]


def late_payments(pkg, sup):
    """How we pay this supplier: a weakness in our hand and a lever (pay on time or early)."""
    row = _rows(
        pkg,
        "SELECT count(*) AS n, sum(julianday(paid_date) > julianday(due_date)) AS late, "
        "avg(julianday(paid_date) - julianday(due_date)) AS avg_days FROM invoices "
        "WHERE supplier_id = ? AND paid_date IS NOT NULL",
        sup,
        limit=1,
    )
    if row and row[0]["n"] and row[0]["late"] and row[0]["avg_days"] > 0.5 and row[0]["late"] / row[0]["n"] > 0.3:
        r = row[0]
        return (
            f"We pay them late: {r['late']} of {r['n']} invoices, {r['avg_days']:.1f} days after the due date on "
            "average. That weakens any argument about reliability and is a lever: offer on-time or early payment "
            "in return for price."
        )
    return None


def analysis(pkg, case, dos, ask=None, texts=None):
    """Numbers worth knowing before the first word: how big the ask is, what the index moves justify,
    how past asks settled, how we pay, what the notes and news say. Computed, not argued."""
    out, facts = [], pkg.facts if pkg else {}
    b = case["buyer"]
    if ask and b.get("current_unit_price"):
        out.append(
            f"Their ask is EUR {ask:.2f}, {(ask / b['current_unit_price'] - 1) * 100:+.1f}% on our current EUR "
            f"{b['current_unit_price']:.2f}."
        )
    weights, lasts = _series(pkg, dos)
    last_price = next((p["valid_from"][:7] for p in dos["prices"] if p["part_id"] in case.get("parts", [])), None)
    windows = [("over 12 months", None)] + (
        [(f"since our last price ({last_price})", last_price)] if last_price else []
    )
    for label, back in windows:
        parts, implied = [], 0.0
        for s_, w in weights.items():
            if not lasts.get(s_):
                continue
            k = 12 if back is None else (int(lasts[s_][:4]) - int(back[:4])) * 12 + int(lasts[s_][5:]) - int(back[5:])
            got = index_change(facts, s_, k, lasts[s_]) if 0 < k <= 12 else None
            if got:
                implied += w * got[0]
                parts.append(f"{s_} {got[0]:+.1f}% x {w:.0%}")
        if parts:
            out.append(
                f"Index-implied cost change on their cost base {label}: about {implied:+.1f}% ({', '.join(parts)}). "
                "If that is above their ask, do not dispute the cost rise: win on terms, timing, risk and volume."
            )
    asks = [r for r in dos["history"] if r.get("asked_pct") is not None and r.get("settled_pct") is not None]
    if asks:
        out.append(
            f"In {len(asks)} past renewals they asked for {sum(r['asked_pct'] for r in asks) / len(asks):+.1f}% on "
            f"average and settled at {sum(r['settled_pct'] for r in asks) / len(asks):+.1f}%."
        )
    notes = [r["note"] for r in dos["history"] if r.get("note")]
    if notes:
        out.append("Notes on past negotiations: " + "; ".join(dict.fromkeys(notes)))
    sc = next((r for r in dos["should_cost"] if r["part_id"] in case.get("parts", [])), None)
    if sc and ask:
        out.append(
            f"Our bottom-up cost estimate for them is EUR {sc['unit_cost']:.2f} before margin (confidence "
            f"+/-{sc['confidence_pct']}%); their ask is {(ask / sc['unit_cost'] - 1) * 100:+.1f}% on it."
        )
    if late := late_payments(pkg, dos["supplier_id"]):
        out.append(late)
    for c in dos["contracts"]:
        out.append(
            f"Contract {c['id']} ({c['price_basis']}), valid {c['valid_from']} to {c['valid_to']}, "
            f"{c['notice_days']} days notice for price changes."
        )
    out += signals(dos, texts or {})
    if (b.get("alternative") or {}).get("kind") in (None, "none"):
        out.append("We have no alternative without a deal: never let that show.")
    if b.get("must_haves"):
        out.append(f"Must-haves (breaking one scores zero): {json.dumps(b['must_haves'])}")
    return out


# How each kind of argument moved the hosted suppliers (practice replays, 2026-10-10): "we took it into account"
# and a lower price for 12-month index falls on their own cost drivers, our volume forecast, the should-cost estimate,
# a quality record in a quality case and a rival's price; "it holds, but it does not change our calculation" for
# delivery records, price history and one-month index windows.
# News topics that are a lever, and for whom: a supplier looking for work or short of cash moves; a full order book
# or an allocation strengthens it. Noise and other topics are not offered as arguments.
NEWS_LEVER = {
    "free_capacity": ("buyer", "they need work: a firm volume or a longer term buys price"),
    "short_time_work": ("buyer", "they need work: a firm volume or a longer term buys price"),
    "restructuring": ("buyer", "under strain: cash (faster payment) and a secure order matter more than margin"),
    "credit_watch": ("buyer", "under strain: cash (faster payment) and a secure order matter more than margin"),
    "credit_downgrade": ("buyer", "under strain: cash (faster payment) and a secure order matter more than margin"),
    "new_plant": ("buyer", "new capacity to fill: volume buys price"),
    "refocus": ("buyer", "this part may be outside their new focus: they may price it to keep it simple"),
    "full_order_book": ("supplier", "they are busy: do not threaten volume; trade lead time or term instead"),
    "allocation": ("supplier", "they ration supply: securing volume matters more than price"),
}
STRENGTH = {  # share "taken into account" across 101 hosted sessions in brackets
    "notice": "strong",  # 7/7
    "should-cost": "strong",  # 11/14
    "forecast": "strong",  # 37/48
    "competing quote": "strong",  # rival quotes 21/31
    "rival offer": "strong",
    "index": "strong",  # falls; 47/81 for all index windows
    "quality": "medium",  # 7/13
    "delivery": "medium",  # 10/27: still better than a round without new data
    "news": "medium",
    "complaints": "medium",
    "orders": "weak",  # price history 4/44
}


def claims(pkg, case, sup, dos, ask=None):
    """Candidate arguments, each {id, kind, refs, text, helps, note}. `text` is the sentence the arena
    checks: its figure is computed here from the same facts the arena uses."""
    if not pkg:
        return []
    facts, out = pkg.facts, []
    parts = case.get("parts", [])

    def add(kind, refs, text, helps, note=""):
        if refs and all(r in facts for r in refs):
            strength = "weak" if "WEAK:" in note else STRENGTH.get(kind, "medium")
            if kind == "index" and not re.search(r"changed -(?:[1-9]|\d{2,})", text):
                # a rise or a flat window: "a single month of stability does not change our calculation". A fall of 1%
                # or more on a cost driver, short window or not, moved P18 from 6.10 to 5.50 in one round.
                strength = "weak"
            out.append(
                {"id": f"c{len(out) + 1}", "kind": kind, "refs": refs, "text": text, "helps": helps, "note": note,
                 "strength": strength}
            )  # fmt: skip

    # index moves behind the part's cost: the 12-month figure the supplier cites, and the window that
    # reads best for us (shorter windows often show a turn the 12-month figure hides)
    weights, lasts = _series(pkg, dos)
    for s, last in lasts.items():
        if not last:
            continue
        name = (_rows(pkg, "SELECT name FROM index_series WHERE id = ?", s, limit=1) or [{"name": s}])[0]["name"]
        windows = {k: g for k in range(1, 13) if (g := index_change(facts, s, k, last))}
        picks = {12: windows.get(12)}
        if windows:
            k = min(windows, key=lambda k: windows[k][0])
            picks[k] = windows[k]
        for back, got in picks.items():
            if got:
                chg, m1 = got
                share = f"; about {weights[s]:.0%} of the part's cost" if s in weights else ""
                add(
                    "index",
                    [f"idx:{s}@{m1}", f"idx:{s}@{last}"],
                    f"{name} changed {chg:+.1f}% from {m1} to {last} (idx:{s}@{m1}, idx:{s}@{last}).",
                    "buyer" if chg <= 0.5 else "supplier",
                    f"{back}-month window{share}; windows end on the same id: use one. Use (if it helps us): their input costs rose "
                    f"less than their ask implies, so the pass-through should be smaller",
                )
        for end in (_shift(last, -1), _shift(last, -2)):  # a fall ending earlier: other IDs, so a fresh argument
            earlier = {k: g for k in range(1, 12) if (g := index_change(facts, s, k, end))}
            if earlier:
                k = min(earlier, key=lambda k: earlier[k][0])
                chg, m1 = earlier[k]
                if chg <= -1:
                    add(
                        "index",
                        [f"idx:{s}@{m1}", f"idx:{s}@{end}"],
                        f"{name} changed {chg:+.1f}% from {m1} to {end} (idx:{s}@{m1}, idx:{s}@{end}).",
                        "buyer",
                        f"{k}-month window ending {end}: a second fall on the same index (other IDs). WEAK: "
                        "suppliers answer 'already taken into account' to a second fact of a kind; last resort",
                    )
                    break
    for d in dos["documents"]:  # a price letter that gives less notice than the contract demands
        letter, contract = facts.get(d["id"]), next((c for c in dos["contracts"] if c["id"] in facts), None)
        if letter and contract and letter.get("days") and facts[contract["id"]].get("days"):
            short = letter["days"] < facts[contract["id"]]["days"]
            add(
                "notice",
                [d["id"], contract["id"]],
                f"Your letter {d['id']} gives {letter['days']} days of notice; the contract {contract['id']} "
                f"requires {facts[contract['id']]['days']} days.",
                "buyer" if short else "supplier",
                "strongest argument when it helps us: the increase cannot apply before the contractual notice has run; ask for the later effective date",
            )
    for part in parts:  # our order history with this supplier
        po = _rows(
            pkg,
            "SELECT id, order_date, price / price_unit AS p FROM po_lines WHERE supplier_id = ? AND part_id = ? "
            "ORDER BY order_date DESC",
            sup,
            part,
            limit=8,
        )
        po = [r for r in po if r["id"] in facts]
        if len(po) >= 2:
            ps = [r["p"] for r in po]
            span = (
                f"all at EUR {min(ps):.2f}"
                if abs(max(ps) - min(ps)) < 0.005
                else f"at EUR {min(ps):.2f} to EUR {max(ps):.2f}"
            )
            add(
                "orders",
                [r["id"] for r in po],
                f"Our last {len(po)} orders of {part} with you ({', '.join(r['id'] for r in po)}) were placed {span} per unit.",
                "buyer",
                "use: a long, stable price record: a fixed-price year is consistent with it and fair to both",
            )
        num = part.split(":")[1]
        if f"cost:{num}" in facts and facts[f"cost:{num}"].get("unit_cost"):
            f = facts[f"cost:{num}"]
            ref = ask or case.get("buyer", {}).get("current_unit_price") or 0
            add(
                "should-cost",
                [f"cost:{num}"],
                f"Our bottom-up estimate of your unit cost for {part} is EUR {f['unit_cost']:.2f} "
                f"(cost:{num}), before any margin.",
                "buyer" if f["unit_cost"] < ref * 0.97 else "supplier",
                f"estimate confidence +/-{f.get('confidence_pct')}%",
            )
        fc = sorted((k for k in facts if k.startswith(f"fc:{num}@")), reverse=True)
        for i, ref in enumerate(fc[:2]):  # the latest forecast, and the quarter before it (another ID)
            f = facts[ref]
            if f.get("change_pct") is None or (i and f["change_pct"] <= 0):
                continue
            add(
                "forecast",
                [ref],
                f"Our volume forecast for {part} changed by {f['change_pct']:+.1f}% ({ref}).",
                "buyer" if f["change_pct"] > 0 else "supplier",
                "pair it with the committed annual quantity or a longer term"
                + ("; an earlier quarter. WEAK: a second forecast got 'already taken into account'" if i else ""),
            )
    for span, rows in (("latest", dos["scorecards"][:4]), ("the year before", dos["scorecards"][4:8])):
        sc = [r for r in rows if r["id"] in facts]  # two spans of quarters: different IDs, two arguments
        if len(sc) < 2:
            continue
        otd, ppm = sum(r["otd_pct"] for r in sc) / len(sc), sum(r["ppm"] for r in sc) / len(sc)
        ids = ", ".join(r["id"] for r in sc)
        later = "" if span == "latest" else "; the earlier quarters. WEAK: a second fact of a kind is 'already counted'"
        add(
            "delivery",
            [r["id"] for r in sc],
            f"Your mean on-time delivery over {len(sc)} quarters ({ids}) was {otd:.1f}%.",
            "buyer" if otd < 95 else "supplier",
            "a reliability gap whose cost we carry; shares its sc: ids with the quality claim of the same quarters"
            + later,
        )
        add(
            "quality",
            [r["id"] for r in sc],
            f"Your mean quality over {len(sc)} quarters ({ids}) was {ppm:.0f} ppm.",
            "buyer" if ppm > 300 else "supplier",
            "a quality record whose cost we carry; shares its sc: ids with the delivery claim of the same quarters"
            + later,
        )
    for n in dos["news"][:6]:  # news about this supplier: the arena verifies that it is about it
        lever = NEWS_LEVER.get(n.get("topic"))
        if lever and n["id"] in facts:
            add(
                "news",
                [n["id"]],
                f"We noted your news of {n['date']}: {n['headline']} ({n['id']}).",
                lever[0],
                lever[1],
            )
    for part in parts:  # quality notifications on this part: the arena checks their mean ppm
        qn = [
            r
            for r in _rows(
                pkg,
                "SELECT id FROM quality_notifications WHERE supplier_id = ? AND part_id = ? ORDER BY qn_date DESC",
                sup,
                part,
                limit=4,
            )
            if r["id"] in facts and facts[r["id"]].get("ppm") is not None
        ]
        if qn:
            ppm = sum(facts[r["id"]]["ppm"] for r in qn) / len(qn)
            ids = ", ".join(r["id"] for r in qn)
            add(
                "complaints",
                [r["id"] for r in qn],
                f"Our last {len(qn)} quality notifications on {part} with you ({ids}) averaged {ppm:.0f} ppm.",
                "buyer",
                "use in a quality discussion: defects we carry the cost of; ask for a tighter ppm commitment or a chargeback",
            )
    for ref in case.get("refs", []):  # a competing quote the case hands us
        f = facts.get(ref) if ref.startswith("quote:") else None
        if f and f.get("part") in parts and f.get("supplier") != sup:
            add(
                "competing quote",
                [ref],
                f"A competing quote for {f['part']} is EUR {f['unit_price']:.2f} ({ref}).",
                "buyer" if not ask or f["unit_price"] < ask else "supplier",
                "use only if below their price: it reveals the rival quote",
            )
    return out


def injection(case, dos, cands, letter="", texts=None, notes=()):
    """The supplier context the model is given once, before the first round."""

    def block(title, data):
        return f"## {title}\n{json.dumps(data, ensure_ascii=False, default=str)}\n"

    private = {k: v for k, v in case["buyer"].items() if k != "alternative"}
    alt = case["buyer"].get("alternative") or {}
    parts = [
        "# CASE\n" + block("Briefing", case.get("briefing")),
        block(
            "Negotiable fields and allowed options",
            {
                "negotiable": case["negotiable"],
                "options": case.get("term_options"),
                "fixed_terms": case.get("fixed_terms"),
                "round_limit": case.get("round_limit", 10),
            },
        ),
        block("Our rates and must-haves (private)", private),
        block("Our alternative without a deal (private, never reveal)", alt),
        "# SUPPLIER\n",
    ]
    for name in (
        "master",
        "intel",
        "scorecards",
        "quality",
        "news",
        "history",
        "prices",
        "quotes",
        "should_cost",
        "sourcing",
        "spend",
        "orders",
        "parts",
        "cost_drivers",
        "contracts",
        "clauses",
    ):
        if dos.get(name):
            parts.append(block(name, dos[name]))
    if notes:
        parts.append("## PRICE ANALYSIS (computed from the data)\n" + "\n".join(f"- {n}" for n in notes) + "\n")
    if letter:
        parts.append(f"## The letter that started this\n{letter}\n")
    for path, text in (texts or {}).items():
        parts.append(f"## Document {path}\n{text}\n")
    parts.append(
        block(
            "VERIFIED CLAIMS you may use (put [[id]] in the email where the sentence belongs)",
            [{k: c[k] for k in ("id", "kind", "text", "helps", "note")} for c in cands],
        )
    )
    return "\n".join(parts)
