"""Golden parity vectors: app stat math vs gopvpsim.

tools/threshold_export emits ``out/<species>_<league>_parity.json`` files of
~25 vectors computed by ``gopvpsim.pokemon.iv_rank`` (see
tools/threshold_export/README.md). This module asserts the app's own stat
math (iv_checker.ivs_to_stats / compute_rank_table) reproduces them:

  * level, CP, HP (the vectors' ``stamina`` field) — exact;
  * attack / defense — exact at the vectors' 5-dp rounding;
  * stat_product — exact at the vectors' 2-dp rounding (raw UNFLOORED
    product, the rank-ordering quantity);
  * rank — exact, when the vector carries one (dense unique 1..N over the
    unfloored product, ties by IV-sum descending).

New ``*_parity.json`` files dropped into the out/ dir are picked up
automatically. Per-file tests skip if the species' base stats aren't pinned
below, and ``test_all_parity_species_have_pinned_base_stats`` emits a single
failure telling the developer to pin them.

No gamemaster is loaded: the suite is network- and cache-isolated, so the
base stats are hardcoded here.
"""
import json
import pathlib

import pytest

from gobattlekit.data.iv_checker import (
    LEAGUE_CAPS,
    compute_rank_table,
    ivs_to_stats,
)

# Canonical, checked-in golden vectors. The exporter writes to its scratch
# out/ dir (gitignored, regenerated every dive); copy a species' *_parity.json
# here and pin its base stats below to add it to the suite.
PARITY_DIR = (
    pathlib.Path(__file__).resolve().parent / 'fixtures' / 'parity'
)

# Base stats pinned from the cached gamemaster snapshot that generated the
# parity vectors (~/Documents/gobattlekit_cache/gamemaster.json, etag
# 237b6353cd7f..., pinned 2026-06-12). Hardcoded so this test never fetches
# or reads a gamemaster. Shadow forms share the base form's stats (shadow is
# a stat-time multiplier, not a base-stat change).
PINNED_BASE_STATS = {
    'Tinkaton': {'atk': 155, 'def': 196, 'hp': 198},
    'Sylveon': {'atk': 203, 'def': 205, 'hp': 216},
    'Ninetales': {'atk': 169, 'def': 190, 'hp': 177},
}

# gopvpsim's iv_rank used LEAGUE_MAX_LEVEL.get(league, 51.0); the app's
# default cap is likewise 51 (level 50 + best buddy).
MAX_LEVEL = 51

PARITY_FILES = sorted(PARITY_DIR.glob('*_parity.json'))


def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def test_parity_files_present():
    """The golden files are checked in; an empty glob means a broken path,
    not an empty corpus — fail loudly instead of silently collecting 0."""
    assert PARITY_FILES, f'No *_parity.json files found in {PARITY_DIR}'


def test_all_parity_species_have_pinned_base_stats():
    """Single clear failure (instead of N quiet skips) when a new parity
    file lands for a species whose base stats aren't pinned yet."""
    unpinned = sorted({
        _load(p)['species'] for p in PARITY_FILES
        if _load(p)['species'] not in PINNED_BASE_STATS
    })
    assert not unpinned, (
        f'Parity vectors exist for {unpinned} but their base stats are not '
        f'pinned. Add them to PINNED_BASE_STATS in {__file__} (copy atk/def/hp '
        f'from the gamemaster snapshot that generated the vectors — see '
        f'tools/threshold_export/README.md). Do NOT make the test load a '
        f'gamemaster; the suite is network- and cache-isolated.'
    )


@pytest.mark.parametrize('parity_path', PARITY_FILES, ids=lambda p: p.stem)
def test_parity_vectors(parity_path):
    data = _load(parity_path)
    species = data['species']
    if species not in PINNED_BASE_STATS:
        pytest.skip(
            f'Base stats for {species!r} not pinned in PINNED_BASE_STATS '
            f'(see test_all_parity_species_have_pinned_base_stats).'
        )

    base = PINNED_BASE_STATS[species]
    shadow = bool(data['shadow'])
    max_cp = LEAGUE_CAPS[data['league']]
    vectors = data['vectors']
    assert vectors, f'{parity_path.name} has no vectors'

    # Rank tables are 4096-combo scans; build at most one per file, and only
    # if any vector actually carries a rank. The shadow flag changes the
    # product ordering and the cache key (and the species string keys the
    # Aegislash-Blade special case), so mirror check_thresholds' naming.
    rank_table = {}
    if any('rank' in v for v in vectors):
        rank_species = f'{species} (Shadow)' if shadow else species
        rank_table = compute_rank_table(
            rank_species, base['atk'], base['def'], base['hp'],
            max_level=MAX_LEVEL, max_cp=max_cp, shadow=shadow,
        )

    if shadow:
        # Guard that the vectors genuinely exercise the shadow path: the
        # same IVs computed WITHOUT shadow must not reproduce the vector's
        # attack, or a broken shadow multiplier could pass unnoticed.
        v0 = vectors[0]
        plain = ivs_to_stats(
            *v0['ivs'], start_level=1,
            base_atk=base['atk'], base_def=base['def'], base_sta=base['hp'],
            max_level=MAX_LEVEL, max_cp=max_cp, shadow=False,
        )
        assert plain is None or round(plain['attack'], 5) != v0['attack'], (
            f'{parity_path.name}: shadow vector is indistinguishable from '
            f'the non-shadow computation — it does not exercise the shadow '
            f'path.'
        )

    problems = []
    for vec in vectors:
        a, d, s = vec['ivs']
        # gopvpsim emits HP under 'stamina'; tolerate 'hp' too.
        want_hp = vec.get('stamina', vec.get('hp'))
        stats = ivs_to_stats(
            a, d, s, start_level=1,
            base_atk=base['atk'], base_def=base['def'], base_sta=base['hp'],
            max_level=MAX_LEVEL, max_cp=max_cp, shadow=shadow,
        )
        if stats is None:
            problems.append(
                f'ivs={a}/{d}/{s}: app found no level under the cap; '
                f"gopvpsim says level {vec['level']} cp {vec['cp']}"
            )
            continue

        errs = []
        if stats['level'] != vec['level']:
            errs.append(f"level app={stats['level']} sim={vec['level']}")
        if stats['cp'] != vec['cp']:
            errs.append(f"cp app={stats['cp']} sim={vec['cp']}")
        if round(stats['attack'], 5) != vec['attack']:
            errs.append(f"attack app={stats['attack']!r} sim={vec['attack']}")
        if round(stats['defense'], 5) != vec['defense']:
            errs.append(f"defense app={stats['defense']!r} sim={vec['defense']}")
        if want_hp is not None and stats['stamina'] != want_hp:
            errs.append(f"hp app={stats['stamina']} sim={want_hp}")
        if 'stat_product' in vec:
            raw = stats['attack'] * stats['defense'] * stats['stamina']
            if round(raw, 2) != vec['stat_product']:
                errs.append(
                    f"stat_product app={raw!r} sim={vec['stat_product']}"
                )
        if 'rank' in vec:
            app_rank = rank_table.get((a, d, s))
            if app_rank != vec['rank']:
                errs.append(f"rank app={app_rank} sim={vec['rank']}")
        if errs:
            problems.append(
                f"ivs={a}/{d}/{s} ({vec.get('why', '?')}): " + '; '.join(errs)
            )

    assert not problems, (
        f"{parity_path.name}: {len(problems)}/{len(vectors)} vectors diverge "
        f"from gopvpsim:\n  " + '\n  '.join(problems)
    )
