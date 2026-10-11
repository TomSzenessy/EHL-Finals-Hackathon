# Haggle evaluation protocol

<!-- index: design | Negotiation experiment measurement and promotion gates | Preparing authorized comparisons and deciding whether a strategy improved. -->

Part of the [experiment plan](./haggle-experiment-plan.md); applies to every
[experiment card](./haggle-experiment-cards.md). Current hosted budget: **zero**.

## Testing and credit discipline

**Phase A — no-credit preparation.** Freeze candidate specification and baseline
code/prompt/model/data hashes. Reproduce archived C, including relationship
charges, and exact hypothetical package scores. Audit proposed claims and
validate term fields, options, must-haves, and alternative ceilings. Offline
replays can measure policy decisions against recorded states; they cannot invent
the supplier's response to an unobserved offer. The scripted simulator checks
plumbing and robustness, not the hosted score hypothesis.

**Phase B — future authorized screening.** Start with E1 and E2 because they have
large structural upside. An illustrative first block is four sessions: one fresh
baseline and one treatment on each case. That block is only a screen, not causal
proof. Specify cases, exact variants, hard session cap, and stopping rule before
asking for authorization. The current allowed budget is **zero**.

**Phase C — replicate survivors.** After explicit authorization, repeat promising
control/treatment pairs with fixed versions, reversing execution order to reduce
time/order effects. Four total observations per arm is a provisional promotion
minimum; this is a pragmatic small-sample gate, not statistical certainty. Stop
a branch after two comparable failures with the predicted mechanism absent.
Revisit only when new evidence changes the mechanism. Limit tuning to three
focused iterations per experiment rather than endless wording variants.

**Phase D — combine only supported changes.** Build the sequence above from
successful components. Run a matched ten-case suite, including P03/P04/P07/P10
as regression controls. An interaction can erase single-case wins; do not add
their estimated uplifts together and call that an achieved mean. Any suite uses
new credits and needs its own explicit authorization.

Record each trial's session/code/model/prompt/data identity; actual sheets and
full C breakdown; claims and their verification/novelty; stated objection and
response; reserved concession used; timeouts/retries; rounds/time; must-haves;
deal or alternative; score and reason for closure. Record failed runs, not only
the best outcome. Report variability across repetitions; the hosted supplier's
random seed is not controlled.

## Promotion, rollback, and remaining uncertainty

Promote only when the observed mean improvement survives repeat comparisons,
the intended mechanism appears in the trace, no known validity requirement is
broken, and the combined suite shows no unexplained regression. Keep the old
policy selectable until hosted evidence supports replacement. Check deadline,
model-failure, rate-limit, must-have, and alternative paths offline before a
release candidate; comply with the competition freeze and final runbook.

Practice case IDs and inferred prices are experiment fixtures. A final policy
must route by case features and supplier evidence, not memorize these targets.
It cannot read the live leaderboard/feed during the final or rely on a result
breakdown that becomes available only after closing a hidden case.

Record mean, range, worst result, deal/must-have failures, and completion time.
At the screening stage a credible positive difference earns replication, not
automatic promotion. A lower worst result or new failure earns further diagnosis;
never hide it behind best-of. The expected-score cost of a new failure must be
included in the mean. Do not require identical outcomes from a stochastic bot.

Unknowns remain: competitor strategy, acceptance of combined counterfactual
terms, portability to hidden supplier/type combinations, and P11 technical
approval validity. Document them as open questions. The central hypothesis is
that **selective package exposure and objection-specific exchanges improve the
acceptance path**. The evidence does not yet establish that hypothesis as a
first-place policy.

## Four-credit baseline replication — 2026-10-11

User authorized four sessions with the baseline first; no candidate was tested.
Two repetitions each of P02 and P08 used unchanged code `c4fb3d5`, model
`gpt-6.1-sol`, effective built-in prompt `45be8588d0`. The obsolete local prompt
file still lacks the required `offers` format and was not the effective prompt.
Exactly four session-open attempts succeeded; no replacement runs were opened.
All four completed with valid deals and satisfied must-haves.

| Case | Run in `simulation/starter-kit/runs/` | Score | Final package |
| --- | --- | ---: | --- |
| P02 | `20261011-021609-8a3d.jsonl` | 73.5344% | €361.23, 90 days, 5% copper deadband |
| P02 | `20261011-021609-6dfa.jsonl` | 73.5344% | Identical |
| P08 | `20261011-021609-a710.jsonl` | 63.5380% | €5.39, 90 days, 36 months, 5% alloy deadband |
| P08 | `20261011-021609-a6d5.jsonl` | 61.3733% | €5.41, otherwise identical |

Four-run mean: **67.9950%**. P08 mean: **62.4556%**, range **2.1648 percentage
points**. This is a selected two-case baseline, not the ten-case suite average
and not an estimate of a candidate's uplift. The earlier P08 result was 64.6204%.
Two fresh observations cannot establish a variance distribution or drift.

P02 offered the same two sheets in both runs: €357.09/no clause/30 days and
€361.23/indexed/90 days. The supplier immediately agreed to the indexed sheet.
Different prose and a Logistics referral in one replay did not change the score.
Both backoffice traces say `My call: counter` followed by the email-reader
agreeing. This repeats the staged acceptance pattern without proving a bypass.
The next discriminating experiment remains removing the indexed opening alone;
these runs did not test whether a fixed-price outcome is acceptable.

P08 kept the same indexed opening but chose different fixed-price alternatives
(30/14 versus 60/14 payment days). Both then used only indexed packages in rounds
2–4, and both ended on round-4 final offers. Supplier main-price paths were
5.54 → 5.45 → 5.41 → 5.39 and 5.54 → 5.48 → 5.44 → 5.41. Volume was explicitly
credited in round 2; delivery was verified without changing the calculation;
quality was described as a fact kind already taken into account. Later price
movement still occurred despite ineffective delivery/quality claims. Staging
those claims is therefore not demonstrated incremental leverage.

One P08 supplier explicitly refused fixed pricing over 36 months; the other
proposed index protection for that duration. The agent then accepted the need
for index protection in its prose and abandoned fixed-price sheets. This supports
testing fixed-price persistence and contract duration separately. It does not
show that the refusal can be overcome. Repeated claims that the same long-term
commitment and index protection are new concessions should be removed from a
future framing variant, after isolating structure changes.

**Decision:** preserve the baseline; no strategy is promoted from these four
runs. Test P02 initial package exposure first, then P08 persistence without new
hedge framing. Small P08 gains near two percentage points need replication;
one favorable replay would be weak evidence. The four authorized credits are
exhausted and further hosted experimentation requires new authorization.

## Two-credit opening-exposure screen — 2026-10-11

User authorized one candidate run each on P02 and P08. The isolated
[`opening_fixed.py`](../simulation/starter-kit/probes/opening_fixed.py) subclass
filtered indexed menu entries in **round 1 only**, preserving existing menu
prices and keys. Later policy, model `gpt-6.1-sol`, code `c4fb3d5`, effective
prompt `45be8588d0`, claim generation and price generation were unchanged.
This tests initial exposure, not sustained fixed-price persistence. Source and
probe SHA `bfcdc29ce028e64eb6ee03cb85396f3916fcc2e193024db64c8c056c3db7f83b`
are embedded in both replay metadata. Default agent was not edited.

Write-ahead record: Local-WAL-001. The issue adapter used a local record because
manifest GitHub target and checkout origin conflict; no repository-target change
was made. Offline checks confirmed filtering without repricing, restoration in
later rounds, fixed-only opening fallback and a shared two-open cap. Exactly two
successful session opens occurred; both runs completed, kept must-haves and had
no HTTP errors, model errors or fallback decisions. No replacements were run.

| Case | Candidate replay | Score | Fresh baseline mean | Difference |
| --- | --- | ---: | ---: | ---: |
| P02 | `20261011-023239-3e55.jsonl` | 73.4801% | 73.5344% | −0.0543 pp |
| P08 | `20261011-023239-be3a.jsonl` | 60.6186% | 62.4556% | −1.8370 pp |

Selected two-case mean: **67.0493%**, versus **67.9950%** for the four baseline
runs (−0.9456 pp). One candidate observation per case is a screen, not a reliable
causal estimate. Removing entries also changes the model's choice of remaining
packages and prose. P02 added a 45-day fixed option; P08 used the identical
4.89/30 and 4.87/14 fixed opening sheets and claim IDs of baseline `a710`, with
different prose. No lower-opening-price experiment was conducted.

P02 stayed open and quoted fixed-price 370.52/45 days and 369.50/30 days after
crediting volume. Round 2 restored the original menu: buyer offered fixed
362.41/45 days and indexed 361.01/90 days. Supplier immediately agreed to the
indexed sheet. The final indexed deal scored slightly worse despite its lower
unit price, consistent with the supplier-health optimum. Withholding the clause
for only one round did not improve the result. A fixed-price path was available,
but its eventual acceptance at a better total cost remains unknown.

P08 supplied its own indexed counter in round 1: 5.35/30 days/zero deadband,
plus 5.45/14 days/5% deadband. It again said 36 months required index protection.
The agent built on the main counter from round 2, offering 4.81, 5.06 and 5.12
on its structure. Supplier moved 5.35 → 5.32 → 5.28 → 5.23 and ended at round 4.
Final package was **5.23/30 days/36 months/zero deadband**. A final alternative
5.35/30 days/5% deadband was also available; acceptance chose the main sheet.
Quality was marked duplicate; delivery was verified without altering calculation.
The fresh-indexed-structure anchor reset made round-2 price lower than round 1;
that is existing baseline behavior, not a second intentional treatment.

### P08 structure diagnosis, calculated offline

Published `total_cost` reproduces actual C=1,029,454.37 and score 60.6186%.
At the **same hypothetical 5.23 price**, changing payment alone to 90 days would
score 68.1488%; changing only deadband to 5% would score 73.3259%; both would
score 80.8561%. No-clause/90 days would score 85.9390%. These are arithmetic
counterfactuals, not supplier-approved offers. The payment loss is 7.5302 points;
the zero-versus-5% deadband loss is 12.7073 points at these fixed terms.
Thus the lower headline price concealed significantly worse structure.

**Decision:** do not promote the opening-only filter. Next separately test
fixed-price persistence; if a clause is eventually traded, explicitly negotiate
payment and deadband instead of accepting the supplier's full counter structure.
The supplier's 36-month objection also warrants an independent shorter-term
comparison. Do not bundle these changes or claim hypothetical 80–86% scores as
achieved. Both authorized credits are spent; no further hosted tests authorized.
