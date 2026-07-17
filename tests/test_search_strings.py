"""Tests for gobattlekit.data.search_strings — in-game search strings and
pvpivs.com deep links generated from threshold targets."""
import re

from gobattlekit.data.iv_checker import get_pokemon_index, ivs_to_stats
from gobattlekit.data.search_strings import (
    BAR_BUCKET,
    _run_term,
    _runs,
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


def test_runs_and_run_term():
    assert _runs({0, 1, 2}) == [(0, 2)]
    assert _runs({0, 3, 4}) == [(0, 0), (3, 4)]
    assert _runs({2}) == [(2, 2)]
    assert _run_term((0, 2), 'attack') == '0-2attack'
    assert _run_term((4, 4), 'hp') == '4hp'


def _pogo_eval(string, a, d, s):
    """Evaluate a search string against one mon's (atk, def, sta) IVs under
    Pokemon GO's REAL grammar: '&' (AND) binds tighter than ',' (OR), no
    parentheses -> the string is an OR of comma-groups, each an AND of
    &-terms. Non-bar terms (species '+name'/dex, 'shadow') are treated as
    matching (we test a single same-species mon). Returns (matched, groups)
    where groups is the list of top-level OR-group term-lists.
    """
    buckets = {'attack': BAR_BUCKET[a], 'defense': BAR_BUCKET[d],
               'hp': BAR_BUCKET[s]}
    groups = [g.split('&') for g in string.split(',')]

    def term_ok(term):
        m = re.fullmatch(r'(\d)(?:-(\d))?(attack|defense|hp)', term)
        if not m:
            return True  # +name / dex / shadow: same species assumed
        lo = int(m.group(1))
        hi = int(m.group(2) or lo)
        return lo <= buckets[m.group(3)] <= hi

    matched = any(all(term_ok(t) for t in g) for g in groups)
    return matched, groups


class TestBuildSearchString:
    def test_azumarill_recall_and_no_species_leak(self):
        # Azumarill: in MINI_GAMEMASTER and has bundled Great targets.
        targets = DEFAULT_THRESHOLDS['Azumarill']['Great']
        result = build_search_string('Azumarill', 'great', targets)
        assert result is not None
        assert result['string'].startswith('+azumarill&')

        _, groups = _pogo_eval(result['string'], 0, 0, 0)
        # SPECIES-LEAK GUARD: under the real comma-lowest grammar, every
        # top-level OR group MUST carry the species term, or the string
        # leaks unrelated species (the 2026-07-17 blocker). This fails on
        # the old '+name&A&B&C,D' rectangle form.
        for g in groups:
            assert '+azumarill' in g, result['string']

        # Recall on the EMITTED string, parsed with the real grammar.
        quals = qualifying_set('Azumarill', 'great', targets)
        assert quals, "Azumarill Great targets should have qualifying IVs"
        assert result['qualifying_count'] == len(quals)
        for a, d, s in quals:
            matched, _ = _pogo_eval(result['string'], a, d, s)
            assert matched, (a, d, s)

        # matched_count is the union of the DNF clauses' rectangles = the
        # full bucket rectangle. Recompute it independently from the axis
        # sizes so a _BUCKET_SIZES off-by-one cannot survive.
        sizes = {0: 1, 1: 5, 2: 5, 3: 4, 4: 1}
        aset, dset, sset = result['buckets']
        expected = (sum(sizes[b] for b in aset)
                    * sum(sizes[b] for b in dset)
                    * sum(sizes[b] for b in sset))
        assert result['matched_count'] == expected
        assert result['matched_count'] >= result['qualifying_count']

    def test_noncontiguous_axis_distributes_without_leak(self):
        # Craft a non-contiguous HP axis (buckets 0 and 4, no 1-3) via an
        # explicit-IV target — the exact shape that broke under the naive
        # rectangle ('...&0hp,4hp' would parse as '(...&0hp) OR 4hp', the
        # bare '4hp' matching every 15-HP mon in storage). Assert DNF
        # distribution: a comma appears AND every OR-group is scoped.
        targets = {'T': {'ivs': [[15, 15, 0], [15, 15, 15]]}}
        result = build_search_string('Azumarill', 'great', targets)
        assert result is not None
        assert result['buckets'][2] == {0, 4}, "HP axis must be split"
        assert ',' in result['string'], "should distribute a split axis"
        _, groups = _pogo_eval(result['string'], 0, 0, 0)
        for g in groups:
            assert '+azumarill' in g, result['string']
        # And the bare-'4hp' leak specifically: no OR-group is a lone stat
        # term.
        for g in groups:
            assert any(t.startswith('+azumarill') for t in g)

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
