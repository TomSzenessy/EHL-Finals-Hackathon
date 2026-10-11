# Haggle

<!-- covers: simulation/starter-kit/** simulation/data/** simulation/brief/** -->

An agent that haggles a supplier's price down over every round a case allows, using verified claims and a
friendly tone, and a page to inspect everything it did. Built on the Tacto Negotiation Arena kit
(`brief/` has the API and the rules, `data/` the data package, `starter-kit/` the code).

```bash
cd simulation/starter-kit
cp .env.example .env          # ARENA_API_KEY, ARENA_DATA=../data, LLM_MODEL, LLM_API_KEY
uv sync --extra ui
uv run --extra ui arena-haggle   # http://127.0.0.1:8100
```

## Run it on a new machine

The supplier dataset is part of the repo (`simulation/data`), so you only add your keys.

1. Install [uv](https://docs.astral.sh/uv/). It fetches Python 3.12 itself.
2. In the cloned repo, run:

   ```bash
   cd simulation/starter-kit
   cp .env.example .env
   uv run --extra ui arena-haggle
   ```

3. Open `.env` and set `LLM_MODEL` and `LLM_API_KEY` for the agent. For Online mode, also set
   `ARENA_API_KEY` (your team key). Offline mode needs only the model keys.

`.env` stays on your machine and is never committed, so the keys are entered once per machine. The page
opens at http://127.0.0.1:8100.

## Online and offline

The header toggle: **Online** plays the 10 hosted practice cases on the real arena (each run uses one of your
200 daily practice sessions); **Offline** plays three examples against the built-in scripted supplier (no
key, no quota; it only teaches the API, not the real suppliers).

## What happens in a run

1. The agent opens the case and reads the supplier's file from the data package.
2. Code prices the target (the cheapest total cost C the case allows, with the supplier-health charge where the
   score has one) and, each round, what our sheets may cost: a low, reasoned first sheet, then steps toward the
   supplier's best sheet that keep us inside the band just under its latest counter where suppliers agree. Every allowed structure is priced to that same cost (the offer menu), except structures that at the
   supplier's price would cost us over 5% more than the best one (a short contract over a longer need). Where the
   supplier-health charge keeps a clause package above that cost, only its cheapest variant is offered (the longest
   payment term: money is worth less to a supplier than to us unless it is under strain). On a rising index without
   that charge the menu holds fixed prices only; the supplier's own clause sheets are still accepted when cheapest.
3. The model picks one to three menu packages and the verified arguments (strongest first, a new one each round)
   and writes a friendly e-mail, leading with the lever that fits the case type. It never sets a price.
4. `agreed` and `final_offer` are accepted at once: a supplier never goes below a sheet it agreed to, and every
   push after a final offer ended in a walk-away. The case closes on the cheapest standing sheet that beats your
   alternative. In an RFQ every call of the session is queued through one gate (the arena answers one at a time),
   every bidder's opening is priced before anyone is answered (so all first offers start from the cheapest
   target any bidder allows), only the two cheapest bidders keep negotiating after round 1, and once the cheapest bidder agrees the other
   gets two last rounds against its price; a
   final offer from the cheapest bidder is accepted at once, before any other call (the arena answers one call
   per session at a time, and a final offer left waiting past 60 s walks away). After round 1 every offer keeps a
   package on the supplier's cheapest-for-us structure, and never repeats the sheets of our last message (a repeat
   moves toward their price, or the thread settles).

An infeasible target menu triggers a guarded counter rather than acceptance of an opening quote. In an RFQ,
a bidder with an open counter cannot terminate other active bidders merely because its own strategy stops.
Regression tests cover both paths (issue #4).

## Live Final

```bash
cd simulation/starter-kit
uv run --extra ui arena-haggle-final   # start before wave 1, leave it running until the last wave closed
```

It polls only the final case list, plays each wave's cases in parallel and closes every case on its cheapest
standing sheet 75 s before the wave's 8-minute cap. Each case is recorded under `runs/` and shows on the page.
If it crashes, start it again: a case already opened is picked up from the arena (the session the 409 names,
or our own open session of that case). All cases share the key's per-second call limit.

Sunday runbook, checklist and the ehl.gg submission: [`docs/live-final.md`](../docs/live-final.md).

## Probes and rehearsals

`starter-kit/probes/` holds the scripts behind the evidence in [`docs/haggle-evidence.md`](../docs/haggle-evidence.md)
(experiment scripts, outside the agent and its lint):

- `probe.py probes/policies/<policy>.py`: one hosted practice session (ask first: quota) played by a hand-written
  policy that tests one idea; recorded under `runs/` with model `scripted`. `policies/` keeps every policy we ran.
- `batch.py [case ids]`: hosted practice cases through the real agent, in parallel (one session each).
- `fetch_cases.py cases.json`: every practice case file, hosted or not (a read, no session).
- `offline19.py cases.json out [--llm broken|slow]`: every case file through the agent against arena-sim (no
  session): no crash, valid sheets, must-haves kept, a deal or the alternative, with the model up or down.
- `final_rehearsal.py cases.json out [--llm ...] [--cap s]`: the Live Final runner over 5 waves of 10 such cases.

## Supplier files

Every supplier on a case card on the Negotiate page is a button (for example "Selvbrunn Drive Systems GmbH ›").
It opens the Suppliers tab on that supplier's full file, no run needed first: company and finances, delivery
and quality by quarter, news, past negotiations, prices, quotes, should-cost, contracts and clauses, spend, and
the full text of every letter and note. The tab also lists every session you have run with that supplier.

## The page

**Negotiate** (pick a case, watch it run; each supplier on a case is a button that opens its full file) ·
**Raw JSON** (every arena and model request and response, as sent; rows you open stay open while a run adds
events) · **Formatted** (the same run as readable e-mails, term sheets, claim verdicts, reasons and result) ·
**Suppliers** (the file of any supplier and its sessions) · **Team** (what the arena API says about us: quota,
best scores, every team's score per final case, practice leaderboard, all sessions, downloads) · **Settings** (model and system prompt file).

Sessions are saved as `starter-kit/runs/<id>.jsonl` and tracked in git (runs whose `model` is `scripted` are
probe sessions played by a fixed script to test one supplier behaviour, not by the agent), so a normal `git push` and `git pull`
syncs them. Each run writes only its own new file, so clones running experiments side by side never conflict;
everything else local (settings, keys, `.haggle_cache/`) is git-ignored. The Team tab reads the arena API live.
Each run records its system prompt and code version. Keys and headers are never recorded. Design and trust boundaries: `docs/design.md`.

## Model and system prompt

Set them on the Settings tab (or in `.env`): any OpenAI-compatible endpoint (`LLM_BASE_URL`, `LLM_ENDPOINT`,
`LLM_MODEL`, `LLM_API_KEY`) or `LLM_PROVIDER=anthropic`. The page stores them in `haggle_settings.json`
(git-ignored; the API key is write-only). The system prompt is the file `starter-kit/prompts/system.md`
(tracked in git; without it the built-in prompt in `agent.py` is used; a file without the `"offers"` answer
format falls back to the built-in prompt, since the model no longer sets prices). There is no such file now, so
the built-in prompt runs; an old-format draft is kept, unused, at `.agent/experiments/prompts/system.legacy-term-sheets.md` (git-ignored).
To experiment in one clone
without touching the others, point the Settings "Prompt file" at an untracked path. Every run records the exact
prompt it used, shown on the Formatted tab.
The model receives the supplier's evidence and your private rates; a local model keeps that on your machine.
`LLM_TIMEOUT` (default 45 s) bounds one call; a slower answer falls back to a plain counter so the arena's
60-second rule is kept.

## Tests

```bash
cd simulation/starter-kit && uv run --extra ui pytest -q
```

## Latest recorded practice evaluation

2026-10-11 01:44 UTC: ten hosted cases on code `c4fb3d5`, model `gpt-6.1-sol`,
effective prompt `45be8588d0` averaged **77.22%**; ten deals, every must-have satisfied,
no API errors or fallback decisions. The local custom prompt uses the old answer schema,
so the existing compatibility guard selects the built-in prompt. Per-case runs and
observations: [Haggle evidence](../docs/haggle-evidence.md#current-system-practice-check--2026-10-11-0144-utc).

The isolated `starter-kit/probes/opening_fixed.py` screen (Local-WAL-001) removes
indexed menu packages in round 1 only, without repricing; later rounds use the
current policy. It does not change the default agent. **Running it opens two
hosted practice sessions and requires explicit authorization each time.** A
shared cap prevents replacement sessions; every replay records the probe source
and SHA as well as the underlying agent/prompt identity. Results and baseline
comparisons live in the [evaluation protocol](../docs/haggle-evaluation-protocol.md).
