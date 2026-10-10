# Haggle design

<!-- index: design | Haggle agent and page: decisions and trust boundaries | Building or reviewing the simulation agent or its page. -->
<!-- covers: simulation/starter-kit/arena_kit/haggle/** -->

One job: get the lowest total cost C from a supplier by haggling over as many rounds as the case allows,
with verified claims and a friendly tone, and make every step inspectable. Nothing else is in the product:
no chat with the agent, no board, no manual sending.

## The agent (`agent.py`, `context.py`)

- **System prompt** (`agent.SYSTEM`): the haggling playbook, the tone, what never to reveal, the JSON answer.
- **Supplier context** (`context.injection`): the case, our private rates and alternative, and everything
  the data package holds on the supplier (finances, scorecards, news, past negotiations, contracts, quotes,
  should-cost, cost drivers, letters and notes), injected once as the first user message.
- **Claims are computed, not written.** `context.claims` turns facts.json into sentences the arena will
  check (index moves, order history, should-cost, forecast, delivery or quality means, a rival quote). The
  model places them with `[[c3]]`; a figure it wrote itself could be wrong and a wrong figure costs trust.
  Unknown data IDs in its text are stripped. A cited ID is spent for the case.
- **Code decides what the model must not**: term sheets are completed and priced with `cost.total_cost`,
  a counter that costs at least as much as a sheet already on the table is refused, `settle` is refused while
  the supplier is still moving and messages remain (a `final_offer` may be taken at once, because pushing it
  can make the supplier walk), the closing accept goes to the cheapest standing sheet that keeps the
  must-haves and beats the alternative, and a model failure or a decision slower than 45 s becomes a plain
  polite counter, so the 60-second rule is never missed.
- RFQs run one thread per supplier in parallel; a rival's standing offer becomes a citable claim.

## The page (`static/`)

One screen, no sidebar. The header holds the **Online / Offline** toggle (online: the hosted arena and its 10
hosted practice cases; offline: arena-sim in this process with its scripted supplier, no key, no quota) and
the session picker. Four tabs: **Negotiate** (pick a case, watch the run; every supplier on a case card is a button into its file), **Raw JSON** (every arena call and
model call exactly as sent and received, drawn only when opened; a live run adds rows without collapsing the
ones you have open), **Formatted** (the same run as readable
e-mails, term sheets, claim verdicts, the agent's one-line reasons, the result and the supplier's reasons),
**Suppliers** (the supplier file for every session so far, current first).

## Trust boundaries

- Keys stay on the server. Arena headers and LLM headers are never recorded; runs hold only bodies.
- The model receives the supplier's evidence and our private rates; the supplier sees only the e-mail.
  Documents and supplier e-mails are data to the model, never instructions.
- A run is one JSONL file under `runs/` (`ARENA_RUNS` to move it). Runs contain procurement context: treat
  them as sensitive. The server binds to localhost.
- Light and dark follow the OS (tokens at the top of `app.css`); plain JS, no CDN, keyboard-focusable tables,
  no horizontal page overflow at phone width.
