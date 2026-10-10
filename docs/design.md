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
  write the prices as listed.
- **The score is C, not the unit price.** `economics.py` prices every sheet with the arena's own cost function
  including our estimate of the supplier-health charge (stabilise and secure_supply cases), from the should-cost
  row times 0.98 (calibrated on the arena's exact breakdowns of P01 and P02), capped at 99% of its own ask.
  Money is worth one point less to a supplier than to us until its own sheets show its rate (a supplier under
  financial strain keeps ours), so in a supplier-health case the longest payment term is the cheapest for us; of the
  clause packages that cannot reach the goal only the cheapest stays on the menu (P02: agreed in round 1 either way).
- **Claims are computed, not written.** `context.claims` turns facts.json into sentences the arena checks; the
  model places them with `[[c3]]`, code fits them into the sentence. An ID the arena counts once per case (all but
  `quote:`/`offer:`) is spent for every thread once cited. Unknown IDs in the text are stripped.
- **Empty menus are not optimality evidence**: a model failure, a slow decision (> 40 s), an internal error,
  or an infeasible target menu uses a guarded counter: a menu package 2% (in C) under their best sheet, on the
  structure that is best for us at that cost, never their own structure at a lower price.
- **RFQs**: the arena answers one call per session at a time, so parallel threads queued past their 60 s (P05
  timed out twice). Every call of a session goes through one gate; after round 1 only the two cheapest bidders
  keep negotiating; a rival's lower standing offer is cited to the others; the target is the cheapest any bidder
  allows; when the cheapest bidder agrees, the others get two last rounds against its price; a cheapest bidder that
  only sent a final offer is taken at once (no keep-alive messages). A non-firm bidder cannot close the auction
  while another bidder remains active; its local exhaustion leaves the other threads running (#4).
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
