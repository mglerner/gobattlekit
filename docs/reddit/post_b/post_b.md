# Post B -- GoBattleKit iOS app (Reddit draft)

Skeleton for the companion app post. Same conventions as Post A:
- `[MICHAEL: ...]` blocks are prose for Michael to write (do NOT AI-fill).
- `**[IMAGE: NN-name.png ...]**` marks where a screenshot goes (named for the
  files in `images/`).
- Usernames are bare `u/` (Reddit pings + auto-links); link them only in the
  GitHub-archive pass.
- Style: no long dashes; avoid honestly / smoke / surface / genuinely / key;
  no "What you get"; no comma-lists of exactly three items.

AUTOMOD STRATEGY (2026-07-15): Post A (link-bearing self-post) got held as
"potential self promotion" for days; mod mail got no reply. So Post B is split:
the POST BODY contains ZERO URLs (domain-based automod rules can't fire on a
linkless text post), and every link lives in a FIRST COMMENT posted immediately
after. The body also makes the app findable with no links at all ("search
GoBattleKit on the App Store") in case the comment gets filtered too. Reddit
uploads (the inline screenshots) are Reddit-hosted media, not external links,
so they're safe to keep in the body.

TITLE:
I made a free, open-source iOS app for PvP. It quizzes you on move counts, timing, and type matchups. It lets you check your actual mons (from PokeGenie or manual typing) against deep-dive stat spreads.

==================== POST BODY (no URLs!) ====================

I never played or watched Pokemon anything until Go. I love the game, but I spent like a year playing it and trying to convince myself that I didn't need to actually memorize the huge freaking list of type matchups. Oops.

Then I spent another year just trying to use vibes to know when the opponent was at a charge move. Ooops.

I'm kind of a nerd, so I wrote a Discord bot to quiz me on those. It was cool (and it relied HEAVILY on game data from PvPoke).

Speaking of being a nerd, I used to read all of the RyanSwag deep dives. Then I'd scan all of my mons into PokeGenie. Then I'd export them to my computer and run a bunch of python scripts to tell me which of my mons met his thresholds. AWKWARD.

I'm good at Python, but know nothing about phone app development. So, I cheated and had Claude help me port all of this to the phone. I FREAKING LOVE IT! For the last couple of Community Days, I went out, caught a bunch of stuff, scanned it into Poke Genie, and my app told me which mons to build ... all on my phone.

As a bonus, I added an optimal timing quiz. Big caveat: I'm just a filthy casual. I've never even hit legend. So, I hope this is useful, please tell me about bugs, and I'm sure you're all better at the game than me :)

(To keep automod happy, all the links are in my first comment below.)

## The quizzes

**[IMAGE: 01-quizzes.png -- the four quiz modes side by side: type-effectiveness (ghost vs flying), move-count (Sableye / Foul Play), move-count sequence (Milotic / Aqua Tail), move-timing (Peck vs Force Palm). Insert/upload here.]**

- **Type effectiveness**: Quiz yourself about type effectivenesses until it's automatic. This one's useful for PVE and PVP.
- **Move counts**: Questions like "how many Shadow Claws does Sableye need for a Foul Play" and "how many Mud Shots does it take Swampert to reach the first four Hydro Cannons?" The answer to that last one is 5/4/5/4 btw.
- **Optimal Move timing**: People like PvPoke have written guides about this, and people like XehrFelrose have made videos (both linked in the comment below), but it turns out that you're giving up a ton of free energy to opponents if you throw your charge moves at the wrong time. So, quiz yourself on things like "you're using Force Palm. Your opponent is using Shadow Claw. What's the most optimal timing to throw your charge move?"

Just a quick note, the examples in this post are all Great League, but the quizzes and IV tools cover all three leagues.

## The IV tools

Oh man. This one makes me happy because I've wanted it for so long. Just me? Who knows.

You know how RyanSwag (u/RyanoftheDay) or JRE47 (u/JRE47) or awesome people on HSH's discord
are always posting deep dives? I always want to know which of my mons would be
Swag-approved etc. If you have PokeGenie's Scan Pro, you can export all of your
scanned mons as a CSV to my app (important note: the app stores everything on
the phone, and never does anything sneaky with it. If you're super paranoid, you
can see all the code on GitHub; link in the comment). If you **don't** have Scan Pro, you can
still enter your IVs by hand. So, works for F2P folks.

**[IMAGE: 02-iv-checker.png -- the PvP IV Checker overview: your own mons checked against the deep-dive spreads, with a 👑 crown. Insert/upload here.]**
**[IMAGE: 03-owned-breakdown.png -- drilling into one species (Clodsire): the owned spread with a 🏆 trophy and the deep-dive tiers it hits. Insert/upload here.]**

Then you can see which of your mons hit the spreads you're looking for. Those
spreads either come from expert sources (SwagTips, people I trust on Discord,
etc) or are auto-generated by my other stuff (the "all 4096 spreads" site from
my last post here; linked below). The auto-generated ones are definitely more
suspect, so they're marked as "[SIM]".

One cool feature inspired by a post from u/orgodemir (linked below): if one of your mons happens to be a Pareto-efficient spread (no other IV beats it on Atk, Def and HP all at once), it gets marked with a crown (👑). Similarly, a trophy (🏆) marks the best of the mons you actually own.

You can also add your own spreads via the "My Spreads" menu. If you get really excited about defining your own spreads (or if some content creator does), there's even a button to copy a spread so you can share it via Discord or whatever.

Did I mention I did this by hand for years with custom Python scripts and Jupyter notebooks? I love having it on my phone.

## Free and open source

I'm a fan of open source in general. Plus, this whole community gives so much out for free. In particular, PvPoke is the most amazing free PoGo resource ever, and this app literally could not exist without it. So obviously I asked Matt if it was OK to even release this (he's in favor) and then I mirrored his MIT open license policy. Just to be clear, there are no ads on the app, no accounts, and it tracks nothing. Again, you can paw through the source on GitHub if you want.

Sorry if it's not the slickest app, but I built it with BeeWare / Toga so that it would all stay in Python. As a bonus, I think I can push out an Android build sometime.

Also, while I'm crediting people, someone on the HSH Discord helped a ton along the way.

## How to get it

It's live on the App Store now (v1.0, iPhone-only, free, no ads, no accounts). The link is in my first comment below, or you can just search the App Store for "GoBattleKit".

## Quick note on AI

I built the guts of all of this myself as a fun hobby project over several years. I definitely used Claude to wrap that all up in a phone app, and to add a couple of features ... and will likely continue using Claude to add more features.

==================== FIRST COMMENT (post immediately after the post) ====================

Links, as promised:

- App Store: https://apps.apple.com/us/app/gobattlekit/id6760953142
- Source code (MIT licensed): https://github.com/mglerner/gobattlekit
- PvPoke: https://pvpoke.com
- PvPoke's fast move registration guide: https://pvpoke.com/articles/strategy/guide-to-fast-move-registration/
- XehrFelrose's move timing video: https://www.youtube.com/watch?v=UA41fzcAb8A
- u/orgodemir's Pareto-efficient IVs post: https://www.reddit.com/r/TheSilphArena/comments/yxzg7f/
- The site the [SIM] spreads come from: https://mglerner.com/pogo-dives
- My earlier post about that site: https://www.reddit.com/r/TheSilphArena/comments/1ugr9qs/i_made_a_website_that_shows_how_all_4096_stack_up/
