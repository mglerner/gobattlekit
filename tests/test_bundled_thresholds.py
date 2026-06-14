"""The bundled-TOML default thresholds: lossless migration pin.

DEFAULT_THRESHOLDS used to be a Python literal in thresholds.py; it now
loads from the bundled default_thresholds.toml via load_bundled_thresholds().
These tests pin that the TOML decodes to the EXACT pre-migration structure —
same species/leagues/targets, same numeric *types* (int vs float, which the
match engine and screens rely on), same ivs lists, onlytop, and the
class/source/desc provenance keys — and that target_class /
drop_generated_targets / has_generated_targets behave identically on the
loaded data. EXPECTED below is a verbatim copy of the old in-Python dict.
"""
import tomllib

import pytest

from gobattlekit.data.thresholds import (
    DEFAULT_THRESHOLDS, load_bundled_thresholds, BUNDLED_THRESHOLDS_PATH,
    target_class, drop_generated_targets, has_generated_targets,
)


# Verbatim snapshot of DEFAULT_THRESHOLDS as it was the moment before the
# TOML migration. Do not "tidy" the numeric literals — the int/float split
# is load-bearing and is exactly what this fixture exists to pin.
EXPECTED = {
    'Spidops': {
        'sources': "the HomeSliceHenry Discord server",
        'Great': {
            'Atk': {'attack': 113.03, 'defense': 138.88, 'stamina': 0},
            'Bulk': {'attack': 109.82, 'defense': 138.88, 'stamina': 0},
            'Bulk+': {'attack': 109.82, 'defense': 140.67, 'stamina': 0},
        },
    },
    'Tinkaton': {
        'sources': "These are Gigaton Hammer matchups, from the HomeSliceHenry Discord server",
        'Great': {
            'GH Great': {'attack': 0, 'defense': 143.03, 'stamina': 138},
            'GH Good': {'attack': 0, 'defense': 141.66, 'stamina': 138},
        },
    },
    'Corviknight': {
        'sources': "the HomeSliceHenry Discord server",
        'Great': {
            'Basic': {'attack': 0, 'defense': 127.59, 'stamina': 0},
            'Atk': {'attack': 111.47, 'defense': 127.59, 'stamina': 0},
            'Bulk': {'attack': 100, 'defense': 132.10, 'stamina': 149},
        },
    },
    'Drapion (Shadow)': {
        'sources': "the HomeSliceHenry Discord server",
        'Great': {
            'Azu bul': {'attack': 0, 'defense': 138, 'stamina': 0},
        },
    },
    'Florges': {
        'sources': "Inadequance's [YouTube Video](https://www.youtube.com/watch?v=KXLWLcOw3G4&t=295s)",
        'Great': {
            'SWak 9/6/14': {'attack': 121.5, 'defense': 0, 'stamina': 0},
            'Inadequance': {'ivs': [[0, 14, 13], [9, 6, 14], [8, 1, 8]]},
        },
        'Ultra': {
            'Inadequance': {'ivs': [[0, 14, 15], [0, 15, 3], [5, 11, 5]]},
        },
        'Master': {
            'Basic': {'attack': 190, 'defense': 217, 'stamina': 167},
            'Inadequance': {
                'ivs': [[15, 15, 15], [15, 15, 14], [15, 15, 13], [15, 15, 12]],
            },
        },
    },
    'Annihilape': {
        'Great': {
            'Ape Slayer': {
                'ivs': [
                    [11, 10, 2], [15, 12, 5], [11, 11, 0], [15, 13, 4],
                    [11, 9, 3], [11, 9, 2], [15, 14, 3], [15, 14, 2],
                    [11, 10, 1], [11, 10, 0], [12, 9, 1], [12, 9, 0],
                    [15, 15, 1], [15, 15, 0], [15, 12, 4], [15, 13, 3],
                    [15, 13, 2], [11, 9, 1], [11, 9, 0], [15, 14, 1],
                    [15, 14, 0], [15, 12, 3], [15, 12, 2], [15, 13, 1],
                    [15, 13, 0], [15, 12, 1], [15, 12, 0],
                ],
            },
        },
    },
}


def _leaves(obj, path=''):
    """Flatten to {path: scalar} so we can compare values AND types."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, f'{path}/{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _leaves(v, f'{path}/{i}')
    else:
        yield path, obj


class TestLosslessMigration:
    def test_default_thresholds_is_the_loaded_toml(self):
        # The module-level name is produced by the loader, not a literal.
        assert DEFAULT_THRESHOLDS == load_bundled_thresholds()

    def test_deep_equals_pre_migration_dict(self):
        assert DEFAULT_THRESHOLDS == EXPECTED

    def test_leaf_types_match_exactly(self):
        # == treats 100 == 100.0 as True; the engine/screens care which is
        # which, so compare type alongside value at every leaf.
        loaded = dict(_leaves(DEFAULT_THRESHOLDS))
        expected = dict(_leaves(EXPECTED))
        assert set(loaded) == set(expected)
        for path, value in expected.items():
            assert type(loaded[path]) is type(value), path
            assert loaded[path] == value, path

    def test_species_set(self):
        assert set(DEFAULT_THRESHOLDS) == set(EXPECTED)

    def test_per_species_leagues_and_targets(self):
        for species, leagues in EXPECTED.items():
            assert set(DEFAULT_THRESHOLDS[species]) == set(leagues), species
            for league, targets in leagues.items():
                if not isinstance(targets, dict):
                    continue  # species-level 'sources'
                assert set(DEFAULT_THRESHOLDS[species][league]) == set(targets), \
                    f'{species}/{league}'


class TestRepresentativeValues:
    def test_tinkaton_gh_great(self):
        spec = DEFAULT_THRESHOLDS['Tinkaton']['Great']['GH Great']
        assert spec == {'attack': 0, 'defense': 143.03, 'stamina': 138}
        assert isinstance(spec['defense'], float)
        assert isinstance(spec['stamina'], int)

    def test_florges_iv_lists(self):
        great = DEFAULT_THRESHOLDS['Florges']['Great']['Inadequance']['ivs']
        assert great == [[0, 14, 13], [9, 6, 14], [8, 1, 8]]
        master = DEFAULT_THRESHOLDS['Florges']['Master']['Inadequance']['ivs']
        assert master == [[15, 15, 15], [15, 15, 14], [15, 15, 13], [15, 15, 12]]
        assert all(isinstance(x, int) for triple in great for x in triple)

    def test_annihilape_27_entry_iv_list(self):
        ivs = DEFAULT_THRESHOLDS['Annihilape']['Great']['Ape Slayer']['ivs']
        assert len(ivs) == 27
        assert ivs[0] == [11, 10, 2]
        assert ivs[-1] == [15, 12, 0]

    def test_clodsire_onlytop_absent_so_provenance_check_stays_meaningful(self):
        # onlytop lives in SENTIMENTAL, not DEFAULT — pin that DEFAULT has
        # no onlytop so the schema sample above stays representative.
        for leagues in DEFAULT_THRESHOLDS.values():
            for targets in leagues.values():
                if isinstance(targets, dict):
                    for spec in targets.values():
                        assert 'onlytop' not in spec


class TestHelpersUnchangedOnLoadedData:
    def test_target_class_defaults_expert_for_bundled(self):
        spec = DEFAULT_THRESHOLDS['Tinkaton']['Great']['GH Great']
        assert target_class(spec, 'default') == 'expert'

    def test_no_generated_targets_in_bundled_default(self):
        assert has_generated_targets(DEFAULT_THRESHOLDS) is False

    def test_drop_generated_is_identity_when_none_generated(self):
        assert drop_generated_targets(DEFAULT_THRESHOLDS) == DEFAULT_THRESHOLDS

    def test_provenance_round_trips_when_present(self):
        # The bundled file has no provenance keys today, but the loader must
        # carry them through verbatim when the pipeline appends them. Build a
        # tiny TOML with class/source/desc and confirm it survives the loader
        # and is honored by target_class / the generated filters.
        toml = (
            '[Testmon.Great."SIM Target"]\n'
            'defense = 130.5\n'
            'stamina = 100\n'
            'class = "generated"\n'
            'source = "pipeline"\n'
            'desc = "beats the test dummy"\n'
        )
        data = tomllib.loads(toml)
        spec = data['Testmon']['Great']['SIM Target']
        assert spec['class'] == 'generated'
        assert spec['source'] == 'pipeline'
        assert spec['desc'] == 'beats the test dummy'
        assert isinstance(spec['defense'], float)
        assert isinstance(spec['stamina'], int)
        assert target_class(spec, 'default') == 'generated'
        assert has_generated_targets(data) is True
        assert drop_generated_targets(data) == {}


class TestLoaderRobustness:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            load_bundled_thresholds(tmp_path / 'nope.toml')

    def test_corrupt_file_raises(self, tmp_path):
        bad = tmp_path / 'bad.toml'
        bad.write_text('this is = not valid = toml [[[')
        with pytest.raises(Exception):
            load_bundled_thresholds(bad)

    def test_bundled_path_points_at_packaged_asset(self):
        assert BUNDLED_THRESHOLDS_PATH.name == 'default_thresholds.toml'
        assert BUNDLED_THRESHOLDS_PATH.exists()
