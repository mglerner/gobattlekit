"""Tests for gobattlekit.data.iv_checker — stat computation, CP math, CSV parsing, thresholds."""
import csv
import math
import pytest
from unittest.mock import patch

from gobattlekit.data.iv_checker import (
    CPM,
    LEAGUE_CAPS,
    get_species_name,
    cp_to_level,
    ivs_to_stats,
    compute_rank_table,
    parse_csv,
    append_user_generated,
    check_thresholds,
    pareto_badges,
    all_iv_stats,
    _scaled_triple,
    _rank_cache,
)


def _hit(a, d, s):
    """Minimal hit shape that pareto_badges reads (scaled stats only)."""
    return {'stats': {'attack': a, 'defense': d, 'stamina': s}}


class TestParetoBadges:
    def test_empty(self):
        assert pareto_badges([]) == []

    def test_local_only_disables_crown(self):
        # all_stats=None -> no global universe, so only local trophy logic.
        hits = [_hit(100, 90, 80), _hit(90, 100, 80), _hit(80, 80, 80)]
        assert pareto_badges(hits) == ['trophy', 'trophy', None]

    def test_crown_for_globally_efficient(self):
        universe = [(100, 100, 100), (90, 90, 90)]
        hits = [_hit(100, 100, 100), _hit(90, 90, 90)]
        # First is efficient (nothing dominates it); second is dominated.
        assert pareto_badges(hits, universe) == ['crown', None]

    def test_best_of_yours_is_not_a_crown(self):
        # An unowned super-spread dominates all your hits, so none is
        # globally efficient -> no crown, just local trophies.
        universe = [(110, 110, 110), (100, 90, 80), (90, 100, 80), (80, 80, 80)]
        hits = [_hit(100, 90, 80), _hit(90, 100, 80), _hit(80, 80, 80)]
        assert pareto_badges(hits, universe) == ['trophy', 'trophy', None]

    def test_two_efficient_both_crowned(self):
        # Two efficient spreads (attack vs defense niche); a dominated third.
        universe = [(100, 80, 80), (80, 100, 80), (70, 70, 70)]
        hits = [_hit(100, 80, 80), _hit(80, 100, 80), _hit(70, 70, 70)]
        assert pareto_badges(hits, universe) == ['crown', 'crown', None]

    def test_single_efficient_hit_crowned(self):
        universe = [(50, 50, 50), (40, 60, 40)]
        assert pareto_badges([_hit(50, 50, 50)], universe) == ['crown']

    def test_single_inefficient_hit_blank(self):
        universe = [(60, 60, 60), (50, 50, 50)]
        assert pareto_badges([_hit(50, 50, 50)], universe) == [None]

    def test_crown_beats_trophy_worked_example(self):
        # A and D are efficient; B is dominated by an unowned Z but beats C;
        # C is dominated by your own B. Crown outranks trophy for A and D.
        A, D, B, C, Z = ((100, 95, 90), (90, 100, 92), (98, 96, 88),
                         (95, 90, 85), (99, 96, 89))
        universe = [A, D, B, C, Z]
        hits = [_hit(*A), _hit(*D), _hit(*B), _hit(*C)]
        assert pareto_badges(hits, universe) == ['crown', 'crown', 'trophy', None]

    def test_tied_efficient_both_crowned(self):
        # Two owned mons share the one efficient spread -> both crowned
        # (neither strictly beats the other), the worse one blank.
        universe = [(100, 100, 100), (50, 50, 50)]
        hits = [_hit(100, 100, 100), _hit(100, 100, 100), _hit(50, 50, 50)]
        assert pareto_badges(hits, universe) == ['crown', 'crown', None]

    def test_duplicate_ivs_all_get_the_same_badge(self):
        # Several mons with the SAME IVs must all earn the badge their spread
        # deserves, not reject each other. Here an unowned Z dominates spread
        # X (so X is not a crown), but X beats C; all three X copies -> 🏆.
        universe = [(110, 110, 110), (100, 90, 80), (80, 80, 80)]
        X, C = (100, 90, 80), (80, 80, 80)
        hits = [_hit(*X), _hit(*X), _hit(*X), _hit(*C)]
        assert pareto_badges(hits, universe) == ['trophy', 'trophy', 'trophy', None]

    def test_aegislash_blade_rounds_down_no_spurious_crown(self):
        # Blade powers up in whole levels only, so the Pareto verdict must
        # compare whole-level-rounded stats on BOTH sides. Regression: the
        # universe rounded (all_iv_stats) but the hit stats didn't, so a
        # bottom-tier spread (0/0/9, level 24.5) dodged domination and got a
        # spurious crown. Base stats hardcoded so no gamemaster is needed.
        BA, BD, BS = 272, 97, 155  # Aegislash (Blade) GL base stats
        universe = all_iv_stats('Aegislash (Blade)', BA, BD, BS, 51, 1500, False)
        rounded = _scaled_triple('Aegislash (Blade)', 0, 0, 9,
                                 BA, BD, BS, 51, 1500, False)
        assert pareto_badges([_hit(0, 0, 0)], universe, points=[rounded]) == [None]
        # The un-rounded half-level stats are the bug: they beat the rounded
        # universe and crown. This documents why _scaled_triple is needed.
        raw = ivs_to_stats(0, 0, 9, 1, base_atk=BA, base_def=BD, base_sta=BS,
                           max_level=51, max_cp=1500, shadow=False)
        raw_pt = (raw['attack'], raw['defense'], raw['stamina'])
        assert pareto_badges([_hit(0, 0, 0)], universe, points=[raw_pt]) == ['crown']


# ── get_species_name ──────────────────────────────────────────────


class TestGetSpeciesName:
    def test_plain_name(self):
        assert get_species_name('Azumarill', '', False) == 'Azumarill'

    def test_normal_form_ignored(self):
        assert get_species_name('Castform', 'Normal', False) == 'Castform'

    def test_alolan_form(self):
        assert get_species_name('Ninetales', 'Alola', False) == 'Ninetales (Alolan)'

    def test_galarian_shadow(self):
        assert get_species_name('Stunfisk', 'Galar', True) == 'Stunfisk (Galarian) (Shadow)'

    def test_shadow_no_form(self):
        assert get_species_name('Swampert', '', True) == 'Swampert (Shadow)'

    def test_unknown_form_passthrough(self):
        # Forms not in FORM_MAP are used as-is
        assert get_species_name('Foo', 'SomeNewForm', False) == 'Foo (SomeNewForm)'


# ── CPM table ─────────────────────────────────────────────────────


class TestCPMTable:
    def test_level_1_is_lowest(self):
        assert CPM[1] == min(CPM.values())

    def test_level_51_is_highest(self):
        assert CPM[51] == max(CPM.values())

    def test_monotonically_increasing(self):
        levels = sorted(CPM.keys())
        for a, b in zip(levels, levels[1:]):
            assert CPM[a] < CPM[b], f"CPM not increasing from {a} to {b}"

    def test_half_level_steps(self):
        levels = sorted(CPM.keys())
        for a, b in zip(levels, levels[1:]):
            assert b - a == 0.5, f"Gap between {a} and {b} is not 0.5"

    def test_expected_range(self):
        assert len(CPM) == 101  # levels 1 through 51 in 0.5 steps


# ── ivs_to_stats ──────────────────────────────────────────────────


class TestIvsToStats:
    """Test stat computation using Azumarill base stats (112/152/225)."""

    BASE = {'base_atk': 112, 'base_def': 152, 'base_sta': 225}

    def test_returns_dict_with_expected_keys(self):
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert result is not None
        assert set(result.keys()) == {'level', 'cp', 'attack', 'defense', 'stamina', 'stat_prod', 'bulk_prod'}

    def test_cp_respects_cap(self):
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert result['cp'] <= 1500

    def test_perfect_ivs_great_league(self):
        # 15/15/15 Azumarill should still fit under 1500 CP
        result = ivs_to_stats(15, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert result is not None
        assert result['cp'] <= 1500

    def test_returns_none_when_cp_exceeds_at_start(self):
        # A tiny max_cp that even level 1 exceeds
        result = ivs_to_stats(15, 15, 15, 1, **self.BASE, max_level=40, max_cp=1.0)
        assert result is None

    def test_higher_level_cap_gives_higher_or_equal_stats(self):
        r40 = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        r51 = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=51, max_cp=1500.99)
        assert r51['stat_prod'] >= r40['stat_prod']

    def test_master_league_no_cap(self):
        result = ivs_to_stats(15, 15, 15, 1, **self.BASE, max_level=40, max_cp=10000.99)
        assert result is not None
        assert result['level'] == 40

    def test_stat_product_formula(self):
        """Verify stat_prod = floor(attack * defense * floor(stamina))."""
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        expected = math.floor(result['attack'] * result['defense'] * result['stamina'])
        assert result['stat_prod'] == expected

    def test_bulk_product_formula(self):
        """Verify bulk_prod = floor(defense * floor(stamina))."""
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        expected = math.floor(result['defense'] * result['stamina'])
        assert result['bulk_prod'] == expected

    def test_start_level_respected(self):
        """Starting at level 20 should give result at level >= 20."""
        result = ivs_to_stats(0, 0, 0, 20, **self.BASE, max_level=40, max_cp=1500.99)
        assert result is not None
        assert result['level'] >= 20

    def test_zero_ivs(self):
        result = ivs_to_stats(0, 0, 0, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert result is not None
        assert result['cp'] > 0

    def test_stamina_is_floored_int(self):
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert isinstance(result['stamina'], int)

    def test_cp_is_int(self):
        result = ivs_to_stats(8, 15, 15, 1, **self.BASE, max_level=40, max_cp=1500.99)
        assert isinstance(result['cp'], int)


# ── cp_to_level ───────────────────────────────────────────────────


class TestCpToLevel:
    BASE = (112, 152, 225)  # Azumarill base_atk, base_def, base_sta

    def test_round_trip(self):
        """Compute stats at a known level, then recover that level from CP."""
        result = ivs_to_stats(8, 15, 15, 1,
                              base_atk=112, base_def=152, base_sta=225,
                              max_level=40, max_cp=1500)
        level = cp_to_level(result['cp'], 8, 15, 15, *self.BASE)
        # The recovered level should be <= the stats level (cp_to_level
        # returns the LOWEST level producing that CP — power-up safe).
        assert level is not None
        assert level <= result['level']

    def test_no_match_returns_none(self):
        # CP=1 is below the floor of 10 — never matches.
        level = cp_to_level(1, 8, 15, 15, *self.BASE)
        assert level is None

    def test_returns_lowest_matching_level(self):
        """If multiple levels produce the same CP, return the lowest (IV10:
        assuming the highest could classify a cap-edge mon as over-cap).
        Weak base stats sit at the CP-10 floor across many low levels —
        a guaranteed duplicate-CP case."""
        from gobattlekit.data.iv_checker import compute_cp
        levels_at_10 = [lvl for lvl, cpm in sorted(CPM.items())
                        if compute_cp(10, 10, 10, 0, 0, 0, cpm) == 10]
        assert len(levels_at_10) > 1, "fixture should produce duplicates"
        assert cp_to_level(10, 0, 0, 0, 10, 10, 10) == min(levels_at_10)

    def test_min_cp_is_10(self):
        """CP floors at 10 (gopvpsim/game parity)."""
        from gobattlekit.data.iv_checker import compute_cp
        assert compute_cp(10, 10, 10, 0, 0, 0, CPM[1]) == 10


# ── compute_rank_table ────────────────────────────────────────────


class TestComputeRankTable:
    def setup_method(self):
        _rank_cache.clear()

    def test_has_4096_entries(self):
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        assert len(table) == 4096  # 16^3

    def test_rank_1_exists(self):
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        assert 1 in table.values()

    def test_all_ranks_positive(self):
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        assert all(r >= 1 for r in table.values())

    def test_max_rank_at_most_4096(self):
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        assert max(table.values()) <= 4096

    def test_caching(self):
        _rank_cache.clear()
        t1 = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        t2 = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        assert t1 is t2

    def test_different_caps_different_tables(self):
        _rank_cache.clear()
        t_great = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        t_ultra = compute_rank_table('Azumarill', 112, 152, 225, 40, 2500.99)
        assert t_great is not t_ultra

    def test_ranks_are_dense_and_unique(self):
        """PvPoke/gopvpsim convention: ranks are 1..N with no shared ranks
        (ties broken by IV-sum descending), replacing the old shared
        competition ranks over floored products (CP7)."""
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        ranks = sorted(table.values())
        assert ranks == list(range(1, len(table) + 1))

    def test_shadow_changes_rank_ordering(self):
        """Shadow multiplies atk ×1.2 / def ×5/6, which reshuffles stat
        products — the shadow table must differ from the regular one."""
        plain = compute_rank_table('Azumarill', 112, 152, 225, 51, 1500)
        shadow = compute_rank_table('Azumarill', 112, 152, 225, 51, 1500,
                                    shadow=True)
        assert plain is not shadow
        assert any(plain[k] != shadow[k] for k in plain)


# ── parse_csv ─────────────────────────────────────────────────────


class TestParseCsv:
    HEADER = 'Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,Shadow/Purified,Lucky\n'

    def _write_csv(self, tmp_path, lines):
        p = tmp_path / 'test.csv'
        p.write_text(self.HEADER + lines, encoding='utf-8-sig')
        return str(p)

    def test_valid_row(self, tmp_path):
        path = self._write_csv(tmp_path, 'Azumarill,,1500,8,15,15,40,0,0\n')
        mons = parse_csv(path)
        assert len(mons) == 1
        m = mons[0]
        assert m['name'] == 'Azumarill'
        assert m['atk_iv'] == 8
        assert m['def_iv'] == 15
        assert m['sta_iv'] == 15
        assert m['cp'] == 1500
        assert m['level'] == 40.0
        assert m['is_shadow'] is False
        assert m['lucky'] is False

    def test_shadow_and_lucky(self, tmp_path):
        path = self._write_csv(tmp_path, 'Swampert,,2400,0,14,13,35,1,1\n')
        mons = parse_csv(path)
        assert mons[0]['is_shadow'] is True
        assert mons[0]['lucky'] is True

    def test_form_field(self, tmp_path):
        path = self._write_csv(tmp_path, 'Ninetales,Alola,1480,0,15,11,40,0,0\n')
        mons = parse_csv(path)
        assert mons[0]['form'] == 'Alola'

    def test_iv_out_of_range_skipped(self, tmp_path):
        path = self._write_csv(tmp_path, 'Bad,,100,16,15,15,20,0,0\n')
        mons = parse_csv(path)
        assert len(mons) == 0

    def test_negative_iv_skipped(self, tmp_path):
        path = self._write_csv(tmp_path, 'Bad,,100,-1,15,15,20,0,0\n')
        mons = parse_csv(path)
        assert len(mons) == 0

    def test_zero_cp_skipped(self, tmp_path):
        path = self._write_csv(tmp_path, 'Bad,,0,8,15,15,20,0,0\n')
        mons = parse_csv(path)
        assert len(mons) == 0

    def test_negative_cp_skipped(self, tmp_path):
        path = self._write_csv(tmp_path, 'Bad,,-5,8,15,15,20,0,0\n')
        mons = parse_csv(path)
        assert len(mons) == 0

    def test_malformed_row_skipped(self, tmp_path):
        lines = (
            'Azumarill,,1500,8,15,15,40,0,0\n'
            'Bad,,not_a_number,8,15,15,20,0,0\n'
            'Registeel,,1400,2,15,14,25,0,0\n'
        )
        path = self._write_csv(tmp_path, lines)
        mons = parse_csv(path)
        assert len(mons) == 2

    def test_missing_column_skipped(self, tmp_path):
        p = tmp_path / 'test.csv'
        p.write_text('Name,CP\nAzumarill,1500\n', encoding='utf-8-sig')
        mons = parse_csv(str(p))
        assert len(mons) == 0

    def test_truncated_row_skipped(self, tmp_path):
        """A short/truncated trailing row (fewer columns than the header)
        must be skipped, not abort the whole import. csv.DictReader fills
        the missing fields with None, so int()/float() raise TypeError."""
        lines = (
            'Azumarill,,1500,8,15,15,40,0,0\n'
            'Azumarill,,14\n'
        )
        path = self._write_csv(tmp_path, lines)
        mons = parse_csv(path)
        assert len(mons) == 1
        assert mons[0]['name'] == 'Azumarill'

    def test_empty_file(self, tmp_path):
        p = tmp_path / 'test.csv'
        p.write_text('', encoding='utf-8-sig')
        # csv.DictReader on empty file should just produce no rows
        mons = parse_csv(str(p))
        assert len(mons) == 0

    def test_header_only(self, tmp_path):
        path = self._write_csv(tmp_path, '')
        mons = parse_csv(path)
        assert len(mons) == 0

    def test_whitespace_in_name_stripped(self, tmp_path):
        path = self._write_csv(tmp_path, '  Azumarill  ,,1500,8,15,15,40,0,0\n')
        mons = parse_csv(path)
        assert mons[0]['name'] == 'Azumarill'

    def test_boundary_ivs(self, tmp_path):
        """IVs at exact boundaries (0 and 15) should be accepted."""
        lines = (
            'A,,100,0,0,0,1,0,0\n'
            'B,,100,15,15,15,1,0,0\n'
        )
        path = self._write_csv(tmp_path, lines)
        mons = parse_csv(path)
        assert len(mons) == 2


# ── append_user_generated ─────────────────────────────────────────


class TestAppendUserGenerated:
    def test_creates_file_with_header(self, tmp_path):
        path = str(tmp_path / 'user.csv')
        append_user_generated(path, 'Azumarill', 8, 15, 15, 1500, 40)
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['Name'] == 'Azumarill'
        assert rows[0]['Atk IV'] == '8'

    def test_appends_without_duplicate_header(self, tmp_path):
        path = str(tmp_path / 'user.csv')
        append_user_generated(path, 'Azumarill', 8, 15, 15, 1500, 40)
        append_user_generated(path, 'Registeel', 2, 15, 14, 1400, 25)
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2

    def test_round_trips_through_parse(self, tmp_path):
        path = str(tmp_path / 'user.csv')
        append_user_generated(path, 'Azumarill', 8, 15, 15, 1500, 40)
        mons = parse_csv(path)
        assert len(mons) == 1
        assert mons[0]['name'] == 'Azumarill'
        assert mons[0]['atk_iv'] == 8


# ── check_thresholds ─────────────────────────────────────────────


class TestCheckThresholds:
    HEADER = 'Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,Shadow/Purified,Lucky\n'

    def _write_csv(self, tmp_path, lines):
        p = tmp_path / 'test.csv'
        p.write_text(self.HEADER + lines, encoding='utf-8-sig')
        return str(p)

    def test_matching_threshold(self, tmp_path):
        path = self._write_csv(tmp_path, 'Azumarill,,1400,8,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0},
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert 'Azumarill' in results
        assert len(results['Azumarill']) == 1
        assert 'Bulky' in results['Azumarill'][0]['matched']

    def test_no_match_when_stats_below_threshold(self, tmp_path):
        path = self._write_csv(tmp_path, 'Azumarill,,1400,0,0,0,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'High Atk': {'attack': 999, 'defense': 0, 'stamina': 0},
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert 'Azumarill' not in results

    def test_pre_evolution_matching(self, tmp_path):
        """A Marill in the CSV should match Azumarill thresholds via evolution lines."""
        path = self._write_csv(tmp_path, 'Marill,,200,8,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0},
                },
            },
        }
        evo_lines = {'Azumarill': ['Marill', 'Azumarill']}
        results = check_thresholds(path, thresholds, league='great', max_level=40,
                                   evolution_lines=evo_lines)
        assert 'Azumarill' in results
        assert results['Azumarill'][0]['is_pre_evo'] is True

    def test_iv_filter(self, tmp_path):
        path = self._write_csv(tmp_path,
                               'Azumarill,,1400,8,15,15,20,0,0\n'
                               'Azumarill,,1400,0,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'Exact': {
                        'attack': 0, 'defense': 0, 'stamina': 0,
                        'ivs': [[8, 15, 15]],
                    },
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert len(results['Azumarill']) == 1
        assert results['Azumarill'][0]['mon']['atk_iv'] == 8

    def test_onlytop_filter(self, tmp_path):
        path = self._write_csv(tmp_path, 'Azumarill,,1400,15,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'Top10': {
                        'attack': 0, 'defense': 0, 'stamina': 0,
                        'onlytop': 10,
                    },
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        # 15/15/15 is not a top-10 IV for Great League Azumarill
        # (it's typically a very low rank since you want low attack)
        if 'Azumarill' in results:
            for entry in results['Azumarill']:
                assert entry['stats']['rank'] <= 10

    def test_include_empty(self, tmp_path):
        path = self._write_csv(tmp_path, '')
        thresholds = {
            'Azumarill': {
                'Great': {
                    'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0},
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40,
                                   include_empty=True)
        assert 'Azumarill' in results
        assert results['Azumarill'] == []

    def test_species_not_in_gamemaster_skipped(self, tmp_path):
        path = self._write_csv(tmp_path, 'FakeMonster,,1400,8,15,15,20,0,0\n')
        thresholds = {
            'FakeMonster': {
                'Great': {
                    'Any': {'attack': 0, 'defense': 0, 'stamina': 0},
                },
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert 'FakeMonster' not in results

    def test_wrong_league_no_match(self, tmp_path):
        path = self._write_csv(tmp_path, 'Azumarill,,1400,8,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Ultra': {
                    'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0},
                },
            },
        }
        # Check Great league but thresholds only define Ultra
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert 'Azumarill' not in results

    def test_gender_filter_for_differentiated_species(self, tmp_path):
        """CP5 / gopvpsim parity: during the evolution walk, an
        'X (Female)' target matches only female-gendered pre-evos; the
        bare 'X' (with a Female sibling in the gamemaster) only male;
        blank gender is permissive. (Mirrors gopvpsim's Lechonk tests —
        evolved female rows arrive as 'X (Female)' via the Form column.)"""
        header = ('Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,'
                  'Shadow/Purified,Lucky,Gender\n')
        p = tmp_path / 'gendered.csv'
        p.write_text(header
                     + 'Lechonk,,500,8,15,15,20,0,0,♂\n'
                     + 'Lechonk,,500,9,15,15,20,0,0,♀\n'
                     + 'Lechonk,,500,10,15,15,20,0,0,\n',
                     encoding='utf-8-sig')
        thresholds = {
            'Oinkologne': {
                'Great': {'M': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
            'Oinkologne (Female)': {
                'Great': {'F': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
        }
        evo_lines = {
            'Oinkologne': ['Lechonk', 'Oinkologne'],
            'Oinkologne (Female)': ['Lechonk', 'Oinkologne (Female)'],
        }
        results = check_thresholds(str(p), thresholds, league='great',
                                   max_level=40, evolution_lines=evo_lines)
        male_hits = {h['mon']['atk_iv'] for h in results['Oinkologne']}
        # ♂ row and blank-gender row; never the ♀ row.
        assert male_hits == {8, 10}
        female_hits = {h['mon']['atk_iv'] for h in results['Oinkologne (Female)']}
        assert female_hits == {9, 10}

    def test_parse_csv_gender_column(self, tmp_path):
        header = ('Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,'
                  'Shadow/Purified,Lucky,Gender\n')
        p = tmp_path / 'g.csv'
        p.write_text(header
                     + 'Azumarill,,1400,8,15,15,20,0,0,♀\n'
                     + 'Azumarill,,1400,8,15,15,20,0,0,♂\n'
                     + 'Azumarill,,1400,8,15,15,20,0,0,\n',
                     encoding='utf-8-sig')
        mons = parse_csv(str(p))
        assert [m['gender'] for m in mons] == ['female', 'male', '']

    def test_parse_csv_without_gender_column(self, tmp_path):
        p = tmp_path / 'g.csv'
        p.write_text(self.HEADER + 'Azumarill,,1400,8,15,15,20,0,0\n',
                     encoding='utf-8-sig')
        mons = parse_csv(str(p))
        assert mons[0]['gender'] == ''

    def test_shadow_stat_multipliers_applied(self, tmp_path):
        """A shadow mon's scaled attack gets ×1.2 and defense ×5/6 (CP3,
        gopvpsim parity) — an attack floor between the plain and shadow
        values passes only for the shadow row."""
        path = self._write_csv(tmp_path,
                               'Azumarill,,1400,8,15,15,20,0,0\n'
                               'Azumarill,,1400,8,15,15,20,1,0\n')  # shadow
        plain = ivs_to_stats(8, 15, 15, 20, base_atk=112, base_def=152,
                             base_sta=225, max_level=40, max_cp=1500)
        floor_between = plain['attack'] * 1.1  # plain fails, ×1.2 passes
        thresholds = {
            'Azumarill (Shadow)': {
                'Great': {'ShadowAtk': {'attack': floor_between,
                                        'defense': 0, 'stamina': 0}},
            },
            'Azumarill': {
                'Great': {'PlainAtk': {'attack': floor_between,
                                       'defense': 0, 'stamina': 0}},
            },
        }
        results = check_thresholds(path, thresholds, league='great',
                                   max_level=40)
        assert 'Azumarill (Shadow)' in results
        assert 'Azumarill' not in results
        # CP itself is unaffected by shadow.
        shadow_stats = results['Azumarill (Shadow)'][0]['stats']
        assert shadow_stats['cp'] == plain['cp']

    def test_qualifying_ivs_filters_sorts_and_caches(self):
        """qualifying_ivs powers the empty-target view; it must respect the
        target spec, sort by rank, and cache (the scan is ~8k ivs_to_stats
        calls on the UI thread — SI12)."""
        from gobattlekit.data.iv_checker import qualifying_ivs
        result = qualifying_ivs(
            'Azumarill', 112, 152, 225,
            {'attack': 0, 'defense': 0, 'stamina': 0, 'onlytop': 10},
            max_level=51, max_cp=1500.99,
        )
        assert 0 < len(result) <= 100
        ranks = [r[0] for r in result]
        assert ranks == sorted(ranks)
        assert all(rank <= 10 for rank in ranks)
        again = qualifying_ivs(
            'Azumarill', 112, 152, 225,
            {'attack': 0, 'defense': 0, 'stamina': 0, 'onlytop': 10},
            max_level=51, max_cp=1500.99,
        )
        assert again is result, "second call should hit the cache"

    def test_rank_table_only_computed_when_needed(self, tmp_path):
        """The 4096-combo rank table is expensive (IV8): it must not be
        computed when the species' league has no targets, nor when no
        matching target uses 'onlytop'."""
        from gobattlekit.data.iv_checker import _rank_cache
        path = self._write_csv(tmp_path, 'Azumarill,,1400,8,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Ultra': {'X': {'attack': 0, 'defense': 0, 'stamina': 0,
                                'onlytop': 10}},
                'Great': {'Y': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40)
        assert 'Y' in results['Azumarill'][0]['matched']
        assert _rank_cache == {}, "rank table computed though nothing needed it"
        """check_thresholds must merge several CSVs — the IV screens pass
        both the PokeGenie export and user_generated.csv, so manual entries
        are no longer invisible while an export is loaded (SI1)."""
        p1 = tmp_path / 'export.csv'
        p1.write_text(self.HEADER + 'Azumarill,,1400,8,15,15,20,0,0\n',
                      encoding='utf-8-sig')
        p2 = tmp_path / 'manual.csv'
        p2.write_text(self.HEADER + 'Registeel,,1279,2,15,14,20,0,0\n',
                      encoding='utf-8-sig')
        thresholds = {
            'Azumarill': {'Great': {'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0}}},
            'Registeel': {'Great': {'Tanky': {'attack': 0, 'defense': 0, 'stamina': 0}}},
        }
        results = check_thresholds([str(p1), str(p2)], thresholds,
                                   league='great', max_level=40)
        assert 'Azumarill' in results
        assert 'Registeel' in results

    def test_branched_pre_evo_matches_all_finals(self, tmp_path):
        """A pre-evo whose line branches (modeled here as Marill evolving into
        both Azumarill and Registeel, standing in for Eevee's 8 lines) must be
        checked against EVERY final form that has thresholds. (Was the P0
        strict-xfail pin; fixed per the all-finals design decision.)"""
        path = self._write_csv(tmp_path, 'Marill,,200,8,15,15,20,0,0\n')
        thresholds = {
            'Azumarill': {
                'Great': {'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
            'Registeel': {
                'Great': {'Tanky': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
        }
        evo_lines = {
            'Azumarill': ['Marill', 'Azumarill'],
            'Registeel': ['Marill', 'Registeel'],
        }
        results = check_thresholds(path, thresholds, league='great', max_level=40,
                                   evolution_lines=evo_lines)
        assert 'Azumarill' in results
        assert 'Registeel' in results
        # Same CSV row, evaluated with each final's own base stats.
        assert results['Azumarill'][0]['is_pre_evo'] is True
        assert results['Registeel'][0]['is_pre_evo'] is True
        assert (results['Azumarill'][0]['stats']['attack']
                != results['Registeel'][0]['stats']['attack'])

    def test_direct_threshold_hit_keeps_priority_over_evo_walk(self, tmp_path):
        """If the pre-evo species has its own targets, it is checked as
        itself only — matching gopvpsim's rule."""
        path = self._write_csv(tmp_path, 'Marill,,200,8,15,15,20,0,0\n')
        thresholds = {
            'Marill': {
                'Great': {'Own': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
            'Azumarill': {
                'Great': {'Bulky': {'attack': 0, 'defense': 0, 'stamina': 0}},
            },
        }
        evo_lines = {'Azumarill': ['Marill', 'Azumarill']}
        results = check_thresholds(path, thresholds, league='great', max_level=40,
                                   evolution_lines=evo_lines)
        assert 'Marill' in results
        assert 'Azumarill' not in results
