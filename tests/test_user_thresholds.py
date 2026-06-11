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
