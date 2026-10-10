"""Play hosted practice cases with the real agent, in parallel (each case uses one practice session: ask first).

usage (from simulation/starter-kit): PYTHONPATH=. .venv/bin/python probes/batch.py [case:P02 case:P11 ...]
No case ids: every hosted practice case. Prints one JSON line per case and the mean."""

import concurrent.futures
import json
import sys

from arena_kit.cli import load_env
from arena_kit.haggle.__main__ import find_data
from arena_kit.haggle.arena import Arenas
from arena_kit.haggle.run import Run
from arena_kit.haggle.settings import Settings

load_env()
s = Settings()
pkg = find_data()
arenas = Arenas(pkg.facts)
cases, _ = arenas.cases("online")
wanted = set(sys.argv[1:])
cases = [c for c in cases if not wanted or c["case_id"] in wanted]


def play(c):
    text, source = s.prompt()
    r = Run("online", c["case_id"], "runs", arenas, pkg, s.llm(), text, source)
    r.execute()
    out = {k: r.meta.get(k) for k in ("run_id", "case_id", "status", "score", "error")}
    print(json.dumps(out), flush=True)
    return out


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(play, cases))
sc = [r["score"] for r in results if isinstance(r["score"], (float, int))]
print(json.dumps({"mean": sum(sc) / len(sc) if sc else None, "completed": len(sc), "attempted": len(results)}))
