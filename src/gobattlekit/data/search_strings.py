#!/usr/bin/env python
"""Generate Pokemon GO in-game search strings and pvpivs.com deep links
from threshold targets.

Design (2026-07-17, from the bclem Reddit feedback + the pvpivs.com
reverse-engineering session):

* The in-game string is the SIMPLE bars-only form: the game's appraisal-bar
  search terms (0attack..4attack etc.) expose IVs only in 5 buckets per stat
  (0, 1-5, 6-10, 11-14, 15), so any string is a CANDIDATE filter, never
  exact. We deliberately do NOT port pvpivs's CP/HP-augmented strings:
  measured on our broad threshold targets they gain only ~1.3-1.5x
  precision while growing to 1.5-4k chars and silently hiding powered-up
  (half-level) mons. The bars-only string is level-independent, so its
  100% recall is unconditional.
* Precision is honestly poor (roughly 5-30% of matched IV spreads
  qualify). Callers MUST surface the matched/qualifying counts returned
  here next to the string (DeathbyToast posts pvpivs strings with exactly
  this "success rate" disclosure).
* pvpivs.com deep links use the rank-checker page's stat-floor params
  (?mon=X&cp=1500&mA=..&mD=..&mHP=..), the same link flavor RyanSwag's
  GamePress deep dives used. Our thresholds ARE stat floors, so the
  mapping is 1:1 and URL length is never a problem.
"""
import urllib.parse

from . import fetcher
from .iv_checker import (
    LEAGUE_CAPS,
    SHADOW_ATK_BONUS,
    SHADOW_DEF_MULT,
    _is_shadow_species,
    compute_rank_table,
    get_pokemon_index,
    ivs_to_stats,
)

# Appraisal-bar buckets: index by IV, value is the in-game search digit.
# 0 = 0, 1 = 1-5, 2 = 6-10, 3 = 11-14, 4 = 15 (verified against Niantic
# help + euphonic.dev + pvpivs searchStr.html line 1129).
BAR_BUCKET = [0] + [1] * 5 + [2] * 5 + [3] * 4 + [4]
_BUCKET_SIZES = {0: 1, 1: 5, 2: 5, 3: 4, 4: 1}

PVPIVS_LEAGUE_CP = {'great': '1500', 'ultra': '2500', 'master': 'ML'}

# Shrink un-shadowed pvpivs floors by this margin so float round-trip
# error can only ADD a borderline IV row to the linked table, never hide
# a qualifying one (recall-safe direction).
_SHADOW_FLOOR_EPSILON = 0.005

_dex_cache = {}
_qualifying_cache = {}


def _dex_number(species):
    """National dex number for a gamemaster speciesName, or None."""
    if not _dex_cache:
        # Late attribute lookup so the test suite's load_gamemaster patch
        # (conftest mock_load_gamemaster) is honored.
        for mon in fetcher.load_gamemaster()['pokemon']:
            _dex_cache[mon['speciesName']] = mon.get('dex')
    return _dex_cache.get(species)


def _base_name(species):
    """Species name minus any '(Shadow)' / '(Form)' parentheticals."""
    name = species
    if name.endswith(' (Shadow)'):
        name = name[:-len(' (Shadow)')]
    if '(' in name:
        name = name.split('(')[0].strip()
    return name


def qualifying_set(species, league, targets, max_level=51):
    """Set of (atk, def, sta) IV combos qualifying for ANY of `targets`.

    `targets` is {name: target_dict} in the bundled-threshold schema
    (attack/defense/stamina floors, optional ivs list, optional onlytop).
    Malformed targets are skipped, mirroring check_thresholds. Cached per
    (species, league, targets-signature).
    """
    max_cp = LEAGUE_CAPS.get(league, 1500)
    # repr() keeps the signature hashable even for malformed hand-edited
    # user targets (ivs=5, onlytop=[10], ...) — those must be SKIPPED like
    # check_thresholds does, not crash the results screen.
    sig = tuple(sorted(
        (name,
         repr(t.get('attack', 0)), repr(t.get('defense', 0)),
         repr(t.get('stamina', 0)),
         repr(t.get('ivs', [])), repr(t.get('onlytop', 0)))
        for name, t in targets.items() if isinstance(t, dict)
    ))
    key = (species, max_level, max_cp, sig)
    if key in _qualifying_cache:
        return _qualifying_cache[key]

    shadow = _is_shadow_species(species)
    base = get_pokemon_index().get(species)
    if base is None:
        _qualifying_cache[key] = set()
        return set()

    rank_table = None
    if any(isinstance(t, dict) and 'onlytop' in t for t in targets.values()):
        rank_table = compute_rank_table(
            species, base['atk'], base['def'], base['hp'],
            max_level=max_level, max_cp=max_cp, shadow=shadow)

    quals = set()
    for a in range(16):
        for d in range(16):
            for s in range(16):
                stats = ivs_to_stats(
                    a, d, s, start_level=1,
                    base_atk=base['atk'], base_def=base['def'],
                    base_sta=base['hp'],
                    max_level=max_level, max_cp=max_cp, shadow=shadow)
                if stats is None:
                    continue
                for target in targets.values():
                    if not isinstance(target, dict):
                        continue
                    try:
                        if not (stats['attack'] >= target.get('attack', 0) and
                                stats['defense'] >= target.get('defense', 0) and
                                stats['stamina'] >= target.get('stamina', 0)):
                            continue
                        if 'ivs' in target and not any(
                                tuple(iv) == (a, d, s)
                                for iv in target['ivs']):
                            continue
                        if 'onlytop' in target and rank_table.get(
                                (a, d, s), 4096) > target['onlytop']:
                            continue
                    except TypeError:
                        continue
                    quals.add((a, d, s))
                    break
    _qualifying_cache[key] = quals
    return quals


def _bucket_term(buckets, stat):
    """'0-2attack' / '0attack,3-4attack' style term for a sorted bucket set."""
    vals = sorted(buckets)
    runs = []
    start = prev = vals[0]
    for v in vals[1:]:
        if v == prev + 1:
            prev = v
        else:
            runs.append((start, prev))
            start = prev = v
    runs.append((start, prev))
    return ','.join(f'{a}{stat}' if a == b else f'{a}-{b}{stat}'
                    for a, b in runs)


def build_search_string(species, league, targets, max_level=51):
    """Bars-only in-game search string for the union of `targets`.

    Returns None when nothing qualifies, else a dict:
      string           ready-to-paste search string
      qualifying_count number of IV combos that actually qualify
      matched_count    number of IV combos the string matches (superset;
                       the string's per-axis buckets form a rectangle)
      buckets          (atk_set, def_set, sta_set) bar-bucket sets, for tests

    Recall is 100% by construction: every qualifying combo's buckets are
    included per axis. Precision = qualifying/matched; callers must show it.
    """
    quals = qualifying_set(species, league, targets, max_level=max_level)
    if not quals:
        return None

    aset = {BAR_BUCKET[a] for a, _, _ in quals}
    dset = {BAR_BUCKET[d] for _, d, _ in quals}
    sset = {BAR_BUCKET[s] for _, _, s in quals}

    name = _base_name(species)
    if name.isalpha():
        prefix = f'+{name.lower()}'
    else:
        # Multi-word / punctuated names ('Mr. Mime', "Farfetch'd") are
        # unreliable as +family terms; a bare dex number matches the
        # species (all forms, no pre-evos) instead.
        dex = _dex_number(species)
        if dex is None:
            return None
        prefix = str(dex)

    parts = [prefix,
             _bucket_term(aset, 'attack'),
             _bucket_term(dset, 'defense'),
             _bucket_term(sset, 'hp')]
    if _is_shadow_species(species):
        parts.append('shadow')

    def _axis_size(bset):
        return sum(_BUCKET_SIZES[b] for b in bset)

    return {
        'string': '&'.join(parts),
        'qualifying_count': len(quals),
        'matched_count': _axis_size(aset) * _axis_size(dset) * _axis_size(sset),
        'buckets': (aset, dset, sset),
    }


def _pvpivs_mon(species):
    """Map a gamemaster speciesName to pvpivs.com's mon= value.

    'Stunfisk (Galarian)' -> 'Stunfisk_Galarian'; 'Mr. Mime' -> 'Mr_Mime';
    shadow suffix dropped (their site models shadow as a checkbox).
    """
    name = species
    if name.endswith(' (Shadow)'):
        name = name[:-len(' (Shadow)')]
    form = ''
    if '(' in name:
        name, form = name.split('(', 1)
        form = form.rstrip(')').strip()
    name = name.strip().replace('.', '').replace("'", '').replace(' ', '_')
    return f'{name}_{form}' if form else name


def build_pvpivs_url(species, league, target):
    """pvpivs.com rank-checker deep link for one stat-floor target.

    Returns {'url': str, 'shadow': bool} or None if the league is unknown.
    For shadow species the floors are un-scaled back to base stats (their
    stat filter runs pre-shadow; the scaling is monotonic so the IV set is
    identical), shrunk by a small epsilon so rounding can only add a
    borderline row, never hide one. 'shadow' is True when the user still
    needs to tick the site's Shadow checkbox to see shadow-scaled stats.
    """
    cp = PVPIVS_LEAGUE_CP.get(league)
    if cp is None or not isinstance(target, dict):
        return None
    if 'ivs' in target:
        # An explicit-IV-list target cannot be expressed as stat floors;
        # linking the unfiltered rank table would present the whole 4096
        # as if it were the target. No link is better than a wrong one.
        return None
    shadow = _is_shadow_species(species)
    params = [('mon', _pvpivs_mon(species)), ('cp', cp)]

    atk = target.get('attack', 0)
    dfn = target.get('defense', 0)
    sta = target.get('stamina', 0)
    if shadow:
        if atk:
            atk = atk / SHADOW_ATK_BONUS - _SHADOW_FLOOR_EPSILON
        if dfn:
            dfn = dfn / SHADOW_DEF_MULT - _SHADOW_FLOOR_EPSILON
    if atk:
        params.append(('mA', f'{atk:.2f}'.rstrip('0').rstrip('.')))
    if dfn:
        params.append(('mD', f'{dfn:.2f}'.rstrip('0').rstrip('.')))
    if sta:
        params.append(('mHP', f'{sta:.2f}'.rstrip('0').rstrip('.')))
    if 'onlytop' in target:
        params.append(('r', str(target['onlytop'])))
    if any(k in ('mA', 'mD') for k, _ in params):
        params.append(('dec', '2'))

    query = '&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in params)
    return {'url': f'https://pvpivs.com/?{query}', 'shadow': shadow}
