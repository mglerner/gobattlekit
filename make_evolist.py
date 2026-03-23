#!/usr/bin/env python
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from gobattlekit.data.evolution_lines import generate_evolution_lines

gm = json.loads((Path.home() / 'Documents/gobattlekit_cache/gamemaster.json').read_text())
evolution_lines = generate_evolution_lines(gm)


# Spot check
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

output_path = Path('src/gobattlekit/data/evolution_lines.json')
output_path.write_text(json.dumps(evolution_lines, indent=2))
print(f"Wrote {len(evolution_lines)} evolution lines to {output_path}")
