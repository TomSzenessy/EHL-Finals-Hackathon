# Haggle evidence

<!-- index: design | What the hosted suppliers did and the rule in code for each lesson | Changing a negotiation rule, or checking why one exists. -->

Practice replays, back office and controlled probes on the hosted arena, 2026-10-10/11 (about 300 sessions; the
probe scripts are in `simulation/starter-kit/probes/`, their sessions under `runs/` with model `scripted`). Every
row names the observation and the code that acts on it; the design itself is in [`design.md`](./design.md).

## The supplier model in one page

- **Code sets the limits, a role decides the move.** The back office shows each reply as "My call: counter / hold /
  accept / final_offer" by the role in charge. Its hard floor sits below where it stops (P11: the arena's C_best
  implies 43.90, the rep holds 45.50); a role's word ("I checked with the boss") is not evidence: the only approval
  flow ever logged fired on a much lower rival quote in a tender ("I give half the step now and check the rest").
- **Concessions come in a supplier's own step**: fixed (Kalwisz 0.50, Werdenfels 0.10 = its "2% needs the pricing
  committee") or shrinking (Donautal 0.10, 0.06, 0.04), then a hold, then `final_offer` (rounds 3-7).
- **Facts are counted by kind, once.** An accepted kind (index fall on its own cost drivers, our forecast, should-cost,
  complaints in a quality case, late notice against the contract, a rival's live offer) buys a step or lowers the
  level; the size of the fact does not matter (P11: -17.1% and -3.7% gave the same path); a second fact of a kind is
  `duplicate`; claims set how fast a supplier reaches its floor, not the floor (P11: every combination ends at 45.50).
  Owner-run firms answer "we did not know that" and move more (P01, the P05 bidders); informed ones "take it into
  account".
- **What costs trust**: an `irrelevant` fact (a rival's orders, an exchange rate: only its listed cost drivers count),
  a `contradicted` one (a figure the arena cannot match, an attached file that does not match its data), pressure or
  an ultimatum (earlier, higher final), a high first sheet (it concedes less), the same sheet sent twice (it walks).
- **What is closed**: a fixed term in a sheet (422, "an offer carries exactly the negotiable fields"); promises of
  fixed terms in the text (it asks for a binding commitment); text that differs from the sheet ("just fix the term
  sheet"); claims about what it said; escalation to the boss; our frame contract's price clause.
- **What a supplier wants is often what the case fixes** (Kalwisz: faster payment, every supplier: "which volume can
  you commit to?"). When the term is negotiable the menu trades it; when it is fixed there is no lever.
- **What works**: a warm e-mail, every accepted kind in round 1, a low reasoned anchor, small steps, accept `agreed` and
  `final_offer` at once; price each package by our total cost (money is worth about a point less to a supplier than
  to us: P02 0.659 -> 0.735); in a tender, a rival's live offer to every bidder each round.
- Leader's records we could not reach with any of the above: P11 0.885, P08 0.916, P02 0.847.

| Observed | Rule in code |
|---|---|
| A supplier that can live with one of our sheets answers `agreed`, then "our agreed offer stands" forever (P05). | Our sheets are the ceiling of the deal: a low, reasoned first sheet, then a shrinking share of the gap per round (`strategy.Schedule`); `agreed` is accepted at once. |
| Suppliers send `final_offer` after 2-6 rounds, and their final price depends on the data they were given far more than on our step size (identical finals in A/B runs). | Steps of 35/30/25/20% of the remaining gap (slower steps scored lower on P07 and P18, never higher); with two messages left, 30%. |
| Pushing after `final_offer` ended in a walk-away 3 of 3 times (P02, P04, P11): no deal scores 0. | A final offer is accepted without another word (`HAGGLE_PROBE_FINAL=1` re-enables the test, for experiments only). |
| C_best sat at 84-87% of the opening price where there is no supplier-health charge, and at the C-optimal margin where there is. | `economics.plan` searches every option down to 85% of their price; it reproduces the arena's `c_best` within 1% on P01, P02, P05 and P08. |
| New verified data moves them ("we took it into account"); a round without it gets "no new data" and a hold. | Claims carry a `strength` (12-month index falls of their cost drivers, forecast, should-cost, rival prices: strong; delivery, price history, one-month windows: weak); the prompt spends two in round 1 and one new one each round. |
| A structure first offered late was agreed at once at a price far above what it took earlier (P02). | A structure new to the supplier is priced 30% of the way from our anchor to the current step. |
| After round 1 a supplier agreed to our sheet in about a third of rounds when it sat at 86-96% of its latest counter (101 sessions); final offers come by round 3-4. | From round 2 our sheet stays at least at 92/94/95.5/96.5/97.5% of their counter (`HAGGLE_BAND`) where that lowers our cost. |
| Suppliers price payment days at their own cost of money (Nordmark: about 7% a year), and pay for security (an index clause, a long contract) far beyond its cash value. | The supplier's rate is read from its own sheets that differ only in payment days; menu packages are tagged (their structure, security, cash), and security packages stay on the menu even 1% above the goal. |
| P02: Nordmark agrees in round 1 to whichever clause package we send; at our own 8% rate the model saw every payment term as equal and sent 45 days at 358.20 (0.659, every run); the clause at 90 days and 361.50 was agreed the same way (0.735, scripted probe and agent). | Until its sheets show a rate, a supplier's money is worth one point less than ours (`economics.SUPPLIER_RATE_DISCOUNT`; strained suppliers keep ours); only the cheapest clause package that misses the goal stays on the menu. |
| A ppm commitment without a chargeback costs the supplier no cash (P11: 45.50 at 300 and at 800 ppm). | It always goes to the tightest allowed value. |
| A rival's live offer is fresh verified data every round. | RFQ: when the cheapest bidder agrees, the others get two more rounds against its price, then the case closes. |
| An accepted fact ("we took it into account") takes 2-5% off and keeps them negotiating; a round without one moves them under 1% and brings the final offer (101 sessions). Accepted: notice 7/7, should-cost 11/14, forecast 37/48, rival prices 21/31, index 47/81, quality 7/13, delivery 10/27, price history 4/44. | Claim strength follows those rates; every e-mail carries one new claim; second-of-a-kind claims with fresh IDs (an earlier forecast quarter, the year-before scorecards, an index fall ending a month earlier) are offered as weak, last-resort claims: suppliers answered "already taken into account". |
| A supplier that freezes its price still trades terms (P03: the same list price at 90 days). | When their price holds twice, we offer their own price with our best terms (longest payment, latest start, tightest ppm). |
| A banded offer in a tender or a health-charge case jumped to the supplier's price (P05, P01). | The band applies to single-supplier cases without a health charge only; in a tender each bidder is capped at the cheapest rival's sheet, ladders climb slower and open from the cheapest target any bidder allows. |
| Controlled probes (2026-10-10 evening, scripted two-line e-mails vs the agent): the suppliers' numbers follow their own code. Claims after round 1, arguments in the text, slower or plainer e-mails and deeper anchors left the price path unchanged (P08 5.58, 5.48, 5.42, 5.38 either way); deep anchors made P07 worse and drew a round-1 final from P10. Terms are re-priced about fairly (90-day payment +0.04-0.07; "no clause" came back as a 0% deadband clause). | No anchor or claim-staging tricks: the anchor stays at the target minus 20% of the room; the levers left are structure, the close and the tender. |
| In a tender, the first thread to decide anchored on its own price because the others had not priced their openings yet (P05: 35.28 to the same bidder that got 28.93 in another run). | Every bidder prepares its target before anyone opens (a barrier); in a tender the schedule records the sheet we really sent, so a fresh structure priced near the anchor does not count as a step (P05: 0.69 best before, 0.81-0.82 after). |
| The arena answers one call per session at a time: a tender bidder's final offer at 184 s was accepted only at 259 s (a rival's send and two status reads queued ahead), the timeout repeated our last sheet and the bidder walked (P05: score 0). | A tender's final offer from the cheapest bidder is accepted inside the same gate slot, with no attachment fetch or status read first; a late move's answer status is read from the thread's `timeouts`; when every thread has ended the close returns the session result instead of crashing. |
| An equal-cost menu offered a 12-month package over a 2-year need at a low price; the supplier countered on that structure at its own level and closed there (P08: 5.86 for 12 months, score 0.10). | The menu never offers a structure that, at their price, costs us more than 5% over the best structure (`TRAP_MARGIN`): short terms and low volumes go, payment, clause and date variants stay. |
| Round-1 claims set the level of the whole path, more claims do not: with none, the round-1 counter was 0.20 higher on P18 (5.70 vs 5.50, final 5.50 vs 5.30) and 0.05 on P08; a third claim added nothing over two; claims after round 1 left the path unchanged. | Round 1 carries the two or three strongest accepted kinds (unchanged). |
| Keeping a clause-free sheet while the supplier countered with its clause looked better in scripted probes (P08 0.67, 0.71), but in the agent the equal-cost price on its 0% clause fell below our previous offer and the supplier closed (0.53-0.64). | Not adopted. |
| After round 1 the model sometimes left the supplier's structure for a 14-day package and the supplier closed there, worse for us (P03: 427.49 at 14 days, 0.855, against 432.15 at 90 days, 0.923). | After round 1 menu package A (their cheapest-for-us structure) is always sent; the model may add one other. |
| A supplier's own alternative sheet is a structure it accepts, and was sometimes the cheaper one for us (P18: 5.30 at 14 days vs 5.40 at 30). | The menu builds on their sheet that is cheapest for us, not on their standing sheet. |
| An empty menu (goal below every structure's lowest price) ended in a counter on the supplier's own 12-month structure, which it agreed to (P18: 0.04). A cheaper alternative sheet ("-a") cannot be accepted directly; settling on a dearer standing sheet walked away from it (P07). | A goal below reach prices the menu at the cheapest reachable cost; the fallback picks a menu package 2% (in C) under their best sheet; a cheaper alternative is sent back before the case closes. |
| A figure the model wrote itself came back `contradicted`, and a final offer followed. A supplier's own earlier quote is `irrelevant` unless the case refers to it. | Every %, EUR or ppm figure in the e-mail must come from a placed claim, a menu price or the supplier's own e-mail, else the e-mail goes back to the model. No own-quote claims. |


2026-10-11 log-mining rules: [action plan](./haggle-action-plan.md).

Detailed night probes continue in [historical probe evidence](./haggle-probe-evidence.md).

## Current-system practice check — 2026-10-11 01:44 UTC

The ten-case result and run table are in the [dated analysis](./haggle-strategy-analysis.md#current-system-practice-check--2026-10-11-0144-utc).

## No-credit strategy analysis — 2026-10-11

The [dated strategy analysis](./haggle-strategy-analysis.md#no-credit-strategy-analysis--2026-10-11) corrects earlier hard-floor conclusions and supports the [experiment plan](./haggle-experiment-plan.md).
