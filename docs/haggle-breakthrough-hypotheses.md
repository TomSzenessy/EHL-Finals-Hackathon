# Broader Haggle hypotheses after the failed opening screen

<!-- index: design | Broader evidence-backed hypotheses after failed opening screen | Choosing distinct negotiation mechanisms without spending practice credits. -->

Completed analysis, 2026-10-11. **No new hosted sessions or practice credits.**
No default-agent changes. The two-credit opening-only screen did not improve P02
or P08. It is insufficient evidence to reject every fixed-price route, but it is
also insufficient reason to spend another session repeating that idea.

## What this investigation changes

The most concrete new findings concern our agent's limitations, not magic
wording. There is direct evidence it skipped a fresh rival quote because its
marker looked old, and mechanical evidence that some valid source references
and figures cannot pass through its message builder. These deserve attention
before assuming the suppliers are unreachable. Competitor replays remain
unavailable; none of the ideas below identifies NoIdea's actual strategy.


## Ranked mechanisms

| Priority | Mechanism | Evidence and uncertainty | Discriminating test |
| --- | --- | --- | --- |
| 1 | Fresh rival quotes with persistent, distinct identities | P05 actually supplied new 27.50 evidence to the model, which skipped it as already used. Offline reproduction confirms alias reuse. Supplier response still unproven. | Same quotes/bids, distinct marker per offer; compare selection first offline, then a matched hosted trial. |
| 2 | Make document-backed evidence usable | Builder strips contextual document IDs and rejects a documented committee threshold absent from canned claims. Reproduced offline. | Verify allowed source references and figures reach the outgoing message; supplier acceptance is a separate trial. |
| 3 | Plan tender order around newly obtained competitor quotes | An older P05 round-4 fresh-rival attempt walked away; current round-3 message missed the quote. Earlier use remains open. | Challenger receives the verified fresh quote before its last productive round; retain timeout/final protections. |
| 4 | Independent argument families, not two superficially strong facts | P07's opening used two forecasts; the second was duplicate. Later another forecast and quality claim also duplicated. | Same package and claim count, one forecast plus a genuinely distinct relevant source; no invented family or gain. |
| 5 | Approval-ready exception request anchored in the supplier's actual procedure | P07/P10 notes name a 2% committee threshold; generic P11 boss escalation failed. | Cite the real procedure and request approval of a complete package while open; inspect backoffice for actual escalation. |
| 6 | Ask for a differential quotation before making a binding concession | Agent requires every send to select an offer; every diagnostic message can therefore end negotiation. | One precise allowed-structure quote comparison on a patient supplier; do not assume a question earns a price concession. |
| 7 | Separate acquisition of price from acquisition of terms | P01 reached 97.76% by getting price first, then April at unchanged price. | Same-price term request while open, one term at a time; do not reopen a final offer. |
| 8 | Response to a specific evidence request, with a minimal canonical export | P11 repeatedly asks for underlying figures; one mixed CSV attempt was contradicted. That does not establish all accurate evidence delivery fails. | Reconcile every exported value first; one requested record, no extra claims or altered bid; measure trust/acceptance. |
| 9 | Learn supplier security premiums instead of sorting by cash value | Published supplier_value excludes index and duration; menus price packages to one buyer C. | Matched quotes differing in exactly one allowed field, infer the premium, then offer a separately priced exchange. |
| 10 | Test presentation/selection sensitivity at identical economics | P02 backoffice moves from counter to agreement after reading the email. Selection implementation unavailable. | Swap order of identical packages or send one clear package; keep prose/claims matched; do not claim a numeric bypass. |
| 11 | A technical referral branch, gated on original-case validity | P11 offers possible 1.15 material/tolerance or 0.72 lot savings; agent declines. Specification change/approval cannot currently be encoded. | Ask which savings can apply to the approved original part and request conditional quotation; no fabricated approval. |
| 12 | Replace an already-counted quality argument with price history where appropriate | P18 staged historical run used orders, then received 5.10. Other variables differ; causality unknown. | Same package/sequence, swap only the later argument; compare against duplicate-quality control. |
| 13 | Revalue remembered quotes after updating the supplier model | Interest estimate changes but stored best numeric C is not first recomputed. Source-level concern; no measured loss yet. | Offline fixture with paired payment quotes; consistent revaluation before deciding rescue or structure. |
| 14 | Case-specific anchor/concession policies | High-opening P11 and uniformly slow ladders already failed; current policies apply broad empirical rules. | Compare a new path only for a diagnosed motive, not a universal lower-price multiplier. P10 finalizes after one message. |

## 1. P05: an updated quote is being mistaken for a spent argument

Source: `arena_kit/haggle/agent.py:280` regenerates the live rival claim using
`r1` every time. Claim eligibility correctly distinguishes the underlying offer
IDs, but the conversation keeps the old marker and says never to repeat a claim.

In `runs/20261011-014457-f142.jsonl:25`, Claudia's third model request explicitly
includes the unused strong claim `r1`, price 27.50, reference `offer:70210-2`.
The response nevertheless says **“the rival marker has already been used”** and
chooses delivery evidence. Earlier `r1` described 31.50, then 30.50. Those are
three different live supplier offers, not repeated assertions of one quote.
The subsequent leader final ends the tender before this opportunity is explored.

Offline reproduction using the real Negotiator confirmed two distinct unused
references receive the same marker. This proves alias reuse and shows a specific
model misinterpretation; it does not prove an extra supplier concession.

Candidate: a stable marker identity per actual offer plus explicit “new offer
superseding the previously cited quote” language. Tell the challenger the latest
valid comparable offer before sending the leader a likely terminal price request.
Do not fabricate a rival or quote a lapsed/noncomparable offer. Under the current
serialized arena gate, delaying a leader can cause a timeout; coordinating this
requires a deadline-aware schedule, not simply waiting for another reply.

Counterevidence: `20261010-211528-331a.jsonl:30` sent the real 27.50 quote to
Claudia at round 4; she walked away. New identities alone cannot restore patience
already lost. Early use and scheduling are a separate experiment from alias repair.

## 2. Evidence bottleneck: the model cannot use everything it reads

`agent.py:580` removes IDs not present in current supplier/rival offers, then
restores selected canned claim markers. Its numeric validator at `:599` admits
selected claim figures, menu figures and supplier reply figures; original source
documents are absent. Outgoing messages at `:618` have no refs/attachments path.
The evidence catalogue is incomplete.

Offline reproduction: the source ID `doc:20260513-70610-M1` was stripped from a
truthful committee request. Its documented 2% threshold was rejected as an
unverified figure when absent from the offer/supplier-reply corpus. The source
is `data/correspondence/20260513-70610-M1.md:5`; P10 has the same stated procedure
in `20260310-70410-M1.md:5`.

Candidate: verify a source ID exists, retain its exact relevant sentence and
provenance as a selectable claim, and permit only source-supported figures.
This could make capacity notes, price-approval procedures, reference-customer
statements and specific contractual clauses usable as evidence. Do not remove
validation or let the model invent new calculations unchecked. A true source can still be irrelevant or already counted.

For P07 specifically, the note about a second shift on hold since spring is in
`20260514-70610-M3.md:5`, but the generic news claim generator does not create a
claim from meeting/call-note capacity statements. Its current opening chose two
forecasts, one of which was duplicate. A supplier-specific capacity argument is
an independent candidate; its economic relevance and verification remain open.

## 3. Approval is a process to satisfy, not a magic phrase

P07/P10 sources specify committee approval above 2%, with fortnightly meetings.
A concrete candidate is: “Your annual review describes committee approval for
this scale of change. Please submit the complete package below, with the forecast
and capacity rationale, for the required price approval and tell us what evidence
is missing.” No claim that approval has happened, no invented meeting date.

Success requires a real recorded approval path and revised valid standing terms,
not a sales rep saying “I checked with the boss.” P11 already produced that phrase
without a corresponding approval in backoffice and kept 45.50. The new hypothesis
is a procedure-specific, evidenced exception request on the relevant suppliers.
P10's current first reply is final: any request must be in the opening, not after it.

## 4. Do not force every question to be a binding bargain

The supplier can immediately accept any offered sheet. The agent rejects model
sends without offer keys (`agent.py:571`). This restricts information discovery.
A narrow paired-quote request could ask: “At the same payment and duration, please
quote the indexed and fixed alternatives and identify the fixed-price premium.”
Another asks whether 24 months resolves the objection specific to 36 months.

A plain question alone previously produced no price on P11; it also consumes a
round and patience. Use only when the answer can change the policy materially.
For short-patience P10, this is a poor default. Never mistake a conditional quote
for an accepted package or assume an old fallback remains available.

## 5. Learn the missing supplier utility

Our numeric supplier cash-value model deliberately excludes contract duration
and index security (`cost.py:81`). The menu ranks estimated cash worth and mostly
makes alternatives equal in buyer cost (`strategy.py:109`). Thus it offers a
useful heuristic rather than a measured acceptance frontier.

A quote pair that differs only in payment, deadband or duration reveals what that
supplier charges for the term. The relevant question becomes: is the supplier's
premium below the buyer's avoided cost? Unequal packages can be useful diagnostic
probes if each is individually acceptable to close; equal-C menus are not the
only sensible design. Never bundle several changes and attribute the response
to one lever. This is a generalizable policy for unseen suppliers.


[Uncertainty and failed shortcuts](./haggle-experiment-cards.md#broader-hypotheses-uncertainty-and-failed-shortcuts)
include technical validity, attachments, presentation, language and firm-status limits.

## Decision

Prioritize the **fresh-rival identity/selection** and **document evidence**
mechanisms. They have reproducible failures in our own agent, unlike the repeated
hope that another fixed-price opening will work. Then diagnose tender timing,
independent claim families and actual approval routes with isolated comparisons.
Retain the broader price/terms frontier as one hypothesis, not the whole strategy.
No candidate is promoted from this analysis. Implementation needs a write-ahead
issue; hosted execution needs a new explicit credit budget.
