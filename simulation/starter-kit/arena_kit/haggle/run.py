"""One negotiation, played start to finish and recorded.

A run is a JSONL file: every event in order (each arena request/response, each model call, each
decision) and `{"meta": ...}` lines with its latest summary. Headers are never recorded, so no key
can end up in a file."""

import hashlib
import json
import os
import threading
import time
import traceback
import uuid
from pathlib import Path

from arena_kit.client import ArenaError
from arena_kit.cost import complete_offer, must_haves_ok, total_cost
from arena_kit.docs import read_document, standard_terms
from arena_kit.play import RemoteTable, closing_move, latest, live_threads, moves_left, standing

from . import economics as eco
from .agent import SYSTEM, Negotiator, Shared
from .context import analysis, claims, document, dossier, injection, names

RESULT_KEYS = ("deal", "supplier_id", "terms", "c_open", "c_deal", "c_best", "score", "end_reason", "must_haves_ok")
LAST_CALL = 2  # rounds each other bidder gets once the cheapest one agreed (RFQ)
# With keep-alive probes the agreed leader is never silent (no timeouts), so the others can get more rounds: after
# `agreed` a supplier answered every *different* lower sheet with its locked agreed sheet and never walked (~100
# messages, P05 bidders up to round 10); the leader's 0.965 on P05 came from a 33-message tender, ours had 7.
# Off by default until experiment E2b (docs/haggle-action-plan.md): HAGGLE_TENDER_KEEPALIVE=1.
LAST_CALL_KEEPALIVE = 6


def tender_keepalive():
    return os.environ.get("HAGGLE_TENDER_KEEPALIVE", "0") in ("1", "true", "yes")


# With slow suppliers even two live threads miss the clock: a bidder whose reply arrived waits behind the other's call
# (2026-10-11 morning: replies up to 55 s against 32 s overnight; both P05 runs got a 409 timeout and an early final
# offer, 0.824 and 0.762 against 0.865). Once the slowest reply passes this, only the cheapest bidder stays live; the
# others' standing offers are still cited to it.
SLOW_REPLY_S = 35
FOCUS = 2  # an RFQ keeps negotiating with this many suppliers after round 1: the arena answers one call per session
# at a time, so a third live thread makes each of the others wait past its 60 s
SKIP_DOCS = ("delivery-schedule", "delivery_schedule")  # attachments the agent does not read: each fetch queues


def code_version():
    """The commit this code runs from, so runs from different clones and experiments can be told apart."""
    import subprocess

    try:
        here = Path(__file__).parent
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=here, capture_output=True, text=True, timeout=3
        )
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=here, capture_output=True, text=True,
                               timeout=3)  # fmt: skip
        return sha.stdout.strip() + ("+changes" if dirty.stdout.strip() else "") or None
    except (OSError, subprocess.SubprocessError):
        return None


def terms_of(threads, sup, sheet_id):
    """The terms of a sheet a supplier sent in this thread, by its id."""
    for m in threads[sup]:
        for x in m.get("term_sheets") or []:
            if x.get("term_sheet_id") == sheet_id:
                return x.get("terms")
    return None


def fetch_needed(table, message):
    """Download the attachments the agent reads (quote PDFs, cost breakdowns, 8D reports) and add their text."""
    for att in message.get("attachments") or []:
        if att.get("attachment_id") and "text" not in att and not any(k in att.get("name", "") for k in SKIP_DOCS):
            att["text"] = read_document(att["name"], table.attachment(att["attachment_id"]))
    return message


class Run:
    # Live Final: stop negotiating this long before the wave's cap (or the slowest round so far plus a margin, if
    # longer) and close on the cheapest standing sheet: a session still open at the cap ends with no deal.
    CLOSE_BEFORE_CAP_S, ROUND_MARGIN_S = 75, 15

    def __init__(
        self, mode, case_id, folder, arenas, pkg, llm, system=None, prompt_source="built-in", deadline=None, case=None
    ):
        self.deadline, self.case_file = deadline, case  # final: a callable giving the wave's cap (time.time())
        self.slowest = 0.0
        self.slowest_reply = 0.0  # the longest a supplier took to answer one of our messages, seconds
        self.id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
        self.path = Path(folder) / f"{self.id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.arenas, self.pkg, self.llm = arenas, pkg, llm
        self.system = system or SYSTEM
        self.events, self.lock = [], threading.Lock()
        self.meta = {
            "run_id": self.id,
            "mode": mode,
            "case_id": case_id,
            "status": "starting",
            "started": time.time(),
            "model": llm.model,
            "prompt_source": prompt_source,
            "code": code_version(),  # which codebase played it: commit, "+changes" if the tree was edited
            "prompt_sha": hashlib.sha256(self.system.encode()).hexdigest()[:10],
        }
        self.prompt_source = prompt_source

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
            # the exact system prompt of this run, so the page shows what this run used (Settings shows the current one)
            self.emit("prompt", source=self.prompt_source, sha=self.meta["prompt_sha"], text=self.system)
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
        table = RemoteTable(client, self.case_file)  # with the case file a crashed final session is resumed
        for wait in (*[10, 20, 30] + [60] * 9, 0):  # the 10 open sessions per key are shared by every clone: ~10 min
            try:
                case, threads = table.open(self.meta["case_id"])
                break
            except ArenaError as exc:
                if exc.status != 429 or "open session" not in str(exc.detail) or not wait:
                    raise
                self.update(status="starting", note=f"waiting for a free session slot: {exc.detail}")
                time.sleep(wait)
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
                fetch_needed(table, m)
        # a resumed final session that had already ended keeps its result; no thread then plays
        self.result, self.negs, self.table = getattr(table, "done", None), {}, table
        self.shared, self.gate, self.close_lock = Shared(), threading.Lock(), threading.Lock()
        self.closing = threading.Event()
        self.last_call = {}  # RFQ: supplier -> rounds left after the cheapest bidder agreed
        self.active, self.dormant = set(live_threads(threads)), set()
        workers = [threading.Thread(target=self._thread, args=(table, case, threads, s)) for s in live_threads(threads)]
        self.ready = threading.Barrier(len(workers)) if len(workers) > 1 else None
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
            ask = (standing(threads[sup])[1] or {}).get("unit_price")
            cands = claims(self.pkg, case, sup, dos, ask)
            letter = document(self.pkg, case["trigger_doc"]) if case.get("trigger_doc") else ""
            alltexts = {d["file"]: document(self.pkg, d["file"], 1500) for d in dos["documents"] if d.get("file")}
            texts = {r["file"]: document(self.pkg, r["file"]) for r in dos["contracts"][:1] if r.get("file")}
            texts.update(
                {d["file"]: document(self.pkg, d["file"], 1500) for d in dos["documents"][:6] if d.get("file")}
            )
            neg = Negotiator(
                case,
                sup,
                self.llm,
                self.pkg,
                injection(case, dos, cands, letter, texts, analysis(self.pkg, case, dos, ask, alltexts)),
                cands,
                lambda rec: self.emit("llm", supplier=sup, **rec),
                self.system,
                self.shared,
            )
            neg.dossier = dos
            self.negs[sup] = neg
            events = threads[sup]
            if self.ready is not None:
                # A tender: every bidder's target is known before anyone opens, so each first sheet starts from the
                # cheapest target any bidder allows. Without this the first thread to decide anchored on its own
                # price (P05: 35.28 to one bidder, 28.93 to the same bidder in another run).
                neg.prepare(events, eco.full_standard(dos, standard_terms(events)))
                neg.target_c()
                try:
                    self.ready.wait(timeout=30)
                except threading.BrokenBarrierError:
                    pass
            while self.result is None and sup in live_threads(threads) and moves_left(case, events) > 0:
                t0 = time.monotonic()
                rnd = sum(m.get("from") == "buyer" for m in events) + 1
                if self._near_cap():
                    self.emit(
                        "decision", supplier=sup, round=rnd, action="cap", rationale="The wave's cap is near: close."
                    )
                    return
                if self.last_call.get(sup, 1) <= 0:
                    return  # its last call is used up: the case closes on the cheapest sheet
                if rnd > 1 and self._out_of_focus(threads, sup):
                    self.dormant.add(sup)
                    self.emit(
                        "decision",
                        supplier=sup,
                        round=rnd,
                        action="dormant",
                        rationale=f"Not among the {self.focus()} best offers: stop so the leaders answer in time.",
                    )
                    return
                action, message, meta = neg.step(events, self._rivals(case, threads, sup), dos)
                self.emit("decision", supplier=sup, round=rnd, action=action, message=message, **meta)
                if action == "settle":
                    self._settled(table, case, threads, sup)
                    message = self._keepalive(case, threads, sup, events)
                    if message is None:
                        return
                    action, meta = "send", {"rationale": "Keep the agreed leader's thread alive while the others bid."}
                    self.emit("decision", supplier=sup, round=rnd, action="keepalive", message=message, **meta)
                with self.gate:  # the arena answers one call per session at a time: queue here, not there
                    if self.result is not None or self.closing.is_set():
                        return
                    sent_at = time.monotonic()
                    try:
                        reply = table.send(sup, message)
                        self.slowest_reply = max(self.slowest_reply, time.monotonic() - sent_at)
                    except ArenaError as exc:
                        if exc.status != 409:
                            raise
                        reply = table.missed(sup, exc)  # late, or the thread or the case has ended
                        if "result" in reply:
                            self.result = reply["result"]
                            return
                    neg.sent()
                    if sup in self.last_call:
                        self.last_call[sup] -= 1
                    tender_final = len(case["suppliers"]) > 1 and reply.get("status") == "final_offer"
                    # a tender's final offer is time-critical: no attachment fetch before deciding (each call queues)
                    events += [{**message, "from": "buyer"}, reply if tender_final else fetch_needed(table, reply)]
                    if tender_final and self._take_final_now(table, case, threads, sup):
                        return
                if "result" in reply:
                    self.result = reply["result"]
                    return
                self.slowest = max(self.slowest, time.monotonic() - t0)
        except Exception as exc:  # one broken thread must not stop the others
            self.emit("error", supplier=sup, error=f"{type(exc).__name__}: {exc}", trace=traceback.format_exc()[-2000:])
        finally:
            self.active.discard(sup)

    def _keepalive(self, case, threads, sup, events):
        """A tender leader that agreed, while the others are on their last call: a sheet one tick under its agreed one
        (a new sheet each time: the same sheet twice made a supplier walk), so its thread never times out. It answers
        with its locked agreed sheet, or agrees to the lower one. None when there is nothing to keep alive."""
        if not tender_keepalive() or self.result is not None or len(case["suppliers"]) < 2:
            return None
        if latest(events).get("status") != "agreed" or moves_left(case, events) <= 1:
            return None
        if not any(n > 0 for s, n in self.last_call.items() if s != sup and s in self.active):
            return None
        _, terms = standing(events)
        if not terms.get("unit_price"):
            return None
        probes = self.__dict__.setdefault("probes", {})
        sent = probes[sup] = probes.get(sup, 0) + 1
        tick = max(0.01, round(terms["unit_price"] * 0.002, 2))
        sheet = complete_offer(case, {**terms, "unit_price": round(terms["unit_price"] - tick * sent, 2)})
        return {
            "subject": f"Re: {latest(events).get('subject', case['title'])}"[:300],
            "body": "Thank you for confirming. While we complete the award decision, could you meet the attached "
            "price on the same terms?\n\nKind regards\nHollerau Pumpenwerke, Purchasing",
            "term_sheets": [{"terms": sheet}],
        }

    def _take_final_now(self, table, case, threads, sup):
        """A tender bidder's final offer, while we still hold the session: accept it at once if it is the cheapest
        standing sheet we know of. The arena answers one call per session at a time, so leaving the gate first let
        a rival's send and two status reads queue ahead of the accept; it arrived 75 s after the final offer, the
        timeout repeated our last sheet, and the bidder walked away (P05, score 0). Only local data, no extra calls."""
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        c_alt = total_cost(case, alt) if alt.get("unit_price") else float("inf")
        ranked = []
        for s in live_threads(threads):
            neg = self.negs.get(s)
            sheet_id, terms = standing(threads[s])
            if neg is None or not sheet_id or not terms.get("unit_price"):
                continue
            std = eco.full_standard(neg.dossier, standard_terms(threads[s]))
            neg.prepare(threads[s], std)
            if must_haves_ok(case, terms, std):
                ranked.append((neg.c(terms, std), s, sheet_id))
        ranked.sort()
        if not ranked or ranked[0][1] != sup or ranked[0][0] >= c_alt:
            return False
        c, _, sheet_id = ranked[0]
        if self.result is not None:  # we hold the gate, so no other thread closes meanwhile
            return True
        self.closing.set()
        self.emit("decision", supplier=sup, round=None, action="accept",
                  rationale=f"Cheapest bidder sent its final offer: accept at once (C(est) {c:,.0f}).")  # fmt: skip
        try:
            self.result = table.close(sup, {"action": {"type": "accept", "term_sheet_id": sheet_id}})
        except ArenaError:
            self.closing.clear()  # the case goes on: the normal close path picks the next sheet
            return False
        return True

    def _near_cap(self):
        cap = self.deadline() if callable(self.deadline) else self.deadline
        return bool(cap) and time.time() > cap - max(self.CLOSE_BEFORE_CAP_S, self.slowest + self.ROUND_MARGIN_S)

    def _out_of_focus(self, threads, sup):
        """In an RFQ with more live threads than `focus()`, is this supplier's best sheet outside the cheapest ones?"""
        live = [s for s in live_threads(threads) if s in self.active and s not in self.dormant]
        if len(live) <= self.focus():
            return False
        ranked = []
        for s in live:
            neg = self.negs.get(s)
            if neg is None or neg.est is None or len(threads[s]) < 3:
                return False  # not every thread has its first reply priced yet
            std = eco.full_standard(neg.dossier, standard_terms(threads[s]))
            ranked.append((neg.their_c(threads[s], std), s))
        ranked.sort()
        return sup not in [s for _, s in ranked[: self.focus()]]

    def focus(self):
        """How many bidders stay live after round 1: one once suppliers answer slowly (B12)."""
        return 1 if self.slowest_reply > SLOW_REPLY_S else FOCUS

    def _settled(self, table, case, threads, sup):
        """A thread is done. Alone, the case closes when every thread is done. In an RFQ, when the cheapest bidder has
        *agreed* (its sheet is locked, and a timeout only repeats that same sheet), every other bidder still talking
        gets LAST_CALL more rounds with the leader's live price cited to it: a descending auction. A leader that only
        sent a final offer is taken at once, since a timeout could push it to walk."""
        if len(case["suppliers"]) < 2:
            return
        with self.close_lock:
            if self.result is not None:
                return
            cands = self._candidates(case, threads)
            if not cands or cands[0][1] != sup:
                return
            others = [s for s in self.active - self.dormant - {sup} if s in live_threads(threads)]
            if latest(threads[sup]).get("status") not in ("agreed", "final_offer") and others:
                return  # local exhaustion is not a reason to terminate the other bidders
            if latest(threads[sup]).get("status") == "agreed" and others and not self.last_call:
                n = LAST_CALL_KEEPALIVE if tender_keepalive() else LAST_CALL
                self.last_call = {s: n for s in others}
                why = f"Cheapest bidder agreed: {n} more rounds for the others against its price."
                self.emit("decision", supplier=sup, round=None, action="last call", rationale=why)
                return
            if any(n > 0 for s, n in self.last_call.items() if s in self.active and s != sup):
                return  # the others are still on their last call; the case closes when they finish
            self.closing.set()  # no other thread starts another call: each one holds the session up to a minute
            with self.gate:
                self.result = self._close(table, case, threads)

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

    def _candidates(self, case, threads):
        """Live threads that still hold a standing sheet, cheapest C(est) first, only those that keep the
        must-haves and beat our alternative."""
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        c_alt = total_cost(case, alt) if alt.get("unit_price") else float("inf")
        try:
            state = self.table.client.session(self.table.session_id)["threads"]
        except ArenaError:
            state = {}
        out = []
        for sup in live_threads(threads):
            if (state.get(sup) or {}).get("closed"):
                continue  # the arena already ended this thread: its sheet is gone
            now_id = (state.get(sup) or {}).get("offer_id")
            if now_id and now_id != standing(threads[sup])[0]:
                self._refresh(sup, threads, now_id)  # a timeout replaced the sheet we know (P05: 422 on accept)
            sheet_id, terms = standing(threads[sup])
            neg = self.negs.get(sup)
            if not sheet_id or neg is None:
                continue
            std = eco.full_standard(neg.dossier, standard_terms(threads[sup]))
            neg.prepare(threads[sup], std)  # a thread closed before its first decision has no estimate yet
            if must_haves_ok(case, terms, std) and (c := neg.c(terms, std)) < c_alt:
                out.append((c, sup, sheet_id))
        return sorted(out)

    def _refresh(self, sup, threads, offer_id):
        """The arena's current sheet of a thread, from its record: while this thread waited for the session (another
        supplier's reply can hold it for a minute), a timeout repeated our last offer and the supplier answered."""
        try:
            t = self.table.client.thread(self.table.session_id, sup)
        except ArenaError:
            return
        # a timeout's answer is kept under "timeouts", not "messages" (P05: agreed 29.24 came back as offer:…-3)
        answers = [m for m in t.get("messages") or [] if m.get("from") != "buyer"]
        answers += [
            {"from": f"arena@{sup}", "status": x.get("status"), "body": x.get("text", ""),
             "term_sheets": [{"term_sheet_id": x["offer_id"], "terms": x.get("terms") or {}}], "attachments": []}
            for x in t.get("timeouts") or [] if x.get("offer_id")
        ]  # fmt: skip
        for m in reversed(answers):
            if any(x.get("term_sheet_id") == offer_id for x in m.get("term_sheets") or []):
                threads[sup].append(m)
                why = f"The arena's standing sheet is now {offer_id}: read it back before accepting."
                self.emit("decision", supplier=sup, round=None, action="refresh", rationale=why)
                return True
        return False

    def _close(self, table, case, threads):
        """Accept the cheapest standing sheet that keeps the must-haves and beats our alternative, else walk away.
        If the arena refuses one (its thread ended meanwhile), try the next."""
        for c, sup, sheet_id in self._candidates(case, threads):
            self.emit(
                "decision",
                supplier=sup,
                round=None,
                action="accept",
                rationale=f"Close on the cheapest standing term sheet that beats the alternative (C(est) {c:,.0f}).",
            )
            try:
                return table.close(sup, {"action": {"type": "accept", "term_sheet_id": sheet_id}})
            except ArenaError as exc:
                if exc.status not in (409, 422):
                    raise
                try:  # the sheet was replaced meanwhile: accept the thread's current sheet if it is the same deal
                    t = self.table.client.thread(self.table.session_id, sup)
                    if not t.get("closed") and t.get("offer_id") and t["offer_id"] != sheet_id:
                        if self._refresh(sup, threads, t["offer_id"]) and standing(threads[sup])[1] == terms_of(
                            threads, sup, sheet_id
                        ):
                            return table.close(sup, {"action": {"type": "accept", "term_sheet_id": t["offer_id"]}})
                except ArenaError:
                    pass
        open_threads = {s: e for s, e in threads.items() if not self._ended(s)}
        if not live_threads(open_threads):  # every thread has ended: nothing left to accept or walk away from
            return self.table.result()
        move = closing_move(case, open_threads)
        self.emit(
            "decision",
            supplier=move["supplier_id"],
            round=None,
            action=move["message"]["action"]["type"],
            rationale="No standing sheet that beats the alternative is left.",
        )
        return table.close(move["supplier_id"], move["message"])

    def _ended(self, sup):
        try:
            return bool(self.table.client.session(self.table.session_id)["threads"][sup].get("closed"))
        except (ArenaError, KeyError):
            return False
