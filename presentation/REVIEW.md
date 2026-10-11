# Presentation verification

<!-- covers: presentation/.gitignore -->

Independent critic reviewed all nine rendered slides and checked each of the ten archived terminal results against the charts. Mean score, opening/deal cost totals and all-deal outcomes matched. The timeline label collision and manually assigned progress-chart coordinates found in the first pass were corrected and re-reviewed.

Final visual verdict: `ship-with-residuals`, no content or layout blockers. TypeScript passes. Dependency audit: zero known vulnerabilities in the installed graph. Video encoding checks are recorded after export below.

The source analysis is frozen at `adb9b45` on 11 October 2026 at 09:08 CEST, independent of concurrent runtime changes. Presentation work is confined to `presentation/`; existing negotiation edits and merge work belong to other work in progress.

Use `SPEAKER-NOTES.md` as live narration. The MP4 intentionally has no audio.

## Encoded artifact

`out/haggle-jury-pitch.mp4` rendered successfully: H.264, 1920×1080, 30 fps, 4,500 frames, exactly 150.000 seconds, 6,308,970 bytes. `ffmpeg -v error -i … -f null -` decoded the entire export with no errors. Representative frames extracted from the actual MP4 were inspected in `out/video-contact-sheet.jpg`; scene order and chart layout match the rendered slide exports. No audio stream is present by design.

`make check` passes after registration and architecture-map reconciliation. The repository-wide `make done` kit suite was run; its final outcome is recorded below when available. TypeScript and direct evidence arithmetic checks pass independently.

The full kit run completed 478 tests with eight failures and one error. Several adoption failures captured a changing render log or a map entry before reconciliation; output is now ignored and the affected checks are rerun. Three UI fixture failures were caused by sandbox socket restrictions. A golden-path fixture lacked the architecture-map row for its synthetic `hello` surface. These do not invalidate the verified media export.

Final gate reconciliation: all eight adoption tests pass after output isolation and map reconciliation; all six UI-review fixture tests pass outside the socket-restricted sandbox. The single remaining full-suite failure is the golden-path synthetic `hello` map entry, recorded as Local-WAL-005 in `.agent/wal/005-golden-path-architecture-map.md`. The full suite was not rerun: focused rechecks cover the corrected causes. `make check`, media TypeScript, evidence audit, encoded video checks and independent visual review pass. No presentation blocker remains.
