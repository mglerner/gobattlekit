# Post B -- artifacts checklist

The draft is `docs/reddit/post_b/post_b.md`; screenshots go in
`docs/reddit/post_b/images/`. Mirrors the Post A workflow.

## TODO

### A. App Store status -- RESOLVED: TestFlight only at launch

The build is TestFlight-approved (beta review); the App Store 1.0.0 submission
is NOT done yet (Michael does it ~2026-06-27, and approval can take a few days
after submitting). So Post B launches with the TestFlight link + "App Store
coming." Add the `apps.apple.com` link later (Reddit self-post edit + the Links
block) once 1.0.0 goes "Ready for Sale."

### B. Capture screenshots (name them exactly) -- DONE

All three captured at 1320x2868 (iPhone 16 Pro Max, iOS 18.6, 9:41 status bar),
in `images/`:

1. `01-quiz.png` -- the type-effectiveness quiz (reused App Store `04_quiz.png`).
2. `02-iv-checker.png` -- PvP IV Checker overview with the 👑 (reused App Store
   `02_iv_checker.png`).
3. `03-owned-breakdown.png` -- Clodsire drill-down: `0/15/14` with 🏆 +
   `1/15/13` dominated (no badge). Captured by staging a second Clodsire in the
   demo CSV so the trophy surfaces (the lone-hit demo CSV never shows 🏆;
   `pareto_badges` needs 2+ owned with one dominated). CSV restored to canonical
   11 rows afterward.

Optional extras (add markers if you use them): the move-timing quiz, the
Help/About orgodemir credit row, a CSV-import result.

### C. Write the [MICHAEL: ...] prose blocks (your voice)

Origin story, humility, the AI note, the Python-on-phone line, who-the-quizzes-
help, the IV-by-hand-for-years bit, the free/OSS ethos, the optional HSH
mention.

### D. Cross-links

- Paste Post A's URL into Post B's "companion post" line + Links (once A is
  live).
- After B posts, add B's URL to Post A's Links block: the gopvpsim archive
  `docs/reddit/post_a/post_a.md` AND the live Post A thread (Reddit lets you
  edit self-post text).

### E. Posting day

- Pick the sub(s): r/pokemongo and/or r/TheSilphArena (JRE double-posts both).
  For the app on r/pokemongo, lead casual.
- SET A FLAIR (silent fail without it). Do NOT toggle "Brand affiliate."
- Inline images via the Markdown-mode round-trip (brief lesson 4).
- Post midday; stick around for early comments. Expect a possible
  "awaiting moderator approval" hold -- normal.

### F. After it's posted -- GitHub finalization

Link usernames to profiles, swap `**[IMAGE]**` markers to `![](images/...)`,
commit. Keep the Reddit-paste form for any other sub.

## Known / resolved facts

- TestFlight: https://testflight.apple.com/join/CpCtGsES
- Three quizzes: move counts, move timing, type effectiveness.
- Efficient-IV badges confirmed (crown = global Pareto, trophy = best you own),
  credited in Help + About. orgodemir post:
  reddit.com/r/TheSilphArena/comments/yxzg7f/
- Credit Matt / EmpoleonDynamite + PvPoke (no Reddit handle; link pvpoke.com).
  Permission granted 2026-06-23.
- HSH contributor stays UNNAMED ("someone on the HSH Discord").
- BeeWare / Toga; iPhone-only; v1.0.0; Android = maybe.
