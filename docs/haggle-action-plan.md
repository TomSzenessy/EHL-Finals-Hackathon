# Haggle action plan to first place

<!-- index: design | Ranked, evidence-backed plan, bug list and experiments for the Live Final | Deciding what to implement, test or run next on the haggle agent. -->

Living document, started 2026-10-11 03:20 CEST. Every claim cites run logs under
`simulation/starter-kit/runs/` (about 330 sessions, ours and a teammate's 33) or code. No practice
session was spent writing it. Status words: **fixed (uncommitted)** = in the working tree with tests,
not yet tried on the hosted arena; **open** = not implemented.

## 1. Where we stand, honestly

| Case | Type / goal | Our best | Our latest | Leader record | Gap | What explains the gap (section 3) |
|---|---|---:|---:|---:|---:|---|
| P01 | price increase / stabilise | 0.978 | 0.953 | 1.000 | 0.02 | price (rival quote 124.20 of 2025 never used) |
| P02 | price increase / stabilise | 0.735 | 0.735 | 0.879 | 0.14 | structural: every clause deal is capped at 0.7354 (F5) |
| P03 | renewal / stabilise | 0.923 | 0.923 | 0.989 | 0.07 | list price frozen; rival quote 429.18 never used |
| P04 | renewal / routine | 0.860 | 0.860 | 0.874 | 0.01 | rival quote 4.29 never used |
| P05 | RFQ / leverage | 0.865 | 0.865 | 0.965 | 0.10 | 14-day payment drift (0.913 at 90 days, B2); rival marker reuse (B5) |
| P07 | bundling / routine | 0.772 | 0.760 | 0.825 | 0.05 | 3 of 5 claims `duplicate` (B3) |
| P08 | raw material / leverage | 0.711 | 0.646 | 0.916 | 0.27 | rival quote never used; duplicate claims (B3) |
| P10 | capacity / secure supply | 0.671 | 0.663 | 0.741 | 0.08 | round-1 `final_offer` in 21 of 21 runs (B7) |
| P11 | quality / quality first | 0.710 | 0.710 | 0.885 | 0.18 | unexplained: 45.50 in all 36 runs (F6) |
| P18 | raw material / leverage | 0.663 | 0.606 | 0.756 | 0.15 | live rival quote 5.45 never used (B1); 14-day drift (B2) |

- Our single-run mean on the current code is 77.2% (2026-10-11 01:44 suite). The leader's board is a best-of.
- **The Live Final is what counts:** hidden cases, one attempt each, run by us. A practice record does not
  carry over; a mechanism that works on unseen suppliers does. Everything below is ranked by that.
- **Realistic target:** the fixes in section 2 address mechanisms present in at least 7 of the 10 practice
  cases. If they behave as the logs suggest, they are worth about +3 to +6 points of mean score. That is
  enough for first place only if the leader's final mean stays near its practice level minus its best-of
  premium. Nobody can promise first; these are the largest gains the evidence supports.

## 2. Bugs, inconsistencies and inefficiencies

Moved to the [bug list](./haggle-bug-list.md): B1 rival quotes, B2 payment drift, B3 claim groups, B4 ignored
prompt file, B5 tender markers (fixed, uncommitted); B6 document evidence (won't do); B7 P10 round-1 final
(experiment E6); B8 lead time (no action); B9 stale docs (fixed).

## 3. Findings that shape the plan

- **F1. An `agreed` sheet is a lock, never a loss.** After `agreed`, a supplier kept its agreed sheet
  against every later sheet in about 100 messages: it never walked and never went lower. Closing at
  once is right. The care has to go into what we send *before* it agrees.
- **F2. Suppliers concede in fixed price ticks, then stop.** P18: 0.10 a round. P11: 0.50. P08: shrinking
  (0.07, 0.04, 0.03). The stop point depends on the data kinds they accepted and on the structure, not on
  our wording (P11: all 36 runs end at 45.50).
- **F3. Accepted facts delay the final offer.** Rounds 3 to 4 with a "we took it into account" reply sent
  `final_offer` 5 to 27% of the time; rounds with rejected or duplicate claims, 33 to 55%. This is a
  correlation, but it is consistent with the brief ("it gives nothing without a move from you").
- **F4. The approval ladder exists and has one known key:** "The buyer shows a much lower rival quote. I
  give half the step now and check the rest" / "Checked: give the rest of the step" (back office, P05).
  B1 makes that key available outside tenders for the first time.
- **F5. P02 is capped by its structure.** Every index-clause package agreed in round 1, at any price, even
  349. The best clause deal scores 0.7354 (we have 0.7353). The 0.879 record needs a deal without the
  clause at about 367.8 on 90 days. Our no-clause attempts stalled at 369.85 on 60 days and 371.88 on 90,
  which matches its estimated full cost of 367.6. No mechanism found; low priority.
- **F6. P11 has no honest lever left: accepted residual.** 45.50 in all 36 runs; the 0.885 record implies
  about 44.45. The managing director's call note (`doc:20260715-70140-M1`): "I cannot sign anything that
  lowers our margin now", "the bank is watching every month". Its one wish, payment within 10 days for a
  cash discount (`doc:20260710-70140-M2`), is a term the case fixes. Every negotiable field nets out against
  us: 1500 ppm saves it about 0.50 and costs us 0.54; a chargeback costs it about 1.19 a unit at its real
  2,376 ppm and saves us at most 0.135. There is no lower rival quote. Plan: keep 0.710.
- **F6b. P02 likewise.** Nordmark's committee must approve any change above 2% (`doc:20260227-70510-M2`),
  the rival quotes are higher (421) and its no-clause steps shrink (0.52, 0.40, 0.30), which fits a
  persona held to the 2% limit with no trigger for approval. Plan: keep 0.735.
- **F8. The practice suppliers may have run on a rule-based fallback brain** overnight (public page). The final always uses the LLM brain. Fixes that follow arena rules (B2, B3, B5) transfer either way; conclusions about fixed price floors may not.
- **F7. Structure value at the final price** (score with only the non-price terms changed): P05 0.865 →
  0.913 at 90 days; P07 0.760 at 90 days (already); P04 0.86 (already best); P03 0.926 at most;
  P10 0.663 → 0.719 at lead time 42.

## 4. What first place realistically takes (revised after the experiments)

The offline estimate of +2 to +5 points rested on B1 and B2; both were refuted on the arena (4b). What
remains measured: B3 and B5 are neutral; B12 is a real, fixable loss in tenders (0.04 to 0.10 per tender
case this morning). The leader's records, some possibly set against the overnight rule-based brain (F8,
B13), cannot be explained from our data. First place now depends on how the leader's agent handles the
final's LLM suppliers, which we cannot measure. What we control: no tender timeouts (B12), no regressions,
a clean start at 11:45.

## 4b. Experiment results, 2026-10-11 07:49-08:00 (8 sessions, user-approved)

| Run | Case | Change tested | Score | Baseline | Verdict |
|---|---|---|---:|---:|---|
| `074922-e418` | P18 | B1 on, B2 | 0.539 | 0.606-0.663 | B1 `irrelevant`: refuted; B2 did not engage |
| `074922-64d6` | P08 | B1 on (old quote, not cited), B2, B3 | 0.591 | 0.614-0.646 | B2 drift to 30 days: reverted |
| `074922-ab30` | P07 | B3 (forecasts grouped across parts) | 0.721 | 0.746-0.772 | grouping too broad: now per part |
| `074922-e2a7` | P05 | B2, B5 | 0.824 | 0.865 | 409 timeout (B12); B2 blocked the term the supplier wanted |
| `075401-ebfd` | P07 | B3 per part | 0.753 | 0.746-0.772 | neutral, no duplicates |
| `075401-4c6c` | P08 | B3, B2 reverted | 0.646 | 0.614-0.646 | neutral |
| `075401-d2ea` | P11 | B3 | 0.626 | 0.710 | the supplier reacted differently (B13), not a B3 effect |
| `075817-0482` | P05 | B10 keep-alive on | 0.762 | 0.865 | not engaged; 409 timeout again (B12) |

**Honest conclusion:** none of this session's levers produced a measured gain. B1 and B2 were wrong and are
off or reverted. B3 and B5 are neutral so far and stay, as they follow documented arena rules. The one
new, measured, fixable loss is B12 (tender timeouts with slow morning suppliers), which will hit every
tender in the final. Nothing found here establishes a route to first place; fixing B12 protects the
tender cases, and the rest of the score rests on the existing agent.

## 5. Action plan (in order; times are Sunday CEST)

| Step | What | Practice sessions | Pass criterion | When |
|---|---|---:|---|---|
| 1-8 | E1-E5, E2b | 8 used | results in 4b | done 08:00 |
| 9 | Commit B3, B5, B4 rename, the Team-tab table; B1 and B10 stay behind flags (off) | 0 | `make done` | now |
| 10 | **Fix B12:** in a tender, when the slowest supplier reply plus our decision time exceeds about 40 s, keep only the cheapest bidder live after round 1 (`run.py` `FOCUS` 2 to 1, adaptive) | 0 | unit test + offline P05 | before 09:00 |
| 11 | 09:00 pre-flight: one P05 session through the final setup (it also tests B12) | 1 (needs OK) | no 409, score ≥ 0.865 | 09:00 |
| 12 | Freeze, submit, start the final runner (`docs/live-final.md`) | 0 | | 11:30 / 11:45 |

### Not doing (tested and failed, or not honest)

Pushing after `final_offer` (walked away 3 of 3), the same sheet sent twice (walked away), text that
differs from the sheet, fixed fields in a sheet (422), boss escalation without a fact, foreign-exchange or
rival purchase-order claims (`irrelevant`), attachments (a mismatch is `contradicted`), a high first
sheet, ultimatums. Never invented quotes or deadlines: the arena checks every ID, and a `contradicted`
costs trust.

## 6. Open questions that would change the plan

- No run ever cited another company's `quote:` ID (the tender cited live `offer:` IDs), so how the arena
  types and checks one is unknown until E1. If E1 returns `irrelevant` or `contradicted`, roll B1 back.
- Does an *old* rival quote (2025) come back `verified` and move the price, or "it holds, but it does not
  change our calculation"? E4 answers it; if the latter, mark old quotes weak.
- Does the rival quote trigger the approval flow for a non-owner role ("Inside Sales", "Key Account
  Manager")? E1's back office answers it.
- Were the P02/P11 records set against the overnight rule-based brain (F8)? Replies carry no marker of the
  brain (checked: 1,357 replies, the same fields throughout), so this cannot be settled offline.
- P11 and P02 records: no mechanism found offline. A competitor's replay, if Tacto publishes them after
  the final, would settle it.
