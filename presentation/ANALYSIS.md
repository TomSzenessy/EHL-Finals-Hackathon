# Jury presentation evidence audit

<!-- index: design | Jury story and dated metric source audit | Reviewing claims in the Remotion hackathon presentation. -->
<!-- covers: presentation/src/evidence.json -->

Snapshot: 11 October 2026, 09:08 CEST. Rolling window: preceding 20 hours.
Git history frozen at `adb9b45`, before presentation work. The initial template
commit was 10 October at 12:21 CEST, approximately 20 h 47 min before capture;
it is outside this exact window. Entire setup at 13:33 is inside but excluded
from project activity. The 36 application commits begin at 17:20 CEST.
Inherited kit files are not counted as features built during the hackathon.

## The story

The team built Haggle, a procurement negotiation agent with a deliberate boundary:
code calculates and enforces every number; a model reads the supplier and writes
the email. Its offer menu prices different legal packages to equal buyer total
cost. Claims are calculated from source facts and inserted through markers,
with every request, response, decision and result inspectable. This is evidenced
by `docs/design.md:12`, `:20`, `:35`, and `:65`.

The strongest hook is **€1.17 million less simulated total cost** across the latest
complete ten-case suite. Sum C_open = €12,759,510.63; sum C_deal = €11,591,349.12;
difference = €1,168,161.51, or approximately 9.16%. These are modeled procurement
costs in the arena's scoring function, including terms and penalties, not actual
money saved. The latest ten logged results are individually listed in evidence.json.
The suite achieved 77.22% mean score, 10 deals, and all must-haves satisfied;
114 HTTP responses were all 200 with zero model errors or decision fallbacks
(`docs/haggle-strategy-analysis.md:7`).

A useful progress chart compares complete suites on the same ten practice cases:
65.25% at 19:54 UTC, 70.99% at 20:20 UTC, and 77.22% at 01:44 UTC. All use
gpt-6.1-sol. This is +11.97 score points from first to last. Code and policy
changed; these are descriptive snapshots, not controlled or replicated causal
experiments. Do not chart incomplete batches as equivalent full-suite means.

## Chronology

- 17:20 CEST: first Haggle agent and inspection page (`63038da`).
- 18:13: real-score optimization, Team and Settings tabs (`46c183a`).
- 19:07: code owns all prices and closes agreed/final offers (`d28e7c7`).
- 19:33: acceptance-band pricing and RFQ auctions (`39e1c7a`).
- 20:25: repaired premature RFQ closure (`7df04bc`).
- 21:14–22:07: cheapest tender targets, final-offer protection, hidden-case
  facts, coverage-trap guard and CI (`fbce507` through `840ec3c`).
- 22:59–23:53: supplier-money calibration, alternative ceiling, must-have
  protection, shared rate limits and crashed-final resumption (`dee671b`,
  `67aadcc`, `c32bd6b`).
- 00:35: Live Final runbook and offline rehearsal evidence (`c4fb3d5`).
- 08:45–08:52: argument reuse fixes, independent rival markers and slow-reply
  tender focus (`445ea04`, `60ab258`, `adb9b45`). Latest clean complete-suite
  measurement predates these changes and does not validate their score effect.

## Coolest defensible insights

1. **Cheapest unit price can be the wrong deal.** In P03, €432.15 with 90-day
   payment beats €427.49 with 14-day payment on total cost
   (`docs/haggle-strategy-analysis.md:32`).
2. **More facts can mean no new evidence.** Latest suite had 40 verified claims,
   11 duplicates, none contradicted or irrelevant. Suppliers count an argument
   family once; another record ID is not necessarily fresh leverage
   (`docs/haggle-strategy-analysis.md:36`).
3. **A structural ceiling beats a cents tweak.** Eleven archived P02 outcomes
   fitted supplier cost and interest with zero residual cents; the best legal
   indexed package scores 73.5404%, essentially the actual 73.5344%. Reaching
   the higher record requires a different accepted structure, not a smaller
   indexed price (`docs/haggle-strategy-analysis.md:64`). Fixed-price acceptance
   remains unproven and must not be presented as achieved.
4. **The system still closes when every model call fails.** An offline rehearsal
   ran 50 cases over five waves: 45 deals, 5 alternatives, zero unresolved cases,
   and self-stop in 11.4 minutes (`HANDOVER.md:23`, `:39`). This is offline
   robustness evidence, not a hosted-final score.
5. **We stopped trusting clever shortcuts.** Pressure, text/sheet mismatch and
   unverified attachments damaged trust or failed to move outcomes. The core
   product uses checked facts and binding terms (`docs/haggle-evidence.md:24`).

## Inventory caveats

The archive contains 312 run records: 310 online, 2 offline, with 305 distinct
session IDs. 293 records say done and contain a result; 288 of those made deals.
There are 11 stale/running and 8 error records. Model labels include 58 scripted
probes, 176 gpt-6.1-sol runs and 78 gpt-6-luna runs. These categories describe
archived records, not independent fresh completed hosted sessions. Do not say
312 successful negotiations or 312 unique sessions.

Do not quote a current rank: documented board snapshots disagree by time, and
practice rank uses best-of scores rather than latest-suite mean. No hosted-final
results exist in this snapshot. Historical kit LOC and generated adapters are
not a measure of hackathon engineering output.
