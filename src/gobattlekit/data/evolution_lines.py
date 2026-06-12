#!/usr/bin/env python
"""
Evolution line generation and loading.
Generates from gamemaster JSON, caches to disk.
"""
import json
import logging
import os
from pathlib import Path
from .fetcher import CACHE_DIR

logger = logging.getLogger(__name__)

BUNDLED_PATH = Path(__file__).parent / 'evolution_lines.json'
CACHED_PATH = CACHE_DIR / 'evolution_lines.json'


def generate_evolution_lines(gamemaster):
    """Generate evolution lines dict from a gamemaster dict."""
    id_to_name = {mon['speciesId']: mon['speciesName'] for mon in gamemaster['pokemon']}

    families = {}
    for mon in gamemaster['pokemon']:
        if 'family' not in mon:
            continue
        fam_id = mon['family']['id']
        if fam_id not in families:
            families[fam_id] = []
        families[fam_id].append({
            'id': mon['speciesId'],
            'name': mon['speciesName'],
            'parent': mon['family'].get('parent'),
            'evolutions': mon['family'].get('evolutions', []),
        })

    def build_lines(members):
        roots = [m for m in members if not m['parent']]
        id_map = {m['id']: m for m in members}
        lines = []

        visited = set()

        def traverse(species_id, current_line):
            if species_id in visited:
                return False
            visited.add(species_id)
            member = id_map.get(species_id)
            if not member:
                return False
            name = id_to_name.get(species_id, species_id)
            current_line = current_line + [name]
            evos = member['evolutions']
            if not evos:
                lines.append(current_line)
            else:
                any_traversed = False
                for evo_id in evos:
                    if traverse(evo_id, current_line):
                        any_traversed = True
                    else:
                        # An already-visited LEAF evolution still ends this
                        # path: a final shared by several roots (Burmy →
                        # Mothim) must map every root, not only the first
                        # one walked. Non-leaf visited evolutions stay
                        # blocked — that's the cycle guard.
                        evo = id_map.get(evo_id)
                        if (evo_id in visited and evo is not None
                                and not evo['evolutions']):
                            evo_name = id_to_name.get(evo_id, evo_id)
                            lines.append(current_line + [evo_name])
                            any_traversed = True
                if not any_traversed:
                    # All evolutions were cyclic/missing — treat as leaf
                    lines.append(current_line)
            return True

        for root in roots:
            traverse(root['id'], [])
        return lines

    evolution_lines = {}
    for fam_id, members in families.items():
        for line in build_lines(members):
            if not line:
                continue
            final = line[-1]
            if final in evolution_lines:
                # Final reachable along several paths: merge pre-evo
                # members (first-seen order); the final stays last.
                existing = evolution_lines[final]
                merged = existing[:-1] + [m for m in line[:-1]
                                          if m not in existing]
                evolution_lines[final] = merged + [final]
            else:
                evolution_lines[final] = line

    return evolution_lines


def save_evolution_lines(evolution_lines):
    """Save evolution lines to cache dir atomically (temp + os.replace)."""
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        tmp = CACHED_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(evolution_lines, indent=2))
        os.replace(tmp, CACHED_PATH)
        logger.info("Saved %d evolution lines to cache.", len(evolution_lines))
    except Exception:
        logger.exception("Could not save evolution lines")


def load_evolution_lines():
    """Load evolution lines — from cache if available, else bundled."""
    if CACHED_PATH.exists():
        try:
            return json.loads(CACHED_PATH.read_text())
        except Exception:
            logger.exception("Could not load cached evolution lines")
    # Fall back to bundled
    try:
        return json.loads(BUNDLED_PATH.read_text())
    except Exception:
        logger.exception("Could not load bundled evolution lines")
        return {}
