# threshold_export

Exports app-consumable IV thresholds from pogo-simulator deep-dive replay
blobs (`userdata/replay/*.replay.pkl.gz`), so GoBattleKit never has to ship
or re-derive simulator state.

The pogo-simulator repo is treated as read-only input.

## Usage

The gobattlekit venv has no numpy, so run with the pogo-simulator pyenv
interpreter (gopvpsim is editable-installed there; the script falls back to
`pogo-simulator/src` on sys.path otherwise):

```sh
cd tools/threshold_export
PYENV_VERSION=3.13.12 pyenv exec python export_thresholds.py \
    /Users/mglerner/coding/MGLPoGo/pogo-simulator/userdata/replay/20260612_142213_Tinkaton_great.replay.pkl.gz \
    --thresholds /Users/mglerner/coding/MGLPoGo/pogo-simulator/thresholds/tinkaton.toml \
    --out out
```

`--thresholds` is optional: the blob embeds the threshold registry it was run
with; pass the TOML to use the (possibly newer) authored file as the expert
source instead.

## Outputs (per species/league)

* `<species>_<league>.toml` — named targets for the app. Each target has
  `class` (`"expert"` = authored TOML spread, `"generated"` = derived from
  the dive's resolved anchors), `source`, `desc`, and either
  `attack`/`defense`/`stamina` stat floors (0 = unconstrained) or an explicit
  `ivs` list. At most 4 targets per species/league; expert spreads take
  slots first, then the strongest resolved anchors clustered into tiers
  (one tier value = min achievable focal stat clearing every anchor in the
  cluster). **`onlytop` keys are never emitted** — the app must never need
  rank tables during a scan; a guard asserts this.
* `<species>_<league>_parity.json` — 25 golden parity vectors computed by
  gopvpsim (`gopvpsim.pokemon.iv_rank(species, league=..., shadow=...)`):
  0/0/0, 15/15/15, the cheapest spread at each target boundary, and a
  deterministic rank-stride sample. Fields per vector: `ivs`, `level`, `cp`,
  `attack`, `defense`, `stamina` (HP), `rank`, `stat_product`. The
  gobattlekit test suite asserts its own stat math against these.
* `<species>_<league>_verification.md` — staleness check: every numeric
  expert claim found in the authored anchors' `description` strings
  (e.g. "143.03 def flips 1-2") is re-derived from post-rebalance data and
  marked MATCH / DIVERGED / OPPONENT-GONE / UNRESOLVABLE. Also reports
  whether the blob's per-IV stats still match the current gamemaster.

## How re-derivation works

The dive embeds its resolved anchors in the blob at
`blob['slayer_iter_result']['resolved_anchors']` (list of
`gopvpsim.anchors.ResolvedAnchor`: continuous stat thresholds per
(opponent, move, damage-tier), resolved with pvpoke-default opponent IVs).
Expert writeups instead quote the minimum *achievable* focal stat (IV-grid
value) and usually assume *rank-1* opponents, so the verifier checks both:

1. quantize each blob-resolved threshold onto the focal IV grid
   (`iv_rank`), and
2. minimally re-resolve each claimed opponent with rank-1 IVs against the
   current gamemaster via `gopvpsim.breakpoints.bulkpoints` /
   `gopvpsim.breakpoints.breakpoints` (no battle re-simulation).

A claim MATCHes if either assumption reproduces it within ±0.011 (experts
quote 2 decimals, sometimes truncated). `+ N hp` claims are checked for
achievability at the matched def floor (HP floors are not part of anchor
resolution; they come from survival sims and are carried through as-is in
the expert spreads).

## 2026-06-12 Tinkaton acceptance run

All 8 documented expert anchors in `thresholds/tinkaton.toml` MATCH the
post-rebalance re-derivation (see `out/tinkaton_great_verification.md`);
the 2026-06-11 and 2026-06-12 blobs resolve to identical anchor sets, i.e.
the June 2026 move rebalance did not move any Tinkaton Great anchor.
