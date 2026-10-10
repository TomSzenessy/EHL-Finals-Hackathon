"""Save every practice case file (hosted or not) as one JSON list, for offline19.py and final_rehearsal.py.
Reads GET /v1/cases?set=practice: no practice session is used.

usage (from simulation/starter-kit): PYTHONPATH=. .venv/bin/python probes/fetch_cases.py cases.json"""

import json
import sys

from arena_kit.cli import load_env
from arena_kit.haggle.arena import Arenas

load_env()
c = Arenas().client("online")
cases = c.cases("practice")
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(cases, f)
print(f"{len(cases)} case files -> {sys.argv[1]}")
