"""Provenance-aware thresholds: the optional class/source/desc metadata.

Covers schema validation, share-text round-trips (Class:/Source: lines),
class resolution via target_class, the SIM filter that backs the screens'
_get_thresholds chokepoint (display AND matching exclusion), and the
regression pin that the match engine ignores the new keys.

The screen-side pref gate itself isn't covered here — toga is not a test
dependency; the suite tests the data layer the screens delegate to.
"""
import pytest

from gobattlekit.data.thresholds import (
    target_class, drop_generated_targets, has_generated_targets,
)
from gobattlekit.data.user_thresholds import (
    add_threshold, replace_threshold, load_user_thresholds,
    parse_threshold_json, parse_threshold_text, format_threshold_text,
)


class TestTargetClass:
    def test_explicit_valid_class_wins(self):
        assert target_class({'class': 'generated'}, 'default') == 'generated'
        assert target_class({'class': 'expert'}, 'user') == 'expert'

    def test_default_store_defaults_to_expert(self):
        assert target_class({'attack': 0}, 'default') == 'expert'

    def test_user_store_defaults_to_user(self):
        assert target_class({'attack': 0}, 'user') == 'user'

    def test_invalid_class_falls_back_to_store_default(self):
        assert target_class({'class': 'vibes'}, 'default') == 'expert'
        assert target_class({'class': 'vibes'}, 'user') == 'user'
        # Defensive: malformed (non-dict) specs resolve, not crash.
        assert target_class('not a dict', 'user') == 'user'


class TestMetadataValidation:
    """The new keys round-trip through the scanner-JSON validator."""

    FRAGMENT = (
        '{"Azumarill": {"Great": {"Sim Bulk": {'
        '"attack": 0, "defense": 143.0, "stamina": 138, '
        '"class": "generated", "source": "pogo-simulator nightly", '
        '"desc": "beats the mirror"}}}}'
    )

    def test_scanner_json_keeps_metadata(self):
        [(species, league, name, spec)] = parse_threshold_json(self.FRAGMENT)
        assert spec['class'] == 'generated'
        assert spec['source'] == 'pogo-simulator nightly'
        assert spec['desc'] == 'beats the mirror'

    @pytest.mark.parametrize("bad,fragment", [
        ("unknown class",
         '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, '
         '"class": "vibes"}}}}'),
        ("non-string source",
         '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, '
         '"source": 3}}}}'),
        ("non-string desc",
         '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, '
         '"desc": ["a"]}}}}'),
    ])
    def test_rejects_malformed_metadata(self, bad, fragment):
        with pytest.raises(ValueError):
            parse_threshold_json(fragment)

    def test_empty_strings_are_dropped_not_stored(self):
        [(_, _, _, spec)] = parse_threshold_json(
            '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, '
            '"source": "  ", "desc": ""}}}}'
        )
        assert 'source' not in spec and 'desc' not in spec


class TestShareTextMetadata:
    """'GoBattleKit Threshold v1' carries optional Class:/Source: lines."""

    def test_round_trip_class_and_source(self):
        t = {'attack': 0, 'defense': 143.0, 'stamina': 138,
             'class': 'generated', 'source': 'pogo-simulator nightly'}
        text = format_threshold_text('Azumarill', 'Great', 'Sim Bulk', t)
        assert 'Class: generated' in text
        assert 'Source: pogo-simulator nightly' in text
        species, league, name, spec = parse_threshold_text(text)
        assert (species, league, name) == ('Azumarill', 'Great', 'Sim Bulk')
        # Q2: the declared class survives import verbatim — no laundering.
        assert spec['class'] == 'generated'
        assert spec['source'] == 'pogo-simulator nightly'

    def test_no_class_line_means_no_class(self):
        """A paste without a Class line stores no class (implicit user)."""
        t = {'attack': 122.5, 'defense': 0, 'stamina': 0}
        text = format_threshold_text('Azumarill', 'Great', 'X', t)
        assert 'Class:' not in text and 'Source:' not in text
        _, _, _, spec = parse_threshold_text(text)
        assert 'class' not in spec and 'source' not in spec

    def test_reshare_preserves_class(self):
        """Import → store → share again keeps the declared class."""
        t = {'attack': 0, 'defense': 0, 'stamina': 0, 'class': 'generated'}
        text = format_threshold_text('Azumarill', 'Great', 'X', t)
        _, _, _, spec = parse_threshold_text(text)
        text2 = format_threshold_text('Azumarill', 'Great', 'X', spec)
        assert 'Class: generated' in text2

    def test_source_value_may_contain_colons(self):
        t = {'attack': 0, 'defense': 0, 'stamina': 0,
             'source': 'sim: https://example.com/dive'}
        text = format_threshold_text('Azumarill', 'Great', 'X', t)
        _, _, _, spec = parse_threshold_text(text)
        assert spec['source'] == 'sim: https://example.com/dive'

    def test_rejects_invalid_class_line(self):
        with pytest.raises(ValueError):
            parse_threshold_text(
                "GoBattleKit Threshold v1\nSpecies: Azumarill\nLeague: Great\n"
                "Name: X\nAttack: 0\nDefense: 0\nStamina: 0\nOnlyTop: 0\n"
                "Class: vibes"
            )


class TestMetadataPersistence:
    """Class/source/desc survive add and replace (edit) unchanged (Q2)."""

    def test_add_threshold_stores_metadata(self):
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0,
                      cls='generated', source='sim', desc='mirror')
        entry = load_user_thresholds()['Azumarill']['Great']['X']
        assert entry['class'] == 'generated'
        assert entry['source'] == 'sim'
        assert entry['desc'] == 'mirror'

    def test_add_threshold_omits_empty_metadata(self):
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0,
                      cls='', source='', desc='')
        entry = load_user_thresholds()['Azumarill']['Great']['X']
        assert entry == {'attack': 0, 'defense': 0, 'stamina': 0}

    def test_replace_carries_metadata_from_form(self):
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0,
                      cls='generated', source='sim', desc='mirror')
        # The edit form prefills the metadata and passes it back through.
        ok = replace_threshold('Azumarill', 'great', 'X',
                               'Azumarill', 'great', 'X', 0, 100.0, 0,
                               cls='generated', source='sim', desc='mirror')
        assert ok
        entry = load_user_thresholds()['Azumarill']['Great']['X']
        assert entry['defense'] == 100.0
        assert entry['class'] == 'generated'
        assert entry['source'] == 'sim'
        assert entry['desc'] == 'mirror'

    def test_replace_can_clear_metadata(self):
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0, cls='generated')
        ok = replace_threshold('Azumarill', 'great', 'X',
                               'Azumarill', 'great', 'X', 0, 0, 0,
                               cls='', source='', desc='')
        assert ok
        entry = load_user_thresholds()['Azumarill']['Great']['X']
        assert 'class' not in entry


class TestSimFilter:
    """drop_generated_targets backs the screens' _get_thresholds
    chokepoint: what disappears from display disappears from matching."""

    THRESHOLDS = {
        'Azumarill': {
            'sources': 'an expert',
            'Great': {
                'Expert': {'attack': 0, 'defense': 0, 'stamina': 0},
                'Sim': {'attack': 0, 'defense': 0, 'stamina': 0,
                        'class': 'generated'},
            },
        },
        'Registeel': {
            'Great': {
                'Sim only': {'attack': 0, 'defense': 0, 'stamina': 0,
                             'class': 'generated'},
            },
        },
    }

    def test_drops_generated_and_emptied_species(self):
        filtered = drop_generated_targets(self.THRESHOLDS, 'default')
        assert list(filtered['Azumarill']['Great']) == ['Expert']
        # All-generated species disappear entirely.
        assert 'Registeel' not in filtered
        # Species-level metadata rides along with surviving leagues.
        assert filtered['Azumarill']['sources'] == 'an expert'
        # The input store is untouched (it's a copy, not in-place).
        assert 'Sim' in self.THRESHOLDS['Azumarill']['Great']

    def test_user_store_unclassed_targets_survive(self):
        """User specs with no class resolve to 'user' — never hidden."""
        store = {'Azumarill': {'Great': {
            'Mine': {'attack': 0, 'defense': 0, 'stamina': 0},
            'Pasted sim': {'attack': 0, 'defense': 0, 'stamina': 0,
                           'class': 'generated'},
        }}}
        filtered = drop_generated_targets(store, 'user')
        assert list(filtered['Azumarill']['Great']) == ['Mine']

    def test_has_generated_targets(self):
        assert has_generated_targets(self.THRESHOLDS, 'default')
        assert not has_generated_targets(
            {'A': {'Great': {'X': {'attack': 0, 'defense': 0, 'stamina': 0}}}},
            'default',
        )

    def test_hidden_targets_excluded_from_matching(self, tmp_path):
        """Matching reads the same filtered dict — counts agree with
        display (Q3)."""
        from gobattlekit.data.iv_checker import check_thresholds
        header = ('Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,'
                  'Shadow/Purified,Lucky\n')
        csv = tmp_path / 'mons.csv'
        csv.write_text(header
                       + 'Azumarill,,1400,8,15,15,20,0,0\n'
                       + 'Registeel,,1500,0,15,15,20,0,0\n',
                       encoding='utf-8-sig')

        shown = check_thresholds(str(csv), self.THRESHOLDS,
                                 league='great', max_level=40)
        assert sorted(shown['Azumarill'][0]['matched']) == ['Expert', 'Sim']
        assert len(shown['Registeel']) == 1

        hidden = check_thresholds(
            str(csv), drop_generated_targets(self.THRESHOLDS, 'default'),
            league='great', max_level=40,
        )
        assert hidden['Azumarill'][0]['matched'] == ['Expert']
        assert 'Registeel' not in hidden


class TestEngineIgnoresMetadata:
    """Regression pin: check_thresholds and qualifying_ivs already ignore
    unknown keys via .get(...) — the new metadata must never affect
    matching."""

    def test_check_thresholds_ignores_new_keys(self, tmp_path):
        from gobattlekit.data.iv_checker import check_thresholds
        thresholds = {'Azumarill': {'Great': {
            'Tagged': {'attack': 0, 'defense': 0, 'stamina': 0,
                       'class': 'generated', 'source': 'sim', 'desc': 'd'},
        }}}
        header = ('Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,'
                  'Shadow/Purified,Lucky\n')
        csv = tmp_path / 'mons.csv'
        csv.write_text(header + 'Azumarill,,1400,0,15,15,20,0,0\n',
                       encoding='utf-8-sig')
        results = check_thresholds(str(csv), thresholds, league='great',
                                   max_level=40)
        assert results['Azumarill'][0]['matched'] == ['Tagged']

    def test_qualifying_ivs_ignores_new_keys(self):
        from gobattlekit.data.iv_checker import qualifying_ivs
        base = {'attack': 0, 'defense': 0, 'stamina': 0}
        tagged = dict(base, **{'class': 'generated', 'source': 'sim',
                               'desc': 'd'})
        plain = qualifying_ivs('Azumarill', 112, 152, 225, base,
                               max_level=40, max_cp=1500)
        with_meta = qualifying_ivs('Azumarill', 112, 152, 225, tagged,
                                   max_level=40, max_cp=1500)
        assert plain == with_meta
        assert with_meta  # the target is satisfiable; the scan found combos
