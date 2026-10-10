"""Rehearse the Live Final offline: our real runner (`final.play_waves`) against arena-sim, 5 waves of 10 hidden-style
cases (copies of the practice case files under new IDs), each wave with its own cap. No arena session is used.

usage (from simulation/starter-kit):
  PYTHONPATH=. .venv/bin/python probes/final_rehearsal.py <cases.json> <out_dir> [--llm real|broken|slow] [--cap S]
--llm broken: every model call fails (the fallback plays); slow: every call takes until the 40 s budget runs out.
--cap: seconds each wave stays open (the final: 480). Prints one line per case and a summary; exits 1 on any case
that did not end in a deal or its alternative."""

import json
import sys
import tempfile
import threading
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

import arena_kit.sim as simmod
from arena_kit.cli import load_env
from arena_kit.haggle.__main__ import find_data
from arena_kit.haggle.arena import Arenas
from arena_kit.haggle.final import play_waves
from arena_kit.haggle.llm import LLMError
from arena_kit.haggle.settings import Settings
from arena_kit.sim import Sim, create_app, load_cases

load_env()
args = sys.argv[1:]
cases_json, out = Path(args[0]), Path(args[1])
mode = args[args.index("--llm") + 1] if "--llm" in args else "broken"
cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 240.0
templates = json.loads(cases_json.read_text())
folder = Path(tempfile.mkdtemp())
waves = {}
for n in range(50):  # 5 waves x 10 cases, cycling through the practice case files
    c = dict(templates[n % len(templates)])
    c["case_id"] = f"case:F{n + 1:02d}"
    (folder / f"F{n + 1:02d}.json").write_text(json.dumps(c))
    waves[c["case_id"]] = n // 10 + 1
pkg = find_data()
simmod.PRACTICE_LIMIT = 10_000


class Transport(httpx.BaseTransport):
    def __init__(self):
        self.app = TestClient(create_app(Sim(load_cases(folder), pkg.facts, no_clock=True)))

    def handle_request(self, request):
        r = self.app.request(request.method, str(request.url), headers=dict(request.headers), content=request.read())
        return httpx.Response(r.status_code, headers=r.headers, content=r.content, request=request)


start = time.time()


def wave_state(w):
    """Wave w opens at (w-1) * (cap + 20) s after the start and stays open for `cap` seconds."""
    opens = start + (w - 1) * (cap + 20)
    now = time.time()
    if now < opens:
        return None
    left = opens + cap - now
    return max(0.0, left)


class FinalArenas(Arenas):
    def client(self, m):
        c = super().client("offline")
        if m == "final":
            practice = c.cases

            def cases(set_="practice"):
                if set_ != "final":
                    return practice(set_)
                out_ = []
                for x in practice("practice"):
                    w = waves.get(x["case_id"])
                    left = wave_state(w) if w else None
                    if left is not None:
                        out_.append({**x, "wave": w, "theme": f"wave {w}", "open": left > 0, "seconds_left": left})
                return out_

            c.cases = cases
        return c


arenas = FinalArenas(pkg.facts, transport=Transport())
arenas.client("offline").http.close()  # register the sim key once
settings = Settings()
real = settings.llm()


class FakeLLM:
    model = f"fake-{mode}"
    timeout = real.timeout

    def chat(self, system, messages, timeout=None, record=None):
        if mode == "slow":
            time.sleep(timeout or 40)
        raise LLMError(f"{mode} model (rehearsal)")


llm = real if mode == "real" else FakeLLM()
system, source = settings.prompt()
t0 = time.time()
runs = play_waves(arenas, pkg, llm, system, source, out, waves=5, poll=1.0)
bad = 0
for r in sorted(runs, key=lambda r: r.meta["case_id"]):
    m = r.meta
    ok = m.get("status") == "done" and (m.get("deal") or (m.get("result") or {}).get("end_reason") != "wave_cap")
    bad += not ok
    print(m["case_id"], f"wave {waves[m['case_id']]}", m.get("status"), "deal" if m.get("deal") else "no deal",
          None if m.get("score") is None else round(m["score"], 3), m.get("error") or "")
print(json.dumps({"cases": len(runs), "deals": sum(bool(r.meta.get("deal")) for r in runs), "not_ok": bad,
                  "minutes": round((time.time() - t0) / 60, 1), "threads_alive": threading.active_count()}))
sys.exit(1 if bad or len(runs) != 50 else 0)
