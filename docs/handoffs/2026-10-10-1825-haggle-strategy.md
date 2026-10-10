# Handoff — Haggle strategy improvement, checkpoint 1

- **Created (UTC):** 2026-10-10, approximately 18:23 UTC.
- **Next actor/session focus:** finish checkpoint 1, then test strict package-cost budgets under issue #5.
- **Sharing boundary:** project team/repository; no credentials in this record.

## Objective and authorization

Improve the negotiation strategy generically toward an **85% ten-case mean**, without supplier-specific tuning. User authorized hosted practice/model experiments and **commit + push at verified checkpoints**, then continued improvement. User subsequently requested a handover to continue later. Pause new experiments now. **85% has not been achieved.** No live-final execution or production deployment is authorized by this task.

## Checkpoints

1. **Orientation and diagnosis — complete.** Started at main `cb53689` ("push (not working) so patrick can continue"), clean tree. `0fead3b` is the earlier checkpoint the user quoted. Root manifest still identifies itself as AI_TEMPLATE; do not silently rewrite governance.
2. **RFQ correctness fix (#4) — implemented, tests passed, live batch finishing.** Two regression tests failed before the fix and pass afterward. Infeasible menus now use guarded fallback counters. A non-firm RFQ leader cannot close the case while rivals remain active. Docs updated. Independent critic found no code blocker; final review awaits batch result.
3. **Strict equal-cost packages (#5) — diagnosed, issue filed, NOT implemented.** Best next experiment; see below.
4. **Further structural/claim experiments — hypotheses only.** No new prompt file or strategy changes have been made this turn beyond checkpoint 2.

## Current working tree and processes

Baseline commit: `cb53689ff25292c633ecce40256a78fde0f85785` on main, remote `TomSzenessy/EHL-Finals-Hackathon`.

Changed: `simulation/starter-kit/arena_kit/haggle/{agent,run}.py`, `simulation/starter-kit/tests/test_haggle.py`, `docs/design.md`, `simulation/README.md`. New hosted batch: ten `simulation/starter-kit/runs/20261010-202006-*.jsonl` files. Root HANDOVER.md is ignored; a committed handoff copy is intended for cross-machine continuation.

At first writing: hosted batch shell session **3091**; `make done` session **57294**. Poll with write_stdin if still available. Do not kill live negotiations: doing so can turn them into timeouts. Check JSONL final meta records instead of launching duplicate runs. These IDs are session-local and may not survive a fresh conversation.

The batch runner was originally `/tmp/haggle-batch.py`; durable local copy `.agent/experiments/haggle-batch.py` (ignored). It uses existing Settings, Arenas, Run and configured credentials, runs up to ten cases in parallel, prints redacted summaries. It accepts optional case IDs. Original issue bodies are `.agent/experiments/issue-{4,5}.md`.

## Evidence

- Latest original complete batch `20261010-195439`: **65.25% mean**, including P05=0. Prior combined `195016`/`195017`: **72.27% mean**. Do not average timestamp subsets separately; these ten cases span two seconds.
- P05 zero traced to empty menus → settle → case-wide accept at opening price while another bidder generated its first counter. Record `runs/20261010-195439-f753.jsonl`, especially events at file lines 7–8 and 15–16.
- Focused new regressions: failed twice before fix, passed afterward.
- Full simulation suite: **49 passed, 2 skipped**, run from simulation/starter-kit with `.venv/bin/python -m pytest tests -q`. Initial sandbox run had localhost socket permission errors; rerun outside sandbox passed. Two hosted tests need dedicated ARENA_TEST_* environment variables and remained skipped.
- Ruff check for changed Python files passed.
- `make done`: change/self-healing gate passed; full template unittest suite still running at first writing. Do not claim full completion until exit result is recorded. Historical local WAL notes template-lifecycle failures after product additions; verify current outcome rather than assuming.
- Actual configured model: **gpt-6.1-sol**, built-in SYSTEM. `prompts/system.md` and haggle_settings.json are absent in this checkout, despite README mentioning them. `.env` exists; never print its contents.
- Arena quota at start: **285/450 practice sessions left**, before this batch of ten. API reachable with escalated network access. Recheck quota before new experiments.

## Why strict package budgets are the next experiment

`strategy.menu` passes **tol=0.01** for indexed structures to `price_for`. That permits a package 1% above target **total spend**, although the model is told every package costs the same. In P02, approximately €22k tolerance is almost half the €47k scoring room. This is a general arithmetic/contract defect, not a supplier-specific hypothesis.

P02's historical €349 agreement scored only **24.78%** due to a €106,278 supplier-health penalty; current €358.20 indexed agreement scores **65.92%**. Lower price alone can hurt. Removing the index clause at unchanged price/payment saves about **€17,508.82** in modeled cost (roughly 37 score points), **conditional on supplier acceptance**. This is not evidence that it will accept that structure.

Next test: remove the special index overshoot tolerance, permit only defensible numerical rounding, and show actual relative costs to the model (fresh structures and terms trades already violate the blanket "same cost" description). Maintain existing final-offer and must-have guards. Synthetic test must reject an expensive clause while preserving feasible alternatives. Evaluate across all ten cases, then repeat promising results.

Other generic hypotheses from independent audit:

- `terms_trade` only explores payment/effective date/ppm. It omits contract, index, volume, lead time, chargebacks. Test legal same-price structures ranked by buyer savings and supplier value before a final offer.
- `strategy.menu` deduplicates by price and rounded C, potentially removing materially different security/contract options; diversify supplier-valued structures before truncation.
- Test staged distinct economic claim kinds versus current front-loading. A verified claim need not be accepted as economically relevant; repeated kinds are often rejected.
- Same-price exhaustive structural bounds: latest P08 could rise from 51.39% to ~64.49% at €5.43 with 90 days/no index; P18 from 53.25% to ~56.42% at €5.40. These are mathematical bounds, not accepted offers. P18 needs a lower price for a large improvement.

## Decisions and constraints

- Optimize **total scored cost**, including supplier-health penalties; not minimum unit price.
- No supplier IDs, memorized prices, or case-specific constants in strategy. Diagnostic case examples are evidence only.
- Keep final-offer probing off: prior real attempts caused walkouts. Do not confuse negotiation with breaking API/system rules.
- Preserve verified claim markers, negotiable options, fixed terms, must-haves and alternative guards. Only standing sheet IDs can be accepted; alternative sheets must be sent back for confirmation.
- Checkpoint 1 is recovery/correctness work, not an 85% breakthrough. Report batch means, failures and stochastic uncertainty honestly.
- User requested web research: completed initial search. MIT warmth research and MESO research support testing warm/firm language and multiple packages; they do not prove this arena's response.

## Exact next actions

1. Read this file; `git status --short`, `git log -3 --oneline`; check whether checkpoint push completed below.
2. Read final meta from all `runs/20261010-202006-*.jsonl`; record ten-case mean and P05 outcome. If session 3091 survives, poll it. Poll make-done session 57294 or read the recorded result below.
3. Finish independent RFQ critic, update issue #4 evidence, commit/push checkpoint if not already done. Root ignored handover alone does not travel through git; use the committed handoff copy.
4. Under issue #5, add strict-budget synthetic regression, implement one bounded change, run simulation tests. Compare all ten hosted cases using the runner; do not combine unrelated prompt changes into the same experiment.
5. Continue only after user resumes. Record each checkpoint, repeat promising candidates, and leave an updated handover. Do not claim 85% until observed on a complete batch and replicated.

To run the local batch helper after resume, from `simulation/starter-kit`:

```sh
PYTHONPATH=. .venv/bin/python ../../.agent/experiments/haggle-batch.py
```

This needs network/model access and consumes ten practice sessions. The helper is ignored and only local; recreate from Settings/Arenas/Run if continuing on another machine.

## Relevant issues and references

- [#4 RFQ premature closure](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/4)
- [#5 package budgets](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/5)
- [#1 prompt strategy](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/1)
- [#2 missing-cost targets](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/2)
- Existing research: `docs/research/negotiation-arena-agent-strategy-2026-10-10.md`, `docs/research/haggling-floor-discovery-2026-10-10.md` (historical proposals can contradict newer evidence).
- [MIT warmth research](https://mitsloan.mit.edu/press/even-ai-wont-tolerate-a-ruthless-negotiator)
- [MESO primary paper](https://research-management.mq.edu.au/ws/portalfiles/portal/132609298/132287967.pdf)
- [Harvard contingent contracts](https://www.pon.harvard.edu/daily/business-negotiations/negotiator-toolbox-capitalize-on-differences/)

## Verified skill suggestions

Use local `.agents/skills/agent-handover/SKILL.md` and `.agents/skills/quality-loop/SKILL.md`, read this session. Independent critic is required for subjective strategy claims. No new third-party tools installed.

## Redaction and retention

No keys, credentials, raw personal data or raw exports in this handover. Share with the project team through its repository. Replace the local snapshot after the next checkpoint; retain committed handoff as historical evidence.

## Final checkpoint update

Hosted batch completed: **10/10 deals, mean 70.9865%**. P05 recovered from zero to **51.0451%**; this is below its historical best and the full batch is below the prior 72.27% baseline. Scores: P01 94.3821, P02 65.9157, P03 92.2833, P04 86.0445, P05 51.0451, P07 71.9572, P08 55.7774, P10 66.2905, P11 70.9896, P18 55.1798 (percent). All run files are complete; no live negotiation remains. No second experiment launched.

Independent critic: ship-with-residuals, no code blocker; 17 focused tests pass. The score target remains open. Repository-wide gate result and commit/push receipt to be added below.


**Pause receipt:** `make done` was interrupted at the user's handover request after its change gate passed; template tests were spending time in `npm view` dependency-drift network calls (`tools/tests/test_check_crash.py`). Exit 130, **not a full pass**. Resume the gate with network access if needed. Simulation 49/2 and focused 17/0 results above remain valid. No hosted runs remain active.

**Prompt provenance confirmed:** every run in this batch contains the exact SYSTEM text in a `kind=prompt` event, matching `meta.prompt_sha`, its source, code version, and model request messages. User explicitly asked to preserve this; retain these records and the existing UI inspection flow.
