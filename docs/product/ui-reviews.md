# UI reviews

<!-- index: launch | Screenshot review history: verdicts, findings, reviewed code digests | judging UI quality or citing review evidence -->

Appended by `make ui-review` (docs/building.md). Screenshots are local in `.agent/reviews/<run>/`; look at each one, record findings, then set the verdict to pass or fix.

## Review 20261010T134159Z

<!-- review: negotiation-workbench=50c68dd42a6ae82d -->

Screenshots in `.agent/reviews/20261010T134159Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- Directory full-page captures were excessively long with all 447 cards; added 24-card progressive loading.

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: fix

## Review 20261010T134449Z

<!-- review: negotiation-workbench=a7574218e2050f8f -->

Screenshots in `.agent/reviews/20261010T134449Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- Directory pagination resolved the excessive page length. Independent session review requested full-width scorecards and a visible small-screen scroll hint; both were implemented in the next review.

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: fix

## Review 20261010T134819Z

<!-- review: negotiation-workbench=6a3e4430b28a9cb3 -->

Screenshots in `.agent/reviews/20261010T134819Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- Opened all four home captures: consistent light-paper theme is intentional in both OS schemes; supplier cards and progressive loading are readable with no page clipping.
- Opened final desktop/mobile session captures in /private/tmp/arena-ui-browser.h8rpIk/: desktop scorecards show every column; mobile tables retain readable columns within a labelled scroll region.
- Real-browser draft/review/send, one-round send, capped automatic run, 390px width and 200% zoom passed with no page errors. Independent critic: no blockers.

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: pass

## Review 20261010T140724Z

<!-- review: negotiation-workbench=5a90819481844d7a -->

Screenshots in `.agent/reviews/20261010T140724Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- Opened all four desktop/mobile captures; layout remains unclipped. Built-in local credentials are automatic and hosted-key controls are hidden locally.
- Real-browser exact Connect, automatic startup, supplier message/reply and reload restoration pass. Online mode's .env preference is enabled by default without automatic hosted connection.

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: pass

## Review 20261010T142514Z

<!-- review: negotiation-workbench=bff25307c4f38dc4 -->

Screenshots in `.agent/reviews/20261010T142514Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- none yet

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: pending

## Review 20261010T142701Z

<!-- review: negotiation-workbench=273148270f11d7c3 -->

Screenshots in `.agent/reviews/20261010T142701Z/` (local); look at every one:

- negotiation-workbench-home-default-phone-light.png
- negotiation-workbench-home-default-phone-dark.png
- negotiation-workbench-home-default-desktop-light.png
- negotiation-workbench-home-default-desktop-dark.png

Findings (screenshot, region, problem, fix):

- Desktop light/dark: local rehearsal actions are enabled and explicitly labelled, supplier cards fit their grid, and the intentionally light theme is consistent.
- Phone light/dark: cards, search and actions fit the page without horizontal clipping; controls remain reachable.
- Session screenshots and browser regressions: all conversation messages remain on one page above an editable reply; evidence/raw attempts are collapsed by default. Editing, supplier replies, next drafts, capped runs, pending-edit pause and closing confirmation passed. Mobile and 200% zoom have no page overflow.

Bar: hierarchy, spacing rhythm, type scale, and contrast hold up next to the references; every
state looks designed; touch targets at least 44 pt; nothing clipped at phone width; light and dark
both intentional.

Verdict: pass
