#!/usr/bin/env python
"""
IV checker — compute battle stats from IVs and check against thresholds.
Ported from the PoGoIVChecker notebook.
"""
import csv
import math
from .fetcher import load_gamemaster

# Form name mapping from PokeGenie CSV to PvPoke gamemaster
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

# CP multiplier table — from gamepress.gg/pokemongo/cp-multiplier
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

# League CP caps
LEAGUE_CAPS = {
    'great': 1500.99,
    'ultra': 2500.99,
    'master': 999999.99,
}

# Max level caps
MAX_LEVELS = {
    'normal': 40,
    'xl': 50,
    'bb': 41,      # best buddy
    'xl_bb': 51,   # XL best buddy
}


def get_species_name(name, form, is_shadow):
    """Convert PokeGenie CSV name+form+shadow to gamemaster species name."""
    form_str = FORM_MAP.get(form, form)
    species = name
    if form_str:
        species = f'{name} ({form_str})'
    if is_shadow:
        species = f'{species} (Shadow)'
    return species


def get_pokemon_index():
    """Return a dict of speciesName -> baseStats from the gamemaster."""
    gm = load_gamemaster()
    return {mon['speciesName']: mon['baseStats'] for mon in gm['pokemon']}


def ivs_to_stats(atk_iv, def_iv, sta_iv, start_level, *,
                 base_atk, base_def, base_sta,
                 max_level=40, max_cp=1500.99):
    """Compute the best battle stats for a mon at the given IVs.

    Returns a dict with level, cp, attack, defense, stamina,
    stat_prod, bulk_prod at the highest level that stays under max_cp.
    Returns None if the mon exceeds max_cp even at start_level.
    """
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


def parse_csv(csv_path):
    """Parse a PokeGenie CSV export.

    Returns a list of dicts with the relevant fields.
    """
    mons = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mons.append({
                    'name': row['Name'].strip(),
                    'form': row['Form'].strip(),
                    'cp': int(row['CP']),
                    'atk_iv': int(row['Atk IV']),
                    'def_iv': int(row['Def IV']),
                    'sta_iv': int(row['Sta IV']),
                    'level': float(row['Level Min']),
                    'is_shadow': row['Shadow/Purified'].strip() == '1',
                    'lucky': row['Lucky'].strip() == '1',
                })
            except (KeyError, ValueError):
                continue
    return mons


def check_thresholds(csv_path, thresholds, league='great', max_level=40):
    """Check which mons from a CSV meet the given thresholds.

    thresholds is a dict of:
    {
        'species_name': {  # gamemaster species name e.g. 'Medicham'
            'league_label': {
                'target_name': {
                    'attack': float,  # minimum attack stat (0 = don't care)
                    'defense': float,
                    'stamina': int,
                }
            }
        }
    }

    Returns a dict of species_name -> list of (mon, stats, matched_targets)
    where matched_targets is a list of target names the mon hits.
    """
    pokemon_index = get_pokemon_index()
    mons = parse_csv(csv_path)
    max_cp = LEAGUE_CAPS.get(league, 1500.99)
    results = {}

    for mon in mons:
        species = get_species_name(mon['name'], mon['form'], mon['is_shadow'])
        if species not in pokemon_index:
            continue
        if species not in thresholds:
            continue

        base = pokemon_index[species]
        stats = ivs_to_stats(
            mon['atk_iv'], mon['def_iv'], mon['sta_iv'], mon['level'],
            base_atk=base['atk'], base_def=base['def'], base_sta=base['hp'],
            max_level=max_level, max_cp=max_cp,
        )
        if stats is None:
            continue

        league_label = league.capitalize()
        if league_label not in thresholds[species]:
            continue

        matched = []
        for target_name, target in thresholds[species][league_label].items():
            if (stats['attack'] >= target.get('attack', 0) and
                    stats['defense'] >= target.get('defense', 0) and
                    stats['stamina'] >= target.get('stamina', 0)):
                matched.append(target_name)

        if matched:
            if species not in results:
                results[species] = []
            results[species].append({
                'mon': mon,
                'stats': stats,
                'matched': matched,
            })

    return results
