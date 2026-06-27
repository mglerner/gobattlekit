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
I made a free, open-source iOS app for PvP. It quizzes you on move counts, timing, and type matchups. It lets you check your actual mons (from PokeGenie or manual typing) against deep-dive stat spreads.

==================== POST BODY ====================

I never played or watched Pokemon anything until Go. I love the game, but I spent like a year playing it and trying to convince myself that I didn't need to actually memorize the huge freaking list of type matchups. Oops.

Then I spent another year just trying to use vibes to know when the opponent was at a charge move. Ooops.

I'm kind of a nerd, so I wrote a Discord bot to quiz me on those. It was cool (and it relied HEAVILY on game data from PvPoke [LINK THIS HERE].

Speaking of being a nerd, I used to read all of the RyanSwag deep dives. Then I'd scan all of my mons into PokeGenie. Then I'd export them to my computer and run a bunch of python scripts to tell me which of my mons met his thresholds. AWKWARD.

I'm good at Python, but know nothing about phone app development. So, I cheated and had Claude help me port all of this to the phone. I FREAKING LOVE IT! For the last couple of Community Days, I went out, caught a bunch of stuff, scanned it into Poke Genie, and my app told me which mons to build ... all on my phone.

As a bonus, I added an optimal timing quiz. Big caveat: I'm just a filthy casual. I've never even hit legend. So, I hope this is useful, please tell me about bugs, and I'm sure you're all better at the game than me :)

## The quizzes

**[IMAGE: 01-quizzes.png -- the three quizzes side by side: type-effectiveness (water vs ice), move-count (Corviknight / Air Cutter), move-timing (Incinerate vs Geomancy). Insert/upload here.]**

- **Type effectiveness**: Quiz yourself about type effectivenesses until it's automatic. This one's useful for PVE and PVP.
- **Move counts**: Questions like "how many Shadow Claws does Sableye need for a Foul Play" and "how many Mud Shots does it take Swampert to reach the first four Hydro Cannons?" The answer to that last one is 5/4/5/4 btw.
- **Optimal Move timing**: People like PvPoke have written [guides](https://pvpoke.com/articles/strategy/guide-to-fast-move-registration/) about this, and people like XehrFelrose have made [videos](https://www.youtube.com/watch?v=UA41fzcAb8A), but it turns out that you're giving up a ton of free energy to opponents if you throw your charge moves at the wrong time. So, quiz yourself on things like "you're using Force Palm. Your opponent is using Shadow Claw. What's the most optimal timing to throw your charge move?"

## The IV tools

Oh man. This one makes me happy because I've wanted it for so long. Just me? Who knows.

You know how RyanSwag [TAG] or JRE47 [TAG]

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

## Why Python on a phone

- It's built with BeeWare / Toga, so the whole app stays in Python.
- [MICHAEL: 1 sentence. Maybe not the slickest-looking app, but Python was the
  point.]
- Because it's BeeWare, an Android build is on the maybe-list. [MICHAEL: set
  expectations, no promised date.]

## Quick note on AI

[MICHAEL: 2-3 sentences. Honest attribution. You built the guts of the original
quiz tool yourself over years; Claude built the phone wrapper. Say plainly which
parts are AI. You can contrast with Post A: the app is more your work, the
Python port was more AI's.]

## Links

- Companion post (the website + Python simulator): [MICHAEL: paste Post A's URL
  once it's live.]
- App Store: [paste once live]
- TestFlight: https://testflight.apple.com/join/CpCtGsES
- Site the spreads come from: https://mglerner.com/pogo-dives
