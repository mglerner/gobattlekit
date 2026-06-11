#!/usr/bin/env python
"""
IV checker — compute battle stats from IVs and check against thresholds.
Ported from the PoGoIVChecker notebook.
"""
import csv
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
    'great': 1500.99,
    'ultra': 2500.99,
    'master': 10000.99,
}

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

    Returns the level as a float (e.g. 20.0 or 20.5), or None if no match found.
    CP is computed as floor((atk * def^0.5 * sta^0.5 * cpm^2) / 10).
    We find the highest level whose computed CP matches the given CP.
    """
    attack = base_atk + atk_iv
    defense = base_def + def_iv
    stamina = base_sta + sta_iv

    best_level = None
    for level, cpm in sorted(CPM.items()):
        computed_cp = int(math.floor(
            (attack * (defense ** 0.5) * (stamina ** 0.5) * (cpm ** 2)) / 10
        ))
        if computed_cp == cp:
            best_level = level
        elif computed_cp > cp and best_level is not None:
            break
    return best_level


def ivs_to_stats(atk_iv, def_iv, sta_iv, start_level, *,
                 base_atk, base_def, base_sta,
                 max_level=40, max_cp=1500.99):
    attack = base_atk + atk_iv
    defense = base_def + def_iv
    stamina = base_sta + sta_iv

    best = None
    level = start_level
    while level <= max_level:
        cpm = CPM.get(level)
        if cpm is None:
            break
        cp = (attack * (defense ** 0.5) * (stamina ** 0.5) * (cpm ** 2)) / 10
        if cp <= max_cp:
            level_attack = attack * cpm
            level_defense = defense * cpm
            level_stamina = stamina * cpm
            stat_prod = math.floor(level_attack * level_defense * math.floor(level_stamina))
            bulk_prod = math.floor(level_defense * math.floor(level_stamina))
            best = {
                'level': level,
                'cp': int(math.floor(cp)),
                'attack': level_attack,
                'defense': level_defense,
                'stamina': int(math.floor(level_stamina)),
                'stat_prod': stat_prod,
                'bulk_prod': bulk_prod,
            }
        level += 0.5
    return best


def compute_rank_table(species, base_atk, base_def, base_sta,
                       max_level, max_cp):
    cache_key = (species, max_level, max_cp)
    if cache_key in _rank_cache:
        return _rank_cache[cache_key]

    logger.info("Computing rank table for %s (max_level=%s)...", species, max_level)
    combos = []
    for a in range(16):
        for d in range(16):
            for s in range(16):
                stats = ivs_to_stats(
                    a, d, s, start_level=1,
                    base_atk=base_atk, base_def=base_def, base_sta=base_sta,
                    max_level=max_level, max_cp=max_cp,
                )
                sp = stats['stat_prod'] if stats is not None else 0
                combos.append((sp, a, d, s))

    combos.sort(reverse=True)

    rank_table = {}
    current_rank = 1
    for i, (sp, a, d, s) in enumerate(combos):
        if i > 0 and sp < combos[i - 1][0]:
            current_rank = i + 1
        rank_table[(a, d, s)] = current_rank

    _rank_cache[cache_key] = rank_table
    return rank_table


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
                })
            except (KeyError, ValueError):
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


def check_thresholds(csv_path, thresholds, league='great', max_level=40,
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
    max_cp = LEAGUE_CAPS.get(league, 1500.99)
    results = {}

    pre_evo_to_final = {}
    if evolution_lines:
        for final, line in evolution_lines.items():
            for member in line:
                pre_evo_to_final[member] = final

    rank_tables = {}

    for mon in mons:
        csv_species = get_species_name(mon['name'], mon['form'], mon['is_shadow'])

        if csv_species in thresholds:
            final_species = csv_species
        elif csv_species in pre_evo_to_final:
            final_species = pre_evo_to_final[csv_species]
        else:
            continue

        if final_species not in pokemon_index:
            continue
        if final_species not in thresholds:
            continue

        base = pokemon_index[final_species]
        stats = ivs_to_stats(
            mon['atk_iv'], mon['def_iv'], mon['sta_iv'], mon['level'],
            base_atk=base['atk'], base_def=base['def'], base_sta=base['hp'],
            max_level=max_level, max_cp=max_cp,
        )
        if stats is None:
            continue

        rank_key = (final_species, max_level, max_cp)
        if rank_key not in rank_tables:
            rank_tables[rank_key] = compute_rank_table(
                final_species,
                base['atk'], base['def'], base['hp'],
                max_level=max_level, max_cp=max_cp,
            )
        stats['rank'] = rank_tables[rank_key].get(
            (mon['atk_iv'], mon['def_iv'], mon['sta_iv']), 4096)

        league_label = league.capitalize()
        if league_label not in thresholds[final_species]:
            continue

        matched = []
        iv_tuple = (mon['atk_iv'], mon['def_iv'], mon['sta_iv'])
        for target_name, target in thresholds[final_species][league_label].items():
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
                # One malformed target (e.g. a string-valued floor from a
                # hand-edited file) must not break the whole check.
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
