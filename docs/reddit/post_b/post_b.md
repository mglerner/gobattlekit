# Post B -- GoBattleKit iOS app (Reddit draft)

Skeleton for the companion app post. Same conventions as Post A:
- `[MICHAEL: ...]` blocks are prose for Michael to write (do NOT AI-fill).
- `**[IMAGE: NN-name.png ...]**` marks where a screenshot goes (named for the
  files in `images/`).
- Usernames are bare `u/` (Reddit pings + auto-links); link them only in the
  GitHub-archive pass.
- Style: no long dashes; avoid honestly / smoke / surface / genuinely / key;
  no "What you get"; no comma-lists of exactly three items.

TITLE:
I made a free, open-source iOS app for PvP. It quizzes you on move counts, timing, and type matchups. It lets you check your actual mons (from PokeGenie or manual typing) against deep-dive strat spreads.

==================== POST BODY ====================

[MICHAEL: 3-4 sentences. The origin story the way you told Matt. The Discord
bot you made years ago that quizzed people on move counts ("how many Shadow
Claws does Sableye need for Foul Play") and type matchups; you wanted it as a
phone app, didn't know mobile dev, used Claude to build the phone version; and
while you were in there you added the PokeGenie-CSV IV-checking you'd wanted
for ages.]

[MICHAEL: 1-2 sentences. Same humility framing as Post A: filthy casual, never
hit Legend, just having fun, not authoritative.]

## Quick note on AI

[MICHAEL: 2-3 sentences. Honest attribution. You built the guts of the original
quiz tool yourself over years; Claude built the phone wrapper. Say plainly which
parts are AI. You can contrast with Post A: the app is more your work, the
Python port was more AI's.]

## Why Python on a phone

- It's built with BeeWare / Toga, so the whole app stays in Python.
- [MICHAEL: 1 sentence. Maybe not the slickest-looking app, but Python was the
  point.]
- Because it's BeeWare, an Android build is on the maybe-list. [MICHAEL: set
  expectations, no promised date.]

## The quizzes

- Move-count quiz: how many fast moves to reach a charged move (the classic
  "how many Shadow Claws does Sableye need for Foul Play").
- Move-timing quiz: when to throw a charged move so you hand over the fewest
  free turns.
- Type-effectiveness quiz: drill the type chart until it's automatic.
- [MICHAEL: 1-2 sentences. Who this is for and why drilling these helps in GBL.
  Useful whether or not you track IVs.]

**[IMAGE: 01-quiz.png -- the type-effectiveness quiz. Insert/upload here.]**

## The IV tools

- Import a CSV that PokeGenie's Scan Pro exports, and the app flags which of
  your own mons meet the IV spreads from the deep dives. No CSV? Type a mon in
  by hand and get the same answer. It runs on your phone; nothing is uploaded.
- The spreads come from the same deep-dive analysis as the website (companion
  post linked below).
- Efficient-IV badges: a crown (👑) marks a Pareto-efficient spread (no other
  IV beats it on Attack, Defense, and Stamina at once), and a trophy marks the
  best of the mons you actually own. Inspired by u/orgodemir's post; credited
  in the Help and About screens.
- [MICHAEL: 1-2 sentences. You did this by hand for years with custom Python +
  Jupyter going back to the SwagTips days; having it live on the phone is the
  upgrade.]

**[IMAGE: 02-iv-checker.png -- the PvP IV Checker overview: your own mons checked against the deep-dive spreads, with a 👑 crown. Insert/upload here.]**
**[IMAGE: 03-owned-breakdown.png -- drilling into one species (Clodsire): the owned spread with a 🏆 trophy and the deep-dive tiers it hits. Insert/upload here.]**

## Free and open source

- The app is free. No ads, no accounts, nothing tracked.
- [MICHAEL: 2-3 sentences on why free / open source. You're a fan of open
  source and this community gives so much away. Call out Matt / EmpoleonDynamite
  and PvPoke specifically as the work this is built on. He gave permission to
  release it.]
- [MICHAEL: optional. Someone on the HSH Discord helped along the way. Reference
  them only as "someone on the HSH Discord," never by name.]

## How to get it

- Public TestFlight beta: https://testflight.apple.com/join/CpCtGsES
- The App Store version (1.0.0, iPhone-only) is in the works but not up yet.
  [MICHAEL: one line -- you'll add the App Store link once it clears review;
  approval can take a few days after you submit.]

## Links

- Companion post (the website + Python simulator): [MICHAEL: paste Post A's URL
  once it's live.]
- App Store: [paste once live]
- TestFlight: https://testflight.apple.com/join/CpCtGsES
- Site the spreads come from: https://mglerner.com/pogo-dives
