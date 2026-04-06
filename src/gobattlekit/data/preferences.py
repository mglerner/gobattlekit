#!/usr/bin/env python
"""
Simple JSON-based preferences persistence.
"""
import json
from .fetcher import CACHE_DIR

_PREFS_FILE = CACHE_DIR / "preferences.json"


def _load_all():
    try:
        if _PREFS_FILE.exists():
            return json.loads(_PREFS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_all(data):
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        _PREFS_FILE.write_text(json.dumps(data))
    except Exception as e:
        print(f"Could not save preferences: {e}")


def get_pref(key, default=None):
    return _load_all().get(key, default)


def set_pref(key, value):
    data = _load_all()
    data[key] = value
    _save_all(data)
