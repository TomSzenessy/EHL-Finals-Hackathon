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
