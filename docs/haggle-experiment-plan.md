# Haggle experiment plan

<!-- index: design | Evidence-backed negotiation experiment protocol and promotion criteria | Designing negotiation experiments to improve mean score without unapproved practice use. -->

**Decision date: 2026-10-11. No hosted execution is authorized by this document.**
The owner has paused all practice-credit spending. This is a design and testing
protocol, not a change to the running agent. File the write-ahead issue before
implementing a behavior change; keep execution status and results in that issue.

## Objective and success measure

Maximize the mean score over cases while keeping valid deals and closing within
the final's time cap. The primary comparison is a **matched suite mean**, not a
leaderboard best-of. Track best-of separately for practice positioning.

The latest ten on code `c4fb3d5`, model `gpt-6.1-sol`, effective prompt
`45be8588d0` averaged **77.2176%**: ten deals, every must-have met, no fallback
decisions or HTTP errors. The local archive's best-of mean was **78.81%**. The
public practice snapshot showed our team at **78.9**, rank 6, and NoIdea at
**88.0**. Closing that best-of gap does not establish an 88% single-attempt
strategy. Treat 88% as an aspiration, not an expected result.

One case gaining ten score points improves a ten-case mean by one point. Rank
experiments by plausible mean gain, acceptance probability, and failure risk.
A possible 100% deal that often walks away can be worse than a reliable 75% deal.

| Case | Latest score | Public case record | Ten-case mean gain if that record is matched |
|---|---:|---:|---:|
| P08 | 64.62% | 91.6% | +2.70 points |
| P11 | 70.99% | 88.5% | +1.75 points |
| P18 | 60.61% | 75.6% | +1.50 points |
| P02 | 73.53% | 87.9% | +1.44 points |
| P05 | 86.52% | 96.5% | +1.00 points |
| P10 | 66.29% | 74.1% | +0.78 points |

These are prioritization targets, not expected uplifts. P11 ranks highly by
potential but has unresolved technical validity; P02 ranks highly by confidence
in a structural mechanism. NoIdea holds the listed records except P18. Matching
the P02/P08/P18 records alone would raise the latest mean only to about **82.85%**.
Reaching 88% also requires acceptance gains in other cases; the first three
experiments are a starting point, not a complete first-place explanation.

Evidence owners: [session findings](./haggle-strategy-analysis.md#no-credit-strategy-analysis--2026-10-11),
[current agent design](./design.md), and [published rules](../simulation/brief/brief.md).
Counterfactuals below mean **what a package would score if accepted**, not proof
the supplier would accept it. Competitor replays are unavailable.

## Evidence that changes the strategy

| Finding | Evidence | Design consequence |
|---|---|---|
| P02's best legal indexed package scores only 73.5404%; current deal is 73.5344%. | Eleven distinct historical outcomes fit supplier cost €367.60 and interest 6.6%, reproducing every C_deal to the cent; all twenty allowed payment/clause combinations evaluated. [Fit findings](./haggle-strategy-analysis.md#p02-structural-ceiling-not-price-optimizer-error). | Test acceptance of fixed-price packages. More price reduction inside the current clause is the wrong objective. |
| P02 agrees in round 1 to the indexed alternative, ending discovery. | [Latest P02](../simulation/starter-kit/runs/20261011-014457-40ab.jsonl), first send and agreement. | Keep the indexed fallback available internally instead of offering it beside the preferred deal immediately. |
| P08 reached €5.17 on a supplier-indexed sheet after repeated buyer fixed-price proposals. | [Persistence probe](../simulation/starter-kit/runs/20261010-214805-9848.jsonl), score 71.07%, versus latest 64.62%. Only first send introduced factual claims. | Separate price discovery from acceptance of the clause. Productive later rounds need not contain another factual claim. |
| P18 reached the same €5.20 with 90-day payment historically and 14-day payment recently. | [Historical P18](../simulation/starter-kit/runs/20261010-225513-7b73.jsonl): 66.35%; [latest](../simulation/starter-kit/runs/20261011-014457-bda3.jsonl): 60.61%. | Preserve payment value; a cheaper nominal alternative can send negotiation down a worse path. This is an observed comparison, not a matched causal trial. |
| P11 already rejected a bid worth more than the competitor record. | [Latest P11](../simulation/starter-kit/runs/20261011-014457-1b1d.jsonl): round 5 offers €44.44/300 ppm/zero chargeback, worth 88.716% if accepted; closes at €45.50, 70.99%. | Change the acceptance path around the bid rather than invent another cents adjustment. |
| P11's engineer offers possible €1.15 savings, but the agent declines the referral. | Same P11 run, supplier reply to round 5 and buyer round 6; no archived technical follow-through identified. | Investigate conditional technical quotations, with approval and same-case validity unresolved. Do not deploy this as an ordinary price discount. |
| P01 improved after negotiating price first and then shifting its date. | [Historical P01](../simulation/starter-kit/runs/20261010-213219-e60c.jsonl): January €132.60, then April at the same price, 97.76%. | Reserve a valuable term concession/request for a later open round when that sequencing fits the cost function. |
| Later new IDs often repeat an already-used argument kind. | Latest suite: 40 verified, 11 duplicate claims, excluding closing confirmations. Earlier tests often found identical final paths despite deeper index windows or extra facts. | Reserve genuinely independent leverage, not another record of the same kind. |

## Proposed negotiation sequence

This sequence is a candidate policy. It adapts to the case rather than using one
universal concession ladder.

1. **Prepare an acceptance map.** Price every valid structure including payment,
   index risk, supplier-health cost, quality, and the alternative. Distinguish
   our estimate from an observed accepted price. Record supplier motives,
   authority requirements, and unresolved objections. Preserve a safe fallback
   internally; a prior quote's continued validity must be checked before closing.
2. **Open on the preferred efficient structure.** Use the two strongest relevant,
   independent argument kinds by default. Make a credible binding offer and one
   question about the obstacle to acceptance. Offer alternatives only if they
   all produce an acceptable outcome; do not include an attractive-to-supplier
   inferior structure merely to satisfy a package-count instruction.
3. **Diagnose the first rejection.** Is it price, cash, security, sorting cost,
   insufficient authority, or missing proof? Answer the actual objection.
   Retain the preferred structure while making a small real move; compare total
   cost explicitly before switching to a nominally cheaper alternative.
4. **Use reserved leverage while still open.** Trade one remaining negotiable
   concession for one concrete supplier concession. Examples: full allowed term
   for fixed price; payment change for a sufficient price reduction; same-price
   later effective date in an increase case. State the exchange and put the
   complete agreement in the term sheet. New facts are optional if there is a
   substantive package change or a useful supplier-led question.
5. **Request acceptance of a complete package.** State precisely which obstacle
   the package resolves and ask whether that package can be approved. Use real
   authority information, not generic escalation or invented approval. Obtain
   the supplier's standing sheet before accepting; prose alone does not bind.
6. **Close safely.** Preserve immediate agreement and final-offer acceptance as
   the default. All structure discovery happens before firm status. Keep
   must-have rescue, alternative ceiling, timeout protection, RFQ immediate
   cheapest-final handling, and the final wave cap. A new policy must not remove
   these protections merely to chase a better benchmark number.

### What to hold back, and what to reveal early

| Leverage | Default timing | Reason / evidence |
|---|---|---|
| Strong cost rebuttal, valid rival offer, case-relevant quality evidence | Opening | Recorded first-round facts set the level of the path; withholding them can worsen later quotes. |
| An independent strong fact directly answering a predictable later objection | Reserve only in a controlled variant | A genuine later reason might prolong productive negotiation, but existing staging probes did not establish a general benefit. |
| Another index window, prior forecast, or quality/delivery rows already covered | Do not reserve as “fresh” leverage | Suppliers repeatedly count these as duplicates. |
| Buyer-valued structure request, such as date or payment improvement | Before final, potentially after price movement | P01 supports sequential price/date negotiation; P18 shows the cost of abandoning valuable payment terms. |
| Supplier-valued concession, such as an index clause | Internal fallback until its price benefit is worth its cost | P02 indexed acceptance ends discovery at a structural ceiling. Withholding it risks worse counters, so test rather than assume. |
| Technical change / engineering approval | Conditional investigation only | P11 referral is untested, but suggestions are informational and cannot be represented in the existing term schema. |

**Claim-staging test:** hold bid sequence, structures, and wording style constant.
Compare all strongest independent claims in round 1 against one strong opening
claim plus one independent strong claim on the first rejection. Measure final
C and acceptance path. Do not change the price ladder at the same time. Promote
staging only if the later benefit exceeds the weaker opening, not merely because
the supplier sends one more reply.

## Broader investigation after the failed screen

The [broader hypotheses](./haggle-breakthrough-hypotheses.md) add a reproduced
fresh-rival marker/selection failure, blocked document evidence, tender timing,
independent argument families and procedure-specific approval requests. The
opening-only candidate did not improve scores; no candidate was promoted.

## Experiments and measurement

Read the [ranked experiment cards](./haggle-experiment-cards.md) for controlled
variants, truthful framing, predicted mechanisms, and failure conditions.
The initial P02/P08 opening-only screen is complete and did not improve scores.
Prioritize the reproduced rival-identity and document-evidence mechanisms from
the broader investigation; fixed-price persistence and P18 payment preservation
remain separate hypotheses. P11 technical referrals require a validity gate.

The [evaluation protocol](./haggle-evaluation-protocol.md) defines no-credit
preparation, future screening and replication, combined-suite validation,
recording, promotion, rollback, and hidden-case limits. Neither document
authorizes hosted execution. Strong opening claims remain the default; reserved
independent facts are an experiment, while reserved concessions are the main
strategy hypothesis.
