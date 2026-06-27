# GoBattleKit Reddit "Post B" -- Pre-Publication Claim Audit

Adversarial multi-agent audit (42 claims, 86 agents) of the factual + trust
claims in `post_b.md`, run 2026-06-27 before posting. Each claim was verified
against the live code/web, then independently re-checked by a skeptic told to
falsify it. Full per-claim verdicts: see the workflow task output.

## 1. Verdict

**Almost safe -- one fix required before posting.** 35 of 36 claims verified
true against the live code/links. A single attribution claim (PvPoke spread
provenance) is **misleading** and must be corrected. No privacy/trust claim is
false; the privacy story (free, no ads, no accounts, nothing tracked, on-device
IV checking, nothing uploaded) is cleanly supported by the code.

## 2. Must fix before posting

### `attr-pvpoke` -- PvPoke spread provenance -- MISLEADING

The claim that "the deep-dive spreads derive from the same analysis as PvPoke"
is half true + half false. The credit to PvPoke/EmpoleonDynamite is correct,
but PvPoke supplies only the **gamemaster + meta rankings**. The deep-dive IV
**spreads** do NOT come from PvPoke -- they come from separately-credited
sources: community PvP deep dives (RyanSwag/GamePress, XehrFelrose's Discord)
plus the gopvpsim simulator pipeline.

- **Evidence:** `src/gobattlekit/screens/about.py:91-117`;
  `src/gobattlekit/data/thresholds.py:4`; `src/gobattlekit/data/fetcher.py:24-29`;
  `tools/threshold_export/README.md:3,24,45,60`; `src/gobattlekit/screens/help.py:51,58`.
- **NOTE (this is your prose to write):** this maps to the `[MICHAEL: ...]`
  free/OSS block. Keep two ideas distinct: (a) PvPoke = game data + rankings
  (credit it, MIT); (b) the spreads = RyanSwag/GamePress + XehrFelrose + gopvpsim.
  The separate idea "the spreads come from the same pipeline as the pogo-dives
  companion website" IS true (pogo-dives and the app share the gopvpsim
  pipeline) -- just don't conflate "companion website" with *PvPoke*.

## 3. Confirmed true (by category)

**Privacy / trust (10)** -- free, no IAP/ad/analytics/tracking SDKs (deps =
toga + certifi only); `PrivacyInfo.xcprivacy` declares NSPrivacyTracking=false;
IV math is pure stdlib + local; the sole network egress is a validator-only GET
to `raw.githubusercontent.com/pvpoke` for public game data (no user data in the
body). User CSV/IVs stay in `~/Documents/gobattlekit_cache`.
(Optional tip-jar = external Venmo/support link, gates nothing -- `about.py:72-83`.)

**Features (16)** -- three quizzes (move counts GL/UL/ML, optimal move timing,
type effectiveness) wired in `app.py:42-44`; PokeGenie CSV import + manual entry
both reach `check_thresholds`; crown = globally Pareto-efficient, trophy = local
frontier of owned mons, matching Help (`data/iv_checker.py:405-465`, `help.py:48,56`).

**Tech (5)** -- Python/BeeWare (Briefcase+Toga), v1.0.0, bundle
`com.mglerner.gobattlekit`, iPhone-only release scope, Android "maybe" technically
possible. `pyproject.toml:1,4,5,184`.

**Attribution (4)** -- orgodemir credited in both Help (`help.py:48`) and About
(`about.py:118-138`); app is MIT/public.

**Links / status (6)** -- pvpoke.com, mglerner.com/pogo-dives, the orgodemir
yxzg7f post (via mirror), and the "in the works but not up yet" App Store hedge
all resolve / are consistent.

## 4. Unverifiable / needs Michael

- **TestFlight open-slot state.** `https://testflight.apple.com/join/CpCtGsES`
  returns 200 and names GoBattleKit, but accept/full slot-state renders
  client-side. **Action:** open it on an iOS device just before posting to
  confirm a free tester slot (10k cap / 90-day expiry).
- **orgodemir reddit link.** reddit.com is bot-blocked from this environment;
  author=orgodemir confirmed only via the pullpush.io mirror. Low risk.
- **iPhone-only is submission scope, not a build lock.** The generated Xcode
  project still carries `TARGETED_DEVICE_FAMILY = "1,2"` + an `~ipad`
  orientation key (`pyproject.toml:195`). Does not affect the post's accuracy;
  tighten before archiving if strict iPhone-only is wanted.
