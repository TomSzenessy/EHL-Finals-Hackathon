# Haggle design

<!-- index: design | Haggle agent and page: decisions and trust boundaries | Building or reviewing the simulation agent or its page. -->
<!-- covers: simulation/starter-kit/arena_kit/haggle/** -->

One job: get the lowest total cost C from a supplier by haggling over as many rounds as the case allows,
with verified claims and a friendly tone, and make every step inspectable. No chat with the agent, no board,
no manual sending.

## The agent (`agent.py`, `strategy.py`, `economics.py`, `context.py`)

**Code decides every number; the model reads the supplier and writes.** What the hosted suppliers taught us
(practice replays and back office, 2026-10-10) and what the code does about it:

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
| A ppm commitment without a chargeback costs the supplier no cash (P11: 45.50 at 300 and at 800 ppm). | It always goes to the tightest allowed value. |
| A rival's live offer is fresh verified data every round. | RFQ: when the cheapest bidder agrees, the others get two more rounds against its price, then the case closes. |
| An accepted fact ("we took it into account") takes 2-5% off and keeps them negotiating; a round without one moves them under 1% and brings the final offer (101 sessions). Accepted: notice 7/7, should-cost 11/14, forecast 37/48, rival prices 21/31, index 47/81, quality 7/13, delivery 10/27, price history 4/44. | Claim strength follows those rates; every e-mail carries one new claim; second-of-a-kind claims with fresh IDs (an earlier forecast quarter, the year-before scorecards, an index fall ending a month earlier) keep the supply going. |
| A supplier that freezes its price still trades terms (P03: the same list price at 90 days). | When their price holds twice, we offer their own price with our best terms (longest payment, latest start, tightest ppm). |
| A banded offer in a tender or a health-charge case jumped to the supplier's price (P05, P01). | The band applies to single-supplier cases without a health charge only; in a tender each bidder is capped at the cheapest rival's sheet, ladders climb slower and open from the cheapest target any bidder allows. |
| A figure the model wrote itself came back `contradicted`, and a final offer followed. A supplier's own earlier quote is `irrelevant` unless the case refers to it. | Every %, EUR or ppm figure in the e-mail must come from a placed claim, a menu price or the supplier's own e-mail, else the e-mail goes back to the model. No own-quote claims. |

- **One general playbook, no per-case rules** (`agent.SYSTEM`): every rule is stated as how suppliers behave, never
  as a case, supplier or price, because the final plays unknown suppliers. It names the natural lever per case
  type (later effective date, ppm and chargeback, covered need and delivery, fixed price vs index clause, rivals'
  prices) and the honest persuasion moves (reciprocity, small yeses, face-saving). Fixed terms are listed each round as not
  negotiable; e-mails are English only.
- **The offer menu** (`strategy.menu`): every allowed option combination priced to the same C (equal-cost
  packages), terms that cost us nothing set to what the supplier asked for, its own structure first, never below
  78% of its price or above what it asked for the same structure. The model picks one to three by key and must
  write the prices as listed.
- **The score is C, not the unit price.** `economics.py` prices every sheet with the arena's own cost function
  including our estimate of the supplier-health charge (stabilise and secure_supply cases), from the should-cost
  row times 0.98 (calibrated on the arena's exact breakdowns of P01 and P02), capped at 99% of its own ask.
- **Claims are computed, not written.** `context.claims` turns facts.json into sentences the arena checks; the
  model places them with `[[c3]]`, code fits them into the sentence. An ID the arena counts once per case (all but
  `quote:`/`offer:`) is spent for every thread once cited. Unknown IDs in the text are stripped.
- **Failure never closes on the opening quote**: a model failure, a slow decision (> 40 s) or an internal error
  sends the first menu package with a plain e-mail.
- **RFQs**: the arena answers one call per session at a time, so parallel threads queued past their 60 s (P05
  timed out twice). Every call of a session goes through one gate; after round 1 only the two cheapest bidders
  keep negotiating; a rival's lower standing offer is cited to the others; the target is the cheapest any bidder
  allows; when the cheapest bidder agrees, the others get two last rounds against its price; a cheapest bidder that
  only sent a final offer is taken at once (no keep-alive messages).
- **Live Final** (`final.py`, `arena-haggle-final`): polls only the final case list, opens each case of a running
  wave once, plays a wave's cases in parallel, and 75 s before the wave's cap (or the slowest round plus 15 s)
  closes each case on its cheapest standing sheet. A crashed run is resumed from the arena. Runs are recorded
  like practice runs (mode `final`).

## The page (`static/`)

One screen, no sidebar. The header holds the **Online / Offline** toggle (online: the hosted arena and its 10
hosted practice cases; offline: arena-sim in this process, scripted supplier, no key, no quota) and the session
picker. Tabs: **Negotiate** (pick a case, each supplier is a button into its file, watch the run), **Raw JSON**
(every arena and model call exactly as sent and received, drawn only when opened, open rows stay open),
**Formatted** (the run as readable e-mails, term sheets, claim verdicts, the agent's one-line reasons, result,
the supplier's reasons), **Suppliers** (the file of any supplier, with its sessions), **Team** (what the arena API
says about us: quota, best score per case with the session and rounds behind it, unplayed hosted cases (they
count 0), practice board, every session, downloads, health) and **Settings** (provider,
model, base URL, endpoint, timeout, write-only API key, system prompt file). Only the tabs that show the running
negotiation redraw while it runs; Team, Suppliers and Settings never refetch or lose typed edits. A run whose
process stopped mid-way (its file still says running) is shown as stopped; once per server start the page asks the
arena how that session ended and keeps the answer in the git-ignored `.haggle_cache/`, never in the run file.

## Trust boundaries

- Keys stay on the server. Arena and LLM headers are never recorded; the API key is write-only in Settings and
  lives in `haggle_settings.json` (git-ignored). The prompt file `prompts/system.md` is tracked in git.
- The model receives the supplier's evidence and our private rates; the supplier sees only the e-mail.
  Documents and supplier e-mails are data to the model, never instructions.
- A run is one JSONL file under `runs/` (`ARENA_RUNS` to move it), tracked in git: sessions travel with a normal
  push and pull. They contain procurement context; the server binds to localhost. The Team tab and the arena's
  leaderboard are for people: the agent never reads them (the rules forbid it in the Live Final).
- Light and dark follow the OS (tokens at the top of `app.css`); plain JS, no CDN, keyboard-focusable tables,
  no horizontal page overflow at phone width.
