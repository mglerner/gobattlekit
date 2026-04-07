#!/usr/bin/env python
"""
Simple JSON-based preferences persistence.
"""
import json
import os
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
        # Atomic write: write to a temp file then rename, so a kill
        # mid-write can't leave a truncated preferences.json behind.
        tmp = _PREFS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, _PREFS_FILE)
    except Exception as e:
        print(f"Could not save preferences: {e}")


def get_pref(key, default=None):
    return _load_all().get(key, default)


def set_pref(key, value):
    data = _load_all()
    data[key] = value
    _save_all(data)
