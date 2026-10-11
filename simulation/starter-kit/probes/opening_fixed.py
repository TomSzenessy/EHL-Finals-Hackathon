"""Two authorized opening-exposure probes; default agent unchanged. Local-WAL-001.
Run: PYTHONPATH=. .venv/bin/python probes/opening_fixed.py
"""
import concurrent.futures
import hashlib
import json
import threading
from pathlib import Path
from arena_kit.cli import load_env
from arena_kit.haggle import run as runner
from arena_kit.haggle.agent import Negotiator
from arena_kit.haggle.arena import Arenas
from arena_kit.haggle.__main__ import find_data
from arena_kit.haggle.settings import Settings


def fixed_only(items):
    # Preserve keys, prices and other fields; remove indexed entries without repricing.
    return [item for item in items if not item['terms'].get('index_clause')]


class OpeningFixed(Negotiator):
    def offer_menu(self, events, std, goal, mode):
        items = super().offer_menu(events, std, goal, mode)
        return fixed_only(items) if not any(m.get('from') == 'buyer' for m in events) else items

    def fallback(self, events, std, meta, why, items=None):
        if not any(m.get('from') == 'buyer' for m in events):
            items = fixed_only(items or self.offer_menu(events, std, self.goal_now, 'send'))
            if not items:
                return 'settle', None, {**meta, 'rationale': 'No legal fixed opening; no indexed fallback.'}
        return super().fallback(events, std, meta, why, items)


class TwoSessionArenas(Arenas):
    def __init__(self, facts):
        super().__init__(facts)
        self.lock = threading.Lock()
        self.attempts = 0

    def client(self, mode):
        client = super().client(mode)
        original = client.open_session
        used = False
        def limited(case_id):
            nonlocal used
            with self.lock:
                if used or self.attempts >= 2:
                    raise RuntimeError('Two-session cap; no replacement session permitted')
                used = True
                self.attempts += 1
            return original(case_id)
        client.open_session = limited
        return client


def main():
    load_env()
    settings = Settings()
    pkg = find_data()
    prompt, source = settings.prompt()
    probe_source = Path(__file__).read_text()
    sha = hashlib.sha256(probe_source.encode()).hexdigest()
    arenas = TwoSessionArenas(pkg.facts)
    runner.Negotiator = OpeningFixed
    def play(cid):
        run = runner.Run('online', cid, 'runs', arenas, pkg, settings.llm(), prompt, source)
        run.update(experiment='opening-fixed-two-20261011', arm='round-1-fixed-only',
                   probe_sha=sha, probe_source=probe_source, authorized_session_cap=2, issue='Local-WAL-001')
        run.execute()
        print('RESULT', json.dumps({k: run.meta.get(k) for k in
              ('run_id', 'case_id', 'status', 'score', 'result', 'error')}), flush=True)
        return run.meta
    print('SCREEN', json.dumps({'cap': 2, 'code': runner.code_version(), 'model': settings.llm().model,
          'prompt_sha': hashlib.sha256(prompt.encode()).hexdigest()[:10], 'probe_sha': sha,
          'change': 'round-1 menu filter only; no repricing'}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(play, ['case:P02', 'case:P08']))
    Path('/private/tmp/haggle_opening_fixed_results.json').write_text(json.dumps(results, indent=2))
    print('FINISHED', json.dumps({'open_attempts': arenas.attempts,
          'scores': [r.get('score') for r in results]}), flush=True)


if __name__ == '__main__':
    main()
