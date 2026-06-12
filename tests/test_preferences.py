"""Tests for preferences.py — load robustness and round-trips.

_PREFS_FILE is redirected to tmp_path by the autouse isolate_app_data
fixture in conftest.py.
"""
import json

from gobattlekit.data import preferences
from gobattlekit.data.preferences import get_pref, set_pref


class TestRoundTrip:
    def test_set_get(self):
        set_pref('skip_intro_iv_checker', True)
        assert get_pref('skip_intro_iv_checker') is True

    def test_missing_key_default(self):
        assert get_pref('nope', default='d') == 'd'


class TestLoadRobustness:
    def test_corrupt_json_renamed_aside(self):
        f = preferences._PREFS_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('{"skip')
        assert get_pref('anything') is None
        assert f.with_suffix('.json.corrupt').exists()
        assert not f.exists()

    def test_valid_but_non_dict_json_does_not_crash(self):
        """A prefs file holding a JSON list/string parsed fine but crashed
        get_pref on .get() (AP15). Treat it like corruption."""
        f = preferences._PREFS_FILE
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps([1, 2, 3]))
        assert get_pref('anything', default='d') == 'd'
        # And a later set_pref starts a fresh dict without crashing.
        set_pref('k', 1)
        assert get_pref('k') == 1
