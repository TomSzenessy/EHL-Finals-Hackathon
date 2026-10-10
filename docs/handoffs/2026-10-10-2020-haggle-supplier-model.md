# Handoff — haggle: supplier model probed, tender and safety fixes, 77.7% practice

<!-- index: operate | Handover record scaffold (local HANDOVER.md or committed handoff) | A fresh actor needs a focused continuation record. -->

- **Created (UTC):** 2026-10-10 20:20
- **Next actor/session focus:** Sunday morning: load the Sunday release, run the 09:00 pre-flight through the final setup, start `arena-haggle-final` before 12:00.
- **Sharing boundary:** project team / this repository. No keys or credentials in this record.

## Objective

Win the Live Final (hidden cases, one attempt each), with the practice board as the proxy. The user asked for an
85% ten-case mean. **Not reached:** the best score any team holds on each practice case averages about 85%, so 85%
means matching every record at once.

## Current state

- **Committed baseline:** `main` at `840ec3c` and earlier today `fbce507`, `f8ee0b1`, `527674d`, `50899c0`.
- **Working tree:** clean except new run records.
- **Done (verified on the hosted arena):**
  - Practice board: 77.7% best-of mean, rank 2 (leader 83.9%). Best per case: P01 0.978, P02 0.659, P03 0.923,
    P04 0.860, P05 0.865, P07 0.772, P08 0.711 (scripted probe), P10 0.671, P11 0.710, P18 0.618.
  - Single-run full batches on today's code: 74.6, 73.3, 76.2, 74.5 (earlier code: 71.0, 72.3).
  - Tender (P05) from 0.51-0.69 to 0.81-0.87: every bidder's target is priced before anyone opens (barrier);
    the cheapest bidder's final offer is accepted inside the same gate slot (the arena answers one call per
    session at a time; a late accept made a bidder walk, score 0).
  - Safety: no empty menus (deep goals clamp to the cheapest reachable cost), the fallback never counters on the
    supplier's own short-term structure (P18 scored 0.04 that way), a cheaper supplier alternative is sent back
    before closing, the menu never offers a coverage trap (12-month term over a 2-year need: P08 scored 0.10),
    after round 1 the package on their cheapest-for-us structure is always sent.
  - Hidden-case readiness: case-only facts become claims and are shown to the model; Sunday-release news and
    letters for the supplier join the dossier (read from `../data/release-sunday` when it exists).
  - CI: red since the first product commit; fixed (template self-tests no longer inherit the simulation surface,
    `uv` installed in CI, design doc split into `docs/design.md` + `docs/haggle-evidence.md`). Confirm the run
    for `840ec3c` is green.
- **Remaining:** see Exact next action.

## Evidence already collected

| Check / artifact | Result | Date/command | Evidence type |
|---|---|---|---|
| Scripted probes (`model: scripted` runs in `simulation/starter-kit/runs/`) | Supplier numbers follow its code: plain two-line e-mails, claims every round, and the agent produce the same price path; anchors are ignored; stalling brings an earlier, higher final; a text argument the supplier agreed with left its price unchanged | 2026-10-10 18:30-20:00 UTC, hosted practice | deployed |
| Sandbox D01 probes | Terms-only change after a final offer: 3/3 restated, no walk; 1% price push after a final: 1 walk in 2 | 2026-10-10, sandbox (no quota) | deployed |
| `/v1/live` per-case records | Records: P01 1.0, P02 0.847, P03 0.936, P04 0.874, P05 0.924, P07 0.812, P08 0.916, P10 0.702, P11 0.807, P18 0.677 | 2026-10-10 20:10 UTC | provider |
| `make verify` | passes locally (tools suites, simulation suite, doctor) | 2026-10-10 | test |
| Case durations | every case under 4.7 min (P05 max 277 s); wave cap 8 min, close 75 s before | runs of 2026-10-10 | deployed |

## Decisions and constraints

- No prompt injection, fake audit headers, invented budgets or defects: the numbers are code-driven (text did not
  move them), invented facts come back `contradicted`, and the jury reads replays.
- Final offers are accepted, never pushed (walk risk). No case-specific constants.
- Structure lever: suppliers re-price payment days and clauses about fairly; a clause-free lead looked good in
  scripted probes but not in the agent (recorded in `docs/haggle-evidence.md`, not adopted).

## Blockers and open questions

- How the leaders reach P08 0.92 / P02 0.85 / P11 0.81 is unknown; our probes found no lever beyond structure
  and the close. Hypothesis to test if time allows: the round-1 price depends on which claim kinds are taken
  into account in round 1.
- Third tender bidder often times out in round 1 (calls are serialized); harmless so far.

## Exact next action

1. After 08:00 Sunday: download the release (`uv run arena data` from `simulation/starter-kit`, or
   `GET /v1/data`) into `simulation/data/release-sunday/`, then run one practice case and check the dossier shows
   the new letters/news for its supplier.
2. 09:00 pre-flight: one practice case through the final setup on the final machine; then
   `uv run --extra ui arena-haggle-final` before 12:00 and leave it running.

## Relevant paths and issues

- `simulation/starter-kit/arena_kit/haggle/{agent,strategy,run,context}.py`, `docs/design.md`,
  `docs/haggle-evidence.md`, `simulation/README.md`.
- Earlier checkpoint: [`2026-10-10-1825-haggle-strategy.md`](./2026-10-10-1825-haggle-strategy.md).

## Verified skill suggestions

none

## Redaction and retention check

No secrets, keys or personal data. Share within the team repository; delete after the final.
