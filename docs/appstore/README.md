# App Store submission kit

Drafts for the public 1.0.0 App Store release. Files here are ready to use; the
items that need a human are flagged. Full context is in the plan and in
`docs/reviews/2026-06-23_prerelease_review.md`.

## What is here

| File                            | Use                                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------ |
| `store_listing.md`              | Name, subtitle, promo text, keywords, description for App Store Connect                    |
| `app_review_notes.md`           | Paste into App Review Information > Notes                                                  |
| `sample_pokegenie.csv`          | Attach for the reviewer to test CSV import (11 mons, deliberate hit/miss mix, GL-verified) |
| `privacy_and_rating_answers.md` | Pre-filled App Privacy + Age Rating answers                                                |

The web pages (privacy policy, marketing landing, support) live in `../../website/`
and are deployed with `website/publish_website.sh`. The App Store Privacy Policy URL
is `https://mglerner.com/gobattlekit/privacy.html`; the Marketing URL is
`https://mglerner.com/gobattlekit/`.

Live status of the remaining human steps is tracked in the working session, not
here. The screenshots come last, after the UI and all other items are settled.

## Screenshots — captured set in `screenshots/6.9/`

iPhone-only, portrait. As of 2026 App Store Connect requires only the **6.9"**
set (1320x2868); the 6.5" slot is only needed if you skip 6.9". The captured
set (all 1320x2868) lives in `screenshots/6.9/`:

  1. `01_home.png` — Home
  2. `02_iv_checker.png` — PvP IV Checker with results (👑/🏆 badges, [SIM])
  3. `03_my_targets.png` — My PvP IV Targets (empty "getting started" state)
  4. `04_quiz.png` — Type Effectiveness quiz mid-question
  5. `05_about.png` — About (credits + attributions)

How they were captured (repeatable):
- **Emoji-bug workaround:** the iOS 26.x simulator renders color emoji as tofu
  (`?` boxes) — a known xcodes/runtime bug. Capture on an **iOS 18.6** runtime
  with **iPhone 16 Pro Max** (same 6.9"/1320x2868, emoji render correctly).
- Build for the sim (`briefcase build iOS`), `xcrun simctl install`, then
  `xcrun simctl status_bar <udid> override --time 9:41 ...` for a clean status
  bar and `xcrun simctl io <udid> screenshot ...` for exact-resolution PNGs.
- The IV Checker shot is populated by dropping `sample_pokegenie.csv` into the
  app container at `Documents/gobattlekit_cache/pokegenie_export.csv`.

## Submission walkthrough

The step-by-step build/upload/submit sequence is Part C of the approved plan
(`~/.claude/plans/mossy-wishing-twilight.md`). Short form: fix-ups are already in
the repo, so it is build at 1.0.0 via `./prepare_ios.sh`, archive in Xcode with
team MF55GHNQC2, upload, then fill the listing from the drafts here and submit.
