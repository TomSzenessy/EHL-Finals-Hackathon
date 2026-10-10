# Live Final: run and submit

<!-- index: operate | How the Live Final runs, our Sunday runbook and the ehl.gg submission | Before Sunday 12:00: setting up, starting or submitting the agent. -->

Sources: the kit's `brief/submission.md`, `README.md` and `starter-kit/README.md` (tacto-ai/negotiation-arena-kit),
`simulation/brief/api.md` ("Live Final in waves"). Agent design: [`design.md`](./design.md); what the suppliers taught
us: [`haggle-evidence.md`](./haggle-evidence.md).

## How the final works

- **We run our agent ourselves**, on our machine with our own keys. Tacto runs the suppliers, not our code. The commit
  we name on ehl.gg is the code that must be running; the top 10 are checked for pushes after the freeze.
- **12:00: code freeze and start, together.** The agent must already be running and polling. From 12:00 no human in
  the loop, and the agent must not read `/v1/events`, `/screen`, `/leaderboard`, `/results` (or their JSON).
- **5 themed waves.** A wave's cases (about 10; 50 hidden suppliers in all) appear for every team at the same moment.
  `GET /v1/cases?set=final` answers 403 until wave 1 starts, then lists every started wave's cases with `wave`,
  `theme`, `open`, `seconds_left`. One session per case; up to 10 open sessions per key.
- **8 minutes per wave** (the host may extend one: read `seconds_left`). A session still open at the cap ends with
  no deal: the alternative's score, 0 if there is none. One attempt per case; an abandoned case is no deal.
- Each wave scores 0-100 (mean case score x 100); points add up over the 5 waves. Replays are public afterwards.

## Our runner: `arena-haggle-final`

`simulation/starter-kit/arena_kit/haggle/final.py`, playing the same agent as practice. It polls only the final case
list (every 4 s), opens each case of a running wave once, plays up to 10 in parallel and closes each case on its
cheapest standing sheet that keeps the must-haves and beats the alternative, 75 s before its wave's cap (or the
slowest round so far plus 15 s, if longer). Built-in safety, each tested offline on all 19 practice case files and in
a 5-wave rehearsal (`simulation/starter-kit/probes/final_rehearsal.py`):

- the model slow or down: a decision over 40 s plays a guarded, code-priced counter; every case still closes;
- a supplier sheet that breaks a must-have is sent back once with the must-have kept, before any walk-away;
- no sheet ever costs more than our alternative; a final offer is accepted, never pushed (pushing walked 3 of 3);
- one per-second call budget for all cases of our key, patient retries on a short 429;
- a crash: start the same command again; it picks up every open session (from the 409, or our session list).

## Sunday runbook

All commands from `simulation/starter-kit`, on the machine and network used for the final.

| When | Do | Check |
|---|---|---|
| 08:00 | `uv run arena data --out ../data/sunday` then make the release folder `../data/release-sunday` (the folder that holds the release's `facts.json`), or `export ARENA_RELEASE=<that folder>` | `uv run --extra ui python -c "from arena_kit.haggle.__main__ import find_data; print(find_data().release)"` prints the folder, not `None` |
| 08:15 | `uv run pytest -q` | all pass |
| 09:00 | Pre-flight (1 practice session): `PYTHONPATH=. .venv/bin/python probes/batch.py case:P02` | a deal, score about 0.735, in under 5 min |
| by 11:30 | `uv run arena me` (the key works); LLM credits and rate limits for about an hour of 10 parallel cases | team shown; provider dashboard |
| 11:30 | Freeze candidate: `git status` clean, `git push`, note `git rev-parse HEAD` | the hash goes into the ehl.gg description |
| 11:45 | `caffeinate -dimsu uv run --extra ui arena-haggle-final 2>&1 \| tee -a final.log` (power cable in, lid open) | log line `haggle final: model ...` |
| 12:00-~13:00 | Hands off. Read only `final.log` and the runs folder; do not open the page's Team tab (it reads the board) | each wave: `case:... done score=... deal=True` lines |
| crash | the same command again | it logs the resumed cases |

Environment (names only; values live in `simulation/starter-kit/.env`, never in git): `ARENA_URL`,
`ARENA_API_KEY`, `ARENA_DATA` (`../data`), `ARENA_RELEASE` (optional), `LLM_PROVIDER`, `LLM_BASE_URL`,
`LLM_ENDPOINT`, `LLM_MODEL`, `LLM_API_KEY` (or `ANTHROPIC_API_KEY` with `LLM_PROVIDER=anthropic`), `LLM_TIMEOUT`.

## Submission on ehl.gg (by 12:00)

1. **Repo**: the GitHub URL. The jury and tum.ai (who run a code agent over every submission) must be able to open it:
   the repo is private now; make it public at 12:00, when every team is frozen, or add the accounts Tacto names.
   No keys in the repo (checked: none in the tree or the history; `.env` and `haggle_settings.json` are ignored).
2. **Commit hash**: the one noted at 11:30, in the description.
3. **Description** (draft):

   > Code decides every number, the model reads the supplier and writes. For each case the agent reads the case file
   > and the supplier's whole record in the data package (contracts and clauses, call and meeting notes, letters,
   > news, scorecards, complaints, order prices, forecasts, should-cost, the index series behind the part's cost, and
   > the Sunday release). It prices every term sheet with the arena's own cost function, including our estimate of
   > the supplier-health charge, and offers equal-cost packages across the allowed options, so the supplier's choice
   > shows what it values. It opens low with reasons, then moves a shrinking share of the gap, staying near the
   > supplier's counter where suppliers agree. Every argument is a fact the arena can check (index falls on the
   > supplier's own cost drivers, our forecast, should-cost, late notice against the contract, rivals' live offers in
   > a tender), computed from the data, one new kind per round. It takes an agreement or a final offer at once, closes
   > on the cheapest standing sheet that keeps the must-haves and beats our alternative, and walks away only when
   > nothing does. The rules come from about 300 practice sessions and controlled probes, each recorded.

4. **Slides** for the top-10 pitch (13:00): pick one replay and walk through it (a good one: P02, where the cost
   model chose the 90-day clause package the supplier agreed to in round 1).
