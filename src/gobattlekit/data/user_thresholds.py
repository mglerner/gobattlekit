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
    except json.JSONDecodeError:
        # File is corrupt (partial write from a prior kill, manual edit gone
        # wrong). Rename it aside so the next save_user_thresholds() can't
        # clobber what might still be recoverable, and start fresh — same
        # pattern as preferences.py.
        corrupt_path = USER_THRESHOLDS_FILE.with_suffix(".json.corrupt")
        try:
            os.replace(USER_THRESHOLDS_FILE, corrupt_path)
            logger.warning("User thresholds file was corrupt; moved to %s", corrupt_path)
        except OSError:
            logger.exception("Could not move corrupt user thresholds file aside")
        return {}
    except OSError:
        logger.exception("Could not read user thresholds")
        return {}


def save_user_thresholds(thresholds):
    """Save user thresholds to JSON atomically (temp + os.replace).

    Returns True on success, False on failure — callers performing
    destructive sequences must check it before assuming the data landed.
    """
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        tmp = USER_THRESHOLDS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(thresholds, indent=2))
        os.replace(tmp, USER_THRESHOLDS_FILE)
        return True
    except Exception:
        logger.exception("Could not save user thresholds")
        return False


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


def replace_threshold(orig_species, orig_league, orig_name,
                      species, league, name, attack, defense, stamina,
                      onlytop=0):
    """Replace one threshold entry with another as a SINGLE load-modify-save
    transaction. The previous delete-then-add sequence saved twice; a failure
    of the second save lost the original entry with no trace (SI10).

    Returns True if the save succeeded; on False, the on-disk file is
    untouched.
    """
    thresholds = load_user_thresholds()
    orig_label = orig_league.capitalize()
    try:
        del thresholds[orig_species][orig_label][orig_name]
        if not thresholds[orig_species][orig_label]:
            del thresholds[orig_species][orig_label]
        if not thresholds[orig_species]:
            del thresholds[orig_species]
    except KeyError:
        pass
    entry = {'attack': attack, 'defense': defense, 'stamina': stamina}
    if onlytop > 0:
        entry['onlytop'] = onlytop
    league_label = league.capitalize()
    thresholds.setdefault(species, {}).setdefault(league_label, {})[name] = entry
    return save_user_thresholds(thresholds)


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


def prune_propagated_pre_evos(evolution_lines):
    """One-time cleanup for entries written by the (removed) import-path
    pre-evolution propagation.

    Those copies never matched anything — they pitted the FINAL form's
    scaled-stat floors against the PRE-EVO's base stats — and worse, their
    presence shadowed the correct evolution-line mapping in
    check_thresholds. Identification is conservative: a pre-evo species
    entry is pruned only when its final form carries the same league+name
    with IDENTICAL spec values (exactly what the propagation wrote).

    Returns True if anything was removed (and saved).
    """
    thresholds = load_user_thresholds()
    pre_evo_to_finals = {}
    for final, line in evolution_lines.items():
        for member in line:
            if member != final:
                pre_evo_to_finals.setdefault(member, []).append(final)

    changed = False
    for species in list(thresholds.keys()):
        for final in pre_evo_to_finals.get(species, []):
            if final not in thresholds:
                continue
            for league_label in list(thresholds[species].keys()):
                final_entries = thresholds.get(final, {}).get(league_label, {})
                for name in list(thresholds[species][league_label].keys()):
                    if thresholds[species][league_label][name] == final_entries.get(name):
                        del thresholds[species][league_label][name]
                        changed = True
                if not thresholds[species][league_label]:
                    del thresholds[species][league_label]
        if species in thresholds and not thresholds[species]:
            del thresholds[species]

    if changed:
        save_user_thresholds(thresholds)
    return changed


def clear_all_thresholds():
    """Delete all user thresholds."""
    save_user_thresholds({})
    return {}


def get_all_species(pokemon_index):
    """Return sorted list of all species names from the gamemaster."""
    return sorted(pokemon_index.keys())

