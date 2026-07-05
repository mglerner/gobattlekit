"""Tests for user_thresholds.py — load/save robustness and round-trips.

USER_THRESHOLDS_FILE is redirected to tmp_path by the autouse
isolate_app_data fixture in conftest.py.
"""
import json

import pytest

from gobattlekit.data import user_thresholds
from gobattlekit.data.user_thresholds import (
    load_user_thresholds, save_user_thresholds, add_threshold,
    delete_threshold, clear_all_thresholds, replace_threshold,
    prune_propagated_pre_evos, parse_threshold_json, parse_threshold_text,
    format_threshold_text, import_threshold_entries,
)


class TestLoadRobustness:
    def test_missing_file_returns_empty(self):
        assert load_user_thresholds() == {}

    def test_round_trip(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 143.0, 138, onlytop=10)
        data = load_user_thresholds()
        assert data == {
            'Azumarill': {'Great': {'Bulky': {
                'attack': 0, 'defense': 143.0, 'stamina': 138, 'onlytop': 10,
            }}},
        }

    def test_corrupt_file_is_renamed_aside_not_clobbered(self):
        """A corrupt thresholds file must be moved to .corrupt so the next
        save can't overwrite possibly-recoverable user data (DL8; mirrors
        the preferences.py pattern)."""
        f = user_thresholds.USER_THRESHOLDS_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('{"Azumarill": {"Great"')  # truncated write

        assert load_user_thresholds() == {}
        corrupt = f.with_suffix('.json.corrupt')
        assert corrupt.exists(), "corrupt file should be renamed aside"
        assert not f.exists()
        # The original bytes survive for manual recovery.
        assert corrupt.read_text() == '{"Azumarill": {"Great"'

        # A subsequent add starts fresh without destroying the .corrupt copy.
        add_threshold('Registeel', 'great', 'Tanky', 0, 0, 0)
        assert 'Registeel' in load_user_thresholds()
        assert corrupt.read_text() == '{"Azumarill": {"Great"'

    def test_valid_json_but_not_a_dict_is_reset_not_returned(self):
        """A file holding valid JSON that isn't an object (a list, from a
        sync conflict or bad edit) must be treated like corruption — every
        mutation function indexes it as species->leagues and would crash
        otherwise. Mirrors the preferences.py non-dict guard."""
        f = user_thresholds.USER_THRESHOLDS_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('["Azumarill"]')

        assert load_user_thresholds() == {}
        assert f.with_suffix('.json.corrupt').exists()
        # The mutation path that used to crash now works on a fresh dict.
        assert add_threshold('Registeel', 'great', 'Tanky', 0, 0, 0) is True
        assert 'Registeel' in load_user_thresholds()


class TestSaveAndDelete:
    def test_save_is_atomic_no_tmp_left_behind(self):
        save_user_thresholds({'A': {}})
        f = user_thresholds.USER_THRESHOLDS_FILE
        assert not f.with_suffix('.json.tmp').exists()

    def test_delete_cleans_empty_parents(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 0, 0)
        delete_threshold('Azumarill', 'great', 'Bulky')
        assert load_user_thresholds() == {}

    def test_delete_missing_is_noop(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 0, 0)
        delete_threshold('Registeel', 'great', 'Nope')
        assert 'Azumarill' in load_user_thresholds()

    def test_clear_all(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 0, 0)
        assert clear_all_thresholds() == {}
        assert load_user_thresholds() == {}


class TestReplaceThreshold:
    """Editing must be one transaction: the old delete-then-add sequence
    could lose the original when the second save failed (SI10)."""

    def test_replace_moves_entry(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 0, 0)
        ok = replace_threshold(
            'Azumarill', 'great', 'Bulky',
            'Azumarill', 'ultra', 'Bulkier', 0, 150.0, 140, onlytop=5,
        )
        assert ok
        data = load_user_thresholds()
        assert 'Great' not in data.get('Azumarill', {})
        assert data['Azumarill']['Ultra']['Bulkier'] == {
            'attack': 0, 'defense': 150.0, 'stamina': 140, 'onlytop': 5,
        }

    def test_failed_save_preserves_original_on_disk(self):
        add_threshold('Azumarill', 'great', 'Bulky', 0, 143.0, 138)

        def boom(*args, **kwargs):
            raise OSError("disk full")
        # Scoped context, NOT the shared monkeypatch fixture + undo():
        # undo() reverts the autouse isolation too and leaks onto the
        # real app cache.
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(user_thresholds.os, 'replace', boom)
            ok = replace_threshold(
                'Azumarill', 'great', 'Bulky',
                'Registeel', 'great', 'Tanky', 0, 0, 0,
            )
        assert not ok
        # The original entry is untouched on disk — nothing was half-applied.
        data = load_user_thresholds()
        assert data['Azumarill']['Great']['Bulky'] == {
            'attack': 0, 'defense': 143.0, 'stamina': 138,
        }
        assert 'Registeel' not in data

    def test_save_reports_failure(self):
        def boom(*args, **kwargs):
            raise OSError("disk full")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(user_thresholds.os, 'replace', boom)
            assert save_user_thresholds({'A': {}}) is False
        assert save_user_thresholds({'A': {}}) is True


class TestScannerJsonContract:
    """The live cross-project contract: pogo-simulator's dive pages emit
    'Copy for IV scanner' JSON fragments (its commit b97113f) in exactly
    the schema parse_threshold_json accepts (TS2, IV1)."""

    # Verbatim shapes from the b97113f emitter: composite cards export
    # stat floors; matchup cards export explicit member IV lists.
    COMPOSITE = ('{"Azumarill": {"Great": {"High Bulk": '
                 '{"attack": 0, "defense": 143.03, "stamina": 138}}}}')
    IVS_CARD = ('{"Azumarill": {"Great": {"Beats the mirror": '
                '{"attack": 0, "defense": 0, "stamina": 0, '
                '"ivs": [[8, 15, 15], [9, 15, 15]]}}}}')

    def test_composite_card_parses(self):
        entries = parse_threshold_json(self.COMPOSITE)
        assert entries == [('Azumarill', 'Great', 'High Bulk',
                            {'attack': 0, 'defense': 143.03, 'stamina': 138})]

    def test_ivs_card_parses(self):
        [(species, league, name, spec)] = parse_threshold_json(self.IVS_CARD)
        assert spec['ivs'] == [[8, 15, 15], [9, 15, 15]]

    def test_import_round_trips_through_check_thresholds(self, tmp_path):
        """End to end: fragment → import → stored → check_thresholds
        matches by explicit IVs."""
        from gobattlekit.data.iv_checker import check_thresholds
        import_threshold_entries(parse_threshold_json(self.IVS_CARD))

        header = 'Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,Shadow/Purified,Lucky\n'
        csv = tmp_path / 'mons.csv'
        csv.write_text(header
                       + 'Azumarill,,1400,8,15,15,20,0,0\n'   # in the list
                       + 'Azumarill,,1400,0,15,15,20,0,0\n',  # not in the list
                       encoding='utf-8-sig')
        results = check_thresholds(str(csv), load_user_thresholds(),
                                   league='great', max_level=40)
        assert len(results['Azumarill']) == 1
        assert results['Azumarill'][0]['mon']['atk_iv'] == 8

    def test_import_merges_without_clobbering(self):
        add_threshold('Registeel', 'ultra', 'Mine', 0, 200.0, 180)
        import_threshold_entries(parse_threshold_json(self.COMPOSITE))
        data = load_user_thresholds()
        assert data['Registeel']['Ultra']['Mine']['defense'] == 200.0
        assert data['Azumarill']['Great']['High Bulk']['stamina'] == 138

    @pytest.mark.parametrize("bad,fragment", [
        ("not json", "GoBattleKit Threshold v1"),
        ("not an object", '["Azumarill"]'),
        ("unknown league", '{"Azumarill": {"Holiday": {"X": {"attack": 0, "defense": 0, "stamina": 0}}}}'),
        ("unknown key", '{"Azumarill": {"Great": {"X": {"atack": 1, "defense": 0, "stamina": 0}}}}'),
        ("string floor", '{"Azumarill": {"Great": {"X": {"attack": "122", "defense": 0, "stamina": 0}}}}'),
        ("negative floor", '{"Azumarill": {"Great": {"X": {"attack": -1, "defense": 0, "stamina": 0}}}}'),
        ("iv out of range", '{"Azumarill": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, "ivs": [[16, 0, 0]]}}}}'),
        ("iv pair not triple", '{"Azumarill": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, "ivs": [[1, 2]]}}}}'),
        ("empty ivs", '{"Azumarill": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, "ivs": []}}}}'),
        ("empty name", '{"Azumarill": {"Great": {" ": {"attack": 0, "defense": 0, "stamina": 0}}}}'),
    ])
    def test_rejects_malformed(self, bad, fragment):
        with pytest.raises(ValueError):
            parse_threshold_json(fragment)

    def test_lowercase_league_normalized(self):
        entries = parse_threshold_json(
            '{"Azumarill": {"great": {"X": {"attack": 0, "defense": 0, "stamina": 0}}}}'
        )
        assert entries[0][1] == 'Great'


class TestNonFiniteRejected:
    """json.loads accepts Infinity, and int(float('inf')) raises
    OverflowError (not ValueError) — both import parsers must surface a
    displayable ValueError instead of letting it escape a ValueError-only
    handler and leave Import silently dead."""

    @pytest.mark.parametrize("fragment", [
        '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": 0, "onlytop": Infinity}}}}',
        '{"A": {"Great": {"X": {"attack": 0, "defense": 0, "stamina": Infinity}}}}',
        '{"A": {"Great": {"X": {"attack": Infinity, "defense": 0, "stamina": 0}}}}',
        '{"A": {"Great": {"X": {"attack": NaN, "defense": 0, "stamina": 0}}}}',
    ])
    def test_json_non_finite_rejected(self, fragment):
        with pytest.raises(ValueError):
            parse_threshold_json(fragment)

    @pytest.mark.parametrize("stat,value", [
        ("Stamina", "inf"),
        ("OnlyTop", "inf"),
        ("Attack", "inf"),
    ])
    def test_text_infinity_rejected(self, stat, value):
        fields = {
            'Species': 'Azumarill', 'League': 'Great', 'Name': 'X',
            'Attack': '0', 'Defense': '0', 'Stamina': '0', 'OnlyTop': '0',
        }
        fields[stat] = value
        text = "GoBattleKit Threshold v1\n" + "\n".join(
            f"{k}: {v}" for k, v in fields.items())
        with pytest.raises(ValueError):
            parse_threshold_text(text)


class TestThresholdTextFormat:
    """The 'GoBattleKit Threshold v1' user-to-user share format (TS10)."""

    def test_round_trip_floors(self):
        t = {'attack': 122.5, 'defense': 110.0, 'stamina': 128, 'onlytop': 25}
        text = format_threshold_text('Azumarill', 'Great', 'Mirror', t)
        species, league, name, spec = parse_threshold_text(text)
        assert (species, league, name) == ('Azumarill', 'Great', 'Mirror')
        assert spec == t

    def test_round_trip_ivs(self):
        t = {'attack': 0, 'defense': 0, 'stamina': 0, 'ivs': [[8, 15, 15]]}
        text = format_threshold_text('Azumarill', 'Great', 'Mirror', t)
        _, _, _, spec = parse_threshold_text(text)
        assert spec['ivs'] == [[8, 15, 15]]

    def test_rejects_bad_header_and_missing_fields(self):
        with pytest.raises(ValueError):
            parse_threshold_text("Something else\nSpecies: Azumarill")
        with pytest.raises(ValueError):
            parse_threshold_text("GoBattleKit Threshold v1\nSpecies: Azumarill")

    def test_rejects_unknown_league(self):
        t = {'attack': 0, 'defense': 0, 'stamina': 0}
        text = format_threshold_text('Azumarill', 'Holiday', 'X', t)
        with pytest.raises(ValueError):
            parse_threshold_text(text)

    def test_old_versions_unaffected_by_ivs_line(self):
        """The Ivs line is additive: a parser that ignores unknown lines
        (the pre-ivs app) still reads the floors."""
        t = {'attack': 5.0, 'defense': 0, 'stamina': 0, 'ivs': [[1, 2, 3]]}
        text = format_threshold_text('Azumarill', 'Great', 'X', t)
        assert 'Attack: 5.0' in text and text.startswith('GoBattleKit Threshold v1')


class TestIvsFirstClass:
    def test_add_threshold_stores_ivs(self):
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0, ivs=[[8, 15, 15]])
        data = load_user_thresholds()
        assert data['Azumarill']['Great']['X']['ivs'] == [[8, 15, 15]]

    def test_replace_preserves_ivs(self):
        """Editing floors must not silently drop an explicit IV list (IV2)."""
        add_threshold('Azumarill', 'great', 'X', 0, 0, 0, ivs=[[8, 15, 15]])
        ok = replace_threshold('Azumarill', 'great', 'X',
                               'Azumarill', 'great', 'X', 0, 100.0, 0)
        assert ok
        entry = load_user_thresholds()['Azumarill']['Great']['X']
        assert entry['defense'] == 100.0
        assert entry['ivs'] == [[8, 15, 15]]

    def test_malformed_stored_target_skipped_not_fatal(self, tmp_path):
        """A string-valued floor in the stored file must not break the
        whole check (IV5)."""
        from gobattlekit.data.iv_checker import check_thresholds
        thresholds = {
            'Azumarill': {'Great': {
                'Broken': {'attack': '122'},
                'Fine': {'attack': 0, 'defense': 0, 'stamina': 0},
            }},
        }
        header = 'Name,Form,CP,Atk IV,Def IV,Sta IV,Level Min,Shadow/Purified,Lucky\n'
        csv = tmp_path / 'mons.csv'
        csv.write_text(header + 'Azumarill,,1400,8,15,15,20,0,0\n',
                       encoding='utf-8-sig')
        results = check_thresholds(str(csv), thresholds, league='great',
                                   max_level=40)
        assert results['Azumarill'][0]['matched'] == ['Fine']


class TestPrunePropagatedPreEvos:
    """One-time cleanup of entries written by the import path's pre-evo
    propagation (SI2, removed per the 2026-06-11 Batch-0 decision).

    A propagated entry is identified conservatively: a pre-evo species
    carrying the same league+name AND identical spec values as its final
    form's entry — exactly what the propagation block wrote."""

    EVO_LINES = {
        'Azumarill': ['Marill', 'Azumarill'],
        'Registeel': ['Registeel'],
    }

    def test_removes_propagated_copy(self):
        spec = {'attack': 0, 'defense': 143.0, 'stamina': 138}
        add_threshold('Azumarill', 'great', 'Imported', **spec)
        add_threshold('Marill', 'great', 'Imported', **spec)  # propagated copy
        changed = prune_propagated_pre_evos(self.EVO_LINES)
        assert changed
        data = load_user_thresholds()
        assert 'Marill' not in data
        assert 'Imported' in data['Azumarill']['Great']

    def test_keeps_user_created_pre_evo_target_with_different_values(self):
        add_threshold('Azumarill', 'great', 'Default', 0, 143.0, 138)
        # Same league+name but the user's own numbers — NOT a propagated copy.
        add_threshold('Marill', 'great', 'Default', 0, 50.0, 60)
        changed = prune_propagated_pre_evos(self.EVO_LINES)
        assert not changed
        data = load_user_thresholds()
        assert data['Marill']['Great']['Default'] == {
            'attack': 0, 'defense': 50.0, 'stamina': 60,
        }

    def test_keeps_pre_evo_target_without_final_counterpart(self):
        add_threshold('Marill', 'great', 'My Marill', 0, 50.0, 60)
        assert not prune_propagated_pre_evos(self.EVO_LINES)
        assert 'Marill' in load_user_thresholds()

    def test_noop_on_empty(self):
        assert not prune_propagated_pre_evos(self.EVO_LINES)
        assert load_user_thresholds() == {}
