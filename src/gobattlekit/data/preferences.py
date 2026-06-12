#!/usr/bin/env python
"""
Simple JSON-based preferences persistence.
"""
import json
import logging
import os
from .fetcher import CACHE_DIR

logger = logging.getLogger(__name__)

_PREFS_FILE = CACHE_DIR / "preferences.json"


def _move_corrupt_aside():
    """Rename the prefs file aside so a later save doesn't clobber what
    might still be recoverable."""
    corrupt_path = _PREFS_FILE.with_suffix(".json.corrupt")
    try:
        os.replace(_PREFS_FILE, corrupt_path)
        logger.warning("Preferences file was corrupt; moved to %s", corrupt_path)
    except OSError:
        logger.exception("Could not move corrupt preferences file aside")


def _load_all():
    if not _PREFS_FILE.exists():
        return {}
    try:
        data = json.loads(_PREFS_FILE.read_text())
    except json.JSONDecodeError:
        # File is corrupt (partial write from a prior kill, disk bitrot,
        # manual edit gone wrong).
        _move_corrupt_aside()
        return {}
    except OSError:
        # Permission / I/O issue — fall back to defaults rather than crash,
        # but make the failure visible in logs.
        logger.exception("Could not read preferences")
        return {}
    if not isinstance(data, dict):
        # Valid JSON but not an object (a list, string, ...) — .get() on it
        # would crash every get_pref. Treat like corruption.
        logger.warning("Preferences file held %s, not an object; resetting",
                       type(data).__name__)
        _move_corrupt_aside()
        return {}
    return data


def _save_all(data):
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        # Atomic write: write to a temp file then rename, so a kill
        # mid-write can't leave a truncated preferences.json behind.
        tmp = _PREFS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, _PREFS_FILE)
    except Exception:
        logger.exception("Could not save preferences")


def get_pref(key, default=None):
    return _load_all().get(key, default)


def set_pref(key, value):
    data = _load_all()
    data[key] = value
    _save_all(data)
