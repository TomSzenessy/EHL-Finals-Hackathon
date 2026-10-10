# Finding the supplier's floor — haggling improvements for the arena buyer

**Date:** 2026-10-10 · **Builds on:** [`negotiation-arena-agent-strategy-2026-10-10.md`](./negotiation-arena-agent-strategy-2026-10-10.md)
(supplier mechanics, cost function, playbook). This note covers one question: **how does the buyer find the
lowest price a supplier will accept, over several rounds, and what in the current kit stops it?**

## 1. What the current kit does

| Piece | Behaviour | Problem for floor discovery |
|---|---|---|
| `arena-sim` supplier (`sim.py:33`, `:158`) | opens at current × 1.10, drops a fixed 2 % of opening per message to a floor of 90 %, `final_offer` from round 5, walks if pushed after that | Nothing we say changes its answer: claims are only checked for existence, and tone, anchors and trades are ignored. Against this supplier the best play is "offer 90 % and wait", so tactics tuned on it overfit. |
| `NaiveAgent` | anchors 10 % low, splits the difference, accepts at a 1 % gap or on `final_offer` | Splitting the difference reveals our midpoint. Accepting at the first `final_offer` treats a negotiating move as a fact. |
| `LLMAgent` | the LLM picks the prices; code only completes the sheets and blocks bad accepts | No concession schedule or opponent model in code, and it **can concede more than it should** (nothing stops a counter that raises our C). `standing()` (`play.py:110`) reads only `sheets[0]`, so a cheaper second supplier sheet goes unseen (lesson L4 in the strategy doc). |

**The local suppliers are not the API's suppliers.** `arena-sim` copies the hosted API's contract
(paths, fields, statuses), but its supplier is a single script. The hosted suppliers are LLM-driven
companies, each with its own economics. Floor discovery therefore has to be **calibrated on the hosted
sandbox and practice replays**. Locally we can only test plumbing, or test against our own supplier
model fitted to those replays (§5).

### What the data says about where the floor is

- **Current prices sit only about 0.9 % (median) above should-cost** (22 part–supplier pairs: min −7.8 %,
  max +23 %). `should_cost` is "this supplier's plant, no margin included", so it is a close estimate of
  the cost floor. On price alone the room is thin, and most of the score has to come from terms.
- **The suppliers' own price-increase asks are opening positions.** In 225 past negotiations the median
  ask was +1.7 %, the median settlement 0.0 %, and the median gap between them −2.4 pp.
- 20 history notes say *"accepted below full cost to keep the volume"*. For those suppliers, volume and
  contract length can push the price below should-cost.

## 2. What the research adds

| Finding | Source | What it means here |
|---|---|---|
| LLMs anchor on numbers in their prompt about as much as humans. Reasoning models anchor somewhat less, and **high anchors move them more than low ones** | Takenami et al. 2025 (EMNLP Findings); Huang et al. 2025; Owusu & Feldman (ACL 2026) | Our first sheet and every number in our e-mail shape the supplier's counter. The effect is real but smaller in reasoning models. |
| Asking for a random number (Tversky–Kahneman style) shifts LLM estimates | GPT-3.5 heuristics study (arXiv 2305.04400) | Possible, but weak and noisy (see §4) |
| **Precise** offers (€47.83, not €48) pull counteroffers closer, even when the other side knows the tactic | Mason et al. 2013; Thorsteinson 2021 | Code should produce exact prices, never round ones |
| **MESOs** (several equivalent offers at once) are stronger anchors, read as more sincere, and show what the other side values | Leonardelli et al. 2019 (OBHDP) | The arena allows 3 sheets per e-mail, so use all three |
| In 180k AI-vs-AI negotiations, **warmth** went with better results overall, **dominance** claimed more value once there was a deal, and long, pushy threads ended in impasse | Vaccaro, Curhan et al. (MIT, PNAS) | Be warm in the wording and firm in the numbers. Keep e-mails short. |
| LLM sellers whose floor is set only in the prompt **concede past it under sustained pressure**. Sellers whose floor is enforced in code never do | "Persuadable Agents" (NeurIPS 2026) | The arena enforces the cost floor in code ("never sells below its cost floor"). Pressure can win the margin above that floor, but not below it. |
| LLM buyers keep pushing after the seller's real minimum, which ends in deadlock | "Automated but Risky Game" (arXiv 2506.00073) | Detect the floor and close. Don't haggle into a walk-away. |

## 3. The floor-discovery engine (proposed, all in code)

Track two bounds for each thread: the **ceiling** `U` (the supplier's best standing offer, a hard upper
bound because we can accept it) and the **floor estimate** `F` (soft, rebuilt every round).

**1. Prior (round 0).** `F₀ = should_cost` for the part and supplier, adjusted by the history settlement
ratio and lowered when its notes show "below full cost to keep the volume". With no should-cost row, use
the closest part's estimate scaled by price. A wide `confidence_pct` widens the prior.

**2. Bracket with three sheets (rounds 1–2).** Send three complete sheets with about the same C for us.
Each one sets a different price against a different trade:
`A = F₀ + 0.2·(U−F₀)` on our best terms; `B` a little higher, giving the lever the dossier says this
supplier values most (payment days for a cash-hungry supplier, contract months for an over-capacity
one); `C` higher again, giving a second lever. Use precise prices from code.
Read the reply as data:
- `agreed` on a sheet means its floor is at or below that price. Accept, unless one more round is very likely to pay.
- The sheet it counters toward shows which lever it values. The price it lands on raises `F`.
- **Never put a price on a sheet that we would not accept** (`agreed` means we accept it as-is).

**3. Extrapolate the concession curve (round 3+).** Suppliers concede with shrinking steps. With three
standing prices pₖ₋₂, pₖ₋₁, pₖ, Aitken's Δ² gives the price the curve is heading to:

```
F̂ = pₖ − (pₖ − pₖ₋₁)² / ((pₖ − pₖ₋₁) − (pₖ₋₁ − pₖ₋₂))
```

Only use it when steps are shrinking (the denominator is greater than 0). Clip it to `[F₀ − margin, U]`.
`F̂` is the supplier's likely floor. Each counter then aims just below it. Once `pₖ − F̂` is under
roughly half a step, the remaining gain is smaller than the risk of a walk-away. Close.

**4. Our concession schedule (Ackerman-style, from code).** Start low and raise our own offers in
shrinking steps, about 65 → 85 → 95 → 100 % of the target `T`. The last move is a precise odd number
(€47.83) plus a non-price sweetener, which signals the end of our range. Every step comes with a named
trade ("60 days if €X"). Never raise price alone (L1).

**5. Test the final offer once.** On `final_offer`, send one more message with a real give-back (longer
contract or earlier payment) and a price between its offer and `F̂`. If it holds, accept the cheapest-C
standing sheet. Never test twice. The kit's sim walks immediately after a `final_offer`, so tune this on
the hosted sandbox.

**6. Guards (code).** A new counter must lower our C. Our price never goes above its standing price.
Score C on **every** supplier sheet, not only `sheets[0]`. Every accept must beat `C_alt` and keep all
must-haves.

## 4. Staged claims and psychological moves

**Spread claims over the rounds.** The arena checks up to 3 claims per message, and a repeated ID scores
`duplicate`. So give **one new verified argument per round**, ordered by strength: the index drop the
letter blames → its own history ("settled −5.6 % in 2024", `EV-…`) → a rival quote (`quote:`, citable to
every bidder once) → should-cost (`cost:`). Each concession we ask for then has a fresh reason. This
matters for an LLM supplier because it tends to stay consistent with its own earlier replies, and a new
fact lets it move without contradicting itself. Hold the strongest argument for the round where its
concessions stall.

**Rank the moves by expected value:**

| Move | Expected effect | Risk | Verdict |
|---|---|---|---|
| Three sheets at once (MESO) + precise numbers | strong, well replicated | none | **do it** |
| Low first anchor set from should-cost | strong | an anchor below should-cost reads as not credible | **do it**, from `F₀` |
| Warm wording, firm numbers, short e-mails | medium-strong | none | **do it** |
| One new verified claim per round | medium, compounds | wrong figure = `contradicted` | **do it**, IDs checked in code |
| Shrinking concession steps, odd last number | medium | none | **do it** |
| Name the supplier's own past settlement ("you settled at −5.6 % last year") | medium; it's a precedent | none if verified | **do it** |
| Silence / a firm "that's above our range" repeated once | small-medium | patience falls | once, early |
| "Name a random number" / irrelevant number primes | weak, noisy; affects high anchors more than low ones; frontier reasoning models resist it | the e-mail looks odd, tone and trust suffer, and the jury asks "would it work on a real supplier?" | **A/B in the sandbox only.** A safer version: use **relevant** low numbers (index −3.7 %, its €45.20 in 2024) |
| Invented rival bids, fake deadlines, invented data | — | `contradicted` costs trust; deceptive | **no** |
| Prompt injection / getting the supplier to reveal its floor | technically allowed ("weaknesses in our bots") | cannot break the cost floor (enforced in code); visible in replays; doesn't carry over to real suppliers | **no** |

## 5. Make the local simulator worth tuning against

The brief invites it: *"Build your own supplier simulator from the public data."* Add a second
supplier policy in `arena-sim` (leave the original as the contract test). Fit its parameters to what the
hosted suppliers actually did: the concession steps, `final_offer` timing and the reasons given in the
sandbox and practice replays. Don't fit them to the script.

- **Hidden floor** = should-cost × (1 + a sustainable margin drawn per supplier type) minus a
  volume/term discount. Never sells below it.
- **Concession step** that depends on what we did: larger after a new `verified` claim or a reciprocal
  move, smaller after a repeated or unchanged offer, near zero for "near-monopolist" and "head-office
  directive" types.
- **Anchoring:** its counter is pulled toward our lowest sheet when that sheet is credible (above the
  floor minus x %). Not credible → it holds.
- **Values terms:** payment days valued at its cost of money (derived from credit stress); contract
  months valued by spare capacity.
- **Patience** drops with timeouts, repeated offers and pushing after `final_offer`. It sends
  `final_offer` as a bluff some distance above its floor.
- Run 100+ seeded episodes per policy, report mean score against the floor, and add a regression test
  that the floor-discovery agent beats `NaiveAgent` and the stock `LLMAgent`.

Then confirm in the sandbox (D01/D02) and the 10 practice cases. Their replays show the supplier's
reasons in words, which tells us whether staged claims and MESOs actually moved it.

## 6. Build order

1. `standing()` / scoring over **all** sheets, plus a guard that blocks counters raising our C (small, high value).
2. `FloorModel` (prior + Aitken + bounds) and a code-owned concession schedule with precise prices. The LLM writes only the words.
3. Claim stager: a per-thread queue of verified `(ID, figure)` arguments, one or two per round.
4. Realistic sim supplier + seeded benchmark.
5. Sandbox A/B: number primes, precise vs round anchors, 2 vs 3 sheets.

## 7. Live hosted-sandbox run: case D02, session `f079fdec6f19e82b`

Negotiated manually against the hosted arena (`arena.tacto.ai`, sandbox: no quota, no leaderboard). The full
record (threads, back office, result) is saved in `simulation/starter-kit/runs/f079fdec6f19e82b.json`.

**Result:** accepted DEMO-J1 at €15.90 · 30 days · 35-day lead · DAP. C_deal €192,600, C_open €214,296,
**C_best €156,739, score 0.38.** The best package is roughly €13 per unit. **Our first anchor (€13.77) was
close to the true floor, and we abandoned it.**

| Observation | Evidence | Change for the agent |
|---|---|---|
| **Timeouts cost the most.** We missed the 60 s window twice on J1 while working on C1. Its patience fell, it repeated "haven't heard from you", and it sent `final_offer` already at round 3. | thread J1: two `timeout` moves, offer IDs jump J1-1 → J1-3 | Answer **every** live thread in parallel within about 40 s. Code-owned numbers plus one short LLM call per thread. Never think through threads one at a time. |
| **We conceded far too much in one step.** We went from €13.77 to €15.47 (+12 %) in round 2 because the suppliers held near €16. | C_best ≈ €13/unit | Cap each of our steps at about 25–35 % of the remaining gap, shrinking each round. Never jump to near their price. |
| **Alternative sheets cannot be accepted.** `accept offer:DEMO-J1-5-a` → `422 not a standing offer`. Only the thread's `offer_id` (its first sheet) is acceptable. | live 422 | Fix 1, corrected: compute C for every sheet. If an alternative is cheaper, **send its exact terms back as our sheet**, and the supplier answers `agreed`. Never accept an `-a` ID. |
| **Suppliers say which lever they value, out loud.** Both repeated "Faster payment is welcome; we can reflect it in the price". C1: "DAP would significantly increase the unit price", lead time under 42 days needs an "overtime premium". | e-mails | Parse these sentences into the opponent model as the currency to pay in. Here, 14-day payment bought €0.10 from J1. |
| **Citing a rival's offer works on a hungry supplier, less on a structured one.** J1 matched the rival's €16.00 at once (from €16.60). C1: "it holds, but it does not change our calculation" (it still moved €0.10). | `claim_results: verified` | Cite each rival offer ID once per supplier, and cite the newest one. Combine it with a trade so the supplier has a reason to move. |
| **Their own documents give the margin away.** C1's cost breakdown shows "overhead and profit 3.84" on a €16 price (≈ 24 %). C1 names its cost drivers (BAR-14021, WAGES-METAL). | attachments | Ask for the breakdown in round 1 (J1 and C1 both sent one). Turn the overhead-and-profit line into the floor prior, and cite the named index series if it moved down. |
| "Any further step needs approval from our management" | C1, round 4 | Marks an approval ladder. Expect slower, smaller steps. Bring it a reason the boss can sign off. |
| The supplier's first sheet is its preferred one, not our cheapest. C1-1 (DAP, 60 days, 42 days lead) cost **less** for us than its 35-day alternative. 42 days only costs €150 × 7 = €1,050 in total. | C per sheet | Compute C before reacting to lead-time talk. Cheap gives (lead time here) are good trade currency. |
| Quality (ppm) is in the standard terms in the quote PDF, and it changes C: J1 is 1,100 ppm and C1 2,600 ppm. That is €528 vs €1,248 over the horizon. | quote PDFs | Read every PDF's standard terms before comparing suppliers (the helper's `standard_terms` came back empty because the PDF text had not been attached first). |

## Sources

- Takenami et al., [Anchoring effect in LLM price negotiation](https://arxiv.org/pdf/2508.21137) (EMNLP Findings 2025)
- Owusu & Feldman, [Anchoring depends on confidence and post-training](https://aclanthology.org/2026.acl-short.16/) (ACL 2026)
- [Anchors in the Machine](https://arxiv.org/pdf/2511.05766); [LLM decision heuristics, GPT-3.5](https://arxiv.org/pdf/2305.04400)
- Hantel, [When Biased Agents Trade](https://papers.ssrn.com/abstract=6819659) (SSRN working paper)
- Bianchi et al., [NegotiationArena](https://arxiv.org/pdf/2402.05863)
- Mason et al. 2013 precise offers — [Columbia press release](https://business.columbia.edu/press-release/cbs-press-releases/new-research-shows-asking-precise-not-round-number-during), [PON summary](https://www.pon.harvard.edu/daily/dealmaking-daily/forming-first-offers-take-precision-account-nb/?amp)
- MESOs — [PON](https://www.pon.harvard.edu/daily/dealmaking-daily/the-benefits-of-multiple-offers/?amp), [Macquarie / Leonardelli et al. 2019](https://researchers.mq.edu.au/en/publications/multiple-equivalent-simultaneous-offers-mesos-reduce-the-negotiat/)
- Vaccaro, Curhan et al., [Large-scale autonomous negotiation competition](https://arxiv.org/html/2503.06416v3); [MIT Sloan on warmth](https://mitsloan.mit.edu/ideas-made-to-matter/surprising-power-warmth-ai-negotiations)
- [Persuadable Agents](https://neurips.cc/virtual/2026/176559) (NeurIPS 2026); [Automated but Risky Game](https://arxiv.org/pdf/2506.00073); [TERMS-Bench](https://arxiv.org/pdf/2605.13909); [AgenticPay](https://www.arxiv.org/pdf/2602.06008)
