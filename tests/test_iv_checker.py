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
    _rank_cache,
)


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
                              max_level=40, max_cp=1500.99)
        level = cp_to_level(result['cp'], 8, 15, 15, *self.BASE)
        # The recovered level should be >= the stats level (since cp_to_level
        # finds the *highest* level producing that CP)
        assert level is not None
        assert level >= result['level']

    def test_no_match_returns_none(self):
        # CP=1 is unlikely to match any level for Azumarill
        level = cp_to_level(1, 8, 15, 15, *self.BASE)
        assert level is None

    def test_returns_highest_matching_level(self):
        """If multiple levels produce the same CP, return the highest."""
        # Level 1 and 1.5 both produce very low CP — find a case
        # by brute force
        for target_cp in range(10, 50):
            levels = []
            for lvl in sorted(CPM.keys()):
                cpm = CPM[lvl]
                atk = 112 + 15
                dfn = 152 + 15
                sta = 225 + 15
                cp = int(math.floor((atk * dfn**0.5 * sta**0.5 * cpm**2) / 10))
                if cp == target_cp:
                    levels.append(lvl)
            if len(levels) > 1:
                result = cp_to_level(target_cp, 15, 15, 15, *self.BASE)
                assert result == max(levels)
                break


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

    def test_tied_stat_products_share_rank(self):
        table = compute_rank_table('Azumarill', 112, 152, 225, 40, 1500.99)
        from collections import Counter
        rank_counts = Counter(table.values())
        # If any rank appears more than once, those entries were tied
        ties = {r: c for r, c in rank_counts.items() if c > 1}
        # We just verify the structure is valid — ranks after ties skip numbers
        if ties:
            sorted_ranks = sorted(set(table.values()))
            for i in range(len(sorted_ranks) - 1):
                r = sorted_ranks[i]
                # Next rank should be current rank + count of entries at current rank
                assert sorted_ranks[i + 1] == r + rank_counts[r]


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
