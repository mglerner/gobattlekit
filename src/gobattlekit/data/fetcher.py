#!/usr/bin/env python
"""
Fetch and cache PvPoke game data.
"""
import urllib.request
import urllib.error
import json
import logging
import os
import pathlib
import time
import ssl
import certifi

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 10  # seconds — keep tight so iOS watchdog can't kill us

CACHE_DIR = pathlib.Path.home() / "Documents" / "gobattlekit_cache"
CACHE_TTL = 86400  # refresh once a day
SAVED_CSV = CACHE_DIR / "pokegenie_export.csv"
USER_GENERATED_CSV = CACHE_DIR / 'user_generated.csv'

BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data"
URLS = {
    "gamemaster": f"{BASE_URL}/gamemaster.json",
    "great":      f"{BASE_URL}/rankings/all/overall/rankings-1500.json",
    "ultra":      f"{BASE_URL}/rankings/all/overall/rankings-2500.json",
    "master":     f"{BASE_URL}/rankings/all/overall/rankings-10000.json",
}

def get_csv_path():
    """Return the CSV path to use: PokeGenie export if exists, else user-generated."""
    if SAVED_CSV.exists():
        return str(SAVED_CSV)
    if USER_GENERATED_CSV.exists():
        return str(USER_GENERATED_CSV)
    return None
    
class NoDataError(Exception):
    """Raised when data cannot be fetched and no cache is available."""
    pass

def _read_validators(meta_file):
    """Read the stored ETag / Last-Modified for a cached file, if any."""
    try:
        return json.loads(meta_file.read_text())
    except Exception:
        return {}

def _write_validators(meta_file, headers):
    """Persist the server's ETag / Last-Modified alongside the cache.

    Atomic (temp + os.replace) like the payload write, and only ever called
    AFTER the payload replace succeeds — a new ETag beside old data would
    pin the stale cache behind 304s indefinitely.
    """
    validators = {}
    if headers.get("ETag"):
        validators["etag"] = headers["ETag"]
    if headers.get("Last-Modified"):
        validators["last_modified"] = headers["Last-Modified"]
    try:
        tmp = meta_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(validators))
        os.replace(tmp, meta_file)
    except Exception:
        logger.exception("Could not write cache validators to %s", meta_file)

# In-memory memo of parsed cache files, keyed by data key. The gamemaster
# is ~14MB; without this every consumer call (get_moves, get_pokemon_index,
# ...) re-read and re-parsed it from disk. Entries are validated by mtime.
# Consumers must treat returned data as read-only.
_parsed_cache = {}

def _read_cache(cache_file, key):
    """Parse a cache file, memoized by mtime. Raises on corrupt content."""
    mtime = cache_file.stat().st_mtime
    hit = _parsed_cache.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    data = json.loads(cache_file.read_text())
    _parsed_cache[key] = (mtime, data)
    return data

def _fetch_json(key):
    """Fetch a JSON file from pvpoke, using a local cache.

    Uses cached data if it is less than CACHE_TTL seconds old. Once the cache
    is stale, makes a conditional request (If-None-Match / If-Modified-Since);
    on a 304 Not Modified it just refreshes the cache mtime instead of
    re-downloading and re-deriving data.
    Falls back to stale cache if network is unavailable.
    Raises NoDataError if neither network nor cache is available.
    """
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache_file = CACHE_DIR / f"{key}.json"
    meta_file = CACHE_DIR / f"{key}.meta.json"

    # Use cache if fresh enough
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL:
            try:
                return _read_cache(cache_file, key)
            except (json.JSONDecodeError, OSError):
                # Corrupt cache (e.g. truncated by a pre-0.0.26 non-atomic
                # write). Discard it — including the validators, so the
                # refetch below is unconditional and can't 304 back onto
                # the corrupt file — and fall through to a full fetch.
                logger.warning("Corrupt cache for %s; discarding and refetching", key)
                try:
                    cache_file.unlink()
                    meta_file.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Could not remove corrupt cache for %s", key)

    # Try to fetch fresh data, using conditional headers if we have them so the
    # server can answer 304 Not Modified when the file is unchanged.
    try:
        headers = {}
        if cache_file.exists():
            validators = _read_validators(meta_file)
            if validators.get("etag"):
                headers["If-None-Match"] = validators["etag"]
            if validators.get("last_modified"):
                headers["If-Modified-Since"] = validators["last_modified"]

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        request = urllib.request.Request(URLS[key], headers=headers)
        try:
            with urllib.request.urlopen(request, context=ssl_context, timeout=FETCH_TIMEOUT) as r:
                data = json.loads(r.read().decode())
                response_headers = r.headers
        except urllib.error.HTTPError as e:
            if e.code == 304:
                # Remote unchanged: reset the cache mtime so we don't re-check
                # for another CACHE_TTL, and serve the existing cache.
                os.utime(cache_file, None)
                return _read_cache(cache_file, key)
            raise

        # Atomic write: write to .tmp then os.replace so a kill mid-write
        # can't leave a truncated cache file behind. Validators are written
        # strictly AFTER the payload lands — the reverse order let a kill
        # window pin old data behind 304s forever.
        tmp = cache_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, cache_file)
        _write_validators(meta_file, response_headers)
        _parsed_cache[key] = (cache_file.stat().st_mtime, data)

        # If this is the gamemaster, regenerate evolution lines
        if key == 'gamemaster':
            try:
                from .evolution_lines import generate_evolution_lines, save_evolution_lines
                evo_lines = generate_evolution_lines(data)
                save_evolution_lines(evo_lines)
                # Refresh the in-memory snapshot IN PLACE so modules that
                # did `from .thresholds import EVOLUTION_LINES` at import
                # time see the regenerated lines this session, not after
                # the next app restart.
                from . import thresholds
                thresholds.EVOLUTION_LINES.clear()
                thresholds.EVOLUTION_LINES.update(evo_lines)
            except Exception:
                logger.exception("Could not regenerate evolution lines")
        return data

    except Exception:
        logger.exception("Fetch error for %s", key)

    # Fall back to stale cache if available
    if cache_file.exists():
        try:
            return _read_cache(cache_file, key)
        except (json.JSONDecodeError, OSError):
            logger.exception("Stale cache for %s is corrupt", key)

    # No network and no cache
    raise NoDataError(
        f"Could not fetch data and no cached data is available. "
        f"Please connect to the internet and restart the app."
    )

def load_gamemaster():
    """Load the PvPoke gamemaster data."""
    return _fetch_json("gamemaster")

def load_rankings(league):
    """Load rankings for a given league: 'great', 'ultra', or 'master'."""
    if league not in ("great", "ultra", "master"):
        raise ValueError(f"Unknown league: {league}")
    return _fetch_json(league)
