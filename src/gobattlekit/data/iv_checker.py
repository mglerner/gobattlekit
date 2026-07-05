#!/usr/bin/env python
"""
IV checker — compute battle stats from IVs and check against thresholds.
Ported from the PoGoIVChecker notebook.
"""
import csv
import json
import logging
import math
from .fetcher import load_gamemaster

logger = logging.getLogger(__name__)

FORM_MAP = {
    '': None,
    'Normal': None,
    'Alola': 'Alolan',
    'Galar': 'Galarian',
    'Hisui': 'Hisuian',
    'Paldea': 'Paldean',
    'Altered': 'Altered',
    'Origin': 'Origin',
    'Defense': 'Defense',
    'Speed': 'Speed',
    'Land': 'Land',
    'Sky': 'Sky',
    'Therian': 'Therian',
    'Confined': 'Confined',
    'Hero': 'Hero',
    'Average': 'Average',
    'Small': 'Small',
    'Large': 'Large',
    'Super': 'Super',
    'Pom-Pom': 'Pom-Pom',
    'Rainy': 'Rainy',
    'Snowy': 'Snowy',
    'Trash': 'Trash',
    'Mega': 'Mega',
}

CPM = {
    1: 0.094, 1.5: 0.1351374318, 2: 0.16639787, 2.5: 0.192650919,
    3: 0.21573247, 3.5: 0.2365726613, 4: 0.25572005, 4.5: 0.2735303812,
    5: 0.29024988, 5.5: 0.3060573775, 6: 0.3210876, 6.5: 0.3354450362,
    7: 0.34921268, 7.5: 0.3624577511, 8: 0.3752356, 8.5: 0.387592416,
    9: 0.39956728, 9.5: 0.4111935514, 10: 0.4225, 10.5: 0.4329264091,
    11: 0.44310755, 11.5: 0.4530599591, 12: 0.4627984, 12.5: 0.472336093,
    13: 0.48168495, 13.5: 0.4908558003, 14: 0.49985844, 14.5: 0.508701765,
    15: 0.51739395, 15.5: 0.5259425113, 16: 0.5343543, 16.5: 0.5426357375,
    17: 0.5507927, 17.5: 0.5588305862, 18: 0.5667545, 18.5: 0.5745691333,
    19: 0.5822789, 19.5: 0.5898879072, 20: 0.5974, 20.5: 0.6048236651,
    21: 0.6121573, 21.5: 0.6194041216, 22: 0.6265671, 22.5: 0.6336491432,
    23: 0.64065295, 23.5: 0.6475809666, 24: 0.65443563, 24.5: 0.6612192524,
    25: 0.667934, 25.5: 0.6745818959, 26: 0.6811649, 26.5: 0.6876849038,
    27: 0.69414365, 27.5: 0.70054287, 28: 0.7068842, 28.5: 0.7131691091,
    29: 0.7193991, 29.5: 0.7255756136, 30: 0.7317, 30.5: 0.7347410093,
    31: 0.7377695, 31.5: 0.7407855938, 32: 0.74378943, 32.5: 0.7467812109,
    33: 0.74976104, 33.5: 0.7527290867, 34: 0.7556855, 34.5: 0.7586303683,
    35: 0.76156384, 35.5: 0.7644860647, 36: 0.76739717, 36.5: 0.7702972656,
    37: 0.7731865, 37.5: 0.7760649616, 38: 0.77893275, 38.5: 0.7817900548,
    39: 0.784637, 39.5: 0.7874736075, 40: 0.7903, 40.5: 0.792803968,
    41: 0.79530001, 41.5: 0.797800015, 42: 0.8003, 42.5: 0.802799995,
    43: 0.8053, 43.5: 0.8078, 44: 0.81029999, 44.5: 0.812799985,
    45: 0.81529999, 45.5: 0.81779999, 46: 0.82029999, 46.5: 0.82279999,
    47: 0.82529999, 47.5: 0.82779999, 48: 0.83029999, 48.5: 0.83279999,
    49: 0.83529999, 49.5: 0.83779999, 50: 0.84029999, 50.5: 0.84279999,
    51: 0.84529999,
}

LEAGUE_CAPS = {
    'great': 1500,
    'ultra': 2500,
    'master': 10000,
}

# PvPoke's shadow battle-stat multipliers. CP is NOT affected by shadow —
# only the scaled battle stats are. Mirrors gopvpsim.pokemon.
SHADOW_ATK_BONUS = 6 / 5   # ×1.2
SHADOW_DEF_MULT = 5 / 6    # ×0.8333…


def _is_shadow_species(species):
    return species.endswith(' (Shadow)')


def compute_cp(base_atk, base_def, base_sta, atk_iv, def_iv, sta_iv, cpm):
    """CP at a given CPM. Minimum CP is 10; floored int (gopvpsim parity —
    the old raw-float cap comparison excluded a sliver of legal spreads)."""
    raw = (
        (base_atk + atk_iv)
        * math.sqrt(base_def + def_iv)
        * math.sqrt(base_sta + sta_iv)
        * cpm ** 2
        / 10
    )
    return max(10, math.floor(raw))

# Module-level cache of (species, max_level, max_cp) -> rank table.
# Grows unbounded across screen visits but is bounded in practice by
# (number of target species) × (3 leagues) × (4096 IV combos per entry),
# which is small enough to ignore. If we ever balloon the target list,
# revisit with an LRU.
_rank_cache = {}


def get_species_name(name, form, is_shadow):
    form_str = FORM_MAP.get(form, form)
    species = name
    if form_str:
        species = f'{name} ({form_str})'
    if is_shadow:
        species = f'{species} (Shadow)'
    return species


def get_pokemon_index():
    gm = load_gamemaster()
    return {mon['speciesName']: mon['baseStats'] for mon in gm['pokemon']}


def cp_to_level(cp, atk_iv, def_iv, sta_iv, base_atk, base_def, base_sta):
    """Find the level that produces the given CP for the given IVs and base stats.

    Returns the level as a float (e.g. 20.0 or 20.5), or None if no match
    found. When several levels share the CP, returns the LOWEST — the mon
    can be powered up from there, while assuming the highest could wrongly
    classify a cap-edge mon as over-cap (IV10).
    """
    for level, cpm in sorted(CPM.items()):
        computed_cp = compute_cp(base_atk, base_def, base_sta,
                                 atk_iv, def_iv, sta_iv, cpm)
        if computed_cp == cp:
            return level
        if computed_cp > cp:
            break
    return None


def ivs_to_stats(atk_iv, def_iv, sta_iv, start_level, *,
                 base_atk, base_def, base_sta,
                 max_level=51, max_cp=1500, shadow=False):
    """Stats at the highest level <= max_level whose CP fits max_cp,
    starting the walk at the mon's actual level (it can't power down).

    Shadow applies PvPoke's ×1.2 atk / ×5/6 def to the returned battle
    stats (and the products); CP is unaffected by shadow. Mirrors
    gopvpsim.user_collection.ivs_to_stats_at_cap.
    """
    attack = base_atk + atk_iv
    defense = base_def + def_iv
    stamina = base_sta + sta_iv
    shadow_atk = SHADOW_ATK_BONUS if shadow else 1.0
    shadow_def = SHADOW_DEF_MULT if shadow else 1.0

    best = None
    level = start_level
    while level <= max_level:
        cpm = CPM.get(level)
        if cpm is None:
            break
        cp = compute_cp(base_atk, base_def, base_sta,
                        atk_iv, def_iv, sta_iv, cpm)
        if cp <= max_cp:
            level_attack = attack * cpm * shadow_atk
            level_defense = defense * cpm * shadow_def
            level_stamina = math.floor(stamina * cpm)
            best = {
                'level': level,
                'cp': cp,
                'attack': level_attack,
                'defense': level_defense,
                'stamina': level_stamina,
                'stat_prod': math.floor(level_attack * level_defense * level_stamina),
                'bulk_prod': math.floor(level_defense * level_stamina),
            }
        level += 0.5
    return best


def compute_rank_table(species, base_atk, base_def, base_sta,
                       max_level, max_cp, shadow=False):
    """{(atk_iv, def_iv, sta_iv): rank} for all IV combos under the cap.

    PvPoke/gopvpsim rank convention: dense unique ranks 1..N over the
    UNFLOORED stat product, ties broken by total IV sum descending.
    Combos over the cap even at level 1 are omitted — callers default
    missing combos to 4096. Shadow changes the product ordering, so it is
    part of the cache key. Aegislash (Blade) powers up in whole levels
    only; mirror gopvpsim's round-down.
    """
    cache_key = (species, max_level, max_cp, shadow)
    if cache_key in _rank_cache:
        return _rank_cache[cache_key]

    logger.info("Computing rank table for %s (max_level=%s)...", species, max_level)
    blade_round_down = (species == 'Aegislash (Blade)')
    combos = []
    for a in range(16):
        for d in range(16):
            for s in range(16):
                stats = ivs_to_stats(
                    a, d, s, start_level=1,
                    base_atk=base_atk, base_def=base_def, base_sta=base_sta,
                    max_level=max_level, max_cp=max_cp, shadow=shadow,
                )
                if stats is None:
                    continue
                if blade_round_down and stats['level'] % 1.0 != 0:
                    stats = ivs_to_stats(
                        a, d, s, start_level=1,
                        base_atk=base_atk, base_def=base_def, base_sta=base_sta,
                        max_level=stats['level'] - 0.5, max_cp=max_cp,
                        shadow=shadow,
                    )
                    if stats is None:
                        continue
                raw_product = stats['attack'] * stats['defense'] * stats['stamina']
                combos.append((raw_product, a + d + s, a, d, s))

    # Sort key deliberately excludes the IVs: on exact (product, ivsum)
    # ties, stable sort preserves the ascending a/d/s generation order,
    # matching gopvpsim's tie-break (pinned by tests/test_parity_vectors.py).
    combos.sort(key=lambda c: (c[0], c[1]), reverse=True)

    rank_table = {}
    for i, (_sp, _ivsum, a, d, s) in enumerate(combos):
        rank_table[(a, d, s)] = i + 1

    _rank_cache[cache_key] = rank_table
    return rank_table


_qualifying_cache = {}


def qualifying_ivs(species, base_atk, base_def, base_sta, target,
                   max_level, max_cp, top_n=100):
    """Top-N IV combos satisfying a target spec, sorted by rank ascending.

    Each entry is (rank, atk_iv, def_iv, sta_iv, stats). Cached per
    (species, level/cp caps, target) — the scan is ~8k ivs_to_stats calls
    and the IV screens run it synchronously on the UI thread.
    """
    key = (species, max_level, max_cp,
           json.dumps(target, sort_keys=True, default=list))
    if key in _qualifying_cache:
        return _qualifying_cache[key]

    shadow = _is_shadow_species(species)
    rank_table = compute_rank_table(
        species, base_atk, base_def, base_sta,
        max_level=max_level, max_cp=max_cp, shadow=shadow,
    )
    qualifying = []
    for (a, d, s), rank in rank_table.items():
        stats = ivs_to_stats(
            a, d, s, start_level=1,
            base_atk=base_atk, base_def=base_def, base_sta=base_sta,
            max_level=max_level, max_cp=max_cp, shadow=shadow,
        )
        if stats is None:
            continue
        if not (stats['attack'] >= target.get('attack', 0) and
                stats['defense'] >= target.get('defense', 0) and
                stats['stamina'] >= target.get('stamina', 0)):
            continue
        if 'ivs' in target and not any(
            tuple(iv) == (a, d, s) for iv in target['ivs']
        ):
            continue
        if 'onlytop' in target and rank > target['onlytop']:
            continue
        qualifying.append((rank, a, d, s, stats))

    qualifying.sort(key=lambda x: x[0])
    result = qualifying[:top_n]
    _qualifying_cache[key] = result
    return result


def parse_csv(csv_path):
    """Parse a PokeGenie-format CSV export (or user_generated.csv in same format)."""
    mons = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                atk_iv = int(row['Atk IV'])
                def_iv = int(row['Def IV'])
                sta_iv = int(row['Sta IV'])
                cp = int(row['CP'])
                if not (0 <= atk_iv <= 15 and 0 <= def_iv <= 15 and 0 <= sta_iv <= 15):
                    continue
                if cp <= 0:
                    continue
                # Gender is '♂' / '♀' / '' (optional column — older
                # PokeGenie exports may not have it). Needed to match
                # gender-differentiated species like Oinkologne /
                # Meowstic / Indeedee (gopvpsim parity).
                gender_raw = (row.get('Gender') or '').strip()
                if gender_raw == '♂':
                    gender = 'male'
                elif gender_raw == '♀':
                    gender = 'female'
                else:
                    gender = ''
                mons.append({
                    'name': row['Name'].strip(),
                    'form': row['Form'].strip(),
                    'cp': cp,
                    'atk_iv': atk_iv,
                    'def_iv': def_iv,
                    'sta_iv': sta_iv,
                    'level': float(row['Level Min']),
                    'is_shadow': row['Shadow/Purified'].strip() == '1',
                    'lucky': row['Lucky'].strip() == '1',
                    'gender': gender,
                })
            except (KeyError, ValueError, TypeError):
                continue
    return mons


def append_user_generated(csv_path, name, atk_iv, def_iv, sta_iv, cp, level):
    """Append a manually entered mon to the user_generated CSV in PokeGenie format."""
    import pathlib
    path = pathlib.Path(csv_path)
    write_header = not path.exists() or path.stat().st_size == 0
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Name', 'Form', 'CP', 'Atk IV', 'Def IV', 'Sta IV',
            'Level Min', 'Shadow/Purified', 'Lucky'
        ])
        if write_header:
            writer.writeheader()
        writer.writerow({
            'Name': name,
            'Form': '',
            'CP': cp,
            'Atk IV': atk_iv,
            'Def IV': def_iv,
            'Sta IV': sta_iv,
            'Level Min': level,
            'Shadow/Purified': '0',
            'Lucky': '0',
        })


_iv_stats_cache = {}


def _scaled_triple(species, atk_iv, def_iv, sta_iv,
                   base_atk, base_def, base_sta, max_level, max_cp, shadow):
    """(attack, defense, stamina) scaled-stat triple for one IV spread, with
    Aegislash (Blade)'s whole-level round-down applied. Returns None if the
    spread is over-cap even at level 1.

    Both sides of the Pareto verdict — the all_iv_stats universe AND each hit's
    comparison point — must go through this one path so they round identically.
    Otherwise a half-level Blade hit keeps un-rounded stats, dodges domination
    against the rounded universe, and earns a spurious crown. Mirrors gopvpsim,
    which rounds Blade down before the efficiency comparison.
    """
    stats = ivs_to_stats(
        atk_iv, def_iv, sta_iv, start_level=1,
        base_atk=base_atk, base_def=base_def, base_sta=base_sta,
        max_level=max_level, max_cp=max_cp, shadow=shadow,
    )
    if stats is None:
        return None
    if species == 'Aegislash (Blade)' and stats['level'] % 1.0 != 0:
        stats = ivs_to_stats(
            atk_iv, def_iv, sta_iv, start_level=1,
            base_atk=base_atk, base_def=base_def, base_sta=base_sta,
            max_level=stats['level'] - 0.5, max_cp=max_cp, shadow=shadow,
        )
        if stats is None:
            return None
    return (stats['attack'], stats['defense'], stats['stamina'])


def all_iv_stats(species, base_atk, base_def, base_sta,
                 max_level, max_cp, shadow=False):
    """List of (attack, defense, stamina) scaled-stat triples for every IV
    combo that fits under the cap. Cached per (species, level/cap, shadow).

    Built via _scaled_triple so the universe rounds Aegislash (Blade) down
    exactly the way each hit's comparison point does.
    """
    key = (species, max_level, max_cp, shadow)
    if key in _iv_stats_cache:
        return _iv_stats_cache[key]
    out = []
    for a in range(16):
        for d in range(16):
            for s in range(16):
                triple = _scaled_triple(species, a, d, s, base_atk, base_def,
                                        base_sta, max_level, max_cp, shadow)
                if triple is not None:
                    out.append(triple)
    _iv_stats_cache[key] = out
    return out


def _dominates(a, b):
    """True if stat triple a is at least as good as b on every axis and
    strictly better on at least one (a != b with a >= b elementwise)."""
    return a != b and a[0] >= b[0] and a[1] >= b[1] and a[2] >= b[2]


def pareto_badges(hits, all_stats=None, points=None):
    """Badge each hit in a displayed group by how Pareto-optimal it is.

    Each hit carries scaled stats in hit['stats']; we compare the
    (attack, defense, stamina) triples. `points` optionally overrides those
    comparison triples (aligned to hits) when the verdict must use different
    stats than the card displays — Aegislash (Blade), whose stats round down
    to a whole level for the comparison while the card shows the raw values.
    Returns a list aligned to `hits`:

      'crown'  — globally efficient: no IV spread beats this one on all three
                 stats at once, so it is Pareto-optimal among ALL spreads that
                 could meet the target. Pass `all_stats` (every spread's
                 triple, from all_iv_stats) to enable this. The "efficient
                 IVs" idea from orgodemir's r/TheSilphArena webapp.
      'trophy' — not a crown, but it is on the LOCAL Pareto frontier (no other
                 hit in the group beats it on all three stats) AND at least one
                 hit in the group is dominated, so the badge distinguishes the
                 keepers from strictly-worse mons you own.
      None     — dominated by one of your own hits, the lone hit when it is not
                 globally efficient, or one of several mutually non-dominated
                 hits (badging them all would say nothing).

    Crown takes precedence over trophy. With all_stats=None, crowns are
    disabled and only the local trophy logic runs.

    Why testing against every spread (not just the qualifying ones) is
    correct: a spread that dominates a qualifying mon also qualifies, since
    its stats are >= the mon's >= the target floor. So the Pareto frontier of
    the qualifying set is exactly the global frontier intersected with it.
    """
    n = len(hits)
    badges = [None] * n
    if n == 0:
        return badges
    pts = points if points is not None else [
        (h['stats']['attack'], h['stats']['defense'], h['stats']['stamina'])
        for h in hits]

    crown = [False] * n
    if all_stats is not None:
        for i, p in enumerate(pts):
            crown[i] = not any(_dominates(s, p) for s in all_stats)

    local_nd = {i for i in range(n)
                if not any(_dominates(pts[j], pts[i])
                           for j in range(n) if j != i)}
    some_dominated = len(local_nd) < n

    for i in range(n):
        if crown[i]:
            badges[i] = 'crown'
        elif i in local_nd and some_dominated:
            badges[i] = 'trophy'
    return badges


def check_thresholds(csv_path, thresholds, league='great', max_level=51,
                     evolution_lines=None, include_empty=False):
    """Check every mon in the given CSV(s) against the thresholds.

    csv_path may be a single path or a list of paths; rows from all files
    are merged (the IV screens pass both the PokeGenie export and
    user_generated.csv so manual entries count alongside an import).
    """
    pokemon_index = get_pokemon_index()
    paths = [csv_path] if isinstance(csv_path, (str, bytes)) else list(csv_path)
    mons = []
    for p in paths:
        mons.extend(parse_csv(p))
    max_cp = LEAGUE_CAPS.get(league, 1500)
    results = {}

    # Multi-valued: a branched pre-evo (Eevee, Tyrogue, Wurmple, ...)
    # belongs to EVERY line that contains it. The old single-valued map
    # collapsed it to the last-iterated final (P0 #1, CODE_REVIEW.md).
    pre_evo_to_finals = {}
    if evolution_lines:
        for final, line in evolution_lines.items():
            for member in line:
                if member != final:
                    pre_evo_to_finals.setdefault(member, []).append(final)

    rank_tables = {}
    league_label = league.capitalize()

    for mon in mons:
        csv_species = get_species_name(mon['name'], mon['form'], mon['is_shadow'])

        # A species with its own targets is checked as itself (direct hit
        # keeps priority — same rule as gopvpsim); otherwise check the row
        # against every final form that has targets.
        if csv_species in thresholds:
            candidates = [csv_species]
        else:
            candidates = [f for f in pre_evo_to_finals.get(csv_species, [])
                          if f in thresholds]

        for final_species in candidates:
            if final_species not in pokemon_index:
                continue
            if league_label not in thresholds[final_species]:
                continue
            league_targets = thresholds[final_species][league_label]

            # Gender filter for gender-differentiated species (Oinkologne /
            # Meowstic / Indeedee): an 'X (Female)' target matches only
            # female mons; a bare 'X' with an 'X (Female)' sibling in the
            # gamemaster matches only male. Blank gender is permissive
            # (older exports lack the column). Mirrors gopvpsim.
            mon_gender = mon.get('gender', '')
            if mon_gender:
                if final_species.endswith(' (Female)'):
                    if mon_gender != 'female':
                        continue
                elif f'{final_species} (Female)' in pokemon_index:
                    if mon_gender != 'male':
                        continue

            base = pokemon_index[final_species]
            stats = ivs_to_stats(
                mon['atk_iv'], mon['def_iv'], mon['sta_iv'], mon['level'],
                base_atk=base['atk'], base_def=base['def'], base_sta=base['hp'],
                max_level=max_level, max_cp=max_cp,
                shadow=mon['is_shadow'],
            )
            if stats is None:
                continue

            iv_tuple = (mon['atk_iv'], mon['def_iv'], mon['sta_iv'])

            # The 4096-combo rank table is expensive — build it only when a
            # target in this species/league actually gates on 'onlytop'.
            # Shadow changes the product ordering, so it keys the table.
            if any(isinstance(t, dict) and 'onlytop' in t
                   for t in league_targets.values()):
                rank_key = (final_species, max_level, max_cp, mon['is_shadow'])
                if rank_key not in rank_tables:
                    rank_tables[rank_key] = compute_rank_table(
                        final_species,
                        base['atk'], base['def'], base['hp'],
                        max_level=max_level, max_cp=max_cp,
                        shadow=mon['is_shadow'],
                    )
                stats['rank'] = rank_tables[rank_key].get(iv_tuple, 4096)

            matched = []
            for target_name, target in league_targets.items():
                try:
                    if not (stats['attack'] >= target.get('attack', 0) and
                            stats['defense'] >= target.get('defense', 0) and
                            stats['stamina'] >= target.get('stamina', 0)):
                        continue
                    if 'ivs' in target:
                        if not any(tuple(iv) == iv_tuple for iv in target['ivs']):
                            continue
                    if 'onlytop' in target:
                        if stats['rank'] > target['onlytop']:
                            continue
                except TypeError:
                    # One malformed target (e.g. a string-valued floor from
                    # a hand-edited file) must not break the whole check.
                    logger.warning("Skipping malformed target %s/%s/%s",
                                   final_species, league_label, target_name)
                    continue
                matched.append(target_name)

            if matched:
                if final_species not in results:
                    results[final_species] = []
                results[final_species].append({
                    'mon': mon,
                    'csv_species': csv_species,
                    'final_species': final_species,
                    'is_pre_evo': csv_species != final_species,
                    'stats': stats,
                    'matched': matched,
                })

    if include_empty:
        league_label = league.capitalize()
        for species in thresholds:
            if species not in results:
                if league_label in thresholds[species]:
                    results[species] = []

    return results
