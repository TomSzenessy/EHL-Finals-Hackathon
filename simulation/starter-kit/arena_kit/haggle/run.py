"""One negotiation, played start to finish and recorded.

A run is a JSONL file: every event in order (each arena request/response, each model call, each
decision) and `{"meta": ...}` lines with its latest summary. Headers are never recorded, so no key
can end up in a file."""

import json
import threading
import time
import traceback
import uuid
from pathlib import Path

from arena_kit.client import ArenaError
from arena_kit.play import RemoteTable, closing_move, fetch_documents, live_threads, moves_left, standing

from .agent import Negotiator
from .context import claims, document, dossier, injection, names

RESULT_KEYS = ("deal", "supplier_id", "terms", "c_open", "c_deal", "c_best", "score", "end_reason", "must_haves_ok")


class Run:
    def __init__(self, mode, case_id, folder, arenas, pkg, llm):
        self.id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
        self.path = Path(folder) / f"{self.id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.arenas, self.pkg, self.llm = arenas, pkg, llm
        self.events, self.lock = [], threading.Lock()
        self.meta = {
            "run_id": self.id,
            "mode": mode,
            "case_id": case_id,
            "status": "starting",
            "started": time.time(),
            "model": llm.model,
        }

    # -- recording -----------------------------------------------------------------------------
    def emit(self, kind, **data):
        with self.lock:
            event = {"i": len(self.events), "at": time.time(), "kind": kind, **data}
            self.events.append(event)
            self._write(event)
        return event

    def update(self, **fields):
        with self.lock:
            self.meta.update(fields)
            self._write({"meta": self.meta})

    def _write(self, line):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")

    def hooks(self, client):
        def on_request(request):
            request.extensions["t0"] = time.monotonic()

        def on_response(response):
            request = response.request
            response.read()
            try:
                body = response.json()
            except ValueError:
                body = {"bytes": len(response.content), "content_type": response.headers.get("content-type")}
            try:
                sent = json.loads(request.content) if request.content else None
            except ValueError:
                sent = None
            self.emit(
                "http",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                ms=round((time.monotonic() - request.extensions.get("t0", time.monotonic())) * 1000),
                request=sent,
                response=body,
            )

        client.http.event_hooks = {"request": [on_request], "response": [on_response]}

    # -- the negotiation -----------------------------------------------------------------------
    def execute(self):
        client = None
        try:
            client = self.arenas.client(self.meta["mode"])
            self.hooks(client)
            self._play(client)
            self.update(status="done", finished=time.time())
        except Exception as exc:  # the page shows what stopped it
            detail = exc.detail if isinstance(exc, ArenaError) else str(exc)
            self.emit("error", error=f"{type(exc).__name__}: {detail}", trace=traceback.format_exc()[-2000:])
            self.update(status="error", error=str(detail)[:300], finished=time.time())
        finally:
            if client:
                client.http.close()

    def _play(self, client):
        table = RemoteTable(client)
        case, threads = table.open(self.meta["case_id"])
        self.update(
            session_id=table.session_id,
            title=case["title"],
            type=case["type"],
            status="running",
            suppliers=names(self.pkg, case["suppliers"]),
            round_limit=case.get("round_limit", 10),
        )
        for events in threads.values():
            for m in events:
                fetch_documents(table, m)
        self.result = None
        workers = [threading.Thread(target=self._thread, args=(table, case, threads, s)) for s in live_threads(threads)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        if self.result is None and live_threads(threads):
            self.result = self._close(table, case, threads)
        state = client.session(table.session_id)  # after the end: the score and the supplier's reasons
        result = self.result or state.get("result") or {}
        try:
            client.backoffice(table.session_id)
        except ArenaError:
            pass
        self.update(
            result={k: result.get(k) for k in RESULT_KEYS if k in result},
            score=result.get("score"),
            deal=result.get("deal"),
        )

    def _thread(self, table, case, threads, sup):
        try:
            dos = dossier(self.pkg, sup, case)
            cands = claims(self.pkg, case, sup, dos)
            letter = document(self.pkg, case["trigger_doc"]) if case.get("trigger_doc") else ""
            texts = {r["file"]: document(self.pkg, r["file"]) for r in dos["contracts"][:1] if r.get("file")}
            texts.update(
                {d["file"]: document(self.pkg, d["file"], 1500) for d in dos["documents"][:6] if d.get("file")}
            )
            neg = Negotiator(
                case,
                sup,
                self.llm,
                self.pkg,
                injection(case, dos, cands, letter, texts),
                cands,
                lambda rec: self.emit("llm", supplier=sup, **rec),
            )
            events = threads[sup]
            while self.result is None and sup in live_threads(threads) and moves_left(case, events) > 0:
                rnd = sum(m.get("from") == "buyer" for m in events) + 1
                action, message, meta = neg.step(events, self._rivals(case, threads, sup))
                self.emit("decision", supplier=sup, round=rnd, action=action, message=message, **meta)
                if action == "settle":
                    return
                try:
                    reply = table.send(sup, message)
                except ArenaError as exc:
                    if exc.status != 409:
                        raise
                    reply = table.missed(sup, exc)  # late, or the thread or the case has ended
                    if "result" in reply:
                        self.result = reply["result"]
                        return
                neg.sent()
                events += [{**message, "from": "buyer"}, fetch_documents(table, reply)]
                if "result" in reply:
                    self.result = reply["result"]
                    return
        except Exception as exc:  # one broken thread must not stop the others
            self.emit("error", supplier=sup, error=f"{type(exc).__name__}: {exc}", trace=traceback.format_exc()[-2000:])

    @staticmethod
    def _rivals(case, threads, sup):
        """Other suppliers' standing offers for the same part (an RFQ): citable to this supplier."""
        out = {}
        for other in live_threads(threads):
            if other != sup:
                sheet_id, terms = standing(threads[other])
                if sheet_id and terms.get("unit_price"):
                    out[sheet_id] = terms["unit_price"]
        return out

    def _close(self, table, case, threads):
        """Accept the cheapest standing sheet that keeps the must-haves and beats our alternative, else walk away."""
        move = closing_move(case, threads)
        self.emit(
            "decision",
            supplier=move["supplier_id"],
            round=None,
            action=move["message"]["action"]["type"],
            rationale="Rounds used: close on the cheapest standing term sheet that beats the alternative.",
        )
        for attempt in range(2):
            try:
                return table.close(move["supplier_id"], move["message"])
            except ArenaError as exc:
                if exc.status != 409 or attempt:
                    raise  # a late accept counts as a timeout; the second try has a fresh clock
