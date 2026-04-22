#!/usr/bin/env python
"""
Fetch and cache PvPoke game data.
"""
import urllib.request
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

def _fetch_json(key):
    """Fetch a JSON file from pvpoke, using a local cache.

    Uses cached data if it is less than CACHE_TTL seconds old.
    Falls back to stale cache if network is unavailable.
    Raises NoDataError if neither network nor cache is available.
    """
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache_file = CACHE_DIR / f"{key}.json"

    # Use cache if fresh enough
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL:
            return json.loads(cache_file.read_text())

    # Try to fetch fresh data
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(URLS[key], context=ssl_context, timeout=FETCH_TIMEOUT) as r:
            data = json.loads(r.read().decode())
        # Atomic write: write to .tmp then os.replace so a kill mid-write
        # can't leave a truncated cache file behind.
        tmp = cache_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, cache_file)

        # If this is the gamemaster, regenerate evolution lines
        if key == 'gamemaster':
            try:
                from .evolution_lines import generate_evolution_lines, save_evolution_lines
                evo_lines = generate_evolution_lines(data)
                save_evolution_lines(evo_lines)
            except Exception:
                logger.exception("Could not regenerate evolution lines")
        return data

    except Exception:
        logger.exception("Fetch error for %s", key)

    # Fall back to stale cache if available
    if cache_file.exists():
        return json.loads(cache_file.read_text())

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
