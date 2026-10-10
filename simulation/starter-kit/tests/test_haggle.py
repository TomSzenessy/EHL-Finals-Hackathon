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
    """Stands in for the model: always counters 3% under the supplier's standing price."""

    model, timeout, configured = "scripted", 5, True

    def __init__(self, settle=False):
        self.calls = []

    def chat(self, system, messages, timeout=None, record=lambda r: None):
        text = next(m["content"] for m in reversed(messages) if "STANDING sheet" in m["content"])
        sheet = json.loads(re.search(r"STANDING sheet \S+: (\{.*?\}) ->", text).group(1))
        sheet["unit_price"] = round(sheet["unit_price"] * 0.97, 2)
        reply = json.dumps(
            {
                "action": "settle" if re.search(r"(?<!\d)0 messages left", text) else "send",
                "subject": "Our counter",
                "body": "Thank you for the quote. [[c1]] Could you send a cost breakdown?",
                "term_sheets": [sheet],
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


def test_a_counter_far_below_their_price_is_refused_as_an_insult(pkg):
    from arena_kit.haggle.agent import Feedback

    neg, events = _negotiator(pkg), _thread()
    std = __import__("arena_kit.haggle.economics", fromlist=["x"]).full_standard(neg.dossier, {})
    neg.prepare(events, std)
    ask = {
        "action": "send",
        "body": "Hello",
        "term_sheets": [{"unit_price": 216, "payment_days": 90, "index_clause": None}],
    }
    with pytest.raises(Feedback, match="insult"):
        neg.build(ask, events, {}, {}, std)
    fair = {**ask, "term_sheets": [{"unit_price": 345, "payment_days": 30, "index_clause": None}]}
    assert neg.build(fair, events, {}, {}, std)[0] == "send"


def test_it_does_not_settle_early_but_takes_a_final_offer_without_asking(pkg):
    from arena_kit.haggle import economics as eco
    from arena_kit.haggle.agent import Feedback

    neg = _negotiator(pkg)
    std = eco.full_standard(neg.dossier, {})
    events = _thread("open")
    neg.prepare(events, std)
    with pytest.raises(Feedback, match="cannot settle"):
        neg.build({"action": "settle"}, events, {}, {}, std)  # their sheet is far above our best reachable C
    # "final offer, please decide": the model is not even asked; any further message could end the deal
    neg.llm.calls.clear()
    kind, message, meta = neg.step(_thread("final_offer", price=365.0))
    assert kind == "settle" and message is None and not neg.llm.calls


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
        "/api/settings", json={"model": "m-1", "api_key": "secret-key", "prompt": "My prompt text"}
    ).json()
    assert saved["model"] == "m-1" and saved["has_key"] and saved["configured"]
    assert "secret-key" not in json.dumps(saved)  # the key is write-only
    assert saved["prompt"] == "My prompt text" and (tmp_path / "prompts" / "system.md").exists()
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
