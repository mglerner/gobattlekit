# Device test checklist — pre-1.0.0 App Store release

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
- [ ] Quiz / quiz-summary screens (still NOT wrapped on purpose): on the
      small device, confirm a question + its answers + any reveal still fit
      without clipping. If one clips, flag it — do not assume it's fine.

Threshold-pipeline UI (0.0.29–1.0.0, never device-verified):
- [ ] My PvP IV Targets: provenance shows correctly (expert vs generated
      vs user badges), SIM badges render, and per-hit stat-product rank
      appears for all hits (not just onlytop).
- [ ] The expanded species set (~47) loads and the Edit Targets species
      picker is complete.
- [ ] Add a target, then confirm a forced save failure surfaces the
      "Could not save target" error instead of silently dropping it
      (hard to trigger on-device; at minimum confirm a normal add works).
- [ ] Pareto badges: in a species/target with several of your hits, the
      globally-efficient mon(s) show 👑, a best-of-yours-but-not-optimal mon
      shows 🏆, and a mon beaten by one of your own shows no badge. Check
      both the per-target view and "Show All", on IV Checker and My PvP IV
      Targets. Badges are absent when there is only one hit and it is not
      efficient.

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
- [ ] ✕ (clear CSV): first tap shows the warning in the status line,
      second tap clears; navigating away and back DISARMS it (SI15).
- [ ] Edit Targets → Clear All: arm it, go into Add Target, cancel, come
      back — button must read "Clear All" again and need two taps (SI4).

Import from Text (the live pogo-simulator contract):
- [ ] Paste a "Copy for IV scanner" JSON fragment from a dive page —
      imports (multi-target fragments too); check the target appears and
      matches expected mons (IV1).
- [ ] Paste garbage / a fragment with a typo'd key — clear error message,
      nothing saved (IV5).
- [ ] Share an ivs-bearing target → re-import the text — ivs survive the
      round trip (IV2).

Matching-semantics spot checks (results CHANGED by the parity work):
- [ ] A shadow mon you know well: its scaled atk/def now include ×1.2 and
      ×5/6 — sanity-check one result against PvPoke (CP3).
- [ ] An `onlytop` target: ranks are now PvPoke-style dense unique ranks —
      spot-check one mon's rank against PvPoke's IV table (CP7).
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
- [ ] Rapid double-tap an answer — no double score, no skipped question
      (SQ6).

## Android (emulator session — currently excluded, blockers listed)

- [ ] **SI5 (BLOCKER, fix before testing the rest):** file-picker CSV
      import likely writes NUL bytes — Chaquopy passes `bytearray` to
      `InputStream.read()` by copy. Rewrite the read loop with
      `jarray('byte')` and verify a real import end-to-end. Blocks Google
      Play beta.
- [ ] Inbox polling correctly absent on Android (AP5) — file picker only.
- [ ] URL-open failure dialog (about/help/credits links on an emulator
      with no browser) shows once, no traceback spam (SQ1).
- [ ] Known cosmetic: white border in light mode (accepted, dark forced
      on iOS only — check what Android does with the Material theme).
