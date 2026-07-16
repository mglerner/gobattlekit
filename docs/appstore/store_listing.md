# App Store listing copy

Paste these into App Store Connect. Character limits noted where Apple enforces them.

## App Name (≤30)

GoBattleKit

## Subtitle (≤30)

Battle Quizzes & PvP IV checks

## Promotional Text (≤170)

Drill yourself on type matchups, PvP move counts, and PvP move timing. Check which of your Pokémon are worth building for PvP!

## Keywords (≤100, comma separated, no spaces after commas)

pokemon go,pvp,iv,gbl,great league,ultra league,pokegenie,move counts,trainer battle,timing

## Description

GoBattleKit helps you prep for PvP in Pokémon GO.

The quizzes cover the parts of a battle that come down to reflexes and memory. One asks how many fast moves it takes to reach a charged move. Another teaches when to throw a charged move so you hand your opponent the fewest free turns. A third runs you through type matchups until they are second nature. They are useful for any trainer, whether or not you track IVs.

The IV tools help you decide which Pokémon are worth building. Import a CSV exported from PokeGenie's Scan Pro and GoBattleKit checks every Pokémon against the IV spreads that deep-dive analysis has shown to matter in each league, all on your phone. No CSV on hand? Type a Pokémon in by hand and get the same answer.

You get:
- Quizzes for move counts, move timing, and type effectiveness
- IV target checking for Great League, Ultra League, and Master League
- Enter Pokémon by hand, or bulk-import a CSV from PokeGenie's Scan Pro export
- Your own saved IV targets, with import from pogo-dives deep dives

Your data stays on your device. The app downloads public game data and rankings from PvPoke and keeps your imported CSV and saved targets locally. There are no accounts and no ads. Nothing you do in the app is tracked.

GoBattleKit is an unofficial fan project. It is not affiliated with, endorsed, sponsored, or approved by Niantic, Nintendo, The Pokémon Company, Game Freak, or PokeGenie. Pokémon and Pokémon GO are trademarks of their respective owners.

## URLs (all verified live / HTTP 200 as of 2026-07-08)

| Field              | Value                                         | Required |
| ------------------ | --------------------------------------------- | -------- |
| Support URL        | https://mglerner.com/gobattlekit/support.html | yes      |
| Marketing URL      | https://mglerner.com/gobattlekit/             | no       |
| Privacy Policy URL | https://mglerner.com/gobattlekit/privacy.html | yes      |

The live listing (approved 2026-07-15, verified via the iTunes lookup API):
https://apps.apple.com/us/app/gobattlekit/id6760953142 (app ID 6760953142)

Pages live in `../../website/` and deploy with `website/publish_website.sh`.

## Which App Store Connect page each field lives on

App Store Connect splits the fields across two pages, which is easy to trip on:

- **App Information** (left sidebar > General): App Name, Subtitle, Privacy
  Policy URL, and Category. Set Category to **Utilities** (NOT Games — the app
  is a companion tool, and Games would surface a subcategory picker that does
  not apply and risks a miscategorization rejection). Secondary category:
  **Reference** (optional).
- **Distribution > 1.0 Prepare for Submission** (the version page):
  Promotional Text, Description, Keywords, Support URL, Marketing URL, Version,
  Copyright, Screenshots, and the Build selector.

## Notes for the listing

- Primary Category: Utilities (matches `LSApplicationCategoryType` =
  `public.app-category.utilities` in `pyproject.toml`)
- Secondary category: Reference (optional; do NOT use Entertainment or Games)
- Device family: iPhone only
- Copyright field: 2026 Michael G. Lerner
