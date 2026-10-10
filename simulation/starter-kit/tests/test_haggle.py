# ruff: noqa: E501
"""The haggling agent and its recorder, against arena-sim in this process with a scripted model."""

import json
import re
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from arena_kit.data import DataPackage  # noqa: E402
from arena_kit.haggle.arena import Arenas  # noqa: E402
from arena_kit.haggle.context import claims, dossier  # noqa: E402
from arena_kit.haggle.server import create_app  # noqa: E402

DATA = Path(__file__).parent.parent.parent / "data"
pkg = pytest.fixture(scope="module")(lambda: DataPackage(DATA))


class ScriptedLLM:
    """Stands in for the model: offers the first two packages of the code's menu, or settles when asked to."""

    model, timeout, configured = "scripted", 5, True

    def __init__(self, settle=False):
        self.calls, self.settle = [], settle

    def chat(self, system, messages, timeout=None, record=lambda r: None):
        text = messages[-1]["content"]
        keys = re.findall(r"^- ([A-J]): EUR", text, re.M)
        reply = json.dumps(
            {
                "action": "settle" if self.settle else "send",
                "subject": "Our counter",
                "body": "Thank you for the quote. [[c1]] Could you send a cost breakdown?",
                "offers": keys[:2],
                "rationale": "scripted",
            }
        )
        record({"request": {"messages": messages}, "response": {"text": reply}, "ms": 1, "error": None})
        self.calls.append(messages)
        return reply


def wait(client, rid, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        body = client.get(f"/api/runs/{rid}").json()
        if body["meta"]["status"] in ("done", "error"):
            return body
        time.sleep(0.1)
    raise AssertionError("run did not finish")


def test_claims_are_computed_from_the_facts(pkg):
    case = {"parts": ["part:310010"], "refs": ["quote:7200001"], "buyer": {"current_unit_price": 126.53}}
    cands = claims(pkg, case, "sup:70110", dossier(pkg, "sup:70110", case))
    kinds = {c["kind"] for c in cands}
    assert {"index", "should-cost", "delivery", "competing quote"} <= kinds
    assert all(all(r in pkg.facts for r in c["refs"]) for c in cands)
    assert any("-3.7%" in c["text"] for c in cands)  # the electricity index move from the API brief


def test_offline_run_is_recorded_and_inspectable(pkg, tmp_path):
    llm = ScriptedLLM()
    client = TestClient(create_app(pkg, Arenas(pkg.facts), llm, folder=tmp_path))
    cases = client.get("/api/cases?mode=offline").json()["cases"]
    assert cases
    started = client.post("/api/runs", json={"mode": "offline", "case_id": cases[0]["case_id"]}).json()
    body = wait(client, started["run_id"])
    assert body["meta"]["status"] == "done", body["events"][-1]
    kinds = [e["kind"] for e in body["events"]]
    assert {"http", "llm", "decision"} <= set(kinds)
    sent = [e for e in body["events"] if e["kind"] == "http" and e["path"].endswith("/messages")]
    assert len(sent) >= 3  # it keeps haggling instead of taking the first offer
    assert sent[0]["request"]["message"]["term_sheets"][0]["terms"]["unit_price"] > 0
    assert "X-API-Key" not in json.dumps(body)
    assert body["meta"]["suppliers"][0]["id"].startswith("sup:")
    assert (tmp_path / f"{started['run_id']}.jsonl").exists()
    assert client.get("/api/runs").json()[0]["run_id"] == started["run_id"]
    sup = client.get("/api/suppliers").json()[0]
    assert sup["runs"][0]["run_id"] == started["run_id"]
    assert client.get(f"/api/suppliers/{sup['id']}").json()["master"]["id"] == sup["id"]


def test_online_needs_a_key(pkg, tmp_path, monkeypatch):
    monkeypatch.delenv("ARENA_API_KEY", raising=False)
    client = TestClient(create_app(pkg, Arenas(pkg.facts), ScriptedLLM(), folder=tmp_path))
    assert client.get("/api/cases?mode=online").status_code == 400


# -- the pricing model and the guards, on the numbers of hosted case P02 ----------------------------
CLAUSE = {"series": "CU-NOTATION", "material_share": 0.2, "deadband_pct": 5, "base_month": "2026-08"}
P02 = {
    "case_id": "case:P02", "parts": ["part:350011"], "suppliers": ["sup:70510"], "refs": [], "title": "P02",
    "negotiable": ["unit_price", "payment_days", "index_clause"], "round_limit": 10,
    "fixed_terms": {"lead_time_days": 35, "volume_per_year": 6110, "contract_months": 12,
                    "effective_date": "2027-01-01", "incoterm": "DAP", "tooling_eur": 0},
    "term_options": {"payment_days": [14, 30, 45, 60, 90], "index_clause": [None, CLAUSE]},
    "buyer": {"need_per_year": 6110, "horizon_years": 1.0, "current_unit_price": 348.32, "fallback_unit_price": 376.19,
              "interest_rate": 0.08, "reference_payment_days": 60, "need_lead_time_days": 36, "category_goal": "stabilise",
              "fallback_risk_pct": 10, "index_risk_pct": 4, "late_cost_per_day": 720, "cost_per_defect": 780,
              "sustainable_margin_pct": 0.5, "relationship_eur_per_point": 31920,
              "freight_eur_per_unit": {"EXW": 2.99, "FCA": 2.6, "DAP": 0.0}, "index_paths": {"CU-NOTATION": 0.05},
                "must_haves": [], "alternative": {"kind": "none", "terms": {}}},
}  # fmt: skip
PDF_STANDARD = {"ppm_commitment": 250, "chargeback_eur_per_complaint": 0.0}


def test_pricing_model_reproduces_the_arena_on_p02(pkg):
    from arena_kit.haggle import economics as eco

    dos = dossier(pkg, "sup:70510", P02)
    std = eco.full_standard(dos, PDF_STANDARD)
    assert std["payment_days"] == 30 and std["incoterm"] == "DAP"  # the PDF alone lacks the cash terms
    est = eco.estimate(P02, dos, std, ask=370.96)
    deal = {"unit_price": 349.0, "payment_days": 30, "index_clause": CLAUSE}
    assert eco.cost(P02, deal, std, est) == pytest.approx(2_271_134, rel=0.005)  # the arena's c_deal of a real run
    best = eco.plan(P02, std, est, 370.96)
    assert best["modelled"] and best["target"]["c"] == pytest.approx(2_235_514, rel=0.005)  # the arena's c_best
    assert best["target"]["terms"]["index_clause"] is None  # a clause only costs us here
    assert 350 < best["target"]["terms"]["unit_price"] < 365  # lower is not better in a stabilise case


def _negotiator(pkg, llm=None):
    from arena_kit.haggle.agent import Negotiator

    neg = Negotiator(P02, "sup:70510", llm or ScriptedLLM(), pkg, "context", [], lambda r: None)
    neg.dossier = dossier(pkg, "sup:70510", P02)
    return neg


def _thread(status="open", price=370.96):
    pdf = "Our standard terms (apply to everything not stated above)\nQuality commitment (ppm) 250\n"
    return [{"from": "sales@70510", "status": status, "subject": "Re: P02", "body": "Our offer.",
             "term_sheets": [{"term_sheet_id": "offer:70510-0", "terms": {"unit_price": price, "payment_days": 30, "index_clause": None}}],
             "attachments": [{"name": "quote-offer.pdf", "text": pdf}], "signals": {"reply_delay_days": 1}}]  # fmt: skip


def _std(neg):
    from arena_kit.haggle import economics as eco

    return eco.full_standard(neg.dossier, {})


def _reply(events, status, price, terms=None):
    """The thread after we sent the scripted counter and the supplier answered."""
    sheet = {"unit_price": price, "payment_days": 30, "index_clause": None, **(terms or {})}
    return [*events, {"from": "buyer", "body": "counter"},
            {"from": "sales@70510", "status": status, "subject": "Re: P02", "body": "Our offer.",
             "term_sheets": [{"term_sheet_id": f"offer:70510-{len(events)}", "terms": sheet}],
             "attachments": [], "signals": {}}]  # fmt: skip


def test_code_prices_every_sheet_and_the_first_one_sits_at_the_target(pkg):
    neg, events = _negotiator(pkg), _thread()
    kind, message, meta = neg.step(events)
    assert kind == "send" and 1 <= len(message["term_sheets"]) <= 3
    costs = meta["sheet_costs"]
    target = neg.target_c()
    assert all(abs(c - costs[0]) / costs[0] < 0.002 for c in costs)  # equal-cost packages
    assert target <= costs[0] <= target * 1.002  # a stabilise case opens at the C-optimal price, not below it
    assert all(t["terms"]["unit_price"] < 370.96 for t in message["term_sheets"])
    assert "[[" not in message["body"] and "Because Our" not in message["body"]


def test_our_steps_shrink_and_never_pass_their_sheet(pkg):
    neg, events = _negotiator(pkg), _thread()
    paid = []
    for price in (369.5, 368.9, 368.5, 368.2):
        kind, message, meta = neg.step(events)
        assert kind == "send"
        neg.sent()
        paid.append(max(meta["sheet_costs"]))
        events = _reply(events, "open", price)
    steps = [b - a for a, b in zip(paid, paid[1:], strict=False)]
    assert all(s > 0 for s in steps) and steps == sorted(steps, reverse=True)
    assert paid[-1] < neg.their_c(events, _std(neg))


def test_agreed_is_taken_at_once_without_asking_the_model(pkg):
    neg, events = _negotiator(pkg), _thread()
    neg.step(events)
    neg.sent()
    neg.llm.calls.clear()
    kind, message, _ = neg.step(_reply(events, "agreed", 361.0))
    assert kind == "settle" and message is None and not neg.llm.calls


def test_a_final_offer_is_taken_without_another_word(pkg, monkeypatch):
    # Pushing after "final offer" ended in a walk-away 3 times of 3 on the hosted arena: no deal scores 0.
    neg, events = _negotiator(pkg), _thread()
    neg.step(events)
    neg.sent()
    neg.llm.calls.clear()
    kind, message, _ = neg.step(_reply(events, "final_offer", 370.5))
    assert kind == "settle" and message is None and not neg.llm.calls
    # the probe stays available as an explicit experiment
    monkeypatch.setenv("HAGGLE_PROBE_FINAL", "1")
    neg2, events2 = _negotiator(pkg), _thread()
    neg2.step(events2)
    neg2.sent()
    kind, message, meta = neg2.step(_reply(events2, "final_offer", 370.5))
    assert kind == "send" and meta["mode"] == "probe" and len(message["term_sheets"]) == 1


def test_the_model_may_not_settle_while_the_supplier_still_moves(pkg):
    neg = _negotiator(pkg, ScriptedLLM(settle=True))
    kind, message, meta = neg.step(_thread())
    assert kind == "send" and meta["fallback"]  # three refusals, then the plain counter from the menu
    assert any("Do not settle" in f for f in meta["feedback"])


def test_settings_change_the_model_and_the_prompt_file(pkg, tmp_path, monkeypatch):
    from arena_kit.haggle.settings import Settings

    monkeypatch.chdir(tmp_path)
    for name in ("LLM_MODEL", "LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    client = TestClient(
        create_app(pkg, Arenas(pkg.facts), folder=tmp_path / "runs", settings=Settings(tmp_path / "s.json"))
    )
    first = client.get("/api/settings").json()
    assert first["prompt_is_default"] and not first["configured"]
    saved = client.put(
        "/api/settings", json={"model": "m-1", "api_key": "secret-key", "prompt": 'My prompt text {"offers": []}'}
    ).json()
    assert saved["model"] == "m-1" and saved["has_key"] and saved["configured"]
    assert "secret-key" not in json.dumps(saved)  # the key is write-only
    assert saved["prompt"] == 'My prompt text {"offers": []}' and (tmp_path / "prompts" / "system.md").exists()
    assert client.get("/api/config").json()["model"] == "m-1"
    reset = client.put("/api/settings", json={"reset_prompt": True}).json()
    assert reset["prompt_is_default"]


def test_an_rfq_with_two_suppliers_runs_both_threads_and_closes_cleanly(pkg, tmp_path):
    client = TestClient(create_app(pkg, Arenas(pkg.facts), ScriptedLLM(), folder=tmp_path))
    started = client.post("/api/runs", json={"mode": "offline", "case_id": "case:S02"}).json()
    body = wait(client, started["run_id"], timeout=90)
    assert body["meta"]["status"] == "done"
    assert not [e for e in body["events"] if e["kind"] == "error"], [e for e in body["events"] if e["kind"] == "error"]
    suppliers = {e["supplier"] for e in body["events"] if e["kind"] == "decision" and e.get("round")}
    assert len(suppliers) == 2  # one agent per supplier thread, run in parallel


def test_near_the_wave_cap_a_case_closes_on_the_standing_sheet(pkg, tmp_path):
    from arena_kit.haggle.run import Run

    run = Run("offline", "case:S01", tmp_path, Arenas(pkg.facts), pkg, ScriptedLLM(), deadline=lambda: time.time() + 30)
    run.execute()
    assert run.meta["status"] == "done" and run.meta["deal"]
    actions = [e.get("action") for e in run.events if e["kind"] == "decision"]
    assert actions[0] == "cap" and "accept" in actions  # no message sent: straight to the close


def test_the_final_runner_plays_each_case_of_a_running_wave_once(pkg, tmp_path):
    from arena_kit.haggle.final import play_waves

    class WaveArenas(Arenas):
        """The offline simulator, with a final case list: one wave of two cases, then closed."""

        polls = 0

        def client(self, mode):
            c = super().client("offline")
            if mode == "final":
                practice = c.cases

                def cases(set_="practice"):
                    if set_ != "final":
                        return practice(set_)
                    WaveArenas.polls += 1
                    open_ = WaveArenas.polls < 3
                    return [{**x, "wave": 1, "open": open_, "seconds_left": 300 if open_ else 0}
                            for x in practice("practice")[:2]]  # fmt: skip

                c.cases = cases
            return c

    runs = play_waves(WaveArenas(pkg.facts), pkg, ScriptedLLM(), "system", "test", tmp_path, waves=1, poll=0.05)
    assert sorted(r.meta["case_id"] for r in runs) == ["case:S01", "case:S02"]
    assert all(r.meta["status"] == "done" and r.meta["mode"] == "final" for r in runs)


def test_a_figure_without_a_check_behind_it_is_sent_back(pkg):
    from arena_kit.haggle.agent import unverified_figures

    allowed = "EUR 5.12, payment_days=30 | Copper rose 47.7 % in twelve months"
    assert unverified_figures("We offer EUR 5.12. Copper rose 47.7 % for you.", allowed) == []
    assert unverified_figures("Your on-time delivery was 83.0%, so EUR 4.99 is fair.", allowed) == ["83.0%", "EUR 4.99"]


def test_a_supplier_that_holds_its_price_is_offered_its_price_on_better_terms(pkg):
    neg, events = _negotiator(pkg), _thread()
    neg.step(events)
    neg.sent()
    events = _reply(events, "open", 368.0)
    neg.step(events)
    neg.sent()
    events = _reply(events, "open", 368.0)  # the same price twice: it will not move on price
    kind, message, meta = neg.step(events)
    assert kind == "send" and meta["mode"] == "terms"
    sheet = message["term_sheets"][0]["terms"]
    assert sheet["unit_price"] == 368.0 and sheet["payment_days"] == 90  # their price, our longest payment term


def test_infeasible_target_menu_does_not_accept_opening(pkg, monkeypatch):
    neg, events = _negotiator(pkg), _thread()
    monkeypatch.setattr(neg, "offer_menu", lambda *args: [])
    kind, message, meta = neg.step(events)
    assert kind == "send"
    assert message["term_sheets"][0]["terms"]["unit_price"] < 370.96
    assert meta["fallback"]


def test_open_rfq_leader_does_not_close_while_rival_is_active(tmp_path):
    import threading

    from arena_kit.haggle.run import Run

    run = Run("online", "synthetic", tmp_path, None, None, ScriptedLLM())
    run.result = None
    run.close_lock, run.gate = threading.Lock(), threading.Lock()
    run.closing = threading.Event()
    run.active, run.dormant, run.last_call = {"a", "b"}, set(), {}
    run._candidates = lambda *args: [(100, "a", "offer:a")]
    closed = []
    run._close = lambda *args: closed.append(True)
    threads = {s: [{"from": s, "status": "counter"}] for s in ("a", "b")}
    run._settled(None, {"suppliers": ["a", "b"]}, threads, "a")
    assert not closed
    assert not run.closing.is_set()
    threads["a"][-1]["status"] = "final_offer"
    run._settled(None, {"suppliers": ["a", "b"]}, threads, "a")
    assert closed  # a firm offer still closes before it can expire


def test_a_goal_below_reach_still_gets_a_menu(pkg):
    """A deep anchor lies below every structure's lowest allowed price: the menu offers the cheapest reachable
    packages instead of nothing (an empty menu once ended in a counter on the supplier's own 12-month sheet)."""
    from arena_kit.haggle import strategy as st

    neg, events = _negotiator(pkg), _thread()
    std = _std(neg)
    neg.prepare(events, std)
    items = st.menu(P02, 1.0, std, neg.est, 370.96, [events[0]["term_sheets"][0]["terms"]])
    assert items
    assert all(m["terms"]["unit_price"] >= round(370.96 * st.LOWEST_SHARE, 2) - 0.01 for m in items)
    reach = st.reachable_c(P02, std, neg.est, 370.96)
    assert min(m["c"] for m in items) <= reach * 1.003
    assert all(m["c"] <= reach * 1.011 for m in items)  # index-clause packages keep their 1% allowance


def test_a_cheaper_alternative_sheet_is_sent_back_before_closing(pkg):
    """Only the standing sheet can be accepted: when their own alternative is cheaper for us, we send its terms back
    instead of closing on the dearer standing sheet (P07: the standing 12-month sheet lost to our alternative, the
    36-month alternative did not, and the case ended in a walk-away)."""
    neg, events = _negotiator(pkg), _thread()
    neg.step(events)
    neg.sent()
    events = _reply(events, "final_offer", 369.0, {"payment_days": 14})
    events[-1]["term_sheets"].append({"term_sheet_id": "offer:70510-2-a", "terms": {"unit_price": 360.0,
                                      "payment_days": 30, "index_clause": None}})  # fmt: skip
    kind, message, _ = neg.step(events)
    assert kind == "send"
    assert message["term_sheets"][0]["terms"]["unit_price"] == 360.0
    kind, _, _ = neg.step(_reply(events, "agreed", 360.0))
    assert kind == "settle"


def test_a_letter_that_exists_only_in_the_case_becomes_a_notice_claim(pkg):
    """Hidden cases carry facts of their own (a new letter): its notice period against the contract is a claim."""
    case = {**P02, "facts": {"doc:CASE-LETTER-1": {"supplier": "sup:70510", "date": "2026-10-05", "days": 30,
                                                  "type": "letter", "title": "Price adjustment"}}}  # fmt: skip
    dos = dossier(pkg, "sup:70510", case)
    found = [c for c in claims(pkg, case, "sup:70510", dos, 370.96) if "doc:CASE-LETTER-1" in c["refs"]]
    assert found and found[0]["kind"] == "notice" and found[0]["helps"] == "buyer"
    assert "30 days" in found[0]["text"] and "90 days" in found[0]["text"]


def test_the_menu_never_offers_a_structure_that_is_a_trap_at_their_price(pkg):
    """A 12-month term over a 2-year need is cheap only at a price the supplier never takes: priced at its own level
    it leaves half the need uncovered, and a supplier that counters on it closes there (P08: 0.10)."""
    from arena_kit.haggle import economics as eco
    from arena_kit.haggle import strategy as st

    fixed = {k: v for k, v in P02["fixed_terms"].items() if k != "contract_months"}
    case = {**P02, "negotiable": [*P02["negotiable"], "contract_months"], "fixed_terms": fixed,
            "term_options": {**P02["term_options"], "contract_months": [12, 24]},
            "buyer": {**P02["buyer"], "horizon_years": 2}}  # fmt: skip
    dos = dossier(pkg, "sup:70510", case)
    std = eco.full_standard(dos, PDF_STANDARD)
    est = eco.estimate(case, dos, std, ask=370.96)
    items = st.menu(case, 1.0, std, est, 370.96, [{"unit_price": 370.96, "payment_days": 30, "index_clause": None}])
    assert items and all(m["terms"]["contract_months"] == 24 for m in items)


def test_the_clause_package_is_the_cheapest_one_for_us_in_a_health_charge_case(pkg):
    """A clause package that cannot reach the goal sits at its cheapest price and the supplier agrees to it at once
    (P02, round 1): only the cheapest of them stays on the menu, at the longest payment term, because a supplier
    values money below our rate (P02: 361.50 at 90 days, 0.735, against 358.20 at 45 days, 0.659)."""
    from arena_kit.haggle import economics as eco
    from arena_kit.haggle import strategy as st

    case = {**P02, "term_options": {**P02["term_options"], "payment_days": [14, 30, 45, 60, 90]}}
    dos = dossier(pkg, "sup:70510", case)
    std = eco.full_standard(dos, PDF_STANDARD)
    est = eco.estimate(case, dos, std, ask=370.96)
    assert est["interest_rate"] < case["buyer"]["interest_rate"]
    plan = eco.plan(case, std, est, 370.96)
    items = st.menu(case, plan["target"]["c"], std, est, 370.96, [{"unit_price": 370.96, "payment_days": 30,
                                                                      "index_clause": None}])  # fmt: skip
    clause = [m for m in items if m["terms"]["index_clause"]]
    assert len(clause) == 1 and clause[0]["terms"]["payment_days"] == 90
    assert 359 < clause[0]["terms"]["unit_price"] < 364


def test_a_supplier_under_strain_keeps_our_rate_for_money(pkg):
    from arena_kit.haggle import economics as eco

    dos = {**dossier(pkg, "sup:70510", P02), "news": [{"topic": "restructuring"}]}
    est = eco.estimate(P02, dos, eco.full_standard(dos, PDF_STANDARD), ask=370.96)
    assert est["interest_rate"] == P02["buyer"]["interest_rate"]


def test_our_sheets_never_cost_more_than_our_alternative(pkg):
    """A sheet dearer than our alternative is one we could never close on: offline P12 and P15 (today's contract as the
    alternative) climbed past it, the supplier agreed to our sheet and the close walked away. The climb stops under it."""
    from arena_kit.cost import total_cost
    from arena_kit.haggle.agent import Negotiator

    alt = {"unit_price": 364.0, "payment_days": 30, "index_clause": None}
    case = {**P02, "buyer": {**P02["buyer"], "category_goal": "leverage",
                             "alternative": {"kind": "current_contract", "terms": alt}}}  # fmt: skip
    neg = Negotiator(case, "sup:70510", ScriptedLLM(), pkg, "context", [], lambda r: None)
    neg.dossier = dossier(pkg, "sup:70510", case)
    c_alt = total_cost(case, alt)
    events = _thread()
    for price in (369.9, 369.6, 369.4, 369.3, 369.2, 369.1):
        kind, message, meta = neg.step(events)
        if kind != "send":
            break
        neg.sent()
        assert max(meta["sheet_costs"]) < c_alt
        events = _reply(events, "open", price)


def test_a_sheet_that_breaks_a_must_have_is_sent_back_with_the_must_have_kept(pkg):
    """A field their sheet leaves out closes on their standard terms (offline P11: 6400 ppm against a 1500 limit), or
    their own value breaks the limit (P10: a volume under the need): the close could only walk away, which scores 0.
    Before that, once and even after a final offer, their price goes back with the must-have fields kept."""
    from arena_kit.haggle.agent import Negotiator

    case = {**P02, "buyer": {**P02["buyer"], "must_haves": [{"field": "payment_days", "op": ">=", "value": 45}]}}
    neg = Negotiator(case, "sup:70510", ScriptedLLM(), pkg, "context", [], lambda r: None)
    neg.dossier = dossier(pkg, "sup:70510", case)
    events = _reply(_thread(), "final_offer", 365.0)  # their final sheet: 30 days, under the must-have
    kind, message, _ = neg.step(events)
    assert kind == "send"
    sheet = message["term_sheets"][0]["terms"]
    assert sheet["unit_price"] == 365.0 and sheet["payment_days"] >= 45
    kind, _, _ = neg.step(_reply(events, "final_offer", 365.0))
    assert kind == "settle"  # once only
