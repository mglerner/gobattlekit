#!/usr/bin/env python
"""
Fetch and cache PvPoke game data.
"""
import urllib.request
import json
import pathlib
import time
import ssl
import certifi

CACHE_DIR = pathlib.Path.home() / "Documents" / "gobattlekit_cache"
CACHE_TTL = 86400  # refresh once a day
SAVED_CSV = CACHE_DIR / "pokegenie_export.csv"

BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data"
URLS = {
    "gamemaster": f"{BASE_URL}/gamemaster.json",
    "great":      f"{BASE_URL}/rankings/all/overall/rankings-1500.json",
    "ultra":      f"{BASE_URL}/rankings/all/overall/rankings-2500.json",
    "master":     f"{BASE_URL}/rankings/all/overall/rankings-10000.json",
}

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
        with urllib.request.urlopen(URLS[key], context=ssl_context) as r:
            data = json.loads(r.read().decode())
        cache_file.write_text(json.dumps(data))

        # If this is the gamemaster, regenerate evolution lines
        if key == 'gamemaster':
            try:
                from .evolution_lines import generate_evolution_lines, save_evolution_lines
                evo_lines = generate_evolution_lines(data)
                save_evolution_lines(evo_lines)
            except Exception as e:
                print(f"Could not regenerate evolution lines: {e}")
        return data        
        
        return data
    except Exception as e:
        print(f"Fetch error for {key}: {e}")

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
