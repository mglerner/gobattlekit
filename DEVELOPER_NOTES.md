# GoBattleKit Developer Notes

## Setup
```zsh
cd ~/coding/MGLPoGo
source .venv/bin/activate
cd gobattlekit
```

## Quick Testing
```zsh
briefcase dev
```

Runs the app on macOS without building for iOS/Android. Note: some platform-specific behavior differs (e.g. colors may look different in light/dark mode).

## iOS Build Process

1. Run `prepare_ios.sh` instead of `briefcase create iOS` directly:
```zsh
   ./prepare_ios.sh
```
   This runs `briefcase create iOS` and then copies the required `.xcprivacy` files
   for `_hashlib` and `_ssl` into the support package. These files are needed to
   pass Apple's privacy manifest review (ITMS-91061). They must be copied after
   every `briefcase create iOS` since the build directory is wiped each time.

2. Open `build/gobattlekit/ios/xcode/GoBattleKit.xcodeproj` in Xcode
3. Set signing team to Michael Lerner (Personal Team) — resets on each run of `prepare_ios.sh`
4. Product → Clean Build Folder (Cmd+Shift+K)
5. Product → Archive → Distribute → App Store Connect → Upload

### Verifying the privacy manifest fix
Before distributing, you can verify the fix worked:
- In Xcode Organizer (Window → Organizer), right-click the archive → Show in Finder
- Right-click the `.xcarchive` → Show Package Contents
- Navigate to `Products/Applications/GoBattleKit.app/Frameworks/`
- Confirm `_hashlib.framework` and `_ssl.framework` each contain `PrivacyInfo.xcprivacy`


### TestFlight Notes
- Internal testers get access immediately after upload
- External testers require Beta App Review (can take hours, stricter than internal)
- Apple requires a new version or build number for each upload
- Update `version` in `pyproject.toml` before each build

## Android Build Process
```zsh
briefcase update android
briefcase build android
briefcase run android -d "@Medium_Phone_API_36.1"
```

Must launch emulator from Android Studio first if AVD config is missing.

## Generating Assets

### Icons (if icon SVG changes)
```zsh
python make_icons.py
```
Requires `cairosvg`. Generates all iOS and Android icon sizes.

### Evolution Lines (if gamemaster structure changes)
```zsh
python make_evolist.py
```
Regenerates `src/gobattlekit/data/evolution_lines.json` from PvPoke gamemaster data.

## PvPoke Data URLs
```python
BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data"
```
Note: The old URL format (`/master/` without `refs/heads/`) stopped working in March 2026.

## Known Issues
- **iOS navigation bar** — cannot be hidden via Python/Rubicon without modifying native Xcode project files directly. The `title=""` approach doesn't work on iOS.
- **Android white border** — container has a white border in Android light mode. Cosmetic, accepted for now.
- **`Window content exceeds available space`** — warning on iOS, cosmetic and harmless.
- **`briefcase dev` color differences** — macOS dark mode handling differs from iOS/Android. Trust the device, not dev mode, for color appearance.

## Important Code Notes

### `__main__.py` locale monkey-patch
The locale monkey-patch in `__main__.py` is intentional and required — do not remove it. It fixes a crash on iOS caused by Python's locale module not finding the expected locale settings in the iOS sandbox environment.

### Theme system
All colors, button styles, and layout constants are in `src/gobattlekit/theme.py`. Always add new styles there rather than inline in screen files.

### CSV persistence
The PokeGenie CSV is saved to `CACHE_DIR/pokegenie_export.csv` and auto-loaded on startup. `CACHE_DIR` is `~/Documents/gobattlekit_cache/` on iOS and `/data/user/0/com.mglerner.gobattlekit/files/Documents/gobattlekit_cache/` on Android.

### iOS CSV delivery
iOS uses inbox polling — `app.py` checks `~/Documents/Inbox` every 3 seconds for new CSVs shared from PokeGenie.

### Android CSV delivery
Android uses a file picker Intent (`ACTION_GET_CONTENT`) with an `on_complete` callback. The callback receives `(result_code, result)` — note the two arguments.

### Quiz answer button gradients
Quiz answer buttons use `answer_color_gradient(total_rows, row_index)` from `theme.py` to generate a dark-to-light gradient across the answer rows. This is used in `quiz.py`, `type_quiz.py`, and `timing_quiz.py`. The function interpolates between `#0e2036` (darkest) and `#2a4a7c` (lightest).
