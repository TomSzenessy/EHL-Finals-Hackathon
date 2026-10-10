"""What the agent knows about a supplier, from the data package alone.

`dossier` is the supplier's record (shown on the Suppliers tab and injected into the model).
`claims` are arguments the arena will check, already worded and computed from facts.json, so the
model only chooses which to use: a figure it writes itself could be wrong, and a wrong one costs trust."""

import json
import re

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
    return pkg.query(sql, params, limit=limit) if pkg and pkg.db else []


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
        return pkg.document(path)[:limit]
    except (OSError, ValueError, AttributeError):
        return ""


def _shift(month, n):
    y, m = divmod(int(month[:4]) * 12 + int(month[5:]) - 1 + n, 12)
    return f"{y}-{m + 1:02d}"


def claims(pkg, case, sup, dos):
    """Candidate arguments, each {id, kind, refs, text, helps, note}. `text` is the sentence the arena
    checks: its figure is computed here from the same facts the arena uses."""
    if not pkg:
        return []
    facts, out = pkg.facts, []
    parts = case.get("parts", [])

    def add(kind, refs, text, helps, note=""):
        if refs and all(r in facts for r in refs):
            out.append(
                {"id": f"c{len(out) + 1}", "kind": kind, "refs": refs, "text": text, "helps": helps, "note": note}
            )

    # index moves behind the part's cost (cost drivers and the contract's own index clause)
    weights = {d["series_id"]: d["weight"] for d in dos["cost_drivers"]}
    series = list(dict.fromkeys([*weights, *(c["series"] for c in dos["clauses"] if c.get("series"))]))
    for s in series:
        row = _rows(pkg, "SELECT max(month) AS m FROM index_values WHERE series_id = ?", s, limit=1)
        last = row[0]["m"] if row else None
        info = (_rows(pkg, "SELECT name FROM index_series WHERE id = ?", s, limit=1) or [{"name": s}])[0]["name"]
        for back in (12, 6):
            m1 = _shift(last, -back) if last else None
            a, b = facts.get(f"idx:{s}@{m1}"), facts.get(f"idx:{s}@{last}")
            if a and b:
                chg = (b["value"] / a["value"] - 1) * 100
                share = f"; about {weights[s]:.0%} of the part's cost" if s in weights else ""
                add(
                    "index",
                    [f"idx:{s}@{m1}", f"idx:{s}@{last}"],
                    f"{info} changed {chg:+.1f}% from {m1} to {last} (idx:{s}@{m1}, idx:{s}@{last}).",
                    "buyer" if chg <= 0.5 else "supplier",
                    f"{back}-month window{share}",
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
            add(
                "orders",
                [r["id"] for r in po],
                f"Our last {len(po)} orders of {part} with you ({', '.join(r['id'] for r in po)}) were placed at "
                f"EUR {min(ps):.2f} to EUR {max(ps):.2f} per unit.",
                "buyer",
                "order price history",
            )
        num = part.split(":")[1]
        if f"cost:{num}" in facts and facts[f"cost:{num}"].get("unit_cost"):
            f = facts[f"cost:{num}"]
            add(
                "should-cost",
                [f"cost:{num}"],
                f"Our bottom-up estimate of your unit cost for {part} is EUR {f['unit_cost']:.2f} "
                f"(cost:{num}), before any margin.",
                "buyer"
                if f["unit_cost"] < (case.get("buyer", {}).get("current_unit_price") or 0) * 0.97
                else "supplier",
                f"estimate confidence +/-{f.get('confidence_pct')}%",
            )
        fc = sorted((k for k in facts if k.startswith(f"fc:{num}@")), reverse=True)
        if fc and (f := facts[fc[0]]).get("change_pct") is not None:
            add(
                "forecast",
                [fc[0]],
                f"Our volume forecast for {part} changed by {f['change_pct']:+.1f}% ({fc[0]}).",
                "buyer" if f["change_pct"] > 0 else "supplier",
                "volume outlook",
            )
    sc = [r for r in dos["scorecards"][:4] if r["id"] in facts]
    if len(sc) >= 2:
        otd, ppm = sum(r["otd_pct"] for r in sc) / len(sc), sum(r["ppm"] for r in sc) / len(sc)
        ids = ", ".join(r["id"] for r in sc)
        add(
            "delivery",
            [r["id"] for r in sc],
            f"Your mean on-time delivery over {len(sc)} quarters ({ids}) was {otd:.1f}%.",
            "buyer" if otd < 95 else "supplier",
            "shares sc: ids with the quality claim: use one of the two",
        )
        add(
            "quality",
            [r["id"] for r in sc],
            f"Your mean quality over {len(sc)} quarters ({ids}) was {ppm:.0f} ppm.",
            "buyer" if ppm > 300 else "supplier",
            "shares sc: ids with the delivery claim: use one of the two",
        )
    for ref in case.get("refs", []):  # a competing quote the case hands us
        f = facts.get(ref) if ref.startswith("quote:") else None
        if f and f.get("part") in parts and f.get("supplier") != sup:
            add(
                "competing quote",
                [ref],
                f"A competing quote for {f['part']} is EUR {f['unit_price']:.2f} ({ref}).",
                "buyer",
                "reveals the rival quote to this supplier",
            )
    return out


def injection(case, dos, cands, letter="", texts=None):
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
