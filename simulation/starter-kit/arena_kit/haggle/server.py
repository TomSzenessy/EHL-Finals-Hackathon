"""The page and its JSON: start a run, follow it, read every request and every supplier record."""

import json
import os
import re
import threading
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from arena_kit.client import ArenaError
from arena_kit.data import DataPackage

from .agent import SYSTEM
from .arena import MODES, Arenas
from .context import SUPPLIER_ID, dossier, names
from .llm import LLM, LLMError
from .run import RESULT_KEYS, Run
from .settings import Settings, sha

STATIC = Path(__file__).parent / "static"
RUN_ID = re.compile(r"^[\w-]{1,60}$")


def runs_folder():
    return Path(os.environ.get("ARENA_RUNS", "runs"))


UNFINISHED = ("starting", "running")


CACHE = Path(".haggle_cache/reconciled.json")  # git-ignored: this machine's view, never written into runs/


def _cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def reconcile(meta, arenas):
    """A run file still says "running" but no process plays it (the server stopped mid-way). Ask the arena how the
    session ended. The answer goes to a local, git-ignored cache, never into the run file: run files travel through
    git and are only written by the run that created them, so pulls never conflict."""
    if meta["run_id"] in (cached := _cache()):
        return cached[meta["run_id"]]
    if not meta.get("session_id") or meta.get("mode") not in ("online", "final"):
        return None
    client = arenas.client(meta["mode"])
    try:
        state = client.session(meta["session_id"])
    except ArenaError:
        return None
    finally:
        client.http.close()
    if state.get("status") != "ended":
        return None
    result = state.get("result") or {"deal": False, "end_reason": state.get("end_reason")}
    fixed = {
        **meta,
        "status": "done",
        "reconciled": "the run stopped mid-way; this is the arena's record of how the session ended",
        "result": {k: result.get(k) for k in RESULT_KEYS if k in result} | {"end_reason": state.get("end_reason")},
        "score": result.get("score"),
        "deal": result.get("deal"),
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({**_cache(), meta["run_id"]: fixed}, default=str), encoding="utf-8")
    return fixed


CASE_RESULT = ("status", "score", "saved_eur", "rounds", "end_reason")


def read_run(path):
    """(meta, events) of a recorded run."""
    meta, events = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if "meta" in row:
            meta = row["meta"]
        else:
            events.append(row)
    return meta, events


def create_app(
    pkg: DataPackage | None = None,
    arenas: Arenas | None = None,
    llm: LLM | None = None,
    folder=None,
    settings: Settings | None = None,
):
    arenas = arenas or Arenas(pkg.facts if pkg else {})
    settings = settings or Settings()
    current = lambda: llm or settings.llm()  # noqa: E731  (an explicit llm, used by tests, wins over the settings)
    live: dict[str, Run] = {}
    lock = threading.Lock()
    app = FastAPI(title="haggle", docs_url=None, redoc_url=None, openapi_url=None)
    where = lambda: Path(folder) if folder else runs_folder()  # noqa: E731

    @app.exception_handler(ArenaError)
    async def arena_error(_, exc: ArenaError):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)

    @app.exception_handler(httpx.TransportError)
    async def unreachable(_, exc: httpx.TransportError):
        return JSONResponse({"detail": f"cannot reach the arena ({exc})"}, status_code=502)

    def check_mode(mode):
        if mode not in MODES:
            raise ArenaError(422, "mode must be online or offline")
        return mode

    @app.get("/api/config")
    def config():
        return {
            "prompt_sha": sha(settings.prompt()[0]),  # the prompt a new run would use
            "model": current().model,
            "llm_configured": current().configured,
            "data": pkg is not None,
            "online_key": bool(os.environ.get("ARENA_API_KEY")),
        }

    @app.get("/api/cases")
    def cases(mode: str = "online"):
        found, me = arenas.cases(check_mode(mode))
        return {
            "cases": [
                {
                    "case_id": c["case_id"],
                    "title": c["title"],
                    "type": c["type"],
                    "suppliers": names(pkg, c["suppliers"]),
                    "negotiable": c["negotiable"],
                    "round_limit": c.get("round_limit", 10),
                }
                for c in found
            ],
            "me": me,
        }

    @app.post("/api/runs")
    def start(body: dict):
        model = current()
        if not model.configured:
            raise ArenaError(400, "Set the model and its API key on the Settings tab (or in .env).")
        text, source = settings.prompt()
        run = Run(check_mode(body.get("mode")), body.get("case_id", ""), where(), arenas, pkg, model, text, source)
        with lock:
            live[run.id] = run
        threading.Thread(target=run.execute, daemon=True).start()
        return run.meta

    checked = set()  # stale runs already asked about, once per server start

    def metas():
        out = {}
        for path in sorted(where().glob("*.jsonl")):
            try:
                meta, _ = read_run(path)
            except (ValueError, OSError):
                continue
            if meta:
                if meta.get("status") in UNFINISHED and meta["run_id"] not in live:
                    if meta["run_id"] in (cached := _cache()):
                        meta = cached[meta["run_id"]]
                    elif meta["run_id"] not in checked:  # ask the arena once per server start
                        checked.add(meta["run_id"])
                        try:
                            meta = reconcile(meta, arenas) or meta
                        except Exception:  # noqa: BLE001 - no key, no network: show it as stopped
                            pass
                    if meta.get("status") in UNFINISHED:
                        meta = {**meta, "status": "stopped"}
                out[meta["run_id"]] = meta
        for run in live.values():
            out[run.id] = run.meta
        return sorted(out.values(), key=lambda m: m["started"], reverse=True)

    @app.get("/api/runs")
    def runs():
        return metas()

    @app.get("/api/runs/{rid}")
    def run(rid: str, after: int = 0):
        if not RUN_ID.match(rid):
            raise ArenaError(422, "not a run id")
        if rid in live:
            with live[rid].lock:
                return {
                    "meta": dict(live[rid].meta),
                    "total": len(live[rid].events),
                    "events": live[rid].events[after:],
                }
        path = where() / f"{rid}.jsonl"
        if not path.exists():
            raise ArenaError(404, "no such run")
        meta, events = read_run(path)
        if meta.get("status") in UNFINISHED:  # no process plays it any more (see `metas`)
            meta = _cache().get(rid) or {**meta, "status": "stopped"}
        return {"meta": meta, "total": len(events), "events": events[after:]}

    @app.get("/api/settings")
    def get_settings():
        text, source = settings.prompt()
        return {
            **settings.view(),
            "prompt": text,
            "prompt_source": source,
            "prompt_sha": sha(text),
            "default_prompt": SYSTEM,
            "prompt_is_default": text == SYSTEM,
        }

    @app.put("/api/settings")
    def put_settings(body: dict):
        settings.update(body)
        if body.get("reset_prompt"):
            settings.reset_prompt()
        elif isinstance(body.get("prompt"), str) and body["prompt"].strip():
            settings.save_prompt(body["prompt"])
        return get_settings()

    @app.post("/api/settings/test")
    def test_model():
        try:
            reply = settings.llm().chat(
                "You are a connection test.", [{"role": "user", "content": "Reply with: OK"}], timeout=25
            )
        except LLMError as exc:
            return {"ok": False, "detail": str(exc)}
        return {"ok": True, "detail": reply.strip()[:80]}

    @app.get("/api/team")
    def team(mode: str = "online"):
        """What the arena says about us: team, quota, best scores, practice board, every session, downloads."""
        client, out = arenas.client(check_mode(mode)), {}

        def grab(name, call):
            try:
                out[name] = call()
            except Exception as exc:  # one failing endpoint must not hide the others
                out[name] = {"error": str(getattr(exc, "detail", exc))[:300]}

        grab("me", client.me)
        grab("leaderboard", lambda: client.leaderboard("practice"))
        grab("sessions", lambda: client.sessions("practice"))
        grab("sandbox_sessions", lambda: client.sessions("sandbox"))
        grab("downloads", client.downloads)
        base = str(client.http.base_url).removesuffix("/v1/")
        grab("health", lambda: client.http.get(f"{base}/health").json())
        client.http.close()
        out["recorded"] = {m["session_id"]: m["run_id"] for m in metas() if m.get("session_id")}
        return out

    @app.get("/api/compare")
    def compare(mode: str = "online"):
        """Every team's result per final case, side by side: for people, never for the agent."""
        client = arenas.client(check_mode(mode))
        try:
            board = client.results()
            mine = None
            try:
                mine = client.me().get("team_name")
            except Exception:  # the comparison still works without knowing which column is ours
                pass
            teams, cases = [], {}
            for t in board.get("teams", []):
                name = t["team_name"]
                teams.append({k: t.get(k) for k in ("team_name", "rank", "total", "deals", "rounds", "saved_eur")})
                try:
                    waves = client.team_results(name).get("waves", [])
                except ArenaError:
                    continue
                for w in waves:
                    for c in w.get("cases", []):
                        row = cases.setdefault(
                            c["case_id"],
                            {"case_id": c["case_id"], "title": c.get("title"), "type": c.get("type"),
                             "wave": w.get("n"), "theme": w.get("theme"), "teams": {}},
                        )  # fmt: skip
                        row["teams"][name] = {k: c.get(k) for k in CASE_RESULT}
        finally:
            client.http.close()
        order = sorted(cases.values(), key=lambda r: (r["wave"] or 0, r["case_id"]))
        return {"me": mine, "teams": teams, "cases": order}

    @app.get("/api/suppliers")
    def suppliers():
        """Every supplier met in any run, newest run first, with those runs."""
        out = {}
        for m in metas():
            for s in m.get("suppliers", []):
                row = out.setdefault(s["id"], {**s, "runs": []})
                row["runs"].append(
                    {k: m.get(k) for k in ("run_id", "mode", "case_id", "title", "status", "deal", "score", "started")}
                )
        return list(out.values())

    @app.get("/api/suppliers/{sup}")
    def supplier(sup: str):
        if not SUPPLIER_ID.match(sup):
            raise ArenaError(422, "not a supplier id")
        if pkg is None:
            raise ArenaError(404, "no data package: set ARENA_DATA to the unpacked package folder")
        return dossier(pkg, sup)

    @app.get("/api/document")
    def doc(path: str):
        if pkg is None:
            raise ArenaError(404, "no data package")
        try:
            return {"path": path, "text": pkg.document(path)}
        except (OSError, ValueError):
            raise ArenaError(404, "no such document") from None

    app.mount("/", StaticFiles(directory=STATIC, html=True), name="page")
    return app
