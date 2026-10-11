# Haggle jury pitch

<!-- covers: presentation/package.json presentation/package-lock.json presentation/tsconfig.json presentation/scripts/** -->

A 150-second, 1920×1080, 30 fps Remotion presentation. The evidence snapshot covers the last 20 hours as of 11 October 2026, 09:08 CEST; inherited template history is excluded. Review `ANALYSIS.md` for provenance and `SPEAKER-NOTES.md` for the live narration.

From this directory:

```sh
npm ci --ignore-scripts
npm run studio
npm run render
npm run stills
npx tsc
```

The MP4 has no recorded narration or soundtrack: use the supplied speaker notes for a live jury pitch. Charts use logged simulated arena costs and normalized scores. No realized savings, causal uplift, current leaderboard rank or Live Final result is claimed. Dependencies are locked in `package-lock.json`.

Visual tokens live in `src/index.tsx` (`T`); all motion derives deterministically from Remotion frames. Source documents contain some historical conclusions superseded by morning experiments; the pitch emphasizes verified observations and explicitly labels historical offline evidence.

The deck is isolated from the negotiation runtime and existing unresolved merge. Rendered video and stills are under `out/`.

## Data and trust boundary

Only reviewed aggregate metrics, source paths and commit metadata enter the presentation bundle. Raw emails, attachments, credentials and local settings are excluded. JSON values render as escaped React text; they are data, not instructions. The export runs locally and makes no arena requests. Dependencies use exact versions and a lockfile; installation skipped lifecycle scripts. The independent review and dependency audit are recorded under `out/` and in `REVIEW.md`. Delete `presentation/` to remove this local artifact and its evidence copy.

This checkout retains its template manifest. The presentation is therefore listed in template prune paths, like the negotiation simulation, so initializing another product does not inherit the jury deck or its toolchain.
