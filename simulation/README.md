# Haggle

<!-- covers: simulation/starter-kit/** simulation/data/** simulation/brief/** -->

An agent that haggles a supplier's price down over every round a case allows, using verified claims and a
friendly tone, and a page to inspect everything it did. Built on the Tacto Negotiation Arena kit
(`brief/` has the API and the rules, `data/` the data package, `starter-kit/` the code).

```bash
cd simulation/starter-kit
cp .env.example .env          # ARENA_API_KEY, ARENA_DATA=../data, LLM_MODEL, LLM_API_KEY
uv sync --extra ui
uv run --extra ui arena-haggle   # http://127.0.0.1:8100
```

## Run it on a new machine

The supplier dataset is part of the repo (`simulation/data`), so you only add your keys.

1. Install [uv](https://docs.astral.sh/uv/). It fetches Python 3.12 itself.
2. In the cloned repo, run:

   ```bash
   cd simulation/starter-kit
   cp .env.example .env
   uv run --extra ui arena-haggle
   ```

3. Open `.env` and set `LLM_MODEL` and `LLM_API_KEY` for the agent. For Online mode, also set
   `ARENA_API_KEY` (your team key). Offline mode needs only the model keys.

`.env` stays on your machine and is never committed, so the keys are entered once per machine. The page
opens at http://127.0.0.1:8100.

## Online and offline

The header toggle: **Online** plays the 10 hosted practice cases on the real arena (each run uses one of your
200 daily practice sessions); **Offline** plays three examples against the built-in scripted supplier (no
key, no quota; it only teaches the API, not the real suppliers).

## What happens in a run

1. The agent opens the case and reads the supplier's file from the data package.
2. It gets a system prompt (the playbook) and the supplier context with a price analysis, then answers every
   supplier e-mail with a counter: a friendly e-mail, up to three term sheets, and up to three checked claims.
3. Code prices every term sheet with the arena's own cost function plus an estimate of the supplier-health
   charge (so it optimises the score, not just the unit price), refuses counters that are not cheaper or that
   insult the supplier, and settles only when the supplier has stopped moving or the rounds are used. A
   supplier's "final offer" is accepted without another message: replying to it ended a deal in practice.
4. The case closes on the cheapest standing term sheet that beats your alternative. In an RFQ, one agent
   negotiates with each supplier in parallel and settled threads are kept alive until the others finish.

## Supplier files

Every supplier on a case card on the Negotiate page is a button (for example "Selvbrunn Drive Systems GmbH ›").
It opens the Suppliers tab on that supplier's full file, no run needed first: company and finances, delivery
and quality by quarter, news, past negotiations, prices, quotes, should-cost, contracts and clauses, spend, and
the full text of every letter and note. The tab also lists every session you have run with that supplier.

## The page

**Negotiate** (pick a case, watch it run; each supplier on a case is a button that opens its full file) ·
**Raw JSON** (every arena and model request and response, as sent; rows you open stay open while a run adds
events) · **Formatted** (the same run as readable e-mails, term sheets, claim verdicts, reasons and result) ·
**Suppliers** (the file of any supplier and its sessions) · **Team** (what the arena API says about us: quota,
best scores, practice leaderboard, all sessions, downloads) · **Settings** (model and system prompt file).

Sessions are saved as `starter-kit/runs/<id>.jsonl` and tracked in git, so a normal `git push` and `git pull`
syncs them. Keys and headers are never recorded. Design and trust boundaries: `docs/design.md`.

## Model and system prompt

Set them on the Settings tab (or in `.env`): any OpenAI-compatible endpoint (`LLM_BASE_URL`, `LLM_ENDPOINT`,
`LLM_MODEL`, `LLM_API_KEY`) or `LLM_PROVIDER=anthropic`. The page stores them in `haggle_settings.json`
(git-ignored; the API key is write-only). The system prompt is the file `starter-kit/prompts/system.md`
(tracked in git; without it the built-in prompt in `agent.py` is used). Every run records the prompt hash.
The model receives the supplier's evidence and your private rates; a local model keeps that on your machine.
`LLM_TIMEOUT` (default 45 s) bounds one call; a slower answer falls back to a plain counter so the arena's
60-second rule is kept.

## Tests

```bash
cd simulation/starter-kit && uv run --extra ui pytest -q
```
