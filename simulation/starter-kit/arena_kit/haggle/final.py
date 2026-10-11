"""arena-haggle-final: the Live Final with the haggling agent.

Start it before the first wave and leave it running until the last wave has closed. It polls the final's case list
(nothing else: the leaderboard, results, screen and event feed are off limits during the final), opens each case of a
running wave once, plays all of a wave's cases in parallel (the arena allows 10 open sessions per key) and closes
every case on its cheapest standing sheet shortly before the wave's cap. Every case is recorded like a practice run,
so the page shows it. After a crash, start it again: a case already opened is picked up from the arena."""

import argparse
import logging
import threading
import time
from pathlib import Path

from arena_kit.cli import load_env
from arena_kit.client import ArenaError

from .__main__ import find_data
from .arena import Arenas
from .run import Run
from .settings import Settings

log = logging.getLogger("haggle.final")
MAX_OPEN = 10  # open sessions per key


def play_waves(arenas, pkg, llm, system, source, folder, waves=5, poll=4.0):
    client = arenas.client("final")
    started, closed, caps, runs = set(), set(), {}, []
    slots = threading.Semaphore(MAX_OPEN)

    def one(case):
        with slots:
            run = Run("final", case["case_id"], folder, arenas, pkg, llm, system, source,
                      deadline=lambda w=case["wave"]: caps.get(w), case=case)  # fmt: skip
            runs.append(run)
            log.warning("%s start (wave %s)", case["case_id"], case["wave"])
            run.execute()
            log.warning("%s %s score=%s deal=%s", case["case_id"], run.meta.get("status"), run.meta.get("score"),
                        run.meta.get("deal"))  # fmt: skip

    workers = []
    while len(closed) < waves or any(w.is_alive() for w in workers):
        try:
            cases = client.cases("final")
        except ArenaError as e:
            if e.status != 403:  # 403: no wave has started yet
                log.warning("case list: %s", e.detail)
            cases = []
        except Exception as e:  # noqa: BLE001 - the venue network drops; keep polling
            log.warning("case list: %s", e)
            cases = []
        for case in cases:
            if not case.get("open"):
                closed.add(case["wave"])
                continue
            if case.get("seconds_left") is not None:  # each wave has its own cap; follow an extension
                caps[case["wave"]] = time.time() + case["seconds_left"]
            if case["case_id"] not in started and case.get("seconds_left"):
                started.add(case["case_id"])
                w = threading.Thread(target=one, args=(case,), daemon=True)
                w.start()
                workers.append(w)
        time.sleep(poll)
    client.http.close()
    return runs


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arena-haggle-final", description=__doc__)
    ap.add_argument("--waves", type=int, default=5, help="stop after this many waves have closed")
    ap.add_argument("--runs", default="runs", help="folder for the run records (the page reads it)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
    load_env()
    pkg = find_data()
    settings = Settings()
    llm = settings.llm()
    if not llm.configured:
        raise SystemExit("Set the model and its key first (Settings tab or .env).")
    system, source = settings.prompt()
    log.warning("haggle final: model %s, prompt %s, data %s, release %s", llm.model, source, pkg.root if pkg else None,
                getattr(pkg, "release", None))  # fmt: skip
    runs = play_waves(Arenas(pkg.facts if pkg else {}), pkg, llm, system, source, Path(a.runs), a.waves)
    for r in runs:
        print(r.meta.get("case_id"), r.meta.get("status"), r.meta.get("score"))


if __name__ == "__main__":
    main()
