#!/usr/bin/env python
"""
Simple JSON-based preferences persistence.
"""
from .fetcher import CACHE_DIR
from .jsonstore import load_json_object, save_json_atomic

_PREFS_FILE = CACHE_DIR / "preferences.json"


def _load_all():
    return load_json_object(_PREFS_FILE, "Preferences")


def _save_all(data):
    save_json_atomic(_PREFS_FILE, data)


def get_pref(key, default=None):
    return _load_all().get(key, default)


def set_pref(key, value):
    data = _load_all()
    data[key] = value
    _save_all(data)
