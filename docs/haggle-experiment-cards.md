# Haggle experiment cards

<!-- index: design | Controlled negotiation experiment cards | Selecting a specific score hypothesis to test. -->

Part of the [experiment plan](./haggle-experiment-plan.md). Current hosted budget: **zero**.
Use the [evaluation protocol](./haggle-evaluation-protocol.md) before any trial.

## E1 — P02 sustained fixed-price acceptance

**Priority: high; confidence in structural problem: high; confidence in acceptance: open.**
The indexed score ceiling is known. At 90 days, a no-clause price up to roughly
€367.81 would match 87.9%; €361.42 would score a capped 100%. Those are private
analysis targets, never facts to reveal to the supplier.

First screen **initial package exposure**: control is the current mixed opening;
treatment has only its fixed-price packages in the opening, acknowledging the
copper risk retained by the supplier. Keep fixed fields, claims, price-generation
method, and a prespecified later fallback rule constant. Record whether removing
the readily accepted indexed opening changes acceptance or the counter path.

Separately test **persistence**: use the same fixed-price opening in both arms;
control introduces the clause after one counter, as the prior
[no-index probe](../simulation/starter-kit/probes/policies/p02_noidx.py) did;
treatment continues fixed-price negotiation over a prespecified window. This
comparison isolates fallback timing. Do not attribute an initial-exposure win
to persistence without this second comparison.

Framing candidate: “We recognise that a fixed annual price leaves the input risk
with you and will assess the fixed base accordingly. Please quote the complete
annual package with these payment terms, rather than the indexed base without
its protection.” The annual quantity and duration must remain those of the case.

Reserve the clause as a prospective fallback. Introduce it only if fixed-price
negotiation has stopped and the best current fixed-price C is worse than the
fallback. Never assume the previously observed €361.23 clause will still be
accepted after several rounds. **Success:** a valid clause-free standing sheet
with better score and no greater failure rate. **Failure:** late fallback is
priced worse, refusal/walk-away, or the fixed-price quote stays economically worse.

## E2 — P08 hedge argument × fixed-price persistence

**Priority: high; confidence: medium.** Supplier [July letter](../simulation/data/correspondence/20260706-70710-M1.md)
says material is covered at fixed prices until March 2027. The
[hedge probe](../simulation/starter-kit/probes/policies/p08_hedge.py) kept an index
clause; the best persistence probe did not combine that framing with a binding
clause-free outcome. The combination remains a hypothesis.

First isolate fixed-price persistence from argument changes. If promising, use
a 2×2 comparison: mixed versus fixed-only structures, with versus without the
supplier-specific hedge framing. Keep prices, payment, and factual claim types
matched. Preserve long payment as a separate later trade rather than bundle
every exploratory term into the first test.

Framing: “We recognise that spot falls do not reduce the material you have
already covered. Your letter places that cover through March. What fixed-price
premium do you need for the uncovered period if we commit to the full term?”
Do not pretend the hedge covers the whole contract.

At €5.17/no clause/90 days, the hypothetical score is 92.375%, against the public
91.6% record. Historical €5.17 was indexed: this combined acceptance is **not
proven**. **Success:** accepted lower-C fixed-price terms, not simply a lower
indexed price. **Failure:** rejection of fixed pricing, higher final C, or the
clause returns without a compensating discount.

## E3 — P18 preserve payment, then test portfolio framing

**Priority: high for payment preservation; confidence: medium.**
Start with a structure discipline variant: retain 90-day payment throughout
the normal price path unless the supplier explicitly gives a discount exceeding
its buyer cost. Keep claim sequence and term length unchanged. This tests the
observed €5.20/90 versus €5.20/14 loss directly.

Only afterwards add portfolio framing from the [September note](../simulation/data/correspondence/20260916-70740-M5.md):
the supplier focuses on customers with volume. Trade the longest allowed
contract for a better fixed-price package at the existing annual volume.
Do not promise more units than the case fixes. A three-year commitment beyond
a two-year scoring horizon may matter to the supplier while adding no scored
spend; that is a published lever, not demonstrated acceptance.

At €5.10/no clause/90 days the hypothetical score is 75.901%, near the public
75.6% record. Prior €5.10 outcomes were indexed. **Success:** retain payment
benefit without increasing price enough to erase it; later fixed-price variant
improves C further. **Failure:** supplier prices 90 days or fixed risk too dearly.

## E4 — P11 follow a supplier-led technical referral

**Priority: high information value; promotion blocked on technical validity.**
The engineer's €1.15 saving could bridge the gap from €45.50 to about €44.45;
the €0.72 lot-size saving alone would not. Neither figure is a promised quote.
Earlier payment, on-time payment, larger volume in prose, boss escalation,
attachments, and relaxed ppm were already tried; do not present them as new ideas.

First determine whether a technical variant can validly fulfill this case and
what counts as engineering approval in the simulation. The API calls suggestions
informational, and grade/drawing/lot are absent from negotiable fields. No source
establishes existing approval. If that gate cannot be resolved, keep this as
information gathering and do not count its hypothetical score as a valid uplift.

Conditional request: “Please provide the proposed drawing changes and a
conditional quotation for the wider-tolerance variant, retaining the quality
commitment. Any award remains subject to documented engineering approval.”
For an original-specification route, ask whether a different production lot can
deliver the same approved part and why approval is required; do not assert it can.

**Success:** a validated permissible route, a revised standing quote, and a lower
valid total cost. **Failure:** merely informational savings, unavailable approval,
unrepresented changed specifications, or a lower price whose quality penalty
erases the benefit. No fabricated technical approval or drawing change.

## E5 — P01 sequential price and date

**Priority: medium; evidence: an observed successful path.**
Compare simultaneous price/date exploration with price-first then same-price
date request while the thread remains open. Match factual arguments and payment.
Use a later date only when retaining the current price until that date lowers C;
delaying a price reduction usually sacrifices savings. Never add another message
after an agreed/final response. **Success:** the date gain survives without a
price offset. **Failure:** price resets, early final, or lower supplier-health
benefit makes total C worse. Preserve this case's already strong baseline.

## E6 — Acceptance framing and semantic claim staging

**Priority: second wave, after isolating E1–E3.**
At the same bid and structure, compare generic “please improve your price” with
an objection-specific exchange and request to approve the attached package.
State what the supplier receives and why its stated risk/cost is addressed.
Use a department or committee only where source documents or the reply identify
it. Generic boss requests have already failed; no invented authority or deadline.

Test framing separately from withholding one independent claim. A 2×2 design
can subsequently distinguish framing, staging, and their interaction. P11's
rejected €44.44 is the useful diagnostic bid, not proof that rephrasing will win.
**Success:** higher acceptance at the same economically useful bid; **failure:**
unchanged path, faster final, or lost opening leverage. More pleasant prose or
more rounds alone is not a success measure.


## Broader hypotheses: uncertainty and failed shortcuts

Companion to the [broader investigation](./haggle-breakthrough-hypotheses.md).


- **Technical savings:** 1.15 happens to match P11's price gap, but the engineering
  variant may invalidate the part. Clarify original-specification lot savings or
  real approval requirements before any award; current API calls variants
  informational. A cheaper altered part is not demonstrated score improvement.
- **Minimal evidence:** the earlier kitchen-sink CSV bundled scorecards, complaint
  rows and several unrelated levers, and was contradicted. Some exported values
  match facts.json on inspection; the exact failure cause is unknown. Therefore
  neither “attachments always fail” nor “fixing that CSV will win” is justified.
- **Package order:** staged email interpretation is observable; its numeric guard
  logic is unavailable. Test one consistent package/order change, not fake
  acceptance, contradictory sheet/text or fabricated authority.
- **Language/style:** current prompt mandates English, though the case does not.
  Source-language commercial phrasing is an optional identical-economics test,
  but there is no replay evidence it adds points. Low priority.
- **After agreement:** price firmness does not logically prove term firmness, but
  no safe score gain is established. Keep immediate agreement/final protections
  until a specifically authorized isolated test demonstrates otherwise.
- **Tried failures:** more dramatic index windows, generic boss requests, larger
  fixed volume in prose, early payment outside allowed fields, firm ultimatums,
  misleading text/sheet prices, repeated sheets and pushing final offers.
  These are not fresh breakthrough ideas.
