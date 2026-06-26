# GoBattleKit

A Pokémon GO PvP companion app built with Python/BeeWare (Briefcase + Toga).

## Key info
- Bundle ID: com.mglerner.gobattlekit
- Apple Developer team: MF55GHNQC2 (mglerner@gmail.com, Individual; renews
  2027-03-21). NOTE: an old "Apple Development" cert for a stale team
  `6TV57R6ZCC` lingers in the keychain — it is NOT the team, ignore it.
- Repo: https://github.com/mglerner/gobattlekit
- Current version: 1.0.0 (first public App Store target; 0.0.24 on TestFlight)
- Release status: EmpoleonDynamite (PvPoke author) gave explicit permission
  (2026-06-23) to release the app + the gopvpsim Python port publicly.
  Going to the App Store as 1.0.0, iPhone-only.
- venv: ~/coding/MGLPoGo/.venv
- Project: ~/coding/MGLPoGo/gobattlekit

## Build process
See DEVELOPER_NOTES.md — always use `./prepare_ios.sh` instead of `briefcase create iOS` directly.

## General coding guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Architecture
- `src/gobattlekit/screens/` — all UI screens
- `src/gobattlekit/data/` — data layer (IV checker, thresholds, gamemaster)
- `src/gobattlekit/theme.py` — all colors and button styles
- `src/gobattlekit/app.py` — main app, screen navigation

## Threshold spreads come from gopvpsim (read-only input)

App IV thresholds in `src/gobattlekit/data/default_thresholds.toml` are
produced from the `../gopvpsim` repo: `tools/threshold_export/`
`export_thresholds.py` reads that repo's `thresholds/*.toml` + deep-dive
replay blobs; `bundle_into_app.py` merges them in. The bundler is
**Great-league only** — Ultra/Master targets are hand-maintained in
`default_thresholds.toml` and preserved across re-bundles. See
`tools/threshold_export/README.md` for the contract.

## Current priorities
1. TestFlight 1.0.0 build + device verification — run the full
   `docs/device_test_checklist.md` on a real device (covers the never-verified
   2026-06-11/12 fixes, the 0.0.29-1.0.0 threshold-pipeline UI, and the new
   Home/About scroll changes)
2. App Store submission — collateral is drafted in `docs/appstore/`; human
   steps remaining: host the privacy policy + marketing page, capture
   6.9"/6.5" screenshots, fill App Store Connect from the drafts, archive +
   upload + submit (see Part C of the approved plan / docs/appstore/README.md)
3. Google Play beta testing (blocked on SI5 Android emulator fix; independent
   of the iOS App Store release)

Review status: the 2026-06-23 pre-release review
(`docs/reviews/2026-06-23_prerelease_review.md`) is done; all its code-fixable
findings are fixed except the latent evolution gender-orphan (deferred) and
the Android SI5 leak (Android track). Test suite is 252 passing and isolated.
Sessions 1-3 of `CODE_REVIEW.md` complete; Session 4 partly done (IP/trademark
landed; screenshots + metadata + questionnaires remain).
