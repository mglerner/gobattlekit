#!/usr/bin/env python
"""
Shared JSON-file persistence: corruption-tolerant loads and atomic saves.

preferences.py, user_thresholds.py and evolution_lines.py each kept their
own copy of this logic. fetcher.py deliberately does NOT use it - its
payload write must raise so the caller can fall back to a stale cache.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)


def _move_corrupt_aside(path, label):
    """Rename the file aside so a later save can't clobber what might still
    be recoverable."""
    corrupt_path = path.with_suffix(".json.corrupt")
    try:
        os.replace(path, corrupt_path)
        logger.warning("%s file was corrupt; moved to %s", label, corrupt_path)
    except OSError:
        logger.exception("Could not move corrupt %s file aside", label)


def load_json_object(path, label):
    """Load a JSON object from path. Returns {} if it is missing, unreadable,
    corrupt, or not an object; corrupt/non-object files are moved aside to
    .json.corrupt first. `label` names the file in log messages."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        # File is corrupt (partial write from a prior kill, disk bitrot,
        # manual edit gone wrong).
        _move_corrupt_aside(path, label)
        return {}
    except OSError:
        # Permission / I/O issue - fall back to defaults rather than crash,
        # but make the failure visible in logs.
        logger.exception("Could not read %s file", label)
        return {}
    if not isinstance(data, dict):
        # Valid JSON but not an object (a list, string, ...) - callers
        # index/.get() it as a mapping and would crash. Treat like corruption.
        logger.warning("%s file held %s, not an object; resetting",
                       label, type(data).__name__)
        _move_corrupt_aside(path, label)
        return {}
    return data


def save_json_atomic(path, data, *, indent=None):
    """Write data to path as JSON atomically (temp file + os.replace), so a
    kill mid-write can't leave a truncated file behind.

    Returns True on success, False on failure - failures are logged, never
    raised, so callers that need to know check the return value.
    """
    try:
        path.parent.mkdir(exist_ok=True, parents=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=indent))
        os.replace(tmp, path)
        return True
    except Exception:
        logger.exception("Could not save %s", path.name)
        return False
