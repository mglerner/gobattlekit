"""The bundled-TOML default thresholds: lossless round-trip + provenance pin.

DEFAULT_THRESHOLDS loads from the bundled default_thresholds.toml via
load_bundled_thresholds(). That file is now produced by the threshold
re-dive pipeline (tools/threshold_export/bundle_into_app.py) merging fresh
per-species exports into the prior file — 6 hand-curated species grew to 46
(most carrying pipeline-"generated" targets that light up the SIM toggle),
while Florges' Ultra/Master and the no-fresh-export Annihilape were kept
verbatim.

These tests keep the original intent across that growth:
  * lossless round-trip — the file decodes to a dict that re-emits to the
    exact same bytes (so nothing is silently dropped or reordered) and the
    module-level name is the loader's output, not a stale literal;
  * type-strict leaves — every numeric leaf keeps its int-vs-float identity
    (the match engine and screens rely on it) and ivs stay int triples;
  * provenance behavior — class/source/desc survive the loader and
    target_class / drop_generated_targets / has_generated_targets honor
    them, now that real 'generated' targets are present.
Representative values from updated / preserved species are pinned directly.
"""
import sys
import tomllib
from pathlib import Path

import pytest

from gobattlekit.data.thresholds import (
    DEFAULT_THRESHOLDS, load_bundled_thresholds, BUNDLED_THRESHOLDS_PATH,
    target_class, drop_generated_targets, has_generated_targets,
)

# Make the bundler's emitter importable for the byte-identical round-trip pin.
_TOOLS = Path(__file__).resolve().parents[1] / 'tools' / 'threshold_export'
sys.path.insert(0, str(_TOOLS))
from bundle_into_app import emit_app_toml, APP_HEADER  # noqa: E402


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


class TestLosslessRoundTrip:
    def test_default_thresholds_is_the_loaded_toml(self):
        # The module-level name is produced by the loader, not a literal.
        assert DEFAULT_THRESHOLDS == load_bundled_thresholds()

    def test_file_re_emits_to_identical_bytes(self):
        # The bundler's emitter is a fixed point on the shipped file: decode
        # then re-emit must reproduce it byte for byte. This is the strongest
        # "nothing was lost / nothing drifted" pin we can have now that the
        # content is pipeline-generated rather than a frozen literal.
        orig = BUNDLED_THRESHOLDS_PATH.read_text()
        data = tomllib.loads(orig)
        assert emit_app_toml(data, header=APP_HEADER) == orig

    def test_decode_re_emit_decode_is_stable(self):
        re_emitted = emit_app_toml(DEFAULT_THRESHOLDS, header=APP_HEADER)
        assert tomllib.loads(re_emitted) == DEFAULT_THRESHOLDS

    def test_species_count_grew_to_46(self):
        # 6 hand-curated species + 41 added from the re-dive, minus the
        # targetless Aegislash (Shield) stub the bundler prunes = 46.
        assert len(DEFAULT_THRESHOLDS) == 46
        assert 'Aegislash (Shield)' not in DEFAULT_THRESHOLDS  # pruned (no targets)
        assert 'Aegislash (Blade)' in DEFAULT_THRESHOLDS

    def test_no_onlytop_in_bundled_default(self):
        # onlytop lives in SENTIMENTAL, not DEFAULT; the export pipeline never
        # emits it. Pin its absence so the schema stays scan-safe.
        for leagues in DEFAULT_THRESHOLDS.values():
            for targets in leagues.values():
                if isinstance(targets, dict):
                    for spec in targets.values():
                        assert 'onlytop' not in spec


class TestLeafTypesAreStrict:
    def test_every_stat_leaf_is_int_or_float_not_bool(self):
        for path, value in _leaves(DEFAULT_THRESHOLDS):
            seg = path.rsplit('/', 1)[-1]
            if seg in ('attack', 'defense', 'stamina'):
                assert type(value) in (int, float), path
                assert not isinstance(value, bool), path

    def test_ivs_are_int_triples(self):
        for species, leagues in DEFAULT_THRESHOLDS.items():
            for league, targets in leagues.items():
                if not isinstance(targets, dict):
                    continue
                for name, spec in targets.items():
                    if 'ivs' not in spec:
                        continue
                    for triple in spec['ivs']:
                        assert len(triple) == 3, f'{species}/{league}/{name}'
                        for x in triple:
                            assert type(x) is int, f'{species}/{league}/{name}'

    def test_re_emit_preserves_leaf_types(self):
        # int vs float is load-bearing; confirm it survives a round-trip.
        reloaded = tomllib.loads(emit_app_toml(DEFAULT_THRESHOLDS, header=APP_HEADER))
        a = dict(_leaves(DEFAULT_THRESHOLDS))
        b = dict(_leaves(reloaded))
        assert set(a) == set(b)
        for path, value in a.items():
            assert type(b[path]) is type(value), path
            assert b[path] == value, path


class TestPreservedSpecies:
    def test_florges_keeps_all_three_leagues(self):
        florges = DEFAULT_THRESHOLDS['Florges']
        assert set(k for k in florges if isinstance(florges[k], dict)) == {
            'Great', 'Ultra', 'Master'}

    def test_florges_ultra_and_master_are_verbatim(self):
        florges = DEFAULT_THRESHOLDS['Florges']
        assert florges['Ultra'] == {
            'Inadequance': {'ivs': [[0, 14, 15], [0, 15, 3], [5, 11, 5]]},
        }
        assert florges['Master'] == {
            'Basic': {'attack': 190, 'defense': 217, 'stamina': 167},
            'Inadequance': {
                'ivs': [[15, 15, 15], [15, 15, 14], [15, 15, 13], [15, 15, 12]],
            },
        }
        basic = florges['Master']['Basic']
        assert all(type(v) is int for v in basic.values())

    def test_florges_great_was_replaced_by_export(self):
        # The export's Great targets (not the old 'SWak 9/6/14'/'Inadequance')
        # now back Great, and at least one is pipeline-generated.
        great = DEFAULT_THRESHOLDS['Florges']['Great']
        assert 'swak' in great
        assert any(target_class(s, 'default') == 'generated' for s in great.values())

    def test_annihilape_preserved_verbatim(self):
        # Annihilape was NOT in the re-dive batch, so its 27-entry ivs target
        # must survive untouched, Great-only, with no provenance keys.
        ann = DEFAULT_THRESHOLDS['Annihilape']
        assert set(k for k in ann if isinstance(ann[k], dict)) == {'Great'}
        assert set(ann['Great']) == {'Ape Slayer'}
        ivs = ann['Great']['Ape Slayer']['ivs']
        assert len(ivs) == 27
        assert ivs[0] == [11, 10, 2]
        assert ivs[-1] == [15, 12, 0]
        assert all(type(x) is int for triple in ivs for x in triple)
        assert 'class' not in ann['Great']['Ape Slayer']


class TestRepresentativeValues:
    def test_tinkaton_gh_great_expert_and_generated_coexist(self):
        great = DEFAULT_THRESHOLDS['Tinkaton']['Great']
        gh = great['GH Great']
        assert gh['attack'] == 0 and type(gh['attack']) is int
        assert gh['defense'] == 143.03 and type(gh['defense']) is float
        assert gh['stamina'] == 138 and type(gh['stamina']) is int
        assert target_class(gh, 'default') == 'expert'
        # at least one generated target on the same species
        assert any(target_class(s, 'default') == 'generated'
                   for s in great.values())

    def test_shadow_species_keyed_with_suffix(self):
        # Shadow exports carry the base name in-file; the bundler keys them
        # with the ' (Shadow)' suffix the app expects.
        assert 'Drapion (Shadow)' in DEFAULT_THRESHOLDS
        assert 'Altaria (Shadow)' in DEFAULT_THRESHOLDS
        assert 'Altaria' in DEFAULT_THRESHOLDS  # base form distinct


class TestProvenanceHelpers:
    def test_has_generated_targets_now_true(self):
        assert has_generated_targets(DEFAULT_THRESHOLDS) is True

    def test_many_species_have_generated_targets(self):
        n = 0
        for leagues in DEFAULT_THRESHOLDS.values():
            for targets in leagues.values():
                if not isinstance(targets, dict):
                    continue
                if any(target_class(s, 'default') == 'generated'
                       for s in targets.values()):
                    n += 1
                    break
        assert n >= 20  # in practice 40

    def test_drop_generated_removes_only_generated(self):
        filtered = drop_generated_targets(DEFAULT_THRESHOLDS)
        # No generated targets survive.
        assert has_generated_targets(filtered) is False
        # Expert targets (e.g. Tinkaton GH Great) do survive.
        assert 'GH Great' in filtered['Tinkaton']['Great']
        # Florges keeps its preserved Ultra/Master (no generated targets there).
        assert filtered['Florges']['Ultra'] == DEFAULT_THRESHOLDS['Florges']['Ultra']
        assert filtered['Florges']['Master'] == DEFAULT_THRESHOLDS['Florges']['Master']

    def test_provenance_round_trips_when_present(self):
        # A class/source/desc target survives the loader and is honored by
        # target_class / the generated filters.
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
