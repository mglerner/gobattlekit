# GoBattleKit

A Pokémon GO PvP companion app built with Python/BeeWare (Briefcase + Toga).

## Key info
- Bundle ID: com.mglerner.gobattlekit
- Apple Developer team: MF55GHNQC2 (mglerner@gmail.com, Individual; renews
  2027-03-21). NOTE: an old "Apple Development" cert for a stale team
  `6TV57R6ZCC` lingers in the keychain — it is NOT the team, ignore it.
- Repo: https://github.com/mglerner/gobattlekit
- Current version: 0.0.31 (0.0.24 on TestFlight)
- venv: ~/coding/MGLPoGo/.venv
- Project: ~/coding/MGLPoGo/gobattlekit

## Build process
See DEVELOPER_NOTES.md — always use `./prepare_ios.sh` instead of `briefcase create iOS` directly.

## Architecture
- `src/gobattlekit/screens/` — all UI screens
- `src/gobattlekit/data/` — data layer (IV checker, thresholds, gamemaster)
- `src/gobattlekit/theme.py` — all colors and button styles
- `src/gobattlekit/app.py` — main app, screen navigation

## Threshold spreads come from pogo-simulator (read-only input)

App IV thresholds in `src/gobattlekit/data/default_thresholds.toml` are
produced from the `../pogo-simulator` repo: `tools/threshold_export/`
`export_thresholds.py` reads that repo's `thresholds/*.toml` + deep-dive
replay blobs; `bundle_into_app.py` merges them in. The bundler is
**Great-league only** — Ultra/Master targets are hand-maintained in
`default_thresholds.toml` and preserved across re-bundles. See
`tools/threshold_export/README.md` for the contract.

## Current priorities
1. TestFlight 0.0.28 build + device verification — run through
   `docs/device_test_checklist.md` (covers the 2026-06-11/12 deep-review
   fixes that need eyes on a device; checklist also has the Android
   blocker, SI5)
2. App Store readiness pass (Session 4 in `CODE_REVIEW.md`): screenshots,
   metadata, age rating, deployment-target/build-number verification
3. Haptic feedback (unexplored)
4. Google Play beta testing (blocked on SI5 Android emulator fix)
5. App Store submission

Deep-review status: all code-fixable findings from
`docs/reviews/2026-06-11_fable5_deep_codebase_review.md` are fixed
(2026-06-12); test suite is 191 passing and safe to run (isolated from
the real cache/network). Sessions 1-3 of `CODE_REVIEW.md` complete.
