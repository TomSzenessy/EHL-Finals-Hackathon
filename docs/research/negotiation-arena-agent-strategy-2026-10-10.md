# Negotiation Arena buyer agent — reverse-engineered supplier mechanics and a general haggling strategy

**Research date:** 2026-10-10 UTC
**Kit:** [`tacto-ai/negotiation-arena-kit`](https://github.com/tacto-ai/negotiation-arena-kit) (MIT code, CC BY 4.0 data/docs)
**Scope:** how the supplier agents decide, what the score actually rewards, and a buyer policy that
derives everything at runtime — no supplier IDs, no memorised prices, no per-case constants.
**Method:** reading the kit source (`brief/`, `starter-kit/arena_kit/*`), mining the data package
(`data/world.sqlite`, `facts.json`), and ten live API calls against the sandbox (logged in §9).

**Boundary.** This is ordinary negotiation strategy: anchoring, trading terms, patience, competition,
reading a counterpart's pattern. It deliberately contains no prompt-injection or system-prompt-extraction
playbook. Getting a merchant's bot to act outside what it is authorised to accept is not bargaining — it is
manipulating someone else's system, it usually breaks their terms of service, and in real deployments the
floor is enforced in code outside the LLM anyway, so a bot saying "yes" binds nobody. The arena itself
rewards exploiting bot weaknesses; the strategy below exploits them only where a real buyer would too:
by noticing that a supplier is short of cash, that its order book is full, or that its stated final price
is a negotiating move rather than a fact.

---

## 1. What we are negotiating against

### 1.1 The contract surface

Your side of the table is the **only** scored artifact: the accepted term sheet. Prose earns nothing
directly (`brief/api.md` §"What counts": "Term sheets bind - nothing else"). Concretely:

| Channel | Binds? | How the arena treats it |
|---|---|---|
| `term_sheets` (0–3 per e-mail) | **yes** | taken exactly as sent; the deal is the sheet you accept |
| `body` prose | no | read and understood as a person would; shapes the answer |
| `refs` + IDs in the body | no | checked against `facts.json`; reported as `verified` / `contradicted` / `irrelevant` / `duplicate` |
| fields your sheet omits | **yes, against you** | close on the supplier's standard terms from its quote PDF (`cost.py:27`, `docs.standard_terms`) |

So the negotiation is a two-channel game: **numbers bind, words steer**. The failure mode of the naive
baseline (`agents/naive.py`) is that it only plays the first channel and does one thing with the second.

### 1.2 The supplier agent's internals

Each supplier is a small simulated company (`brief/brief.md` §2) with a role team behind the e-mail —
an owner or sales rep who writes, a boss who approves bigger moves, and engineering/quality/logistics/
finance/legal who answer their topics and attach documents. Four laws govern it:

1. **A cost floor.** It never sells below its own cost. Unknown to you; estimable from
   `should_cost` (`cost:<part>`, which is explicitly "bottom-up estimate of this supplier's plant, no
   margin included") plus its quotes and what it tells you.
2. **An approval ladder.** Bigger moves need the boss. Proxy in the data: `supplier_intel.group_parent`,
   `owner_type`, and quote remarks such as *"Prices as per current list; discounts not possible this
   year (head-office directive)."*
3. **Quid pro quo.** "it gives nothing without a move from you." Confirmed live (§1.3).
4. **Data is checked, not believed.** At most **3 claims per message**, the figure must sit in the same
   sentence as the ID, tolerance ±0.5 pp for percentages and ±0.5 % otherwise. `verified` ≠ persuasive;
   `contradicted` costs trust.

Inside those limits it decides as the person at the desk would, reading your whole e-mail — your sheets,
your data, and what you signal: questions, arguments, threats, appreciation, urgency. It reacts to tone
and relationship the way a person does, and **padding does not buy price**.

The reference scripted opponent (`sim.py:33`, `:158`) shows the shape of the machine: open 10 % above
your current price, concede a fixed 2 % of the opening per term sheet, floor at 90 %, agree when you meet
it, send `final_offer` from round 5, walk if pushed after. The real suppliers are LLM-driven versions of
the same contract with real per-company economics on top.

### 1.3 Observed behaviour — one live sandbox negotiation

Sandbox `case:D01` (Demo Gießerei; stabilise goal, need 4 000/yr, 2 years, current €48.60, no alternative).

| Round | We sent | It answered | Reading |
|---|---|---|---|
| 0 | — | **€52.90**, 30 d, 12 mo, from 2026-12-01, validity 30 d. Argument: *"WAGES-METAL rose 3.1 % in twelve months and is 28 % of our cost."* | +8.8 % ask, dressed in a driver argument |
| 1 | anchor €47.90 @60 d/24 mo **and** €48.90 @30 d/24 mo, asked for the cost breakdown | **€51.40**, kept its 30 d, took 24 mo and the January start. Breakdown refused: *"our team will address separately"* | Conceded €1.50 — but only for the 24-month commitment. **No move, no move.** |
| 2 | probe pair isolating payment: €49.50 @30 d vs €50.50 @60 d, asked lead time | **Two** sheets: €51.20 @60 d **and** €50.80 @30 d. Status `final_offer`. Validity 30 → 30 d | It priced 30 days of earlier cash at €0.40 ≈ 0.8 %/30 d ≈ **9.4 %/yr** implied cost of money |
| 3 | pushed €49.90 @30 d with "we can sign today" | Held **€51.20 @60 d only** (the 50.80/30 d alternative disappeared), validity dropped 30 → **7 d** | The stated final price held, but it *dropped its own cheaper option* and steered us toward the 51.20 sheet |
| — | accepted €51.20 @60 d | `c_open` €448 810.67 · `c_deal` €418 316.71 · `c_best` €408 623.99 · **score 0.759** | A simple schedule captured 76 % of the available gap |

Back office (`GET /v1/sessions/{sid}/backoffice`) shows the internal loop verbatim:
*"My call: counter."* / *"My call: hold."* / *"Read the buyer's e-mail: … term sheets; we answer with our offer."*

Five transferable lessons, all consistent with the published research on LLM negotiators:

- **L1 — Concession is a purchase, not a reflex.** The first €1.50 came with a 24-month term attached.
  Never move without a move; every concession is a trade you name.
- **L2 — Two sheets are a probe, not a choice.** Varying exactly one dimension between sheets measures the
  supplier's indifference curve. What it counters toward *is* the answer to "what do they actually want".
- **L3 — "Final offer" is a move, not a fact.** It fired on round 2 of 10, then held — test it exactly
  once with a concrete give-back; if it holds, close. Never re-test; a walk costs the case.
- **L4 — Compute C for every standing sheet, not the first one.** It steered us from €50.80@30 d to
  €51.20@60 d. Price was €400 worse, payment €2 704 better → the steered package is ≈ **€360 worse** for
  us. The steering was itself the tell.
- **L5 — Signals are pressure, not facts.** Validity shrinking 30 → 7 days and a repeated "please decide"
  are the bot performing impatience. The only real clock is our own 60 s per message.

### 1.4 What the research literature adds

Mapping the published findings onto these mechanics:

| Finding | Where it lands in the arena |
|---|---|
| Make the first offer; first-offer buyers pay less | Round 0 it quotes; our first e-mail sets the anchor both sides move from |
| Anchor hard, concede slowly, be patient | 10 rounds per thread; early acceptance banks little (the naive agent accepts early by design) |
| Opening numbers dominate final outcomes | The first sheet anchors the whole reply ladder |
| "Don't be the soft buyer"; cautious/high-concession profiles lose | Never send a single generous sheet; always send a trade |
| Read the concession curve; shrinking deltas = the floor | §3 Phase 4: when two consecutive concessions collapse to ~0, the floor is found |
| Create competition | RFQ cases run 2–3 parallel threads and rival `quote:` IDs are citable to every bidder |
| Negotiate terms, not only price | 11 negotiable fields; most are cheaper for us to give than price |
| Stated limits can be false (asserted floor €2.30 vs true €1.32) | L3: test the final offer once |
| Warm, cooperative language → more concessions *(vendor-sourced, unverified)* | Use warm-professional tone by default; it costs nothing and may pay |

---

## 2. The score is the strategy's ground truth

The case scores `(C_open − C_deal) / (C_open − C_best)`, clipped to 0…1 (`brief/api.md`,
`cost.py:162`). `C` is the total cost of covering the need over the horizon. **Every tactical decision is
a decision about `C`.** The published function (`cost.py:125`), term by term:

| Component | Formula | Reading |
|---|---|---|
| price | `pre·current + (committed − pre)·P` | `pre` = units between horizon start and `effective_date`, bought at the **old** price |
| uncovered need | `(N·H − covered)·fallback·(1 + fallback_risk)` | a short commitment is expensive, not cheap |
| payment terms | `spend · r · (d_ref − d)/360` | only paying *earlier* than our reference costs us |
| freight | `committed · freight[incoterm]` | EXW > FCA > DAP |
| late delivery | `late_cost_per_day · max(0, lead − need_lead)` | per day past need, and it can be brutal (€420/day in P01) |
| quality | `committed · ppm/1e6 · (cost_per_defect − min(chargeback, …))` | chargebacks are capped at the defect cost |
| tooling | one-off | amortised over `sold` by the supplier's own cash logic |
| index clause | `new · share · max(0, |path| − deadband)·sign(path)` | a real cost when the index moves against us |
| index risk | `new · share · index_risk_pct` | priced-in risk of holding a clause |
| relationship | `€/point · soft(sustainable_margin − supplier_margin) · years` | **only** for `stabilise` / `secure_supply` |

`committed = volume_per_year · min(contract_months/12, horizon)`, `covered = min(V, N) · years`
(`cost.py:55-65`). Consequences that flip naive intuition:

- **A longer contract is cheaper to give than a lower price** — it costs the buyer only what it *fails*
  to cover, and it is exactly what a supplier wants (volume security).
- **A later `effective_date` is free money**: the gap buys units at the old price. In the sandbox, the
  January start put ≈ 340 of 8 000 units at €48.60 instead of €51.20 → ≈ **€880** on one sheet.
- **Omitting a field is a silent concession** to the supplier's standard terms. Always send complete sheets.
- **In `stabilise` / `secure_supply` cases, squeezing a supplier below its sustainable margin is scored
  against you** (`cost.py:111`, €15 470/point/year in P01). We can price this because
  `should_cost` gives a per-supplier bottom-up cost estimate; the kit exposes
  `supplier_value()` to do it (`cost.py:71`).

The published example in the brief shows how levers compound: €41.60 at 60 days scores **0.64**; the same
€41.60 on a 12-month contract scores **0**, because half the need is uncovered and falls back at €46 plus
3 % risk. Price is one column of an eleven-column table.

---

## 3. The strategy (runtime-adaptive, nothing hardcoded)

### 3.0 Generalization contract

The hidden final shares the world and the rules of the practice set but uses new suppliers, new settings,
and — warned in the brief — up to a third of cases combining supplier and case types practice never shows.
An agent that memorised the practice suppliers meets strangers. Therefore:

- **Every number used at runtime comes from one of three places: the case file, the data package, or an
  observed message.** No supplier ID may appear in code. If you find yourself writing
  `if supplier == "sup:70110"`, delete it.
- **Every threshold is derived, not chosen.** "Low equity" means *below the median of the current
  population*; "declining credit" means *negative 12-month delta*; "concessions have stopped" means
  *two consecutive deltas below ε*. Recompute per case.
- **The policy is a mapping from computed features to a lever priority**, never a lookup of answers.
- **Offline analysis may shape the policy; it may not enter it.** The 225-row settlement statistic in §5
  is a design input and becomes a runtime feature — not a constant.
- **Accept one behaviour change as the guardrail:** every accepted deal must beat `C_alt`, and every
  must-have must hold, checked in code before the accept is sent (`llm.py:146` does exactly this).

### Phase 0 — Dossier (before the clock starts)

Suppliers can take ~a minute to reply and the clock only starts then, so all research happens up front.
Build the dossier generically with these feature extractors:

| Feature | Source | Use |
|---|---|---|
| settlement prior | `negotiation_history`: mean/median `settled_pct ÷ asked_pct` per supplier and per category | the size of the prize; sets the anchor |
| cost floor | `should_cost.unit_cost` for `(part, supplier)`; else nearest part estimate | the walk-away line, and the relationship term |
| claimed-cost drivers | `cost_drivers` weights per part → the index series that matter | builds the falsify-their-argument claim |
| price history | `price_conditions`, `quotes`, `po_lines` for the part | credible anchor, and rival prices |
| cash stress | `credit_index` vs `credit_index_12m_ago`; `equity_ratio_pct` vs population median; note keywords (`pay earlier`, `cash discount`, `bank`, `instal`) | which currency it trades in |
| capacity | `news.topic ∈ {full_order_book, allocation}`; delivery schedule XLSX | whether price will move at all |
| quality risk | latest `scorecards` (`otd_pct`, `ppm`, `colour`, `open_8d_overdue`) | ppm/chargeback levers, 8D |
| authority | `owner_type`, `group_parent`, quote remarks (`head-office directive`, `list conditions`) | whether the desk can move |
| competition | `sourcing` rows per part, `rfqs`, `quotes` | a credible alternative is the strongest lever |
| contract position | `contracts.notice_days` vs `documents.notice_days`, `contract_clauses` | renewal leverage; citable pair |
| relationship stakes | `spend_cube` FY spend share | how much a bad outcome costs *us* |

Read the trigger letter and every attached document (`trigger_doc`, quote PDF, 8D, delivery schedule) —
`docs.read_document` returns their text; the standard terms in the quote PDF are the terms you will
otherwise concede by omission.

### Phase 1 — Open: compute before you speak

1. Compute `C_open` (their standing sheet with standard terms), `C_alt`, and the must-haves.
2. Compute `C` for **every** candidate package you might ever offer, including the complete-lever
   package (longest term the horizon allows, cheapest incoterm, latest effective date, longest payment
   term). That number is your `C_best` estimate and it calibrates every later move.
3. Decide the **walk-away line** now: the price at which `C_deal` ≥ `C_alt`. Most cases have an alternative;
   some are best left without a deal, and the score treats that as a real outcome, not a failure.

### Phase 2 — Anchor and probe (rounds 1–2)

- **Be first and be firm.** Anchor at or slightly below the current price (not absurd: an anchor outside
  the plausible range reads as non-serious and the brief warns true data can meet "that's not our
  reality").
- **Send 2–3 sheets that differ in exactly one dimension each.** A/B on payment days; A/B on contract
  length; A/B on effective date. The sheet it counters toward reveals the lever; the sheets it ignores
  reveal the dead ones. This is the single highest-value move in the whole protocol and the naive agent
  never makes it.
- **Attach one falsifiable data argument, computed to the tolerance**: the index series the letter blames,
  over a legal window (one series, ≤12 months apart, ending inside the last 12 months), rounded to the
  arena's ±0.5 pp. One argument per sentence, ≤3 per message, ID and figure together.
  Worked shape: *"Electricity producer prices changed −3.7 % from 2025-08 to 2026-08 (idx:PPI-D351@2025-08, idx:PPI-D351@2026-08)."*
- **Ask one question** — cost breakdown, earliest lead time, cheaper engineering variant. Answers cost
  the supplier nothing and hand you its cost structure.
- **Never leak** urgency, a budget, a deadline, or the absence of an alternative. Blanks in the sheet
  are read as indifference.

### Phase 3 — Concession engine

Each round, move **our** package a controlled fraction of the way to theirs **and** name a price for
their move:

```
gap_k  = C(theirs_k) − C(ours_k)              # never negative
step_k = gap_k · f_k                           # f ≈ [0.50, 0.35, 0.25, 0.15, 0.10, …]
```

Rules that make it work:

- **Every counter must strictly lower our `C`.** If a "concession" raises our `C`, it is not a concession.
- **Diminishing steps** signal seriousness and keep the ladder moving; a flat ratio buys a better price
  but risks `final_offer` earlier.
- **Pay in the currency §5 says they accept.** Payment days only when `Δprice > spend·r·Δd/360`;
  contract length and volume are usually cheap for us and valuable to them.
- **Quid pro quo every time**: "we can hold 60 days if you can hold €X" / "24 months if the start moves
  to Q2". L1 — no move, no move.
- **Never send one sheet.** A lone sheet is a free concession. Two sheets let you land one while looking
  like you conceded on the other.

### Phase 4 — Opponent model and floor detection

Track each thread's standing offers as a series. Fit the concession curve from the deltas:

- deltas shrinking geometrically → still descending, keep going but extend the schedule;
- deltas flat but > 0 → normal ladder, keep the schedule;
- **two consecutive deltas < ε → the floor is found** — stop paying for rounds and close;
- `final_offer` → test **once** with a genuine give-back (as in §1.3 round 3); holds → close, walks → the
  deal was already the best available;
- `agreed` → it offered exactly our terms; accept immediately, that is a free win;
- `walked_away` / `no_bid` → stop, re-plan, and check the alternative before spending another round.

The supplier's **stated** floor is a negotiating posture, not a constraint. Asserted limits in published
bargaining studies were wrong by large margins (asserted €2.30 against a true €1.32). You never ask it to
reveal its reservation price — you infer the floor from the shape of its concession curve, which is
ordinary practice.

### Phase 5 — Close on `C`, not on price

Accept the standing sheet minimising `C` among those that (a) keep every must-have and (b) beat `C_alt`.
`must_haves` are the one cliff-edge: a broken must-have scores **0**, not "less". A deal that is 2 % worse
than the alternative still beats walking if `C_alt` is worse. And when the bot steers you between its own
sheets, take the cheaper `C`, not the recommended one (L4).

### Phase 6 — Clock, threads, and the cap

- 60 s per message from the supplier's reply; its own reply (up to ~a minute) never counts. HTTP timeout
  ≥ 180 s. A late message is a timeout: your offer repeats, patience drops, three in a row kill the thread.
- Do the thinking offline (Phase 0); keep the in-round decision to arithmetic plus one short LLM call.
- **RFQ:** threads run in parallel; a rival `quote:` may be cited to *every* bidder once each — the
  strongest lever the API offers. Keep two threads alive until the last safe round; award on `C`.
- **Deadline insurance:** ship the kit's `closing_move` pattern — `max(90 s, slowest round + 15 s)`
  before any cap, take the cheapest standing sheet that keeps the must-haves and beats `C_alt`, else walk
  away (`play.py:126`). An unfinished thread scores the alternative; a broken accept scores nothing.

---

## 4. Playbook by case type

The API declares seven types. The mechanics of each, and what the case file tells you to compute:

| Type | The real fight | Compute first | Levers, in order |
|---|---|---|---|
| `price_increase` | separate the increase from the truth | the index series the letter blames, over a legal window | anchor at current price; complete-lever package; settlement prior sets the target; **a delay in `effective_date` is free** |
| `renewal` | the notice window is leverage | letter notice vs contract notice (`doc:` + `ctr:`), the running price | keep the incumbent's terms; multi-year for stability; index clause vs fixed (§ raw_material); walk only if `C_alt` is genuinely better |
| `rfq` | three desks, one award | `C` of every sheet of every thread incl. tooling/freight/lead time | parallel anchors; rival quotes per bidder; a credible second source; award on `C`, never on the first acceptable reply |
| `bundling` | one distributor vs the sum of parts | uncovered-need cost if the bundle misses any line | volume in exchange for amortised tooling/package price; the fallback punishes an incomplete cover |
| `raw_material` | who carries the index | the case's `index_paths` vs `index_risk_pct`; `AS-14404`, `AS-14301`, `CU-NOTATION`, `WB-*` | `material_share`, `deadband_pct`, `base_month`; price the clause with the kit's formula, not by feel |
| `capacity` | secure the supply, price is secondary | `forecasts` vs the allocation, the delivery schedule XLSX | allocation share, lead-time commitment, second-source qualification, expedite costs; low OTD is a fact you may cite |
| `quality` | the supplier pays for its own defects | `sc:`/`qn:` ppm and OTD, `cost_per_defect` | `ppm_commitment`, `chargeback_eur_per_complaint`, 8D dates — price concessions *paid for* in quality commitments |

---

## 5. Counterpart adaptation — computed signals, never names

Features come from Phase 0. The classifier is a rule set over those features; the lever priority is what
the policy consumes. This is how the agent meets a supplier it has never seen.

| Archetype | Detected by | Currency | Caution |
|---|---|---|---|
| **Cash-hungry** | credit-index drop, equity below median, note says *pay earlier* / *bank is watching* / *instalment* | payment days, tooling paid up front, volume certainty | never argue its margin down — it has said it will not sign anything that lowers margin |
| **Capacity-tight** | `full_order_book`, `allocation`, low OTD with rising volume | lead time, allocation share, split volumes | price barely moves; do not bluff a walk-away you cannot execute |
| **Distressed** | credit watch / downgrade / short-time work | fast payment above all; keep the relationship alive | the walk-away is a *quality* risk, not just a price one |
| **Approval ladder** | `group_parent`, *head-office directive*, *list conditions* | contract length, volume, non-list terms | list price is fixed; argue on everything else |
| **Quality-red** | red/amber scorecard, ppm, overdue 8D | ppm commitment, chargebacks, 8D closure dates | its cost of poor quality is a legitimate offset |
| **Family / succession** | `owner_type=family`, succession news | fairness, continuity, tone, modest fairness trades | relationship language moves them more than price |
| **Near-monopolist** | single approved source in `sourcing` | terms, index caps, security, quality | least price movement available; accept it early and move on |

The *strength* of each lever comes from the **settlement prior** — the observed relationship between what
suppliers ask and what they historically settled. In this world it is stark: across **225** past
negotiations, **100 %** settled below the ask, **39 %** settled at exactly 0.0 %, **44 %** settled negative,
median `settled ÷ asked = 0.00`. So an announced increase is an opening position, not a requirement, and
anchoring at the current price is the default rather than the aggressive choice. Compute this per supplier
and per category at runtime; do not hardcode the aggregate.

---

## 6. Anti-patterns (each one is a measurable score loss)

- **Accepting the first offer.** The naive agent does exactly this and it is the baseline to beat.
- **One term sheet per e-mail.** The API allows three; three is how you measure a counterpart.
- **Sending a single cheap term** — a low price on standard terms is a pure gift.
- **Leaking urgency, budget, deadline, or "we have no alternative"** — read and used as pressure.
- **Padding.** "Verified" is not "convincing"; a true argument may meet "that's not our reality".
- **Unknown or wrong figures.** One `contradicted` claim costs trust for the whole case.
- **More than three claims per message**, or a figure without its ID in the same sentence.
- **Re-testing `final_offer`.** Test once, then close.
- **Omitting fields** and letting the standard terms close them.
- **Accepting a sheet without computing `C`** — especially a steered one.
- **Squeezing a `stabilise`/`secure_supply` supplier below sustainable margin** when you can price it.
- **Breaking a must-have.** That is a zero, not a discount.
- **Letting the clock bite** — three timeouts end the thread, and an unfinished thread scores the alternative.
- **Reading the live feed** (`/v1/events`, `/screen`, `/leaderboard`, `/results`) during the final.

---

## 7. Agent architecture this implies

The kit's `agents/llm.py` is the right skeleton but it only sees what the case file points at, and it has
no opponent model. The version that wins:

| Module | Responsibility | Deterministic? |
|---|---|---|
| `CaseModel` / `CostEngine` | the case file, standard terms, `C`, `C_alt`, must-have checks | yes — use the kit's `cost.py` verbatim |
| `DataMiner` | the Phase-0 dossier; `facts.json` lookups; documents to text | yes |
| `Dossier → Archetype` | features → lever priority (§5) | yes |
| `OpponentModel` | per-thread offer history → concession curve, floor estimate, status interpretation | yes |
| `Policy` | phases 1–5: target `C`, schedule `f_k`, package construction, close rule | yes |
| `EmailWriter` | the words: arguments with IDs, the question, the tone — never the numbers | LLM |
| `Guard` | drop unknown IDs, complete and snap sheets, refuse bad accepts, refuse moves that raise our `C` | yes |
| `Orchestrator` | parallel RFQ threads, wave polling, deadline insurance, crash resume | yes |

Principles from the brief that this structure enforces: **numbers come from code, the model writes**;
compute `C` for every sheet and let the model choose arguments and wording; do the heavy research before
opening a session; and **keep an always-valid fallback move** — if the model times out or the case looks
unsafe, send a valid trade rather than lose the case (the kit's `NaiveAgent` fallback is the right
instinct).

Calibration loop, in order: `arena-sim` for plumbing (no quota, no network) → the 10 hosted practice
cases with the replay open after each (every e-mail, the supplier's reasons in words, the exact score) →
re-run when a change is measurable. **Replays are the training signal**: they show which argument moved
which supplier and how far, which is exactly what generalises.

---

## 8. Evidence log

- **Kit source read in full:** `brief/brief.md`, `brief/api.md`, `starter-kit/README.md`,
  `arena_kit/{cost,play,sim,docs,data,client}.py`, `agents/{naive,llm}.py`, `sim_cases/*.json`.
- **Data package mined:** 447 suppliers (46 detailed), 300 negotiation events, 108 quotes, 47 RFQs,
  46 contracts, 414 scorecards, 39 news items, 208 documents, 33 index series, `facts.json`,
  `world.sqlite`.
- **Ten live API calls** (sandbox only — no practice quota spent, no `/v1/events` or leaderboard read):
  `GET /v1/me`, `GET /v1/cases?set=practice`, `GET /v1/cases?set=sandbox`, `POST /v1/sessions` (D01),
  three `POST …/messages`, one accept, `GET …/backoffice`. Result: 0.759, with the transcript in §1.3.

Everything in §2–§5 is either quoted from the kit's published mechanics or computed from the data package;
the §1.3 numbers are from the live session. Where the research literature is cited (LLM bargaining:
anchoring, patience, reading concession curves, false stated limits), it is marked as such — a benchmark
result from frontier-model tournaments, evidence about *LLM negotiators in general*, and the reason to
combine it with this arena's own mechanics rather than trust it alone.

## 9. Sources

- [`brief/brief.md`](https://github.com/tacto-ai/negotiation-arena-kit/blob/main/brief/brief.md),
  [`brief/api.md`](.../brief/api.md) — rules, cost function `C`, scoring, data IDs, what counts.
- `starter-kit/arena_kit/{cost.py,play.py,sim.py,agents/*}` — the kit's own implementation.
- Data package v1 (`data/` in the kit) — the buyer's world as of 2026-09-30.
- Published research on LLM negotiation: bilateral trade with private information (arXiv 2604.16472);
  MERIT feedback in bargaining (arXiv 2602.10467); multi-attribute bargaining (Salesforce AI Research);
  TERMS-Bench beyond deal rate (arXiv 2605.13909); honesty and credulity of LLM salesbots (arXiv 2605.31445);
  AgenticPay (arXiv 2602.06008).