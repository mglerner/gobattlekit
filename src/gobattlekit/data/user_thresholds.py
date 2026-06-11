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


VALID_LEAGUES = ('Great', 'Ultra', 'Master')

# The complete target-spec vocabulary shared with check_thresholds — and
# with pogo-simulator's "Copy for IV scanner" export (its commit b97113f),
# which emits exactly this schema.
_SPEC_KEYS = {'attack', 'defense', 'stamina', 'ivs', 'onlytop'}


def _validate_spec(spec, where):
    """Validate one target spec; returns a normalized copy.

    Raises ValueError with a user-displayable message. Unknown keys are
    rejected rather than ignored: a typo'd key would otherwise silently
    become a match-everything floor via target.get(..., 0).
    """
    if not isinstance(spec, dict):
        raise ValueError(f"{where}: target must be an object.")
    unknown = sorted(set(spec) - _SPEC_KEYS)
    if unknown:
        raise ValueError(f"{where}: unknown keys: {', '.join(unknown)}.")
    out = {}
    for k in ('attack', 'defense', 'stamina'):
        v = spec.get(k, 0)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"{where}: '{k}' must be a non-negative number.")
        out[k] = int(v) if k == 'stamina' else v
    onlytop = spec.get('onlytop', 0)
    if isinstance(onlytop, bool) or not isinstance(onlytop, (int, float)) or onlytop < 0:
        raise ValueError(f"{where}: 'onlytop' must be a non-negative integer.")
    if onlytop:
        out['onlytop'] = int(onlytop)
    if 'ivs' in spec:
        ivs = spec['ivs']
        if (not isinstance(ivs, list) or not ivs
                or not all(isinstance(t, (list, tuple)) and len(t) == 3 for t in ivs)
                or not all(isinstance(x, int) and 0 <= x <= 15 for t in ivs for x in t)):
            raise ValueError(
                f"{where}: 'ivs' must be a list of [atk, def, sta] triples (0-15)."
            )
        out['ivs'] = [list(t) for t in ivs]
    return out


def parse_threshold_json(text):
    """Parse a scanner-JSON fragment: {species: {League: {name: target}}}.

    This is the format pogo-simulator's dive pages emit via "Copy for IV
    scanner". Returns a list of (species, league_label, name, spec) tuples.
    Raises ValueError with a displayable message on any problem — nothing
    is silently dropped or coerced.
    """
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Not valid JSON: {e}") from e
    if not isinstance(obj, dict) or not obj:
        raise ValueError("Expected {species: {League: {name: target}}}.")
    entries = []
    for species, leagues in obj.items():
        if not isinstance(leagues, dict) or not leagues:
            raise ValueError(f"{species}: expected {{League: {{name: target}}}}.")
        for league, names in leagues.items():
            league_label = str(league).capitalize()
            if league_label not in VALID_LEAGUES:
                raise ValueError(
                    f"{species}: unknown league '{league}' "
                    f"(expected one of {', '.join(VALID_LEAGUES)})."
                )
            if not isinstance(names, dict) or not names:
                raise ValueError(f"{species}/{league_label}: expected {{name: target}}.")
            for name, spec in names.items():
                if not str(name).strip():
                    raise ValueError(f"{species}/{league_label}: target name cannot be empty.")
                entries.append((
                    str(species), league_label, str(name),
                    _validate_spec(spec, f"{species}/{league_label}/{name}"),
                ))
    return entries


def format_threshold_text(species, league, name, t):
    """Render a target as the shareable 'GoBattleKit Threshold v1' text."""
    lines = [
        "GoBattleKit Threshold v1",
        f"Species: {species}",
        f"League: {league.replace(' League', '')}",
        f"Name: {name}",
        f"Attack: {t.get('attack', 0)}",
        f"Defense: {t.get('defense', 0)}",
        f"Stamina: {t.get('stamina', 0)}",
        f"OnlyTop: {t.get('onlytop', 0)}",
    ]
    if t.get('ivs'):
        # Optional line; older app versions ignore unknown lines, so they
        # import such a share as floors-only (the pre-ivs behavior).
        lines.append(f"Ivs: {json.dumps(t['ivs'])}")
    return "\n".join(lines)


def parse_threshold_text(text):
    """Parse the 'GoBattleKit Threshold v1' share text.

    Returns (species, league_label, name, spec). Raises ValueError on any
    problem. Species existence is NOT checked here — that needs the
    gamemaster and is the caller's (best-effort) job.
    """
    lines = [l.strip() for l in text.strip().splitlines()]
    if not lines or lines[0] != "GoBattleKit Threshold v1":
        raise ValueError("Not a valid GoBattleKit threshold.")

    data = {}
    for line in lines[1:]:
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        data[key.strip()] = value.strip()

    required = ('Species', 'League', 'Name', 'Attack', 'Defense', 'Stamina', 'OnlyTop')
    for field in required:
        if field not in data:
            raise ValueError(f"Missing field: {field}")

    species = data['Species']
    league_label = data['League'].capitalize()
    if league_label not in VALID_LEAGUES:
        raise ValueError(
            f"Unknown league '{data['League']}' "
            f"(expected one of {', '.join(VALID_LEAGUES)})."
        )
    name = data['Name']
    if not name:
        raise ValueError("Name cannot be empty.")

    try:
        spec = {
            'attack': float(data['Attack']),
            'defense': float(data['Defense']),
            'stamina': int(float(data['Stamina'])),
            'onlytop': int(float(data['OnlyTop'])),
        }
    except ValueError:
        raise ValueError("Invalid stat values.")
    if 'Ivs' in data:
        try:
            spec['ivs'] = json.loads(data['Ivs'])
        except json.JSONDecodeError:
            raise ValueError("Invalid Ivs list.")
    return species, league_label, name, _validate_spec(spec, name)


def import_threshold_entries(entries):
    """Merge parsed (species, league_label, name, spec) entries into the
    stored thresholds in ONE transaction. Returns the entry count; raises
    ValueError if the save fails (nothing half-applied)."""
    thresholds = load_user_thresholds()
    for species, league_label, name, spec in entries:
        thresholds.setdefault(species, {}).setdefault(league_label, {})[name] = spec
    if not save_user_thresholds(thresholds):
        raise ValueError("Could not save imported targets.")
    return len(entries)


def add_threshold(species, league, name, attack, defense, stamina, onlytop=0,
                  ivs=None):
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
    if ivs:
        entry['ivs'] = [list(t) for t in ivs]
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
    orig_entry = thresholds.get(orig_species, {}).get(orig_label, {}).get(orig_name)
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
    if orig_entry and 'ivs' in orig_entry:
        # The edit form has no IV-list UI; carry the explicit list through
        # so editing the floors doesn't silently turn an explicit-IV target
        # into match-everything floors (IV2).
        entry['ivs'] = orig_entry['ivs']
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

