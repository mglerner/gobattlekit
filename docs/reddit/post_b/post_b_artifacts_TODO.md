# Post B -- artifacts checklist

The draft is `docs/reddit/post_b/post_b.md`; screenshots go in
`docs/reddit/post_b/images/`. Mirrors the Post A workflow.

## TODO

### A. App Store status -- RESOLVED: LIVE (2026-07-15)

The app is approved and listed:
https://apps.apple.com/us/app/gobattlekit/id6760953142 (shows v1.0).
The post now leads with the App Store link (in the first comment) and keeps
TestFlight as the "get betas early" option.

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

- Post A is LIVE (2026-07-08):
  https://www.reddit.com/r/TheSilphArena/comments/1ugr9qs/i_made_a_website_that_shows_how_all_4096_stack_up/
  - DONE: added to Post B's Links block (`post_b.md`).
  - OPTIONAL (owner's voice, not AI-filled): add a one-line companion callout
    in the body near the `pogo-dives` mention if you want it more visible than
    the Links block.
- After B posts, add B's URL to Post A's Links block: the gopvpsim archive
  `docs/reddit/post_a/post_a.md` (not present in this repo) AND the live Post A
  thread (Reddit lets you edit self-post text).

### E. Posting day -- automod plan (2026-07-15)

Context: Post A (with links in the body) was held as "potential self
promotion" for days; the 2026-07-08 mod mail asking for a good time to post
got no reply. Plan: give automod nothing to match on.

The sub's written rules (checked 2026-07-15) support the post. Rule 5
("Self-promotion is not allowed") enumerates its scope: "Promoting
tournaments, Discord servers, and subreddits, or posting of your friend-code
is not allowed." A free open-source tool is none of those, and the mods
approving Post A confirms tools are acceptable. The post also satisfies
rule 3 (on topic: PvP) and contains no Discord invites, friend codes, or
tournament promotion -- the HSH mentions are credits only, no links.

- The post body has ZERO URLs; every link is in a first comment (the
  "FIRST COMMENT" block in post_b.md). Post the comment immediately after
  the post goes up.
- The body's fallback if the comment also gets filtered: "search the App
  Store for GoBattleKit" (already in the How-to-get-it section).
- Inline screenshots are Reddit-hosted uploads, not external links -- safe.
- Bare u/ mentions are fine; do not turn them into reddit.com URLs in the
  Reddit paste.
- SET A FLAIR (silent fail without it). Do NOT toggle "Brand affiliate."
- Inline images via the Markdown-mode round-trip (brief lesson 4).
- Post midday; stick around for early comments. If it still lands in the mod
  queue, it should at least be visible-to-you: check it in a logged-out /
  incognito window to confirm it's actually public.
- Pick the sub(s): r/pokemongo and/or r/TheSilphArena (JRE double-posts both).
  For the app on r/pokemongo, lead casual.

### F. After it's posted -- GitHub finalization

Link usernames to profiles, swap `**[IMAGE]**` markers to `![](images/...)`,
commit. Keep the Reddit-paste form for any other sub.

## Known / resolved facts

- App Store (live 2026-07-15): https://apps.apple.com/us/app/gobattlekit/id6760953142
- TestFlight: https://testflight.apple.com/join/CpCtGsES
- Three quizzes: move counts, move timing, type effectiveness.
- Efficient-IV badges confirmed (crown = global Pareto, trophy = best you own),
  credited in Help + About. orgodemir post:
  reddit.com/r/TheSilphArena/comments/yxzg7f/
- Credit Matt / EmpoleonDynamite + PvPoke (no Reddit handle; link pvpoke.com).
  Permission granted 2026-06-23.
- HSH contributor stays UNNAMED ("someone on the HSH Discord").
- BeeWare / Toga; iPhone-only; v1.0.0; Android = maybe.
