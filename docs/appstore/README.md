# App Store submission kit

Drafts for the public 1.0.0 App Store release. Files here are ready to use; the
items that need a human are flagged. Full context is in the plan and in
`docs/reviews/2026-06-23_prerelease_review.md`.

## What is here

| File                            | Use                                                                                |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| `store_listing.md`              | Name, subtitle, promo text, keywords, description for App Store Connect            |
| `privacy_policy.html`           | Host it, then put the URL in App Store Connect (hard blocker)                      |
| `marketing_landing.html`        | Fixes the 404 marketing URL; host at `mglerner.com/gobattlekit` or repoint the URL |
| `app_review_notes.md`           | Paste into App Review Information > Notes                                          |
| `sample_pokegenie.csv`          | Attach for the reviewer to test the CSV import (6 GL meta mons, parses clean)      |
| `privacy_and_rating_answers.md` | Pre-filled App Privacy + Age Rating answers                                        |

## Needs a human before submit

- [ ] Set the contact email in `privacy_policy.html` (line marked CONTACT)
- [ ] Host `privacy_policy.html` and enter the URL in App Store Connect
- [ ] Host `marketing_landing.html` at the `pyproject` url, or change the url; set
      the App Store link in the page once the listing is live
- [ ] Confirm the 1024 app icon is original art (no Niantic/Nintendo assets);
      check it has no alpha: `sips -g hasAlpha src/gobattlekit/resources/icon-1024.png`
- [ ] Capture screenshots (below)
- [ ] Run `docs/device_test_checklist.md` on a real device at 1.0.0

## Screenshot shot list

iPhone-only, portrait. Apple wants a 6.9-inch set and a 6.5-inch set.

- Devices: iPhone 16 Pro Max (6.9") and iPhone 11 Pro Max or 8 Plus (6.5").
  In the Simulator: `briefcase run iOS` and pick the device, or open the built
  Xcode project and run on the simulator, then Cmd+S to save each screenshot.
- Screens to capture (3 to 10 each, same set on both sizes):
  1. Home
  2. PvP IV Checker with results (import `sample_pokegenie.csv` to populate)
  3. My PvP IV Targets
  4. A quiz mid-question (move counts or type effectiveness)
  5. About (shows the credits and the disclaimer)

## Submission walkthrough

The step-by-step build/upload/submit sequence is Part C of the approved plan
(`~/.claude/plans/mossy-wishing-twilight.md`). Short form: fix-ups are already in
the repo, so it is build at 1.0.0 via `./prepare_ios.sh`, archive in Xcode with
team MF55GHNQC2, upload, then fill the listing from the drafts here and submit.
