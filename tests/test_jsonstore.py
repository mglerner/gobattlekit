"""Tests for jsonstore.py - the shared corruption-tolerant load / atomic save
helpers behind preferences, user thresholds and the evolution-line cache."""
import json

from gobattlekit.data.jsonstore import load_json_object, save_json_atomic


class TestLoadJsonObject:
    def test_missing_file_returns_empty(self, tmp_path):
        assert load_json_object(tmp_path / "nope.json", "Nope") == {}

    def test_round_trip(self, tmp_path):
        f = tmp_path / "d.json"
        f.write_text(json.dumps({"a": 1}))
        assert load_json_object(f, "D") == {"a": 1}

    def test_corrupt_json_moved_aside(self, tmp_path):
        f = tmp_path / "d.json"
        f.write_text('{"a"')
        assert load_json_object(f, "D") == {}
        assert not f.exists()
        assert f.with_suffix(".json.corrupt").read_text() == '{"a"'

    def test_non_object_json_moved_aside(self, tmp_path):
        f = tmp_path / "d.json"
        f.write_text(json.dumps([1, 2, 3]))
        assert load_json_object(f, "D") == {}
        assert not f.exists()
        assert f.with_suffix(".json.corrupt").exists()


class TestSaveJsonAtomic:
    def test_creates_parent_and_leaves_no_tmp(self, tmp_path):
        f = tmp_path / "sub" / "d.json"
        assert save_json_atomic(f, {"a": 1}) is True
        assert json.loads(f.read_text()) == {"a": 1}
        assert not f.with_suffix(".json.tmp").exists()

    def test_replaces_existing_file(self, tmp_path):
        f = tmp_path / "d.json"
        save_json_atomic(f, {"a": 1})
        assert save_json_atomic(f, {"b": 2}, indent=2) is True
        assert json.loads(f.read_text()) == {"b": 2}
        assert "\n  " in f.read_text()

    def test_unserializable_data_returns_false(self, tmp_path):
        f = tmp_path / "d.json"
        f.write_text(json.dumps({"a": 1}))
        assert save_json_atomic(f, {"bad": object()}) is False
        # The existing file is untouched by the failed write.
        assert json.loads(f.read_text()) == {"a": 1}
