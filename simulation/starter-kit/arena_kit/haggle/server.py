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

from .arena import MODES, Arenas
from .context import SUPPLIER_ID, dossier, names
from .llm import LLM
from .run import Run

STATIC = Path(__file__).parent / "static"
RUN_ID = re.compile(r"^[\w-]{1,60}$")


def runs_folder():
    return Path(os.environ.get("ARENA_RUNS", "runs"))


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


def create_app(pkg: DataPackage | None = None, arenas: Arenas | None = None, llm: LLM | None = None, folder=None):
    arenas = arenas or Arenas(pkg.facts if pkg else {})
    llm = llm or LLM()
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
            "model": llm.model,
            "llm_configured": llm.configured,
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
        if not llm.configured:
            raise ArenaError(400, "Set LLM_MODEL and LLM_API_KEY in .env, then restart.")
        run = Run(check_mode(body.get("mode")), body.get("case_id", ""), where(), arenas, pkg, llm)
        with lock:
            live[run.id] = run
        threading.Thread(target=run.execute, daemon=True).start()
        return run.meta

    def metas():
        out = {}
        for path in sorted(where().glob("*.jsonl")):
            try:
                meta, _ = read_run(path)
            except (ValueError, OSError):
                continue
            if meta:
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
        return {"meta": meta, "total": len(events), "events": events[after:]}

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
