"""Play the real agent (real model) against arena-sim on every practice case file, hosted or not: no arena sessions.
The sim's supplier is a fixed script, so prices mean nothing; what this checks is what kills a final case: a crash,
an invalid term sheet (the sim enforces exactly the negotiable fields and allowed options, else 422), a broken
must-have, a missing deal, a wrong close.

usage (from simulation/starter-kit): PYTHONPATH=. .venv/bin/python probes/offline19.py <cases.json> <out_dir>
          [--llm broken|slow]   (broken: every model call fails; slow: every model call takes 45 s)"""

import concurrent.futures
import json
import sys
import tempfile
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from arena_kit.cli import load_env
from arena_kit.haggle.__main__ import find_data
from arena_kit.haggle.arena import Arenas
from arena_kit.haggle.llm import LLMError
from arena_kit.haggle.run import Run
from arena_kit.haggle.settings import Settings
from arena_kit.sim import Sim, create_app, load_cases

load_env()
cases_json, out = Path(sys.argv[1]), Path(sys.argv[2])
mode = sys.argv[sys.argv.index("--llm") + 1] if "--llm" in sys.argv else "real"
folder = Path(tempfile.mkdtemp())
for c in json.loads(cases_json.read_text()):
    (folder / f"{c['case_id'].split(':')[1]}.json").write_text(json.dumps(c))
pkg = find_data()


class Transport(httpx.BaseTransport):
    def __init__(self):
        sim = Sim(load_cases(folder), pkg.facts, no_clock=True)
        sim_limit = 10_000
        import arena_kit.sim as simmod

        simmod.PRACTICE_LIMIT = sim_limit
        self.app = TestClient(create_app(sim))

    def handle_request(self, request):
        r = self.app.request(request.method, str(request.url), headers=dict(request.headers), content=request.read())
        return httpx.Response(r.status_code, headers=r.headers, content=r.content, request=request)


arenas = Arenas(pkg.facts, transport=Transport())
arenas.client("offline").http.close()  # register the sim key once, before the threads race for it
settings = Settings()
real = settings.llm()


class FakeLLM:
    model = f"fake-{mode}"
    timeout = real.timeout

    def chat(self, system, messages, timeout=None, record=None):
        if mode == "slow":
            time.sleep(min(45, timeout or 45))
        raise LLMError(f"{mode} model (test)")


llm = real if mode == "real" else FakeLLM()
ids = sorted(load_cases(folder))
out.mkdir(parents=True, exist_ok=True)


def play(cid):
    text, source = settings.prompt()
    r = Run("offline", cid, str(out), arenas, pkg, llm, text, source)
    r.execute()
    m = r.meta
    res = m.get("result") or {}
    return {"case": cid, "status": m.get("status"), "error": m.get("error"), "deal": m.get("deal"),
            "must_haves_ok": res.get("must_haves_ok"), "end": res.get("end_reason"), "score": m.get("score"),
            "terms": res.get("terms")}


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    for row in pool.map(play, ids):
        print(json.dumps({k: v for k, v in row.items() if k != "terms"}), flush=True)
