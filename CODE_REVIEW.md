# GoBattleKit — Pre-App-Store Code Review

## Session plan & progress

Check items off as they land. A future session (Claude or human) should read
this block first to know what's done and what's next.

### Session 1 — Foundations: data layer + startup hardening  _(complete)_
- [x] #15 Add minimal `logging` framework (do first — unblocks #17, #13)
- [x] #2 Atomic writes in `user_thresholds.py`, `evolution_lines.py`, `fetcher.py`
- [x] #3 `preferences.py` specific `JSONDecodeError` handling
- [x] #4 `urlopen` timeout in `fetcher.py`
- [x] #5 Dedup `_safe_setlocale` monkey-patch (remove from `__main__.py`)
- [x] #14 `gamemaster.py` schema validation
- [x] #18 `platform.py` loose substring → `==`
- [x] #19 `app.py:114` bare except

### Session 2 — Screens + async polling  _(complete; iOS-verified on 0.0.27, 2026-06-07)_
- [x] #16 `iv_checker.py:313-316` `getattr` fallback cleanup
- [x] #17 `iv_checker.py` silent `print`s → logger (uses session 1's logger)
- [x] #13 `edit_thresholds.py:57` surface species-list load failure
- [x] #7 `iv_checker.py:445` `load_csv` path reassignment bug
- [x] #9 `app.py:59` polling task reference + lifecycle
- [x] #10 `app.py:100-104` poll must not mutate inactive screens
      — device testing on 0.0.26 found a bug in the *foreground* share path:
      `user_iv_checker_screen.load_csv()` was called on a screen whose
      `build()` had never run → `AttributeError: status_label_file`. Caught by
      the poll's try/except (no hard crash) but the inbox file was never
      cleaned up, so it re-fired every 3s → IV Checker screen flickered.
      **Fixed:** foreground branch now invalidates the user screen's
      `csv_path` instead of calling `load_csv` (matches staging branch); poll
      cleanup moved into a `finally` so a bad CSV can't loop. Both share paths
      (foreground + staging) re-verified on 0.0.27 — no flicker, no errors.
- [~] #8 `iv_checker.py:486-497` Android input-stream FD leak (try/finally)
      — code landed; iOS doesn't exercise this path, so still unverified on
      Android. Android testing is nice-to-have, not a submission blocker.

iOS inbox/CSV-share: staging path verified; foreground path fixed and awaiting
re-test. Android CSV import (file picker) still untested.

### Session 3 — Design decisions  _(complete, 2026-06-12)_
- [x] #1 **P0** Eevee/branched pre-evo mapping — decided: check against
      ALL finals (matches gopvpsim); implemented in commit 37241a4, the
      strict-xfail pin flipped to a passing test.
- [x] #11 `theme.py` `COLOR_BG` light-mode behavior — decided: dark-only,
      enforced via `UIUserInterfaceStyle=Dark` in pyproject.toml (38d5766).
- [x] #12 Paragraph-sizing assumptions — documented in DEVELOPER_NOTES
      ("Wrapping paragraph text") and at the constants in theme.py.

### Session 4 — App Store readiness
- [ ] #6 `pyproject.toml` / Info.plist verification against real `briefcase build iOS`
- [ ] Screenshots for required device sizes
- [ ] App Store Connect metadata (description, keywords, support URL, privacy policy URL)
- [ ] Privacy nutrition labels
- [ ] Age rating questionnaire
- [ ] IP / trademark review (Pokémon naming, icons, data sourcing)
- [ ] App Review notes / demo account

---

Review scope: `src/gobattlekit/` (~5,500 LOC) at v0.0.24. Four parallel passes:
data layer, screens, app shell + theme, cross-cutting concerns. Consolidated,
deduped, and spot-verified against source below.

Priority legend:
- **P0** — blocks submission, or crashes/loses data on a real user path
- **P1** — visible wrong behavior or real bug users will hit
- **P2** — quality, perf, robustness
- **P3** — nit

---

## P0

### 1. Pre-evolution → final-form mapping silently loses branched lines
**`src/gobattlekit/data/iv_checker.py:246-250`**

`evolution_lines` is a dict keyed by *final form*, so a pre-evo that branches
(Eevee → 8 Eeveelutions, Tyrogue → 3, Wurmple → 2, Slowpoke → 2, etc.) appears
as a member in multiple entries. The flattening loop overwrites
`pre_evo_to_final[member]` on each pass; only the last-iterated final form
survives. Dict iteration order is insertion order, which depends on the
gamemaster file — effectively arbitrary from the user's perspective.

**Impact:** for every branching species, 7 of 8 (Eevee) / 2 of 3 (Tyrogue) /
1 of 2 (Wurmple, Slowpoke, etc.) CSV rows resolve to the *wrong* final-form
thresholds. Silent — no error, just wrong results. This is probably the single
biggest correctness defect in the app.

**Fix direction:** make the map multi-valued (`pre_evo_to_final: dict[str, list[str]]`)
and iterate all candidates in `check_thresholds`, merging results per final
form. Requires touching the callers that consume `final_species`.

---

## P1

### 2. Non-atomic writes to three user-data files
- **`src/gobattlekit/data/user_thresholds.py:27`** — `USER_THRESHOLDS_FILE.write_text(...)`
- **`src/gobattlekit/data/evolution_lines.py:79`** — `CACHED_PATH.write_text(...)`
- **`src/gobattlekit/data/fetcher.py:58`** — `cache_file.write_text(json.dumps(data))`

`preferences.py:24-28` already has the correct pattern (write to `.tmp`, then
`os.replace`). If iOS kills the app mid-write (backgrounded, OOM, user force-quit),
these three files can be left truncated. Load paths return `{}` on JSONDecodeError,
so the user silently loses thresholds / cached rankings / evolution data.

Severity: user_thresholds is P1 (user-authored data, no fallback). Evolution
lines and fetcher cache are closer to P2 because evolution_lines.py:94 falls
back to bundled data and fetcher re-fetches on next run — but the pattern
should be fixed for all three.

**Fix direction:** copy the pattern from `preferences.py:24-28`.

### 3. `preferences.py:16` swallows all load errors silently
**`src/gobattlekit/data/preferences.py:13-17`**

```python
try:
    if _PREFS_FILE.exists():
        return json.loads(_PREFS_FILE.read_text())
except Exception:
    pass
return {}
```

A corrupt prefs file (e.g. truncated from a prior kill) returns `{}`, wiping
all settings with no visible sign. There's no way to distinguish "file missing"
from "file unreadable" — the bug is invisible unless you check the console.

**Fix direction:** catch `JSONDecodeError` explicitly (rename the file to
`preferences.json.corrupt` and start fresh), let other errors propagate.

### 4. `fetcher.py:56` — `urlopen` with no timeout
**`src/gobattlekit/data/fetcher.py:56`**

```python
with urllib.request.urlopen(URLS[key], context=ssl_context) as r:
```

No `timeout=`. If the pvpoke CDN hangs (stalled TCP, captive portal), this
blocks the event loop indefinitely. iOS will SIGKILL the process after its
watchdog timeout and the user sees a crash on launch. This is called
from app startup (`app.py:64`).

**Fix direction:** `urlopen(..., timeout=10)`, and let the existing
`except Exception` (line 70) fall through to stale cache.

### 5. Duplicate `_safe_setlocale` monkey-patch
**`src/gobattlekit/__main__.py:3-9` and `src/gobattlekit/app.py:11-17`**

The same locale patch is defined in both files. When `__main__.py` imports
`app`, it runs twice (second one wins). Not a bug today, but a trap — if
someone deletes the `__main__.py` copy thinking it's dead code, they'll
break iOS locale handling and the root cause will be non-obvious.

**Fix direction:** delete it from `__main__.py`; keep the single copy in
`app.py` with a comment explaining why it exists (DEVELOPER_NOTES has context).

### 6. `pyproject.toml` — Info.plist / submission config gaps
**`pyproject.toml:170-185`** (iOS block)

Currently only sets `CFBundleDocumentTypes`, `LSSupportsOpeningDocumentsInPlace`,
`UISupportedInterfaceOrientations*`. Missing:
- `ITSAppUsesNonExemptEncryption = false` — without this, every submission
  asks export-compliance questions.
- `LSApplicationCategoryType` (e.g. `"public.app-category.utilities"`) —
  required for App Store metadata.
- Explicit iOS deployment target — Briefcase has a default, but pinning it
  avoids silent drift.
- `build_number` — needs to increment per upload; Briefcase can auto-increment
  but making it explicit helps.

These are *likely* but not *certain* P0 submission blockers — Briefcase may
auto-generate some. **Verify during the App Store readiness pass** (next
session) against an actual `briefcase build iOS` output.

### 7. `iv_checker.py:445` — CSV path updated before copy succeeds
**`src/gobattlekit/screens/iv_checker.py:445` area (load_csv)**

`self.csv_path` is set to the source file path before `shutil.copy2()` runs.
If the copy raises (permission, disk full), the attribute reassignment to
`SAVED_CSV` on line 451 never happens, but `_run_check()` is still called on
line 454 with the source path — which may be in a temp dir that the OS then
cleans up, or not readable on a second read.

**Fix direction:** set `self.csv_path = None` in the except, return early
before `_run_check()`.

---

## P2

### 8. Android input stream leak
**`src/gobattlekit/screens/iv_checker.py:486-497`**

`ContentResolver.openInputStream(uri)` opens a stream that's only closed on
the success path. Exception in the write loop → FD leak. Wrap in try/finally
or context-manage it.

### 9. Inbox polling task is fire-and-forget
**`src/gobattlekit/app.py:59`** — `asyncio.create_task(self._poll_inbox(None))`

Task reference discarded; loop runs forever (line 91 `while True`). If an
exception slips past the broad `except Exception` on line 114, the coroutine
dies silently, CSV monitoring stops, and there's no signal to the user or
developer. Also keeps polling when the app is backgrounded (battery drain,
though small).

**Fix direction:** hold the task reference on `self._poll_task`; structured
log on loop entry/exit; consider cancelling on `on_exit` / pausing on
backgrounding.

### 10. Poll updates inactive screens
**`src/gobattlekit/app.py:100-104`**

When a new CSV is detected, `show_iv_checker()` + `user_iv_checker_screen.load_csv()`
run regardless of which screen the user is on. Rapid navigation during a
poll tick can stomp on state for a screen the user just left.

**Fix direction:** check current active screen before mutating; or make
`load_csv` a no-op if the screen isn't visible.

### 11. `theme.py:14` — `COLOR_BG = "#000000"` broken on light mode
**`src/gobattlekit/theme.py:14`**

Comment literally says "maybe a bad idea for light mode." Toga's system theme
detection is limited, so this is a design decision more than a code fix:
either force dark styling everywhere, or adapt `COLOR_BG` per platform/mode.
Flagging as P2 because the app is visually broken for light-mode users.

### 12. Paragraph sizing heuristic is fragile
**`src/gobattlekit/theme.py:234, 238`**

`_PARAGRAPH_CHARS_PER_LINE` / `_PARAGRAPH_LINE_HEIGHT` are hardcoded to iPhone
screenshots from 2026-04-08 per the comment. Fine for current scope; will
break on iPad support, larger system fonts (accessibility), or any
localization. Document assumptions or add a calibration test.

### 13. `edit_thresholds.py:57` — species list load fails silently to empty list
**`src/gobattlekit/screens/edit_thresholds.py:57`**

`_ensure_species_list` bare-excepts and sets `[]`. User sees an empty picker
with no error explanation. Surface the error to `status_label_stats` or a
dialog.

### 14. `gamemaster.py:9-18` — no validation on gamemaster schema
**`src/gobattlekit/data/gamemaster.py:9-18`**

`get_moves()` assumes every move has `energyGain`. If pvpoke reshuffles their
schema, moves silently disappear without warning. Low probability, low blast
radius, but an explicit check (or try/except with a log) is cheap insurance.

### 15. No logging framework — ~20 `print()` calls in production code
Pattern across `app.py`, `data/*.py`, `screens/iv_checker.py`. On iOS these
go to the console only visible via Xcode; TestFlight users can't surface them
and neither can App Review. Also: if anything accidentally prints user data
(e.g. CSV contents in an error path), that becomes a disclosure question for
App Store privacy labels.

**Fix direction:** minimal `logging` config (stderr on mobile). Replace
`print(f"error: ...")` with `logger.exception(...)` so you get stack traces
in the iOS device logs.

---

## P3

### 16. `iv_checker.py:313-316` — unnecessary `getattr` fallbacks
**`src/gobattlekit/screens/iv_checker.py:313-316`**

`getattr(self, '_manual_atk_input', toga.TextInput())` — the widgets are
guaranteed to exist by call ordering, so the fallback is dead code that
masks any real ordering bug. Drop the fallback, access directly.

### 17. `iv_checker.py:502, 842` — silent `print` on disk ops
Clear-CSV and related failures print to console only. Either surface to
status label or drop the print.

### 18. `platform.py:7-8` — loose substring match
**`src/gobattlekit/platform.py:7-8`** — use `sys.platform == 'ios'`, not
`'ios' in sys.platform`. No real-world collision, but tighter is free.

### 19. `app.py:114` — bare `except Exception` in polling loop
Consider re-raising `KeyboardInterrupt` / `SystemExit`. Minor — the loop is
in an asyncio task so signals aren't really reaching it.

---

## What's clean — don't re-review

Confidence items from the parallel pass, worth calling out so we don't
revisit them:

- **IV math correctness** — data-layer review found no off-by-one or
  formula bugs in `iv_checker.py`. Tests (127 existing) cover the core cases.
- **CSV parsing** — handles BOM, Pokémon name variants, shadow/lucky, level
  range.
- **Screen lifecycle / async cancellation** — quiz screens cancel pending
  advance tasks on re-entry (commit be18739 landed this); no stale-task
  UI updates observed.
- **Theme helpers usage** — `show_widget` / `hide_widget` used consistently;
  no direct style edits outside of dynamic answer highlighting.
- **Navigation** — screens instantiated once in `startup()` and reused; no
  leaked references from transient navigation.
- **Privacy manifest** — `resources/PrivacyInfo.xcprivacy` is present and
  correctly structured (empty `NSPrivacyAccessedAPITypes`, no tracking);
  `prepare_ios.sh` copies manifests for `_hashlib` and `_ssl` post-build.
- **Secrets** — no API keys, tokens, or credentials in source.
- **Input validation** — manual IV/CP entry validates ranges (0-15 IVs,
  CP > 0), species existence, level calculability.
- **Icon assets** — all required sizes present (1024 App Store icon, iOS
  and Android variants).

---

## Suggested triage order

**Before the App Store readiness pass, fix:**
1. The Eevee evolution bug (#1) — correctness, and the fix probably touches
   a caller contract so it's easier to do now than later.
2. The three non-atomic writes (#2) — ~10 lines each.
3. Dedup the locale patch (#5) — 1-line change, removes a trap.
4. Add `urlopen` timeout (#4) — one kwarg.

**Defer to the readiness pass (will be confirmed there):**
- pyproject.toml Info.plist config (#6) — needs `briefcase build iOS`
  output to see what's auto-generated.

**Everything else — optional before submission**, but #7 (load_csv path
reassignment), #8 (Android FD leak), #9-10 (polling), and #15 (logging) are
the ones I'd most want fixed if time allowed. The rest is cleanup.
