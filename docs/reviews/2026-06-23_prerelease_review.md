# Pre-release review — 2026-06-23 (v0.0.31 → 1.0.0)

Multi-agent, adversarially-verified review run before taking GoBattleKit from
TestFlight (0.0.24) to a public App Store release as 1.0.0. 38 agents across 8
code dimensions plus App Store / TODO audits; every code finding was verified
by an independent skeptic agent before landing here. 10 candidate findings were
rejected as false positives or confirmations.

Outcome of the code itself: **0 P0 bugs, 1 P1, 8 P2, 8 P3**. Test suite 241
passing and isolated (CLAUDE.md's "191" was stale). The gap to the App Store is
collateral and process, not code quality.

## Confirmed findings and disposition

Status key: FIXED (this pass), DEFERRED (out of scope for 1.0), PROCESS (handled
in the App Store walkthrough, not a code change).

| #   | Sev | Finding                                      | Status                                                     |
| --- | --- | -------------------------------------------- | ---------------------------------------------------------- |
| 1   | P1  | No Pokémon/Niantic trademark disclaimer      | FIXED — Legal section in `about.py` + store copy           |
| 2   | P2  | `development_team` stale `6TV57R6ZCC`        | FIXED — `pyproject.toml` → `MF55GHNQC2`                    |
| 3   | P2  | `load_user_thresholds` non-dict crash        | FIXED — isinstance guard + test                            |
| 4   | P2  | Silent add-target save failure               | FIXED — `add_threshold` returns bool, add branch checks it |
| 5   | P2  | PvPoke MIT notice not retained               | FIXED — `THIRD_PARTY_NOTICES.md`                           |
| 6   | P2  | Evolution gender-orphan post-process missing | DEFERRED — latent; no Female-form target today             |
| 7   | P2  | No pinned iOS deployment target              | FIXED — `min_os_version = "13.0"`                          |
| 8   | P2  | Version-as-build-number                      | FIXED — separate `build` field                             |
| 9   | P2  | Privacy-manifest verification manual-only    | FIXED — assertion added to `prepare_ios.sh`                |
| 10  | P3  | `prepare_ios.sh` "Personal Team" text        | FIXED                                                      |
| 11  | P3  | PokeGenie trademark, no disclaimer           | FIXED — folded into the Legal disclaimer                   |
| 12  | P3  | EmpoleonDynamite not named in credit         | FIXED — `about.py` credit line                             |
| 13  | P3  | Bundled-dep license notices missing          | FIXED — `THIRD_PARTY_NOTICES.md`                           |
| 14  | P3  | `append_user_generated` non-atomic           | SKIPPED — self-healing on read; conscious skip for 1.0     |
| 15  | P3  | `links.py` dialog task not referenced        | FIXED — strong ref held                                    |
| 16  | P3  | Sync CSV parse in poll loop                  | SKIPPED — small CSVs; conscious skip for 1.0               |
| 17  | P3  | Android SI5 NUL-byte / FD-leak               | DEFERRED — Android track, does not gate iOS                |

## Rejected (verified false positives / confirmations)

Recorded so they are not re-litigated: the branched-evo P0 is correctly fixed and
tested; atomic writes + urlopen timeout + prefs corrupt-recovery are present; the
inbox poll-task lifecycle is correct (reference held, cancellable, fail-safe);
startup does not block the iOS watchdog; the stale team ID does not actually reach
the generated Xcode project (which already uses `MF55GHNQC2`); the privacy manifest
already passes Apple review (cleared TestFlight); the Info.plist submission keys are
present; and the privacy posture matches a "Data Not Collected" label.

## App Store readiness (the real gate)

Hard blockers remaining, all PROCESS rather than code:

- Hosted **Privacy Policy URL** (none exists). Draft prepared in
  `docs/appstore/privacy_policy.html`.
- **Marketing URL** `https://mglerner.com/gobattlekit` returns 404. Landing page
  draft prepared; or repoint the URL.
- **Screenshots** for 6.9" and 6.5" iPhone (none exist).
- **Store listing copy**, **App Privacy** ("Data Not Collected"), **Age Rating**,
  **content-rights/IP declaration**. Draft answers in `docs/appstore/`.
- **App Review notes** + sample PokeGenie CSV (the CSV-import flow is non-obvious
  to a reviewer with no CSV).
- **Device verification**: the full `docs/device_test_checklist.md` is unrun, and
  the 0.0.29–1.0.0 UI has never been seen on a device.

Already handled: export compliance (`ITSAppUsesNonExemptEncryption=false`),
`LSApplicationCategoryType=utilities`, 1024 icon + all sizes, deployment target
13.0, the privacy manifest.
