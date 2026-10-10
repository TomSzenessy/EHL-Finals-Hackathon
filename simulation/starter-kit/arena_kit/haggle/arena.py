"""The two places a negotiation can happen: the hosted arena (online) or arena-sim in this process
(offline: a scripted supplier, no key, no quota)."""

import os

import httpx
from fastapi.testclient import TestClient

from arena_kit.client import ArenaClient, ArenaError
from arena_kit.play import hosted
from arena_kit.sim import Sim, create_app, load_cases

LOCAL_URL = "http://local.arena"
MODES = ("online", "offline")


class _InProcess(httpx.BaseTransport):
    def __init__(self, facts):
        self.app = TestClient(create_app(Sim(load_cases(), facts, no_clock=True)))

    def handle_request(self, request):
        r = self.app.request(request.method, str(request.url), headers=dict(request.headers), content=request.read())
        return httpx.Response(r.status_code, headers=r.headers, content=r.content, request=request)


class Arenas:
    """Hands out one ArenaClient per run. The offline simulator is shared and keeps its sessions."""

    def __init__(self, facts=None, transport=None):
        self._offline = transport or _InProcess(facts or {})
        self._offline_key = None

    def client(self, mode):
        if mode == "offline":
            c = ArenaClient(LOCAL_URL, transport=self._offline)
            c.http.headers.pop("X-API-Key", None)
            if self._offline_key is None:
                self._offline_key = c.register("Haggle", "sim")["api_key"]
            c.http.headers["X-API-Key"] = self._offline_key
            return c
        if mode != "online":
            raise ArenaError(422, "mode must be online or offline")
        if not os.environ.get("ARENA_API_KEY"):
            raise ArenaError(400, "Online needs ARENA_API_KEY in .env (your team's key from the arena).")
        return ArenaClient(os.environ.get("ARENA_URL", "https://arena.tacto.ai"))

    def cases(self, mode):
        """The cases to pick from: the 10 hosted practice cases online, the simulator's examples offline."""
        c = self.client(mode)
        try:
            return hosted(c.cases("practice")), (c.me() if mode == "online" else None)
        finally:
            c.http.close()
