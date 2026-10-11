# Haggle design

<!-- index: design | Haggle agent and page: decisions and trust boundaries | Building or reviewing the simulation agent or its page. -->
<!-- covers: simulation/starter-kit/arena_kit/haggle/** -->

One job: get the lowest total cost C from a supplier by haggling over as many rounds as the case allows,
with verified claims and a friendly tone, and make every step inspectable. No chat with the agent, no board,
no manual sending.

## The agent (`agent.py`, `strategy.py`, `economics.py`, `context.py`)

**Code decides every number; the model reads the supplier and writes.** What the hosted suppliers taught us and
the rule in code for each lesson: [`haggle-evidence.md`](./haggle-evidence.md).

- **One general playbook, no per-case rules** (`agent.SYSTEM`): every rule is stated as how suppliers behave, never
  as a case, supplier or price, because the final plays unknown suppliers. It names the natural lever per case
  type (later effective date, ppm and chargeback, covered need and delivery, fixed price vs index clause, rivals'
  prices) and the honest persuasion moves (reciprocity, small yeses, face-saving). Fixed terms are listed each round as not
  negotiable; e-mails are English only.
- **The offer menu** (`strategy.menu`): every allowed option combination priced to the same C (equal-cost
  packages), except structures that at their price cost us over 5% more than the best one (a short term over a
  longer need), terms that cost us nothing set to what the supplier asked for, its own structure first, never below
  78% of its price or above what it asked for the same structure. The model picks one to three by key and must
  write the prices as listed. **Fixed price on a rising index** (`economics.hold_fixed_price`): when every clause
  option costs us more than none and there is no supplier-health charge, the menu holds fixed-price sheets only
  (their structure without the clause, no terms trade on their clause sheet); the supplier's own clause sheets
  are still accepted when they are the cheapest for us by C (P08/P18 scripted hold 0.63-0.71 against agent
  medians 0.56/0.55).
- **The score is C, not the unit price.** `economics.py` prices every sheet with the arena's own cost function
  including our estimate of the supplier-health charge (stabilise and secure_supply cases), from the should-cost
  row times 0.98 (calibrated on the arena's exact breakdowns of P01 and P02), capped at 99% of its own ask.
  Money is worth one point less to a supplier than to us until its own sheets show its rate (a supplier under
  financial strain keeps ours), so in a supplier-health case the longest payment term is the cheapest for us; of the
  clause packages that cannot reach the goal only the cheapest stays on the menu (P02: agreed in round 1 either way).
  No package pays faster than the supplier's standard unless it is short of cash (strain news, a skonto in its
  master data, or a credit index of 240 or worse: `economics.cash_hungry`) or one of its sheets asked for it, and none pays faster than its standing sheet once that sheet granted longer payment
  (`strategy.fast_pay_trap`; `HAGGLE_FAST_PAY=1` turns it off): suppliers counter on our structure at the same price.
  Round 1 keeps free levers back for round 2: no contract beyond the scoring horizon and no lead time faster than
  the supplier quoted (`strategy.beyond_horizon`, `faster_than_quoted`; `HAGGLE_HOLD_TERM=0` turns it off). A single
  capacity-tight supplier (capacity case, allocation or full-order-book news) gets a first ask of at least 92% of its
  price (`HAGGLE_TIGHT_FIRST_ASK`): deeper first asks drew P10's final offer at once. While a supplier announces a
  step still to come ("clarify this internally", "needs approval from our management") we give only a tenth of the
  gap and never settle (`agent.OWED`, `HAGGLE_OWED_HOLD=0` turns it off). Sources: our runs and two other teams'
  published findings (WhemDev ehl-tacto, sellm), recorded in `docs/haggle-bug-list.md`.
- **Claims are computed, not written.** `context.claims` turns facts.json into sentences the arena checks; the
  model places them with `[[c3]]`, code fits them into the sentence. An ID the arena counts once per case (all but
  `quote:`/`offer:`) is spent for every thread once cited. Unknown IDs in the text are stripped. Beyond the case
  refs, `context.rival_quote` searches all facts for another company's lower quote on the case's single part (the
  supplier's own quotes are `irrelevant` to the arena); off by default, since the API brief checks only case
  quotes (`HAGGLE_RIVAL_QUOTES=1`). In a tender, `Run._keepalive` can keep an agreed leader's thread alive with new
  lower sheets while the others bid on (`HAGGLE_TENDER_KEEPALIVE=1`, off by default).
- **Empty menus are not optimality evidence**: a model failure, a slow decision (> 40 s), an internal error,
  or an infeasible target menu uses a guarded counter: a menu package 2% (in C) under their best sheet, on the
  structure that is best for us at that cost, never their own structure at a lower price.
- **Never a sheet we could not close on**: no sheet costs more than our alternative (today's contract, a second-source
  quote): the climb, the menu and the terms trade stop under it. A supplier sheet that breaks a must-have (a field it
  leaves out closes on its standard terms) is sent back once, even after a final offer, at its price with the
  must-have fields kept, before the close would walk away. All API clients of one key share its per-second limit.
- **Never the same sheets twice** (`Negotiator.no_repeat`): a supplier walked away when our sheet repeated the last
  one (P08). A repeat moves each sheet a fifth of the way to their price (at least a cent, the e-mail's figure with
  it) while it stays under their sheet and our alternative; otherwise the thread settles.
- **RFQs**: the arena answers one call per session at a time, so parallel threads queued past their 60 s (P05
  timed out twice). Every call of a session goes through one gate; after round 1 only the two cheapest bidders
  keep negotiating, and only the cheapest once a supplier reply took over 35 s (`Run.focus`: morning replies of up
  to 55 s cost both P05 runs a 409); a rival's lower standing offer is cited to the others; the target is the cheapest any bidder
  allows; when the cheapest bidder agrees, the others get two last rounds against its price; a cheapest bidder that
  only sent a final offer is taken at once (no keep-alive messages). A non-firm bidder cannot close the auction
  while another bidder remains active; its local exhaustion leaves the other threads running (#4).
- **Live Final** (`final.py`, `arena-haggle-final`): logs its model, prompt, data and Sunday release folder once at
  start (`release None` means the release is missing), then polls only the final case list, opens each case of a running
  wave once, plays a wave's cases in parallel, and 75 s before the wave's cap (or the slowest round plus 15 s)
  closes each case on its cheapest standing sheet. A crashed run is resumed from the arena: the running session is
  read from the 409 (any session id in it) or, failing that, from our own final session list. Runs are recorded
  like practice runs (mode `final`).

## The page (`static/`)

One screen, no sidebar. The header holds the **Online / Offline** toggle (online: the hosted arena and its 10
hosted practice cases; offline: arena-sim in this process, scripted supplier, no key, no quota) and the session
picker. Tabs: **Negotiate** (pick a case, each supplier is a button into its file, watch the run), **Raw JSON**
(every arena and model call exactly as sent and received, drawn only when opened, open rows stay open),
**Formatted** (the run as readable e-mails, term sheets, claim verdicts, the agent's one-line reasons, result,
the supplier's reasons), **Suppliers** (the file of any supplier, with its sessions), **Team** (what the arena API
says about us: quota, best score per case with the session and rounds behind it, unplayed hosted cases (they
count 0), every team's score per final case side by side (our rank and gap to the best per case, from
`/v1/results/{team}`; for people only, the agent never reads it), practice board, every session, downloads, health) and **Settings** (provider,
model, base URL, endpoint, timeout, write-only API key, system prompt file; the prompt box shows the prompt a new run
uses, a prompt without the `"offers"` format is refused, and every tab warns when the code on disk changed after the
server started, since Python keeps the code it imported). Only the tabs that show the running
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
