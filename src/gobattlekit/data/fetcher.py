#!/usr/bin/env python
import urllib.request
import json
import pathlib
import time
import ssl
import certifi

CACHE_DIR = pathlib.Path.home() / "Documents" / "gobattlekit_cache"
CACHE_TTL = 86400  # refresh once a day

BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data"

URLS = {
    "gamemaster": f"{BASE_URL}/gamemaster.json",
    "great":      f"{BASE_URL}/rankings/gobattleleague/overall/rankings-1500.json",
    "ultra":      f"{BASE_URL}/rankings/gobattleleague/overall/rankings-2500.json",
    "master":     f"{BASE_URL}/rankings/gobattleleague/overall/rankings-10000.json",
}

def _fetch_json(key):
    """Fetch a JSON file from pvpoke, using a local cache."""
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL:
            return json.loads(cache_file.read_text())
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(URLS[key], context=ssl_context) as r:
        data = json.loads(r.read().decode())
    cache_file.write_text(json.dumps(data))
    return data

def load_gamemaster():
    """Load the PvPoke gamemaster data."""
    return _fetch_json("gamemaster")

def load_rankings(league):
    """Load rankings for a given league: 'great', 'ultra', or 'master'."""
    if league not in ("great", "ultra", "master"):
        raise ValueError(f"Unknown league: {league}")
    return _fetch_json(league)

