#!/usr/bin/env python3
"""Export app-consumable thresholds + parity vectors from a gopvpsim
deep-dive replay blob.

Run with the gopvpsim uv-managed venv interpreter (the gobattlekit venv has
no numpy); the interpreter is `<sibling_path>/.venv/bin/python`:

    /Users/mglerner/coding/gopvpsim/.venv/bin/python export_thresholds.py \
        /path/to/<run>.replay.pkl.gz --out out/

Emits three files into --out:

    <species>_<league>.toml              app-consumable named targets
    <species>_<league>_parity.json       golden parity vectors (gopvpsim math)
    <species>_<league>_verification.md   expert-vs-rederived anchor check

Rules baked in (load-bearing for the app):
  * NEVER emits `onlytop` keys — the app must never need rank tables at scan
    time. A guard asserts this on every emitted target.
  * At most MAX_TARGETS targets per species/league. Authored TOML spreads
    (class="expert") win slots first; remaining slots are filled from the
    strongest resolved anchors, clustered into tiers (class="generated").
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import json
import math
import pickle
import re
import sys
import tomllib
from collections import Counter
from datetime import date
from pathlib import Path

# gopvpsim lives in the sibling checkout. Its path is the SINGLE SOURCE OF
# TRUTH in tools/threshold_export/sibling_path — edit that one file to repoint
# it (e.g. when the pogo-simulator dir is renamed to gopvpsim). gopvpsim is
# editable-installed in the 3.13.12 pyenv; SIM_SRC is the source-tree fallback
# for any other interpreter.
SIM_DIR = Path(__file__).with_name("sibling_path").read_text().strip()
SIM_SRC = str(Path(SIM_DIR) / "src")
try:
    import gopvpsim  # noqa: F401
except ImportError:
    sys.path.insert(0, SIM_SRC)

from gopvpsim.breakpoints import (
    breakpoints as scan_breakpoints,
    bulkpoints as scan_bulkpoints,
)
from gopvpsim.data import load_gamemaster, parse_types
from gopvpsim.moves import get_moves
from gopvpsim.pokemon import iv_rank
from gopvpsim.thresholds import (
    IvListSpread, StatCutoffSpread, load_file as load_threshold_file,
)

# Expert writeups quote stats to 2 decimals (sometimes truncated, sometimes
# rounded), so a re-derived grid value matches an expert claim iff it is
# within this tolerance.
EXPERT_TOL = 0.011
MAX_TARGETS = 4
CLUSTER_EPS = 0.75          # stat distance for grouping anchor floors into a tier
N_PARITY_VECTORS = 25
FORBIDDEN_TARGET_KEYS = {"onlytop"}

# Current GL rankings (list order == rank, matched on speciesName). Used only
# when --curation is given; overridable via --rankings.
DEFAULT_RANKINGS = Path(
    "/Users/mglerner/coding/pvpoke/src/data/rankings/all/overall/"
    "rankings-1500.json"
)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def trunc2(x: float) -> float:
    return math.floor(x * 100) / 100


def toml_quote(s: str) -> str:
    return json.dumps(s)  # valid TOML basic string


def toml_key(s: str) -> str:
    """A TOML key segment: bare if safe, else a quoted key. Species names
    like 'Corsola (Galarian)' contain spaces/parens and must be quoted."""
    return s if re.fullmatch(r"[A-Za-z0-9_-]+", s) else toml_quote(s)


def load_blob(path: Path) -> dict:
    with gzip.open(path, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# gopvpsim lookups
# ---------------------------------------------------------------------------

def gm_entry(species: str) -> dict | None:
    gm = load_gamemaster()
    return next((m for m in gm["pokemon"] if m["speciesName"] == species), None)


def species_types(species: str) -> list[str]:
    entry = gm_entry(species)
    return parse_types(entry) if entry else []


def species_moves(species: str) -> list[dict]:
    """Union of fast + charged move dicts for a species (full movepool)."""
    entry = gm_entry(species)
    if entry is None:
        return []
    fast_db, charged_db = get_moves()
    out = [fast_db[m] for m in entry.get("fastMoves", []) if m in fast_db]
    out += [charged_db[m] for m in entry.get("chargedMoves", []) if m in charged_db]
    return out


class StatGrid:
    """Achievable focal stat values (from iv_rank) + quantization helpers.

    A continuous anchor threshold becomes the *minimum achievable* focal stat
    that satisfies it ("grid floor") — that is what expert writeups quote.
    """

    def __init__(self, records: list[dict]):
        self.records = records
        self.defs = sorted({r["def_"] for r in records})
        self.atks = sorted({r["atk"] for r in records})

    def floor(self, stat: str, threshold: float, strict: bool) -> float | None:
        vals = self.defs if stat == "def" else self.atks
        i = (bisect.bisect_right(vals, threshold) if strict
             else bisect.bisect_left(vals, threshold))
        return vals[i] if i < len(vals) else None

    def in_range(self, stat: str, threshold: float) -> bool:
        vals = self.defs if stat == "def" else self.atks
        return vals[0] <= threshold < vals[-1]


# ---------------------------------------------------------------------------
# Targets (deliverable a)
# ---------------------------------------------------------------------------

def expert_targets(league_thresholds) -> list[dict]:
    out = []
    for name, spread in league_thresholds.spreads.items():
        if getattr(spread, "deprecated", False):
            continue
        t = {
            "name": name,
            "class": "expert",
            "source": spread.source or "authored threshold TOML",
            "desc": spread.description or name,
        }
        if isinstance(spread, StatCutoffSpread):
            t.update(attack=spread.attack, defense=spread.defense,
                     stamina=spread.stamina)
        elif isinstance(spread, IvListSpread):
            t["ivs"] = [list(iv) for iv in spread.ivs]
        out.append(t)
    return out


def _cluster_floors(parent_floors: dict[str, float]) -> list[tuple[float, list[str]]]:
    """Group per-parent grid floors into tiers within CLUSTER_EPS.

    Returns [(tier_floor, [parents]), ...] sorted by floor descending; the
    tier floor is the minimum floor in the cluster (every member's anchor is
    cleared at that stat value or above... members above it are NOT cleared,
    so we use the max instead: at the max floor every member is cleared).
    """
    items = sorted(parent_floors.items(), key=lambda kv: -kv[1])
    clusters: list[tuple[float, list[str]]] = []
    for parent, floor in items:
        if clusters and clusters[-1][0] - floor <= CLUSTER_EPS:
            top, members = clusters[-1]
            members.append(parent)
        else:
            clusters.append((floor, [parent]))
    # A tier clears all its members only at the cluster's MAX floor.
    return [(max(parent_floors[p] for p in members), members)
            for top, members in clusters]


# ---------------------------------------------------------------------------
# Curation: drop anchors whose opponent has fallen out of the current meta
# (deliverable 1). See curation.toml for the rule.
# ---------------------------------------------------------------------------

def base_name(opponent: str) -> str:
    """Opponent display name with a trailing ' (Shadow)' stripped."""
    return opponent[: -len(" (Shadow)")] if opponent.endswith(" (Shadow)") else opponent


def load_curation(path: Path) -> dict:
    cfg = tomllib.loads(path.read_text())
    return {
        "rank_threshold": int(cfg.get("rank_threshold", 50)),
        "keep_names": set(cfg.get("keep_names", [])),
    }


def load_rankings(path: Path) -> dict[str, int] | None:
    """speciesName -> 1-indexed rank, or None if the file is unavailable."""
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARNING: rankings unavailable ({path}): {e}; keeping all anchors")
        return None
    return {e["speciesName"]: i + 1 for i, e in enumerate(data)}


def keep_anchor(opponent: str | None, ranks: dict[str, int], cfg: dict) -> bool:
    """True if an anchor's opponent should be kept under the curation rule."""
    if not opponent:
        return True  # no opponent (e.g. CMP anchors) -> never curated out
    if base_name(opponent) in cfg["keep_names"]:
        return True
    rank = ranks.get(opponent)
    return rank is not None and rank <= cfg["rank_threshold"]


def curate_anchors(resolved_anchors, ranks: dict[str, int] | None, cfg: dict):
    """Filter resolved anchors by the curation rule; log a per-species summary.

    If ranks is None (rankings missing) everything is kept.
    """
    if ranks is None:
        return list(resolved_anchors)
    kept, dropped = [], []
    for a in resolved_anchors:
        (kept if keep_anchor(getattr(a, "opponent", None), ranks, cfg)
         else dropped).append(a)

    kept_opps = Counter(getattr(a, "opponent", None) or "(no opponent)" for a in kept)
    drop_opps = Counter(getattr(a, "opponent", None) or "(no opponent)" for a in dropped)
    print(f"curation: kept {len(kept)} anchors, dropped {len(dropped)} "
          f"(rank>{cfg['rank_threshold']} & not on keep-list)")
    for opp in sorted(set(kept_opps) | set(drop_opps)):
        k, d = kept_opps.get(opp, 0), drop_opps.get(opp, 0)
        verdict = "DROP" if d and not k else ("KEEP" if k and not d else "MIXED")
        print(f"  {opp}: kept {k}, dropped {d} [{verdict}]")
    return kept


def generated_targets(resolved_anchors, grid: StatGrid, n_slots: int) -> list[dict]:
    """Curate up to n_slots targets from resolved anchors.

    For each parent anchor, take its strongest sub-anchor whose threshold is
    achievable (in the focal stat range) and quantize to the grid. Cluster
    per-parent floors into tiers; emit the strongest def-side tier(s) and one
    atk-side tier.
    """
    if n_slots <= 0 or not resolved_anchors:
        return []

    best: dict[str, dict] = {"def": {}, "atk": {}}
    for a in resolved_anchors:
        stat = "def" if a.target_stat == "def" else "atk"
        if not grid.in_range(stat, a.threshold_value):
            continue
        floor = grid.floor(stat, a.threshold_value, a.strict)
        if floor is None:
            continue
        cur = best[stat].get(a.parent)
        if cur is None or floor > cur:
            best[stat][a.parent] = floor

    def describe(stat: str, members: list[str]) -> str:
        kind = "bulkpoints" if stat == "def" else "breakpoints/CMP"
        names = sorted(m.replace("auto_", "").replace("_blkp_any", "")
                        .replace("_brkp_any", "").replace("_", " ")
                       for m in members)
        shown = ", ".join(names[:4])
        more = f" +{len(names) - 4} more" if len(names) > 4 else ""
        return f"Clears strongest in-range {kind} vs {shown}{more}."

    out = []
    def_clusters = _cluster_floors(best["def"])
    atk_clusters = _cluster_floors(best["atk"])

    # Highest-value def tiers first, reserving one slot for an atk tier if any.
    n_def = max(0, n_slots - (1 if atk_clusters else 0))
    for floor, members in def_clusters[:n_def]:
        out.append({
            "name": f"Gen bulk {trunc2(floor):.2f}",
            "class": "generated",
            "source": "deep-dive resolved anchors (replay blob)",
            "desc": describe("def", members),
            "attack": 0.0, "defense": trunc2(floor), "stamina": 0.0,
        })
    if atk_clusters and len(out) < n_slots:
        floor, members = atk_clusters[0]
        out.append({
            "name": f"Gen attack {trunc2(floor):.2f}",
            "class": "generated",
            "source": "deep-dive resolved anchors (replay blob)",
            "desc": describe("atk", members),
            "attack": trunc2(floor), "defense": 0.0, "stamina": 0.0,
        })
    return out[:n_slots]


def emit_toml(path: Path, species: str, league: str, sources: str,
              targets: list[dict], blob_name: str) -> None:
    for t in targets:
        bad = FORBIDDEN_TARGET_KEYS & set(t)
        assert not bad, f"forbidden key(s) {bad} in target {t['name']!r}"
    lines = [
        f"# Generated by tools/threshold_export/export_thresholds.py",
        f"# from {blob_name} on {date.today().isoformat()}. Do not hand-edit.",
        "",
        f"[{toml_key(species)}]",
        f"sources = {toml_quote(sources)}",
        "",
    ]
    for t in targets:
        lines.append(f'[{toml_key(species)}.{league}.targets.{toml_quote(t["name"])}]')
        lines.append(f'class = {toml_quote(t["class"])}')
        lines.append(f'source = {toml_quote(t["source"])}')
        lines.append(f'desc = {toml_quote(t["desc"])}')
        if "ivs" in t:
            ivs = ", ".join(f"[{a}, {d}, {s}]" for a, d, s in t["ivs"])
            lines.append(f"ivs = [{ivs}]")
        else:
            lines.append(f'attack = {t["attack"]:g}')
            lines.append(f'defense = {t["defense"]:g}')
            lines.append(f'stamina = {t["stamina"]:g}')
        lines.append("")
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Parity vectors (deliverable b)
# ---------------------------------------------------------------------------

def parity_vectors(records: list[dict], targets: list[dict]) -> list[dict]:
    """~25 representative IV combos with gopvpsim-computed stats.

    Always includes 0/0/0 and 15/15/15, plus the cheapest spread at each
    target's stat boundary, plus a deterministic stride sample over the
    rank-ordered IV space (no randomness).
    """
    by_iv = {(r["atk_iv"], r["def_iv"], r["sta_iv"]): r for r in records}
    picked: dict[tuple, str] = {}

    def pick(iv: tuple, why: str) -> None:
        if iv in by_iv and iv not in picked:
            picked[iv] = why

    pick((0, 0, 0), "corner: worst IVs")
    pick((15, 15, 15), "corner: hundo")

    for t in targets:
        if "ivs" in t:
            for iv in t["ivs"][:2]:
                pick(tuple(iv), f"member of iv-list target {t['name']!r}")
            continue
        cands = [r for r in records
                 if (t["attack"] <= 0 or r["atk"] >= t["attack"])
                 and (t["defense"] <= 0 or r["def_"] >= t["defense"])
                 and (t["stamina"] <= 0 or r["hp"] >= t["stamina"])]
        if not cands:
            continue
        # boundary member: minimal constrained stat, tie-broken by IV tuple
        key_stat = "def_" if t["defense"] > 0 else "atk"
        cands.sort(key=lambda r: (r[key_stat],
                                  r["atk_iv"], r["def_iv"], r["sta_iv"]))
        r = cands[0]
        pick((r["atk_iv"], r["def_iv"], r["sta_iv"]),
             f"boundary of target {t['name']!r}")

    ranked = sorted(records, key=lambda r: r["rank"])
    need = N_PARITY_VECTORS - len(picked)
    step = max(1, len(ranked) // max(1, need))
    for r in ranked[::step]:
        if len(picked) >= N_PARITY_VECTORS:
            break
        pick((r["atk_iv"], r["def_iv"], r["sta_iv"]), "deterministic rank-stride sample")

    out = []
    for iv, why in picked.items():
        r = by_iv[iv]
        out.append({
            "ivs": list(iv),
            "level": r["level"],
            "cp": r["cp"],
            "attack": round(r["atk"], 5),
            "defense": round(r["def_"], 5),
            "stamina": r["hp"],
            "rank": r["rank"],
            "stat_product": round(r["stat_product"], 2),
            "why": why,
        })
    out.sort(key=lambda v: tuple(v["ivs"]))
    return out


# ---------------------------------------------------------------------------
# Expert-anchor verification (deliverable c / acceptance test)
# ---------------------------------------------------------------------------

CLAIM_RE = {
    "def": re.compile(r"(\d+\.\d+)\s*def\b"),
    "atk": re.compile(r"(\d+\.\d+)\s*atk\b"),
    "hp": re.compile(r"\+\s*(\d+)\s*hp\b"),
}


def expert_claims(anchor) -> dict:
    """Parse numeric expert claims out of an anchor's description string."""
    out = {}
    for stat, rx in CLAIM_RE.items():
        m = rx.search(anchor.description or "")
        if m:
            out[stat] = float(m.group(1))
    return out


def rank1_tiers(focal_types, focal_moves, opponent: str, side: str,
                grid: StatGrid, league: str) -> list[tuple[str, int, float]]:
    """Minimal re-resolution of one opponent's tiers with RANK-1 opponent IVs
    (the assumption expert writeups use), against the current gamemaster.

    side="def": bulkpoints (opponent's threat moves vs focal defense).
    side="atk": damage breakpoints (focal's moves vs opponent defense).
    Returns [(move_id, damage, continuous_threshold), ...].
    """
    shadow = opponent.endswith(" (Shadow)")
    ranked = iv_rank(opponent, league=league, shadow=shadow)
    if not ranked:
        return []
    r1 = ranked[0]
    otypes = species_types(opponent)
    tiers = []
    if side == "def":
        lo, hi = grid.defs[0], grid.defs[-1]
        for mv in species_moves(opponent):
            for bp in scan_bulkpoints(mv, r1["atk"], otypes, focal_types, lo, hi):
                tiers.append((mv["moveId"], bp.damage, bp.def_threshold))
    else:
        lo, hi = grid.atks[0], grid.atks[-1]
        for mv in focal_moves:
            for bp in scan_breakpoints(mv, focal_types, r1["def_"], otypes, lo, hi):
                tiers.append((mv["moveId"], bp.damage, bp.atk_threshold))
    return tiers


def verify_anchors(anchors: dict, resolved_anchors, grid: StatGrid,
                   focal_types, focal_moves, league: str,
                   records: list[dict]) -> list[dict]:
    """For every anchor whose description carries a numeric expert claim,
    re-derive the post-rebalance grid value and produce a verdict row."""
    by_parent: dict[str, list] = {}
    for a in resolved_anchors:
        by_parent.setdefault(a.parent, []).append(a)

    rows = []
    for name, anchor in anchors.items():
        claims = expert_claims(anchor)
        stat = "def" if "def" in claims else ("atk" if "atk" in claims else None)
        if stat is None:
            continue
        expert = claims[stat]
        opponent = getattr(anchor, "opponent", None)
        row = {
            "anchor": name, "opponent": opponent, "stat": stat,
            "expert": expert, "hp_claim": claims.get("hp"),
        }

        if opponent and gm_entry(opponent) is None:
            row.update(verdict="OPPONENT-GONE", rederived=None,
                       note=f"{opponent!r} not in current gamemaster")
            rows.append(row)
            continue

        strict = (stat == "def")  # bulkpoints use >, breakpoints use >=
        candidates = []  # (assumption, move, dmg, threshold, grid_floor)
        for a in by_parent.get(name, []):
            if a.target_stat != stat:
                continue
            g = grid.floor(stat, a.threshold_value, a.strict)
            if g is not None:
                candidates.append(("pvpoke-default opp IVs (blob resolution)",
                                   a.move_id, a.damage, a.threshold_value, g))
        if opponent:
            for mid, dmg, thr in rank1_tiers(focal_types, focal_moves,
                                             opponent, stat, grid, league):
                g = grid.floor(stat, thr, strict)
                if g is not None:
                    candidates.append(("rank-1 opp IVs (re-resolved, current gamemaster)",
                                       mid, dmg, thr, g))

        if not candidates:
            row.update(verdict="UNRESOLVABLE", rederived=None,
                       note="no resolved sub-anchors in blob and re-resolution "
                            "produced no tiers in the focal stat range")
            rows.append(row)
            continue

        hits = [c for c in candidates if abs(c[4] - expert) <= EXPERT_TOL]
        if hits:
            # Prefer the blob-resolved hit when both assumptions reproduce it.
            hit = hits[0]
            row.update(verdict="MATCH", rederived=round(hit[4], 4),
                       note=f"{hit[1]} tier {hit[2]} thr {hit[3]:.4f} "
                            f"under {hit[0]}")
        else:
            nearest = min(candidates, key=lambda c: abs(c[4] - expert))
            row.update(verdict="DIVERGED", rederived=round(nearest[4], 4),
                       note=f"nearest tier {nearest[1]} {nearest[2]} thr "
                            f"{nearest[3]:.4f} under {nearest[0]}")

        if row.get("hp_claim") and row.get("rederived"):
            floor = row["rederived"]
            max_hp = max((r["hp"] for r in records if r[
                "def_" if stat == "def" else "atk"] >= floor - 1e-9), default=0)
            row["hp_note"] = (f"hp >= {int(row['hp_claim'])} achievable at this "
                              f"{stat} floor: {'yes' if max_hp >= row['hp_claim'] else 'NO'} "
                              f"(max achievable hp {max_hp})")
        rows.append(row)
    return rows


def gamemaster_consistency(blob, records) -> str:
    """Compare blob-time stats (moveset meta) against current gopvpsim stats."""
    meta = blob["moveset_data"][0]["meta"] if blob.get("moveset_data") else []
    by_iv = {(r["atk_iv"], r["def_iv"], r["sta_iv"]): r for r in records}
    worst = 0.0
    n = 0
    for a, d, s, level, cp, atk, deff, hp in meta:
        r = by_iv.get((a, d, s))
        if r is None or r["level"] != level or r["cp"] != cp or r["hp"] != hp:
            return ("MISMATCH: blob-time level/cp/hp differ from current "
                    "gopvpsim — gamemaster changed since the dive ran")
        worst = max(worst, abs(r["atk"] - atk), abs(r["def_"] - deff))
        n += 1
    return (f"OK: all {n} blob IV spreads match current gopvpsim stats "
            f"(max |stat delta| {worst:.2e})")


def write_verification_md(path: Path, species: str, league: str, blob_name: str,
                          rows: list[dict], gm_check: str) -> None:
    lines = [
        f"# {species} ({league}) — expert anchor verification",
        "",
        f"Blob: `{blob_name}`  ",
        f"Generated: {date.today().isoformat()} by `export_thresholds.py`",
        "",
        f"Blob vs current gamemaster: {gm_check}",
        "",
        "Expert claims are parsed from anchor `description` strings in the",
        "authored thresholds TOML. Re-derived values are minimum achievable",
        "focal stat values (IV-grid quantized) that clear the matching damage",
        "tier, computed two ways: from the blob's embedded resolved anchors",
        "(pvpoke-default opponent IVs) and by minimal re-resolution with",
        "rank-1 opponent IVs (`gopvpsim.breakpoints.bulkpoints/breakpoints`,",
        "current gamemaster). A claim MATCHes if either assumption reproduces",
        "it within ±0.011 (experts quote 2 decimals).",
        "",
        "| anchor | opponent | expert | re-derived | verdict | detail |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        expert = f"{r['expert']:.2f} {r['stat']}"
        if r.get("hp_claim"):
            expert += f" + {int(r['hp_claim'])} hp"
        red = f"{r['rederived']:.4f}" if r.get("rederived") is not None else "—"
        detail = r.get("note", "")
        if r.get("hp_note"):
            detail += f"; {r['hp_note']}"
        lines.append(f"| {r['anchor']} | {r.get('opponent') or '—'} | {expert} "
                     f"| {red} | {r['verdict']} | {detail} |")
    lines.append("")
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blob", type=Path, help="replay blob (*.replay.pkl.gz)")
    ap.add_argument("--thresholds", type=Path, default=None,
                    help="authored thresholds TOML; overrides the registry "
                         "embedded in the blob as the expert source")
    ap.add_argument("--out", type=Path, required=True, help="output directory")
    ap.add_argument("--curation", type=Path, default=None,
                    help="curation TOML (e.g. curation.toml); when given, "
                         "resolved anchors whose opponent is out of the meta "
                         "are dropped before clustering. Default: no curation.")
    ap.add_argument("--rankings", type=Path, default=DEFAULT_RANKINGS,
                    help="rankings JSON for the curation rule "
                         "(list order == rank, matched on speciesName)")
    args = ap.parse_args(argv)

    blob = load_blob(args.blob)
    species = blob["species"]
    league = blob["league"]                      # e.g. "great"
    league_key = league.capitalize()             # registry key, e.g. "Great"
    shadow = bool(blob.get("shadow"))
    # A limited-cup dive is mechanically its league (CP cap, iv_rank, registry
    # lookup all stay league-native), but a cup dive's thresholds are a
    # DIFFERENT meta and must NOT overwrite the species' real league
    # thresholds in the app. Route cup exports to a cup-labelled filename +
    # TOML table key so they can neither match bundle_into_app's
    # `*_great.toml` glob NOR collide on the `Species.Great` schema key.
    # (App-side cup toggles are Phase 3; this guard is naming-only.)
    cup = blob.get("cup")
    export_label = cup or league                 # "equinox" for a cup dive, else "great"

    registry = blob.get("threshold_registry")
    if args.thresholds is not None:
        registry = load_threshold_file(args.thresholds)
    sp = registry.species(species) if registry else None
    lt = sp.leagues.get(league_key) if sp else None
    sources = (sp.sources if sp else "") or "replay blob (no authored TOML)"
    spreads_lt = lt if lt else None

    resolved = (blob.get("slayer_iter_result") or {}).get("resolved_anchors") or []
    records = iv_rank(species, league=league, shadow=shadow)
    grid = StatGrid(records)
    focal_types = species_types(species)
    focal_moves = species_moves(species)

    gen_anchors = resolved
    if args.curation is not None:
        cfg = load_curation(args.curation)
        ranks = load_rankings(args.rankings)
        gen_anchors = curate_anchors(resolved, ranks, cfg)

    targets = expert_targets(spreads_lt) if spreads_lt else []
    targets += generated_targets(gen_anchors, grid, MAX_TARGETS - len(targets))
    targets = targets[:MAX_TARGETS]

    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"{slugify(species)}{'_shadow' if shadow else ''}_{export_label}"
    blob_name = args.blob.name

    toml_path = args.out / f"{stem}.toml"
    emit_toml(toml_path, species, export_label, sources, targets, blob_name)

    vectors = parity_vectors(records, targets)
    parity_path = args.out / f"{stem}_parity.json"
    parity_path.write_text(json.dumps({
        "species": species, "league": league, "shadow": shadow,
        "blob": blob_name,
        "generated": date.today().isoformat(),
        "generator_calls": [
            f"gopvpsim.pokemon.iv_rank({species!r}, league={league!r}, "
            f"shadow={shadow}) -> per-IV level/cp/atk/def/hp/stat_product/rank",
        ],
        "vectors": vectors,
    }, indent=2) + "\n")

    rows = verify_anchors(lt.anchors if lt else {}, resolved, grid,
                          focal_types, focal_moves, league, records)
    gm_check = gamemaster_consistency(blob, records)
    verif_path = args.out / f"{stem}_verification.md"
    write_verification_md(verif_path, species, league, blob_name, rows, gm_check)

    print(f"wrote {toml_path}")
    print(f"wrote {parity_path}  ({len(vectors)} vectors)")
    print(f"wrote {verif_path}")
    print(json.dumps({"verdicts": rows}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
