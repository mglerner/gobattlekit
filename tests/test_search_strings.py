"""Tests for gobattlekit.data.search_strings — in-game search strings and
pvpivs.com deep links generated from threshold targets."""
import re

from gobattlekit.data.iv_checker import get_pokemon_index, ivs_to_stats
from gobattlekit.data.search_strings import (
    BAR_BUCKET,
    _bucket_term,
    _pvpivs_mon,
    build_pvpivs_url,
    build_search_string,
    qualifying_set,
)
from gobattlekit.data.thresholds import DEFAULT_THRESHOLDS


def test_bar_bucket_boundaries():
    # In-game appraisal-bar search buckets: 0, 1-5, 6-10, 11-14, 15.
    assert BAR_BUCKET[0] == 0
    assert BAR_BUCKET[1] == BAR_BUCKET[5] == 1
    assert BAR_BUCKET[6] == BAR_BUCKET[10] == 2
    assert BAR_BUCKET[11] == BAR_BUCKET[14] == 3
    assert BAR_BUCKET[15] == 4
    assert len(BAR_BUCKET) == 16


def test_bucket_term_run_collapse():
    assert _bucket_term({0, 1, 2}, 'attack') == '0-2attack'
    assert _bucket_term({0, 3, 4}, 'hp') == '0hp,3-4hp'
    assert _bucket_term({2}, 'defense') == '2defense'


class TestBuildSearchString:
    def test_azumarill_great_recall_and_format(self):
        # Azumarill: in MINI_GAMEMASTER and has bundled Great targets.
        targets = DEFAULT_THRESHOLDS['Azumarill']['Great']
        result = build_search_string('Azumarill', 'great', targets)
        assert result is not None
        assert result['string'].startswith('+azumarill&')

        # Independent recall check on the EMITTED string, not the bucket
        # sets: parse each axis term back into allowed-IV sets and verify
        # every qualifying combo passes. Guards the formatting, which is
        # what actually ships.
        allowed = {}
        for term in result['string'].split('&')[1:]:
            stat = re.search(r'(attack|defense|hp)', term).group(1)
            ivs = set()
            for piece in term.split(','):
                lo_hi = re.match(r'(\d)(?:-(\d))?', piece)
                lo = int(lo_hi.group(1))
                hi = int(lo_hi.group(2) or lo)
                for bucket in range(lo, hi + 1):
                    ivs |= {iv for iv in range(16) if BAR_BUCKET[iv] == bucket}
            allowed[stat] = ivs

        quals = qualifying_set('Azumarill', 'great', targets)
        assert quals, "Azumarill Great targets should have qualifying IVs"
        assert result['qualifying_count'] == len(quals)
        for a, d, s in quals:
            assert a in allowed['attack']
            assert d in allowed['defense']
            assert s in allowed['hp']

        # matched_count is exactly the rectangle the emitted string
        # matches — pin it to the independently parsed axis sets so a
        # _BUCKET_SIZES off-by-one cannot survive (review 2026-07-17).
        assert result['matched_count'] == (
            len(allowed['attack']) * len(allowed['defense'])
            * len(allowed['hp']))
        assert result['matched_count'] >= result['qualifying_count']

    # Shadow attack floor only reachable WITH the x1.2 shadow bonus:
    # Azumarill's non-shadow Great-league attack tops out well below 95,
    # so this floor separates shadow from non-shadow stat scaling.
    SHADOW_ATK_FLOOR = {'attack': 95, 'defense': 0, 'stamina': 0}

    def test_shadow_scaling_parity_with_ivs_to_stats(self):
        # qualifying_set must apply shadow stat scaling. Expected set is
        # derived independently via ivs_to_stats(shadow=True), so an
        # accidental shadow=False inside qualifying_set cannot pass
        # (review 2026-07-17: this exact mutant survived the old suite).
        base = get_pokemon_index()['Azumarill (Shadow)']
        expected = set()
        for a in range(16):
            for d in range(16):
                for s in range(16):
                    st = ivs_to_stats(
                        a, d, s, start_level=1,
                        base_atk=base['atk'], base_def=base['def'],
                        base_sta=base['hp'],
                        max_level=51, max_cp=1500, shadow=True)
                    if st is not None and st['attack'] >= 95:
                        expected.add((a, d, s))
        assert expected, "floor must be reachable with the shadow bonus"

        got = qualifying_set('Azumarill (Shadow)', 'great',
                             {'Atk': self.SHADOW_ATK_FLOOR})
        assert got == expected
        # And the same floor on the non-shadow species gives a DIFFERENT
        # set (unreachable without the x1.2 bonus).
        plain = qualifying_set('Azumarill', 'great',
                               {'Atk': self.SHADOW_ATK_FLOOR})
        assert plain != got

    def test_shadow_species_appends_shadow_term(self):
        result = build_search_string(
            'Azumarill (Shadow)', 'great', {'Atk': self.SHADOW_ATK_FLOOR})
        assert result is not None
        assert result['string'].startswith('+azumarill&')
        assert result['string'].endswith('&shadow')

    def test_form_species_keeps_family_prefix(self):
        # Generic '(Form)' strip -> '+family' prefix, no shadow term.
        result = build_search_string(
            'Oinkologne (Female)', 'great',
            {'Any': {'attack': 0, 'defense': 0, 'stamina': 0}})
        assert result is not None
        assert result['string'].startswith('+oinkologne&')
        assert not result['string'].endswith('&shadow')

    def test_malformed_user_targets_are_skipped_not_crashes(self):
        # Hand-edited user thresholds reach this code; mirror
        # check_thresholds' tolerance (skip, never raise).
        for bad in ({'ivs': 5}, {'ivs': [1, 2, 3]}, {'onlytop': [10]},
                    {'attack': 'high'}):
            result = build_search_string(
                'Azumarill', 'great',
                {'Bad': bad,
                 'Good': {'attack': 0, 'defense': 100, 'stamina': 0}})
            assert result is not None  # the good target still counts

    def test_punctuated_name_falls_back_to_dex(self):
        # 'Mr. Mime' is unreliable as a +family term; expect the dex
        # number prefix instead. Catch-all target qualifies everything.
        result = build_search_string(
            'Mr. Mime', 'great',
            {'Any': {'attack': 0, 'defense': 0, 'stamina': 0}})
        assert result is not None
        assert result['string'].split('&')[0] == '122'

    def test_no_qualifiers_returns_none(self):
        # Impossible floor: nothing qualifies.
        result = build_search_string(
            'Azumarill', 'great',
            {'Impossible': {'attack': 99999, 'defense': 0, 'stamina': 0}})
        assert result is None


class TestPvpivsUrl:
    def test_stat_floor_target(self):
        target = DEFAULT_THRESHOLDS['Tinkaton']['Great']['GH Good']
        link = build_pvpivs_url('Tinkaton', 'great', target)
        assert link['shadow'] is False
        url = link['url']
        assert url.startswith('https://pvpivs.com/?')
        assert 'mon=Tinkaton' in url
        assert 'cp=1500' in url
        assert 'mD=141.66' in url
        assert 'mHP=138' in url
        assert 'dec=2' in url
        assert 'mA=' not in url  # attack floor is 0 -> omitted

    def test_form_and_league_mapping(self):
        target = {'attack': 0, 'defense': 100, 'stamina': 0}
        assert _pvpivs_mon('Stunfisk (Galarian)') == 'Stunfisk_Galarian'
        assert _pvpivs_mon('Mr. Mime') == 'Mr_Mime'
        link = build_pvpivs_url('Stunfisk (Galarian)', 'ultra', target)
        assert 'mon=Stunfisk_Galarian' in link['url']
        assert 'cp=2500' in link['url']
        link = build_pvpivs_url('Tinkaton', 'master', target)
        assert 'cp=ML' in link['url']
        assert build_pvpivs_url('Tinkaton', 'little', target) is None

    def test_shadow_floors_unscaled(self):
        # Shadow floors are stored shadow-scaled; the URL must carry
        # base-stat floors (their filter runs pre-shadow): atk / 1.2 and
        # def * 1.2, each minus a small recall-safe epsilon. Non-round
        # floors + DIRECTIONAL assertions: the emitted floor must sit
        # strictly BELOW the un-scaled value, so a flipped epsilon sign
        # (which hides borderline qualifying rows on pvpivs) cannot pass
        # (review 2026-07-17: the sign-flip mutant survived the old
        # tolerance-based assertions).
        target = {'attack': 121.3, 'defense': 100.3, 'stamina': 90}
        link = build_pvpivs_url('Altaria (Shadow)', 'great', target)
        assert link['shadow'] is True
        assert 'mon=Altaria' in link['url']
        emitted_atk = float(re.search(r'mA=([\d.]+)', link['url']).group(1))
        emitted_def = float(re.search(r'mD=([\d.]+)', link['url']).group(1))
        unscaled_atk = 121.3 / 1.2       # 101.083...
        unscaled_def = 100.3 * 1.2       # 120.36
        assert emitted_atk < unscaled_atk
        assert emitted_def < unscaled_def
        assert unscaled_atk - emitted_atk <= 0.011  # epsilon + rounding
        assert unscaled_def - emitted_def <= 0.011
        assert 'mHP=90' in link['url']  # stamina unaffected by shadow

    def test_ivs_list_target_gets_no_link(self):
        # An explicit-IV-list target can't be expressed as stat floors;
        # linking the unfiltered rank table would misrepresent it.
        target = {'ivs': [[0, 15, 14], [1, 15, 11]]}
        assert build_pvpivs_url('Azumarill', 'great', target) is None

    def test_onlytop_maps_to_rank_param(self):
        target = {'attack': 0, 'defense': 0, 'stamina': 0, 'onlytop': 25}
        link = build_pvpivs_url('Tinkaton', 'great', target)
        assert 'r=25' in link['url']
