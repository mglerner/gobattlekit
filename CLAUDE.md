# GoBattleKit

A Pokémon GO PvP companion app built with Python/BeeWare (Briefcase + Toga).

## Key info
- Bundle ID: com.mglerner.gobattlekit
- Apple Developer team: 6TV57R6ZCC
- Repo: https://github.com/mglerner/gobattlekit
- Current version: 0.0.27 (0.0.24 on TestFlight)
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
1. Pre-App-Store fixes — see `CODE_REVIEW.md` for the 4-session plan and progress checklist (session 1 complete; session 2 next)
2. Haptic feedback (unexplored)
3. Write unit tests
4. Google Play beta testing (later)
5. App Store submission (later)
