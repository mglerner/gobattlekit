#!/usr/bin/env python
"""
User-defined IV thresholds — load, save, and manage.
Stored as JSON in the cache directory.
"""
import json
import logging
import os
from .fetcher import CACHE_DIR

logger = logging.getLogger(__name__)

USER_THRESHOLDS_FILE = CACHE_DIR / 'user_thresholds.json'


def load_user_thresholds():
    """Load user thresholds from JSON. Returns empty dict if file doesn't exist."""
    if not USER_THRESHOLDS_FILE.exists():
        return {}
    try:
        return json.loads(USER_THRESHOLDS_FILE.read_text())
    except Exception:
        logger.exception("Could not load user thresholds")
        return {}


def save_user_thresholds(thresholds):
    """Save user thresholds to JSON atomically (temp + os.replace)."""
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        tmp = USER_THRESHOLDS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(thresholds, indent=2))
        os.replace(tmp, USER_THRESHOLDS_FILE)
    except Exception:
        logger.exception("Could not save user thresholds")


def add_threshold(species, league, name, attack, defense, stamina, onlytop=0):
    """Add a threshold entry for a species/league. Saves immediately."""
    thresholds = load_user_thresholds()
    if species not in thresholds:
        thresholds[species] = {}
    league_label = league.capitalize()
    if league_label not in thresholds[species]:
        thresholds[species][league_label] = {}
    entry = {'attack': attack, 'defense': defense, 'stamina': stamina}
    if onlytop > 0:
        entry['onlytop'] = onlytop
    thresholds[species][league_label][name] = entry
    save_user_thresholds(thresholds)
    return thresholds


def delete_threshold(species, league, name):
    """Delete a single threshold entry. Saves immediately."""
    thresholds = load_user_thresholds()
    league_label = league.capitalize()
    try:
        del thresholds[species][league_label][name]
        # Clean up empty dicts
        if not thresholds[species][league_label]:
            del thresholds[species][league_label]
        if not thresholds[species]:
            del thresholds[species]
    except KeyError:
        pass
    save_user_thresholds(thresholds)
    return thresholds


def clear_all_thresholds():
    """Delete all user thresholds."""
    save_user_thresholds({})
    return {}


def get_all_species(pokemon_index):
    """Return sorted list of all species names from the gamemaster."""
    return sorted(pokemon_index.keys())

