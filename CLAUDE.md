# GoBattleKit

A Pokémon GO PvP companion app built with Python/BeeWare (Briefcase + Toga).

## Key info
- Bundle ID: com.mglerner.gobattlekit
- Apple Developer team: 6TV57R6ZCC
- Repo: https://github.com/mglerner/gobattlekit
- Current version: 0.0.21 (TestFlight)
- venv: ~/coding/MGLPoGo/.venv
- Project: ~/coding/MGLPoGo/gobattlekit

## Build process
See DEVELOPER_NOTES.md — always use `./prepare_ios.sh` instead of `briefcase create iOS` directly.

## Architecture
- `src/gobattlekit/screens/` — all UI screens
- `src/gobattlekit/data/` — data layer (IV checker, thresholds, gamemaster)
- `src/gobattlekit/theme.py` — all colors and button styles
- `src/gobattlekit/app.py` — main app, screen navigation

## Current priorities
1. Haptic feedback (unexplored)
2. Write unit tests
3. Google Play beta testing (later)
4. App Store submission (later)
