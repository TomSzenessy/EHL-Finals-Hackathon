# Haggle design

<!-- index: design | Haggle agent and page: decisions and trust boundaries | Building or reviewing the simulation agent or its page. -->
<!-- covers: simulation/starter-kit/arena_kit/haggle/** -->

One job: get the lowest total cost C from a supplier by haggling over as many rounds as the case allows,
with verified claims and a friendly tone, and make every step inspectable. No chat with the agent, no board,
no manual sending.

## The agent (`agent.py`, `economics.py`, `context.py`)

- **System prompt** (`agent.SYSTEM`, overridable with a file, see Settings): the playbook (anchoring, lever
  probing, calibrated questions, loss framing, shrinking conditional concessions, persistence), tone, what never
  to reveal, the JSON answer. Every run records the prompt hash and the raw request carries the full text.
- **Supplier context** (`context.injection`): the case, our private rates and alternative, everything the data
  package holds on the supplier, a PRICE ANALYSIS (ask vs index-implied cost, past settlements, late payments,
  contract notice, signals from notes and news such as cash strain or free capacity), injected once.
- **The score is C, not the unit price.** `economics.py` prices every sheet with the arena's own cost function
  including our estimate of the supplier-health charge (stabilise and secure_supply cases), which needs the
  supplier's full cost: the should-cost row times 0.98, capped at 99% of its own ask. The 0.98 is calibrated on
  settled hosted sessions (the arena's exact breakdown implied 129.95/130.04 vs 132.64 on P01 and 367.6/367.8 vs
  374.95 on P02); with it the model reproduces `c_deal` and `c_best` of P02 within 0.15%. `plan` searches the
  allowed options for the cheapest sheet (TARGET) and `levers` shows what each change costs us. Code shows the
  model these numbers each round; the supplier never hears them. In a stabilise case a lower price can raise C.
- **Claims are computed, not written.** `context.claims` turns facts.json into sentences the arena checks
  (index windows incl. the most favourable one, order history, should-cost, forecast, delivery or quality means,
  contract notice, a rival quote), each with a usage hint and a `helps` flag. The model places up to three with
  `[[c3]]`; a figure it wrote itself could be wrong. Unknown data IDs in its text are stripped; a cited ID is spent.
- **Guards**: sheets are completed and priced; a counter that costs more than the cheapest sheet ever offered is
  refused; no counter more than 12% under their price (an insult ends the thread); `settle` is refused while
  their sheet is clearly worse than the TARGET; a worse later counter is answered by asking for the best earlier
  terms back; a model failure, a slow decision (> 45 s) or an internal error becomes a plain polite counter,
  so the 60-second rule is kept and a crash never closes the case on the opening quote.
- **`final_offer` is a stop signal.** After "final offer, please decide" any reply that is not a yes (a question,
  a counter, a restructure) ended the deal in a live run. The agent does not call the model and the case closes
  on their sheet if it beats the alternative. All room must be won before that point.
- **RFQs**: one thread and one agent per supplier, in parallel, citing rivals' standing offers. The arena ends a
  thread left silent for 60 s after the supplier's reply, taking the offer with it, so a settled thread is kept
  alive (their own standing terms sent back with thanks) until the others finish, and the final accept goes to
  the cheapest C(est) among threads the arena still lists as open, trying the next if one is refused.

## The page (`static/`)

One screen, no sidebar. The header holds the **Online / Offline** toggle (online: the hosted arena and its 10
hosted practice cases; offline: arena-sim in this process, scripted supplier, no key, no quota) and the session
picker. Tabs: **Negotiate** (pick a case, each supplier is a button into its file, watch the run), **Raw JSON**
(every arena and model call exactly as sent and received, drawn only when opened, open rows stay open),
**Formatted** (the run as readable e-mails, term sheets, claim verdicts, the agent's one-line reasons, result,
the supplier's reasons), **Suppliers** (the file of any supplier, with its sessions), **Team** (what the arena API
says about us: quota, best scores, practice board, every session, downloads, health) and **Settings** (provider,
model, base URL, endpoint, timeout, write-only API key, system prompt file). Only the tabs that show the running
negotiation redraw while it runs; Team, Suppliers and Settings never refetch or lose typed edits.

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
