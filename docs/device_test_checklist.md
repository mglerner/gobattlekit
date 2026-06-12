# Device test checklist — post-deep-review (for 0.0.28+)

Everything below changed in the 2026-06-11/12 review fixes and needs eyes
on a real device or emulator. Source findings in
`docs/reviews/2026-06-11_fable5_deep_codebase_review.md`.

## iOS (TestFlight 0.0.28 or `briefcase run iOS`)

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
