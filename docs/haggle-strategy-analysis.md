# Haggle scoring and strategy analysis — 2026-10-11

<!-- index: design | Dated practice scoring analysis and latest-suite results | Tracing negotiation strategy hypotheses to session evidence and counterfactual calculations. -->

Evidence supporting the [experiment plan](./haggle-experiment-plan.md).

## Current-system practice check — 2026-10-11 01:44 UTC

User-authorized ten-case hosted evaluation, one run per case: mean **0.7721756276 (77.22%)**.
All ten made deals with must-haves satisfied. All 114 recorded HTTP responses were 200; no
model errors or decision fallbacks. This is a single-run mean, not the best-of leaderboard.

Effective system: code `c4fb3d5`, model `gpt-6.1-sol`, prompt SHA `45be8588d0`.
The untracked `prompts/system.md` uses the obsolete `term_sheets` answer schema and lacks
`"offers"`, so Settings rejects it and uses the built-in system. This evaluation measures
the effective current system, not that custom file. No prior clean-version run matched
the current runtime code; older `+changes` versions lack enough provenance to prove equality.

| Case | Score | Run under simulation/starter-kit/runs |
|---|---:|---|
| case:P01 | 95.28% | `20261011-014457-a580.jsonl` |
| case:P02 | 73.53% | `20261011-014457-40ab.jsonl` |
| case:P03 | 92.28% | `20261011-014457-bc90.jsonl` |
| case:P04 | 86.04% | `20261011-014457-b3d4.jsonl` |
| case:P05 | 86.52% | `20261011-014457-f142.jsonl` |
| case:P07 | 76.00% | `20261011-014457-5922.jsonl` |
| case:P08 | 64.62% | `20261011-014457-347f.jsonl` |
| case:P10 | 66.29% | `20261011-014457-2285.jsonl` |
| case:P11 | 70.99% | `20261011-014457-1b1d.jsonl` |
| case:P18 | 60.61% | `20261011-014457-bda3.jsonl` |

Observed negotiation behavior: P02 agreed to the opening 90-day clause package (361.23),
and P10 issued a final offer after one message (31.70). P03's 432.15 at 90 days beats its
427.49 at 14 days in total cost. P05 closed its tender at 27.50. P11 held 45.50 despite
further verified arguments. P08/P18 remain weakest at 64.62%/60.61%: their clause and
payment structures matter, and further facts did not force a lower price. Across negotiation
replies (excluding closing confirmations), claims were 40 verified, 11 duplicate, none
contradicted or irrelevant. New record IDs of an already-used kind still get counted as
duplicates, especially P07 (three). No strategy or prompt changes were made for this check.

## No-credit strategy analysis — 2026-10-11

Scope: 271 completed hosted practice results in the local archive, the latest ten,
current policy/scoring code, public practice standings and existing session back-office
reports. No new sessions were opened; no practice credits spent; no strategy changed.
The public board returned gLarPC rank 6 / 78.9 and NoIdea rank 1 / 88.0.
Public build records: P01 100.0, P02 87.9, P03 98.9, P04 87.4, P05 96.5,
P07 82.5, P08 91.6, P10 74.1, P11 88.5, P18 75.6 percent. P04/P18
records belong to other teams. Source: https://arena.tacto.ai/live and
https://arena.tacto.ai/v1/leaderboard?set=practice (read during build, never final).
These are best-of records, not comparable to a fresh-suite average. Our local
archive best-of mean is 78.81%; selecting old successes cannot explain the gap.

### Corrected model: observed plateaus are not proven hard floors

Earlier statements here that "floors are code" or that P11 45.50 is a real floor
were too strong. The hosted decision implementation is unavailable. These are
plateaus across tried policies. Published rules say economics/authority impose
hard limits but whole-email interpretation matters within them. Backoffice
P02 says "My call: counter" then "we agree" after reading our offer. This is
evidence of staged interpretation, not proof of bypassable numeric safeguards.
Competitor strategies cannot be identified from our own replays.

### P02: structural ceiling, not price optimizer error

Using eleven distinct archived P02 outcomes (prices 349.00–371.88, payment
14/30/45/60/90, clause and no clause), the published cost function fits full
supplier cost **367.60** and interest **6.6%** with **zero residual cents**
for every C_deal. It reproduces the latest 361.23/90-day/5%-deadband-clause
C=2,248,046.44. Across all twenty legal payment/clause structures, optimizing
positive price, the best clause package scores **73.5404%** at 361.33/90days.
The actual package scores 73.5344%. Smaller deadbands are worse. Contract and
volume are fixed in this case. Therefore, assuming unchanged case/scoring, the
87.9% record requires a no-clause deal. Lowering the current clause price cannot
bridge the gap and can increase the relationship penalty. Coarse price-grid
error was considered and rejected: price_for already refines the minimum.

A no-clause/90-day deal at approximately **367.81** matches 87.9%; its economic
optimum around **361.42** scores a capped 100%. These are counterfactual costs,
not demonstrated accepted offers. Our archived no-clause90 result at371.88
scores50.67%. The problem is convincing the supplier to price lost security
less dearly. Current round1 offers fixed-price357.09/30days alongside a clause
package361.23/90days; the supplier accepts the latter and code immediately closes.
High-value hypothesis: negotiate fixed-price packages first and hold the clause
as a fallback instead of letting it terminate discovery in round1. Earlier
fixed-price failures mean this is a targeted hypothesis, not a guaranteed fix.

### Raw materials: separate achievable price from indexed exposure

P08 historical scripted run20261010-214805-9848 reached supplier5.17 with
0%-deadband clause after persistent fixed-price buyer proposals and no new
facts after round1 (71.07%). Latest closes5.38 with5%-deadband and90days
(64.62%). At5.17, no clause and90days would score **92.375%**, close to or
above the public91.6 record. Acceptance of this combined package is unproven.
This explains a plausible route without needing a vastly lower nominal price:
get the low-price path while preserving/removing the costly security provision.

P18 historical agent20261010-225513-7b73 closes5.20/90days at66.35%;
latest closes the same5.20 at14days for60.61%. The latest path selected a
nominally cheaper14day alternative. The historical90day result is confirmed
evidence of avoidable loss, though not a matched causal test. Recorded
persistent fixed-price probes reach5.10 with a supplier clause. At5.10/no-clause/
90days the counterfactual score is **75.901%**, near the public75.6 record.
Again, accepting the combined terms is the unresolved step.

### P11: acceptance behavior is the missing lever

The latest run already offered44.44/300ppm/no chargeback at round5; supplier
held45.50. If accepted, that exact44.44 sheet would score **88.716%**, slightly
above the public88.5 record. Thus inventing a better number cannot solve this:
we already proposed one. The record at unchanged300ppm/0chargeback corresponds
to about44.453 (not44.55; the earlier approximate inversion was incorrect).
Even hypothetical500 chargeback at our45.50 only raises70.99 to73.25.
The needed difference is acceptance path, framing, authority or interaction
history within allowed economics, rather than more index facts or cents tweaks.
No competitor replay is available to discriminate those explanations.

### Policy changes worth designing before another hosted test

1. Independent fixed-price/security/cash proposal paths; avoid presenting an
   inferior but easy-to-accept clause package before testing the preferred deal.
2. Price non-price concessions at the supplier's acceptance-equivalent price,
   not only at an equal estimated buyer cost. Track all-in cost explicitly in
   every menu entry; current text says "every package costs us the same" even
   when retained clause packages sit above goal.
3. Keep term structure when historical paths converge to the same price, and
   negotiate valuable terms while status is still open. P01 archived97.76%
   negotiated price first then moved the same price's date to April.
4. Separate the supplier's normal counter path from the buyer-offer acceptance
   path. Future tests should change one package/timing/framing variable against
   the same bid, instead of adding another similar factual argument.
5. Deduplicate semantic claim kinds as well as IDs; stop requiring new weak
   facts when none remain. Historical P08 shows rounds without new facts can
   still make progress. Preserve immediate final-offer protection: its failed
   probes remain relevant.

Rejected shortcuts: arbitrary fixed-field changes (422), unsupported rival prices,
repeating sheets, pushing finals, and asserting local scripted-simulator wins
predict hosted score gains. Local simulation verifies mechanics only. No changes
to live negotiation policy have been made. The first-place path remains a set of
evidence-backed hypotheses until authorized hosted tests show acceptance.

Independent critic reproduced the eleven-outcome P02 fit and raw-material
counterfactual scores. An apparent P03 missed-alternative gain was rejected:
its calculation omitted supplier-health cost and confused the standing sheet
with the alternative. No such guaranteed gain is claimed here.


The [four-credit baseline replication](./haggle-evaluation-protocol.md#four-credit-baseline-replication--2026-10-11)
completed on 2026-10-11: P02 repeated 73.5344%; P08 scored 63.5380% and 61.3733%.
No candidate was tested or promoted; all four authorized credits were used.

## Price-for-terms frontier after the opening screen

The [two-credit screen](./haggle-evaluation-protocol.md#two-credit-opening-exposure-screen--2026-10-11)
failed to improve either case. P08's cheaper 5.23 package scored only 60.6186%
because it carried 30-day payment and a zero-deadband clause. To turn the lesson
into an actionable negotiation hypothesis, solve the published cost equation for
the highest price at each structure, holding its other final fields constant:

| P08 structure | Maximum price matching achieved 60.6186% | Maximum matching fresh baseline 62.4556% | Maximum matching public 91.6% record |
| --- | ---: | ---: | ---: |
| 90 days, 5% deadband | 5.41697 | 5.40000 | 5.13074 |
| 90 days, no clause | 5.46605 | 5.44893 | 5.17723 |
| 30 days, no clause | 5.39365 | 5.37675 | 5.10865 |

These are offline break-even calculations, not quotes or acceptance evidence.
They reveal substantial room to offer a higher price in exchange for valuable
terms. For example, a fixed-price/90-day bid below 5.44893 would beat the fresh
baseline; a 5.17 fixed-price/90-day agreement would exceed the public 91.6%
record. Do not reveal scoring paths, internal break-even values or the public
record to the supplier. Present the commercial exchange: higher fixed base in
return for retained risk and longer payment. Keep fixed quantity/specifications.

Three distinct next hypotheses, not one bundled candidate: (1) sustained
fixed-price persistence over a preregistered window; (2) same-price request for
one valuable term while the thread remains open; (3) a priced risk/payment trade
where the allowed premium is computed before negotiation. Test shorter duration
separately from these. Existing final/agreed closing protections remain; no
post-final experiments or fabricated approvals. This frontier illustrates a
possible scoring advantage, not evidence of NoIdea's actual strategy.
