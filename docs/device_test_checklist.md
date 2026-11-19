# Device test checklist — pre-1.0.0 App Store release

Conventions (2026-08-05 evidence pass): a `- [x]` here means the item's success
criterion is fully covered WITHOUT a device, and the indented `VERIFIED` line
names the tests + commit that cover it — it does NOT mean anyone ran it on
hardware. An item whose logic is pinned by tests but whose remaining risk is
on-device rendering/behavior stays `- [ ]` with an indented `NOTE (2026-08-05)`
line. Items with neither line are untouched: they still need a human holding a
phone.

Everything below needs eyes on a real device or emulator before the public
release. Two groups: the 2026-06-11/12 review fixes (never device-verified;
source in `docs/reviews/2026-06-11_fable5_deep_codebase_review.md`), and the
0.0.29–1.0.0 changes that post-date the original checklist (threshold
pipeline + provenance UI, plus the 1.0.0 scroll/legal changes).

## iOS (TestFlight 1.0.0 or `briefcase run iOS`)

Small-screen layout (1.0.0 scroll changes):
- [ ] Run on a SMALL device (iPhone SE, the minimum the iOS 13 target
      allows) and a LARGE one: Home and About now scroll. Confirm the
      About/Help row on Home and the Help/Back buttons on About are
      reachable, and nothing clips at the bottom.
- [ ] About screen: the new "Legal" disclaimer paragraph wraps fully (no
      clipping), and the PvPoke credit reads "by EmpoleonDynamite".
      NOTE (2026-08-05): wrap logic verified by
      tests/test_label_wrapping.py::test_no_label_clips_on_narrow_phone (runs
      tools/check_label_wrapping.py over every screen, about.py included); the
      credit string is source-pinned at src/gobattlekit/screens/about.py:92 but
      no test asserts it. Residual risk is iOS rendering only.
- [ ] About screen contact: the new "Discord: TitanTrainers15" button (Developer
      section) opens the right Discord profile, and the two Discord buttons
      (contact-the-dev vs XehrFelrose community invite) don't read as confusing.
- [ ] Quiz / quiz-summary screens (still NOT wrapped on purpose): on the
      small device, confirm a question + its answers + any reveal still fit
      without clipping. If one clips, flag it — do not assume it's fine.

Threshold-pipeline UI (0.0.29–1.0.0, never device-verified):
- [ ] My PvP IV Targets: provenance shows correctly (expert vs generated
      vs user badges), SIM badges render, and per-hit stat-product rank
      appears for all hits (not just onlytop).
      NOTE (2026-08-05): logic verified by tests/test_provenance.py
      (TestTargetClass, TestSimFilter, TestMetadataPersistence) and
      tests/test_bundled_thresholds.py::TestProvenanceHelpers; per-hit rank by
      tests/test_iv_checker.py::TestCheckThresholds. Residual risk is iOS
      rendering only.
- [ ] The expanded species set (~47) loads and the Edit Targets species
      picker is complete.
      NOTE (2026-08-05): logic verified by
      tests/test_bundled_thresholds.py::TestLosslessRoundTrip::test_species_count_grew_to_47
      and tests/test_threshold_species_parity.py (every bundled species
      resolves against the real gamemaster); residual risk is the on-device
      picker rendering only.
- [x] Add a target, then confirm a forced save failure surfaces the
      "Could not save target" error instead of silently dropping it
      (hard to trigger on-device; at minimum confirm a normal add works).
      VERIFIED (2026-08-05):
      tests/test_edit_thresholds_screen.py::TestFloorValidation::test_forced_save_failure_surfaces_error
      patches Path.write_text to raise OSError, driving the real
      save_json_atomic -> add_threshold -> screen path, and asserts the
      "Could not save target" error with nothing stored; commit e1bbd5b. The
      item itself concedes this is not triggerable on-device.
- [ ] Pareto badges: in a species/target with several of your hits, the
      globally-efficient mon(s) show 👑, a best-of-yours-but-not-optimal mon
      shows 🏆, and a mon beaten by one of your own shows no badge. Check
      both the per-target view and "Show All", on IV Checker and My PvP IV
      Targets. Badges are absent when there is only one hit and it is not
      efficient.
      NOTE (2026-08-05): logic verified by
      tests/test_iv_checker.py::TestParetoBadges (crown vs trophy vs blank,
      ties, duplicate IVs, single-hit cases, the worked example); residual risk
      is iOS rendering only.

Visual / theme:
- [ ] Force-dark (`UIUserInterfaceStyle=Dark`): set the PHONE to light
      mode, launch — app must render fully dark, no light chrome, no
      white-on-white MultilineTextInputs (SQ7's acute case).
- [ ] Card spacing: quiz summary, intro, help, IV credits cards now have
      8pt top/side margins and HONOR margin_bottom (was uniformly 8, most
      callers asked for 12) — eyeball that nothing looks cramped/floaty
      (SQ3).
- [ ] Long error text: trigger a manual-entry validation error ("Could not
      find a level matching CP...") — must wrap, not clip (SI8).
      NOTE (2026-08-05): logic verified by
      tests/test_label_wrapping.py::test_no_label_clips_on_narrow_phone; the
      message is routed through theme.paragraph_text at
      src/gobattlekit/screens/iv_checker.py:326. Residual risk is iOS rendering
      only.
- [ ] Residual SI8 decision: force an "Error reading CSV" (share a
      garbage .csv) — the status line is still a one-line Label; decide
      whether the truncation is acceptable or the status row should be
      reworked.

CSV share paths:
- [ ] Share a PokeGenie CSV to the CLOSED app — must import on launch
      (AP1; previously silently swallowed).
- [ ] Share while ON "My PvP IV Targets" — must stay on that screen and
      refresh (SI14), not jump to the default checker.
- [ ] Share mid-quiz — must stage silently; next IV navigation shows it.
- [ ] Share the same file twice in a row — second share re-imports.

Destructive-action guards:
- [x] ✕ (clear CSV): first tap shows the warning in the status line,
      second tap clears; navigating away and back DISARMS it (SI15).
      VERIFIED (2026-08-05): tests/test_iv_checker_screen.py::TestClearCsvDisarm
      (arm -> in-screen navigation disarms; arm -> re-check disarms; two
      consecutive taps really delete) plus the same three cases on the user
      screen in TestUserScreenSharesBasePaths; commits f2a180b, fc05f78. The
      warning itself is a static two-line literal with an explicit newline.
- [x] Edit Targets → Clear All: arm it, go into Add Target, cancel, come
      back — button must read "Clear All" again and need two taps (SI4).
      VERIFIED (2026-08-05):
      tests/test_edit_thresholds_screen.py::TestClearAllDisarm drives the real
      button handlers - arm, enter Add Target, press Cancel, and the label is
      back to "Clear All" with nothing deleted; two consecutive taps still
      clear; commit e1bbd5b.

Import from Text (the live gopvpsim contract):
- [ ] Paste a "Copy for IV scanner" JSON fragment from a dive page —
      imports (multi-target fragments too); check the target appears and
      matches expected mons (IV1).
      NOTE (2026-08-05): logic verified by
      tests/test_user_thresholds.py::TestScannerJsonContract (composite and
      ivs-bearing cards parse, multi-target fragments merge without clobbering,
      the import round-trips through check_thresholds); residual risk is the
      on-device paste/import UI only.
- [x] Paste garbage / a fragment with a typo'd key — clear error message,
      nothing saved (IV5).
      VERIFIED (2026-08-05):
      tests/test_user_thresholds.py::TestScannerJsonContract::test_rejects_malformed
      (10 cases incl. non-JSON and a typo'd "atack" key; parse raises before
      anything reaches the store) and
      tests/test_edit_thresholds_screen.py::TestImportErrorWrapping::test_import_error_uses_wrapping_widget
      for the surfaced message; commits ae24a8e, 8b96c98.
- [x] Share an ivs-bearing target → re-import the text — ivs survive the
      round trip (IV2).
      VERIFIED (2026-08-05):
      tests/test_user_thresholds.py::TestIvsFirstClass::test_share_text_reimport_keeps_ivs
      walks the full store -> format_threshold_text -> parse_threshold_text ->
      import_threshold_entries -> store loop and asserts the ivs list survives;
      commit e1bbd5b.

Matching-semantics spot checks (results CHANGED by the parity work):
- [x] A shadow mon you know well: its scaled atk/def now include ×1.2 and
      ×5/6 — sanity-check one result against PvPoke (CP3).
      VERIFIED (2026-08-05): pure math, no device involved.
      tests/test_parity_vectors.py::test_parity_vectors checks golden gopvpsim
      fixtures incl. ninetales_shadow_great_parity.json, and guards that the
      shadow vector is not reproducible without the shadow multipliers;
      tests/test_iv_checker.py::TestComputeRankTable::test_shadow_changes_rank_ordering
      pins the reshuffle. Commits 674ef44, 6d9ef44.
- [x] An `onlytop` target: ranks are now PvPoke-style dense unique ranks —
      spot-check one mon's rank against PvPoke's IV table (CP7).
      VERIFIED (2026-08-05): pure math, no device involved.
      tests/test_iv_checker.py::TestComputeRankTable::test_ranks_are_dense_and_unique
      (ranks are exactly 1..N, no ties) plus the rank assertions in
      tests/test_parity_vectors.py::test_parity_vectors against the gopvpsim
      goldens. Commits 674ef44, 6d9ef44.
- [ ] A branched pre-evo (an Eevee with targets on two Eeveelutions) —
      appears under BOTH finals, annotated "(Eevee)" (P0 #1).

Startup / offline:
- [ ] Airplane mode + fresh install (no cache): error screen with wrapped
      text and a working "Try Again" after re-enabling network (AP3/AP4).
- [ ] Airplane mode + cold cache, tap a quiz: same recoverable error
      screen, not a dead button (AP2 lazy loads).
- [ ] Normal launch feels fast (startup no longer fetches; first quiz
      tap pays the load — should be brief with a warm cache).

Quizzes:
- [ ] Timing quiz: "Timing doesn't matter" button color matches the
      palette; correct answer highlights on BOTH correct and failed
      questions; failed reveal lingers ~2.5s (SQ4/SQ8).
      NOTE (2026-08-05): only partly pinned - the 2.5s failed-reveal delay is a
      source constant (src/gobattlekit/screens/timing_quiz.py:144) and
      tests/test_quiz_streak_flame.py covers the wrong-answer path; the button
      color and the correct-answer highlight have no test at all. Still needs
      eyes.
- [x] Rapid double-tap an answer — no double score, no skipped question
      (SQ6).
      VERIFIED (2026-08-05): tests/test_quiz_double_tap.py fires the real
      answer handler twice for all three quizzes and asserts the score/streak
      move once AND that exactly one advance task is scheduled (a second one
      is what skipped a question); commit eea06b9, guard from 2c987b1.

## Android (emulator session — currently excluded, blockers listed)

- [ ] **SI5 (BLOCKER, fix before testing the rest):** file-picker CSV
      import likely writes NUL bytes — Chaquopy passes `bytearray` to
      `InputStream.read()` by copy. Rewrite the read loop with
      `jarray('byte')` and verify a real import end-to-end. Blocks Google
      Play beta.
      NOTE (2026-08-05): read loop rewritten with jarray (commit 00713e4);
      end-to-end emulator import verification still required.
- [x] Inbox polling correctly absent on Android (AP5) — file picker only.
      VERIFIED (2026-08-05): code inspection IS the verification here -
      _start_inbox_poll returns before creating the task unless ON_IOS
      (src/gobattlekit/app.py:139), so no poll task can exist on Android;
      commit 7686e0b.
- [ ] URL-open failure dialog (about/help/credits links on an emulator
      with no browser) shows once, no traceback spam (SQ1).
- [ ] Known cosmetic: white border in light mode (accepted, dark forced
      on iOS only — check what Android does with the Material theme).
