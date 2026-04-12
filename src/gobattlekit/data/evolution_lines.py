#!/usr/bin/env python
"""
Evolution line generation and loading.
Generates from gamemaster JSON, caches to disk.
"""
import json
from pathlib import Path
from .fetcher import CACHE_DIR

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
                return
            visited.add(species_id)
            member = id_map.get(species_id)
            if not member:
                return
            name = id_to_name.get(species_id, species_id)
            current_line = current_line + [name]
            evos = member['evolutions']
            if not evos:
                lines.append(current_line)
            else:
                for evo_id in evos:
                    traverse(evo_id, current_line)

        for root in roots:
            traverse(root['id'], [])
        return lines

    evolution_lines = {}
    for fam_id, members in families.items():
        for line in build_lines(members):
            if line:
                final = line[-1]
                evolution_lines[final] = line

    return evolution_lines


def save_evolution_lines(evolution_lines):
    """Save evolution lines to cache dir."""
    try:
        CACHE_DIR.mkdir(exist_ok=True, parents=True)
        CACHED_PATH.write_text(json.dumps(evolution_lines, indent=2))
        print(f"Saved {len(evolution_lines)} evolution lines to cache.")
    except Exception as e:
        print(f"Could not save evolution lines: {e}")


def load_evolution_lines():
    """Load evolution lines — from cache if available, else bundled."""
    if CACHED_PATH.exists():
        try:
            return json.loads(CACHED_PATH.read_text())
        except Exception as e:
            print(f"Could not load cached evolution lines: {e}")
    # Fall back to bundled
    try:
        return json.loads(BUNDLED_PATH.read_text())
    except Exception as e:
        print(f"Could not load bundled evolution lines: {e}")
        return {}
