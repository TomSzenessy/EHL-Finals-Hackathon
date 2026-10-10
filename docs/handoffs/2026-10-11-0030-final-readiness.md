# Handoff: haggle agent ready for the Live Final, Sunday steps left

- **Created (UTC):** 2026-10-10 22:30 (00:30 CEST Sunday)
- **Next actor/session focus:** the Sunday steps in [`docs/live-final.md`](../live-final.md): 08:00 data release,
  09:00 pre-flight, 11:30 freeze candidate and ehl.gg submission, 11:45 start `arena-haggle-final`.
- **Sharing boundary:** project team / this repository (private; to be shared with the jury at 12:00). No keys.

## Objective

Win the Live Final: 5 waves of about 10 hidden cases, one attempt each, run by us from our machine. The practice
board (best-of per case) is a proxy only. User rule: every hosted practice session or suite run needs the user's OK
(quota about 125 left, nothing frees up before the final).

## Current state

- **Commits since the 2020 handoff** (all pushed to `main`): supplier money one point under ours and the cheapest
  clause package (`dee671b`, P02 0.659 -> 0.735 in the agent); never a sheet above the alternative, the must-have
  rescue, one rate budget per key (`67aadcc`); resume a final session whatever the 409 says (`c32bd6b`); evidence of
  every probe (`f0c72ec` ... `32bad54`); probes, runbook and this handoff (next commit).
- **Practice board:** about 78.9 (3rd; NoIdea 86.9 holds 9 records). Single-run mean on current code: 75.3%.
- **Robustness, offline (no sessions):** all 19 practice case files close through the agent with the model up and
  with it failing on every call (`probes/offline19.py`); the final runner over 5 waves x 10 cases
  (`probes/final_rehearsal.py`, model failing on every call): 50 cases, 45 deals, 5 on their alternative, none
  open at a cap, the runner stopped by itself after wave 5 (11.4 min).
- **Experiments that did not move a floor** (about 20 sessions, all recorded in `docs/haggle-evidence.md`): hedge
  letter, rival orders, deep and FX index windows, attachments, alternative mentions, text promises of fixed terms,
  pressure, high anchor, sign-today asks, fixed terms in a sheet (422), boss escalation, text vs sheet mismatch,
  gaslighting, owner walk-through, frame-contract price clause.

## Evidence already collected

| Check / artifact | Result | Date/command | Evidence type |
|---|---|---|---|
| `uv run pytest -q` (simulation/starter-kit) | 59 passed, 2 skipped | 2026-10-11 00:20 | test |
| `probes/offline19.py` real model / broken model | 19/19 close (17 deals, 2 on their alternative) both ways | 2026-10-11 00:05 | offline sim |
| Hosted agent run P02 on `dee671b` | 0.735 (agreed round 1, clause 90 days 361.23) | 2026-10-10 22:54 | deployed |
| `probes/final_rehearsal.py --llm broken --cap 120` | 50 cases, 45 deals, 5 alternative, 0 not ok, exit 0 | 2026-10-11 00:35 | offline sim |
| Repo secret scan (tree and history) | no keys; `.env`, `haggle_settings.json` ignored | 2026-10-11 00:20 | static |

## Decisions and constraints

- Code decides every number; final offers are accepted, never pushed; no sheet above the alternative.
- No deception in the agent: the probes showed personas compare text with the sheet and the arena checks every
  figure; it buys nothing and costs trust.
- The repo is private; make it public at 12:00 (every team frozen) or add the accounts Tacto names.

## Blockers and open questions

- The Sunday release zip layout is unknown until 08:00: put the folder holding its `facts.json` at
  `simulation/data/release-sunday` or set `ARENA_RELEASE`, then check `find_data().release` (runbook).
- Optional offline improvement not made: stop repeating a claim kind the supplier already accepted (P07 sent four
  forecasts, three `duplicate`). Needs a hosted check before trusting it.

## Exact next action

08:00: `cd simulation/starter-kit && uv run arena data --out ../data/sunday`, place the release, run the check
command in `docs/live-final.md`; then follow the runbook table row by row.

## Relevant paths and issues

- `docs/live-final.md`, `docs/haggle-evidence.md`, `docs/design.md`, `simulation/README.md`
- `simulation/starter-kit/arena_kit/haggle/{agent,strategy,economics,final,run}.py`, `arena_kit/{client,play}.py`
- `simulation/starter-kit/probes/`

## Verified skill suggestions

none

## Redaction and retention check

No keys, credentials or personal data. Delete after the final.
