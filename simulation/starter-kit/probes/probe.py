"""Scripted probe: play one hosted practice case with a hand-written policy and record it like a run.

usage (from simulation/starter-kit):  .venv/bin/python probes/probe.py probes/policies/<policy.py> [experiment-name]

A policy file defines  CASE = "case:P08"  and  def move(st) -> dict | None.
`st` has: case, supplier (id), round (1..), history [(our_message, their_reply)], opening (their round-0 message),
last (their latest reply message). Return {"accept": "<offer id>"} to close, {"walk": True} to walk away,
or a message {"subject", "body", "term_sheets": [{"terms": {...}}], "refs": [...]}. None accepts their standing sheet.
The run file lands in runs/ with model "scripted" so the page and the analysis scripts read it like any other run."""

import importlib.util
import json
import sys
import time
import uuid
from pathlib import Path

from arena_kit.cli import load_env

load_env()
from arena_kit.client import ArenaError  # noqa: E402
from arena_kit.haggle.arena import Arenas  # noqa: E402

policy_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("policy", policy_path)
pol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pol)
experiment = sys.argv[2] if len(sys.argv) > 2 else policy_path.stem

run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
path = Path("runs") / f"{run_id}.jsonl"
events = []


def write(line):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")


meta = {"run_id": run_id, "mode": "online", "case_id": pol.CASE, "status": "running", "started": time.time(),
        "model": "scripted", "prompt_source": f"probe:{policy_path.name}", "code": "probe", "experiment": experiment}


def emit(method, p, request, response, status=200):
    ev = {"i": len(events), "at": time.time(), "kind": "http", "method": method, "path": p, "status": status,
          "request": request, "response": response}
    events.append(ev)
    write(ev)


c = Arenas().client("online")
write({"i": 0, "at": time.time(), "kind": "prompt", "source": f"probe:{policy_path.name}", "sha": "probe",
       "text": policy_path.read_text()})
s = c.open_session(pol.CASE)
emit("POST", "/v1/sessions", {"case_id": pol.CASE}, s)
sid = s["session_id"]
meta["session_id"] = sid
write({"meta": meta})
case = s["case"]
sup = case["suppliers"][0]
opening = s["threads"][sup][-1]
st = {"case": case, "supplier": sup, "round": 0, "history": [], "opening": opening, "last": opening}


def show(m):
    sh = [x["terms"] for x in m.get("term_sheets") or []]
    print(f"  THEM status={m.get('status')} sheets={json.dumps(sh)} claims={m.get('claim_results')}")
    print("  " + (m.get("body") or "").replace("\n", " | ")[:3500])


print(run_id, pol.CASE, sid)
show(opening)
result = None
while True:
    st["round"] += 1
    mv = pol.move(st)
    while mv and mv.get("free_tests"):  # messages the arena should refuse with a 422: no round is used
        st.setdefault("free", [])
        for name, t in mv["free_tests"]:
            try:
                r = c.send_message(sid, sup, t)
                st["free"].append((name, "ACCEPTED", r))
                emit("POST", f"/v1/sessions/{sid}/threads/{sup}/messages", {"message": t, "free_test": name}, r)
                st["history"].append((t, r))
                st["last"] = r
                print(f"FREE {name}: ACCEPTED status={r.get('status')} sheets={[x['terms'] for x in r.get('term_sheets') or []]}")
                show(r)
            except ArenaError as e:
                st["free"].append((name, e.status, e.detail))
                emit("POST", f"/v1/sessions/{sid}/threads/{sup}/messages", {"message": t, "free_test": name},
                     {"error": e.status, "detail": e.detail}, status=e.status)
                print(f"FREE {name}: HTTP {e.status} {e.detail}")
        mv = pol.move(st)
    last = st["last"]
    if mv is None or mv.get("accept"):
        oid = (mv or {}).get("accept") or (last.get("term_sheets") or [{}])[0].get("term_sheet_id")
        print(f"r{st['round']} ACCEPT {oid}")
        r = c.accept(sid, oid)
        emit("POST", f"/v1/sessions/{sid}/accept", {"offer_id": oid}, r)
        break
    if mv.get("walk"):
        r = c.walk_away(sid)
        emit("POST", f"/v1/sessions/{sid}/walk_away", None, r)
        break
    print(f"r{st['round']} US sheets={json.dumps([x['terms'] for x in mv.get('term_sheets') or []])}")
    print("  " + mv.get("body", "").replace("\n", " | ")[:900])
    r = c.send_message(sid, sup, mv)
    emit("POST", f"/v1/sessions/{sid}/threads/{sup}/messages", {"message": mv}, r)
    st["history"].append((mv, r))
    st["last"] = r
    show(r)
    if r.get("status") in ("walked_away", "no_bid"):
        break
fin = c.session(sid)
emit("GET", f"/v1/sessions/{sid}", None, fin)
res = fin.get("result") or {}
meta.update(status="done", score=res.get("score"), deal=res.get("deal"), finished=time.time(),
            rounds=fin.get("rounds"), result={k: res.get(k) for k in ("deal", "supplier_id", "terms", "c_open", "c_deal", "c_best", "score", "end_reason", "must_haves_ok")})
write({"meta": meta})
print("RESULT score", res.get("score"), "deal", res.get("c_deal"), "best", res.get("c_best"), "terms", json.dumps(res.get("terms")))
print("breakdown", json.dumps({k: round(v) for k, v in (res.get("cost_breakdown") or {}).items() if v}))
