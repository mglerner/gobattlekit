# App Store submission kit

Drafts for the public 1.0.0 App Store release. Files here are ready to use; the
items that need a human are flagged. Full context is in the plan and in
`docs/reviews/2026-06-23_prerelease_review.md`.

## What is here

| File                            | Use                                                                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `store_listing.md`              | Name, subtitle, promo text, keywords, description for App Store Connect                                                                |
| `app_review_notes.md`           | Paste into App Review Information > Notes                                                                                              |
| `sample_pokegenie.csv`          | Attach for the reviewer to test CSV import (12 mons, deliberate hit/miss mix, GL-verified; two Clodsire show the 🏆 trophy)             |
| `sample_pokegenie.zip`          | The CSV zipped for attaching in ASC, which rejects `.csv`; untracked — regenerate with `zip sample_pokegenie.zip sample_pokegenie.csv` |
| `privacy_and_rating_answers.md` | Pre-filled App Privacy + Age Rating answers                                                                                            |

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

## EU availability — DSA trader status (fixed 2026-07-16)

Day one after the 1.0.0 launch, Reddit users reported "This app is not
available in your country or region." Storefront checks confirmed the app was
live in the US/UK/CA/AU but 404 in DE/FR/NL — i.e. missing from **all EU
storefronts, and only EU storefronts**.

Cause: the EU **Digital Services Act trader-status declaration** was never
completed. Since Feb 2025 Apple silently excludes an app from the 27 EU
storefronts until the developer declares trader or non-trader; App Store
Connect lets you submit anyway, so the first release skipped it without
warning.

Fix (done 2026-07-16): declared **non-trader** in App Store Connect > Business
> legal entity > trader status. Correct for this app: free, no monetization,
hobby project. The EU listing carries a "developer is not a trader" label and
no personal contact info is published. If the app ever monetizes (paid, IAP,
ads), the status must change to **trader**, which requires an Apple-verified
address/phone/email displayed publicly on the EU App Store. Propagation to EU
storefronts takes a few hours to a day; no resubmission or review needed.

## Submission walkthrough

The step-by-step build/upload/submit sequence is Part C of the approved plan
(`~/.claude/plans/mossy-wishing-twilight.md`). Short form: fix-ups are already in
the repo, so it is build at 1.0.0 via `./prepare_ios.sh`, archive in Xcode with
team MF55GHNQC2, upload, then fill the listing from the drafts here and submit.
