# Shared negotiation prompt evaluation

The prompt override is `starter-kit/prompts/system.md`. It applies to every new dashboard run; existing runs
keep the prompt they started with. Reset to the built-in prompt in Settings to roll back. The evaluation
addresses [issue #1](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/1).

The source rules are the [Arena FAQ](https://arena.tacto.ai/faq), `brief/brief.md` and `brief/api.md`. The
objective is total cost over the case's fixed need and horizon; supplier health, uncovered need, payment,
quality and index risk can outweigh unit-price savings. Hidden best attainable cost is fixed. Verified
claims do not guarantee that a supplier will make a concession.

## Method and provenance

The comparison uses the existing configured `gpt-6-luna` model and hosted practice suppliers. Each variant
is a separate negotiation, with at most three concurrent sessions per evaluation process. Supplier replies
are stochastic. One baseline and one retained-strategy run per case cannot establish a reliable causal
improvement. No final-wave, leaderboard-driven strategy or hidden-test result is claimed.

The first broad revision weakened the opening offers and was rejected. A second focused revision also
underperformed on the motor and bearing cases. The retained third strategy preserves the original strong
opening and adds targeted corrections: avoid double-counting the supplier-health charge, require complete
binding packages, keep proposed terms out of prose, use relevant checked evidence, move toward agreement
after a refusal, and test economically useful structures before a final offer.

Scored runs record the snapshot of their system text in the raw model request and evaluation metadata.
After the third strategy was snapshotted, three source clarifications made the illustrative JSON valid,
made multiple packages conditional on valid alternatives, and clarified that uncovered need is a cost
rather than an automatic validity failure. Local contract checks cover these clarifications; the optional
external replay was blocked by automatic approval review because it would resend recorded private
negotiation context. It was replaced by local checks. The final clarified text has not been replayed against
all hosted suppliers.

## Verification boundaries

The full starter-kit suite passed: **40 passed, 2 skipped**, with the two hosted-suite skips caused by unset
optional test configuration. Separate live practice runs provide the hosted evidence. Local contract checks
validate the prompt's example JSON and the recorded binding messages' field completeness, finite prices and
claim counts. Prompt text alone cannot guarantee that a model follows every instruction: occasional
redundant claim wording remains in observed e-mails, even where the claim was verified.

Two existing runner limitations are tracked separately: [optimistic missing-cost targets and settlement
retries](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/2), and [effective prompt provenance in
normal run metadata](https://github.com/TomSzenessy/EHL-Finals-Hackathon/issues/3). Evaluation runs add the
hash explicitly; normal runs retain the actual text in the raw model request.

All recorded evaluations are in `starter-kit/runs/`. Review the corresponding result, cost breakdown and
supplier replies in the dashboard before drawing conclusions from an individual score. Scores from an
earlier model or previous team-best run are not treated as same-model baselines.
