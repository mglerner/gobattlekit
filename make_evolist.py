#!/usr/bin/env python
import json
from pathlib import Path

gm = json.loads((Path.home() / 'Documents/gobattlekit_cache/gamemaster.json').read_text())

# Build lookup: speciesId -> speciesName
id_to_name = {mon['speciesId']: mon['speciesName'] for mon in gm['pokemon']}

# Build family groups: family_id -> list of members
families = {}
for mon in gm['pokemon']:
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
    """Build all evolution lines for a family as lists of speciesNames."""
    roots = [m for m in members if not m['parent']]
    id_map = {m['id']: m for m in members}

    lines = []

    def traverse(species_id, current_line):
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

# Build the full dict: final_form -> full_line
evolution_lines = {}
for fam_id, members in families.items():
    for line in build_lines(members):
        if len(line) >= 1:
            final = line[-1]
            evolution_lines[final] = line

# Spot-check against hand-curated data
hand_curated = {
    'Medicham': ['Meditite', 'Medicham'],
    'Walrein': ['Spheal', 'Sealeo', 'Walrein'],
    'Azumarill': ['Azurill', 'Marill', 'Azumarill'],
    'Trevenant': ['Phantump', 'Trevenant'],
    'Obstagoon': ['Zigzagoon (Galarian)', 'Linoone (Galarian)', 'Obstagoon'],
    'Slowbro (Galarian)': ['Slowpoke (Galarian)', 'Slowbro (Galarian)'],
    'Slowking (Galarian)': ['Slowpoke (Galarian)', 'Slowking (Galarian)'],
    'Annihilape': ['Mankey', 'Primeape', 'Annihilape'],
    'Golem (Alolan)': ['Geodude (Alolan)', 'Graveler (Alolan)', 'Golem (Alolan)'],
    'Sandslash (Alolan)': ['Sandshrew (Alolan)', 'Sandslash (Alolan)'],
    'Marowak (Alolan)': ['Cubone', 'Marowak (Alolan)'],
    'Corviknight': ['Rookidee', 'Corvisquire', 'Corviknight'],
    'Greninja': ['Froakie', 'Frogadier', 'Greninja'],
    'Decidueye': ['Rowlet', 'Dartrix', 'Decidueye'],
    'Runerigus': ['Yamask (Galarian)', 'Runerigus'],
    'Cofagrigus': ['Yamask', 'Cofagrigus'],
    'Froslass': ['Snorunt', 'Froslass'],
    'Altaria': ['Swablu', 'Altaria'],
    'Chesnaught': ['Chespin', 'Quilladin', 'Chesnaught'],
}

print("=== Spot Check ===")
all_pass = True
for final, expected in sorted(hand_curated.items()):
    got = evolution_lines.get(final)
    match = '✓' if got == expected else '✗'
    if got != expected:
        all_pass = False
    print(f'{match} {final}')
    if got != expected:
        print(f'  expected: {expected}')
        print(f'  got:      {got}')

print()
if all_pass:
    print("All spot checks passed!")
else:
    print("Some spot checks failed — review before writing JSON.")

# Write JSON
output_path = Path('src/gobattlekit/data/evolution_lines.json')
output_path.parent.mkdir(exist_ok=True, parents=True)
output_path.write_text(json.dumps(evolution_lines, indent=2))
print(f"Wrote {len(evolution_lines)} evolution lines to {output_path}")    
