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

Header toggle: **Online** plays the 10 hosted practice cases on the real arena (each run uses one of your
200 daily practice sessions); **Offline** plays three examples against the built-in scripted supplier (no
key, no quota; it only teaches the API, not the real suppliers).

## What happens in a run

1. The agent opens the case and reads the supplier's file from the data package.
2. It gets a system prompt (the playbook) and the supplier context, then answers every supplier e-mail with
   a counter: a friendly e-mail, up to three term sheets, and up to two checked claims.
3. Code prices every term sheet with the published cost function, refuses counters that are not cheaper, and
   settles only when the supplier has stopped moving or the rounds are used.
4. The case closes on the cheapest standing term sheet that beats your alternative.

## The page

**Negotiate** (pick a case, watch it run) · **Raw JSON** (every arena and model request and response, as
sent; rows you open stay open while a run is still adding events) · **Formatted** (the same run as readable e-mails, term sheets, claim verdicts, reasons and result) ·
**Suppliers** (the supplier file for the current and every earlier session).

Runs are saved as `starter-kit/runs/<id>.jsonl` (git-ignored). Keys and headers are never recorded. Design
and trust boundaries: `docs/design.md`.

## Model

Any OpenAI-compatible endpoint (`LLM_BASE_URL`, `LLM_ENDPOINT`, `LLM_MODEL`, `LLM_API_KEY`) or
`LLM_PROVIDER=anthropic`. The model receives the supplier's evidence and your private rates; a local model
keeps that on your machine. `LLM_TIMEOUT` (default 45 s) bounds one call; a slower answer falls back to a
plain counter so the arena's 60-second rule is kept.

## Tests

```bash
cd simulation/starter-kit && uv run --extra ui pytest -q
```
