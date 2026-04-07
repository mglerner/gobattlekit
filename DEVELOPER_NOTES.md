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

## GitHub
`https://github.com/mglerner/gobattlekit` (public)

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

### Wrapping paragraph text — never use `toga.Label` for body text
`toga.Label` does **not** wrap. Long strings overflow the right edge of the screen on iOS and Android. This bit us in commit `85ab5ff` ("status label wrapping…"), which is why most body text in the app is rendered as a `toga.MultilineTextInput(readonly=True)` instead of a `Label`. Toga 0.5 has no wrapping label widget; tracked upstream at `beeware/toga#1325`.

**The rule:** for any paragraph of body text, use the `paragraph_text()` helper from `theme.py`:

```python
from ..theme import paragraph_text
card.add(paragraph_text(body, font_size=14))
```

`paragraph_text()` returns a read-only `MultilineTextInput` sized from the text length using a conservative chars-per-line estimate (tuned from real device screenshots — see the constants in `theme.py`), plus one line of slack so we never truncate.

**Do NOT:**
- Use `toga.Label` for anything longer than a single line of fixed text. It will overflow.
- Hand-roll your own `MultilineTextInput`-with-height-math at call sites. Use the helper so the whole app stays consistent if we re-tune the heuristic later.
- Try to set `width=...` on a `Label` to get wrapping. It does not work.

**Single-line text** (titles, status lines, button labels, card headings) can stay as `toga.Label` — that's fine, those don't need wrapping.

**Quiz question labels** (`quiz.py`, `type_quiz.py`, `timing_quiz.py`) intentionally use a `MultilineTextInput` with a *fixed* height instead of `paragraph_text`, because the height needs to be predictable across questions of varying length so the answer buttons below don't jump around between questions. Don't "fix" those by switching them to `paragraph_text`.

**If you need to re-tune the heuristic:** the constants are `_PARAGRAPH_CHARS_PER_LINE` and `_PARAGRAPH_LINE_HEIGHT` at the bottom of `theme.py`. Take screenshots of the worst-case body text (currently the IV Checker intro "Reading results" card and the Move Count Quiz "How it works" card), measure visible chars-per-line and line-height in pt, and adjust. Always err on the side of slightly *under*-counting chars-per-line so we never truncate.

### CSV persistence
The PokeGenie CSV is saved to `CACHE_DIR/pokegenie_export.csv` and auto-loaded on startup. `CACHE_DIR` is `~/Documents/gobattlekit_cache/` on iOS and `/data/user/0/com.mglerner.gobattlekit/files/Documents/gobattlekit_cache/` on Android.

### iOS CSV delivery
iOS uses inbox polling — `app.py` checks `~/Documents/Inbox` every 3 seconds for new CSVs shared from PokeGenie.

### Android CSV delivery
Android uses a file picker Intent (`ACTION_GET_CONTENT`) with an `on_complete` callback. The callback receives `(result_code, result)` — note the two arguments.

### Quiz answer button gradients
Quiz answer buttons use `answer_color_gradient(total_rows, row_index)` from `theme.py` to generate a dark-to-light gradient across the answer rows. This is used in `quiz.py`, `type_quiz.py`, and `timing_quiz.py`. The function interpolates between `#0e2036` (darkest) and `#2a4a7c` (lightest).

### Quiz question type selection
The move count quiz uses weighted random selection between question types: 70% first charge move, 30% sequence (`FIRST_WEIGHT = 0.7` in `quiz.py`). There are also streak limits — no more than 4 consecutive first charge questions (`MAX_FIRST_STREAK`) or 2 consecutive sequence questions (`MAX_SEQUENCE_STREAK`). This is implemented in `_pick_question_type()` in `quiz.py`.

### CSV loading priority
`get_csv_path()` in `data/fetcher.py` returns the CSV to use: PokeGenie export (`pokegenie_export.csv`) if it exists, otherwise user-generated (`user_generated.csv`). Both live in `CACHE_DIR`.

### Manual Pokémon entry
Users can enter Pokémon manually without a PokeGenie CSV. Entries are saved to `user_generated.csv` in PokeGenie CSV format using `append_user_generated()` in `data/iv_checker.py`. The CSV is loaded automatically on next launch.

### IV threshold targets: stat floors vs. explicit IV lists
A target in `data/thresholds.py` can be specified two ways, and they can be combined:

- **Stat floors** — `'attack' / 'defense' / 'stamina'` are minimums on the *scaled* stats (`base + iv`, level-adjusted), not raw IVs. `0` means "don't care".
- **Explicit IV list** — `'ivs': [[atk, def, sta], ...]` matches only the listed raw IV triples.
- **`onlytop: N`** — additionally requires the mon's overall stat-product rank to be ≤ N.

When multiple keys are present they are AND-combined in `check_thresholds()` (`data/iv_checker.py`). The important gotcha: combining `ivs` with a stat floor like `'attack': 122` does **not** mean "atk IV ≥ 122" — it means "this raw IV combo, *and* the resulting scaled attack stat is ≥ 122". That's the right behavior for cases like "30 IVs that win the mirror, but I also need a bulk point against another mon", but it's easy to misread the floor as an IV constraint.

### IV target species list
Both IV Checker and My PvP IV Targets now always show all species with
targets for the current league, regardless of whether any Pokémon are
loaded. Species with no hits show as "Species (0)". Clicking a species
with 0 hits shows qualifying IV combinations (top 100 by stat product,
displayed by IVs descending).

