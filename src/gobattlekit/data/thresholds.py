#!/usr/bin/env python
"""
Default IV thresholds for common Great League mons.
Sourced from PvP IV deep dives (primarily RyanSwag/GamePress).

Each entry is:
{
    'Species Name': {
        'Great': {
            'Target Name': {
                'attack': float,  # minimum attack stat (0 = don't care)
                'defense': float,
                'stamina': int,
            }
        }
    }
}

A value of 0 means "don't care" for that stat.
"""

EVOLUTION_LINES = {
    # Single-stage or no pre-evos needed
    'Registeel': ['Registeel'],
    'Lickitung': ['Lickitung'],
    'Stunfisk (Galarian)': ['Stunfisk (Galarian)'],
    'Tapu Fini': ['Tapu Fini'],
    'Deoxys (Defense)': ['Deoxys (Defense)'],
    'Carbink': ['Carbink'],
    'Dunsparce': ['Dunsparce'],
    'Dedenne': ['Dedenne'],

    # Two-stage
    'Medicham': ['Meditite', 'Medicham'],
    'Walrein': ['Spheal', 'Sealeo', 'Walrein'],
    'Azumarill': ['Azurill', 'Marill', 'Azumarill'],
    'Trevenant': ['Phantump', 'Trevenant'],
    'Corviknight': ['Rookidee', 'Corvisquire', 'Corviknight'],
    'Whimsicott': ['Cottonee', 'Whimsicott'],
    'Dewgong': ['Seel', 'Dewgong'],
    'Sandslash': ['Sandshrew', 'Sandslash'],
    'Sandslash (Alolan)': ['Sandshrew', 'Sandslash (Alolan)'],
    'Swampert': ['Mudkip', 'Marshtomp', 'Swampert'],
    'Jumpluff': ['Hoppip', 'Skiploom', 'Jumpluff'],
    'Altaria': ['Swablu', 'Altaria'],
    'Toxapex': ['Mareanie', 'Toxapex'],
    'Toxicroak': ['Croagunk', 'Toxicroak'],
    'Araquanid': ['Dewpider', 'Araquanid'],
    'Quagsire': ['Wooper', 'Quagsire'],
    'Clodsire': ['Wooper (Paldean)', 'Clodsire'],
    'Noctowl': ['Hoothoot', 'Noctowl'],
    'Lanturn': ['Chinchou', 'Lanturn'],
    'Froslass': ['Snorunt', 'Froslass'],
    'Dubwool': ['Wooloo', 'Dubwool'],
    'Goodra': ['Goomy', 'Sliggoo', 'Goodra'],
    'Marowak (Alolan)': ['Cubone', 'Marowak (Alolan)'],
    'Cofagrigus': ['Yamask', 'Cofagrigus'],
    'Runerigus': ['Yamask (Galarian)', 'Runerigus'],
    'Slowbro': ['Slowpoke', 'Slowbro'],
    'Slowking': ['Slowpoke', 'Slowking'],
    'Slowbro (Galarian)': ['Slowpoke (Galarian)', 'Slowbro (Galarian)'],
    'Slowking (Galarian)': ['Slowpoke (Galarian)', 'Slowking (Galarian)'],
    'Charjabug': ['Grubbin', 'Charjabug'],
    'Vikavolt': ['Grubbin', 'Charjabug', 'Vikavolt'],

    # Three-stage
    'Venusaur': ['Bulbasaur', 'Ivysaur', 'Venusaur'],
    'Chesnaught': ['Chespin', 'Quilladin', 'Chesnaught'],
    'Greninja': ['Froakie', 'Frogadier', 'Greninja'],
    'Obstagoon': ['Zigzagoon (Galarian)', 'Linoone (Galarian)', 'Obstagoon'],
    'Decidueye': ['Rowlet', 'Dartrix', 'Decidueye'],
    'Annihilape': ['Mankey', 'Primeape', 'Annihilape'],
    'Golem (Alolan)': ['Geodude (Alolan)', 'Graveler (Alolan)', 'Golem (Alolan)'],
    'Corviknight': ['Rookidee', 'Corvisquire', 'Corviknight'],
}

DEFAULT_THRESHOLDS = {
    'Medicham': {
        'Great': {
            'The Good (105.38 Atk, 138.6 Def, 140 HP)': {
                'attack': 105.38, 'defense': 138.6, 'stamina': 140},
            'Premium Cut (105.87 Atk, 138.64 Def, 140 HP)': {
                'attack': 105.87, 'defense': 138.64, 'stamina': 140},
            'Mirror Slayer (108 Atk)': {
                'attack': 108, 'defense': 0, 'stamina': 0},
        },
    },
    'Walrein': {
        'Great': {
            'GOD TIER (114.46 Atk, 114.75 Def, 148 HP)': {
                'attack': 114.46, 'defense': 114.75, 'stamina': 148},
            'Azu Slayer (112.06 Atk, 114.75 Def, 151 HP)': {
                'attack': 112.06, 'defense': 114.75, 'stamina': 151},
        },
        'Ultra': {
            'Mirror Slayer HP (145.28 Atk, 145 Def, 201 HP)': {
                'attack': 145.28, 'defense': 145, 'stamina': 201},
            'Best of the Best (147.45 Atk, 145.3 Def, 197 HP)': {
                'attack': 147.45, 'defense': 145.3, 'stamina': 197},
        },
    },
    'Azumarill': {
        'Great': {
            'Medicham Consistency (137.64 Def)': {
                'attack': 0, 'defense': 137.64, 'stamina': 0},
            'Hits the Min (135.78 Def, 192 HP)': {
                'attack': 0, 'defense': 135.78, 'stamina': 192},
            'General (132.8 Def, 187 HP)': {
                'attack': 0, 'defense': 132.8, 'stamina': 187},
        },
    },
    'Stunfisk (Galarian)': {
        'Great': {
            'High Bulk (99 Atk, 124.75 Def, 174 HP)': {
                'attack': 99, 'defense': 124.75, 'stamina': 174},
            'Mirror Slayer (101.79 Atk, 127.34 Def)': {
                'attack': 101.79, 'defense': 127.34, 'stamina': 0},
            'Bulk Mirror Slayer (101.79 Atk, 124.75 Def, 172 HP)': {
                'attack': 101.79, 'defense': 124.75, 'stamina': 172},
        },
    },
    'Registeel': {
        'Great': {
            'Raid Only (186.7 Def, 127 HP)': {
                'attack': 0, 'defense': 186.7, 'stamina': 127},
            'Trade Only (190.09 Def, 129 HP)': {
                'attack': 0, 'defense': 190.09, 'stamina': 129},
        },
        'Ultra': {
            'Raid Only (240.5 Def, 165 HP)': {
                'attack': 0, 'defense': 240.5, 'stamina': 165},
            'Trade Only (244.4 Def, 167 HP)': {
                'attack': 0, 'defense': 244.4, 'stamina': 167},
        },
    },
    'Trevenant': {
        'Great': {
            'Best (124 Atk, 105.8 Def, 128 HP)': {
                'attack': 124, 'defense': 105.8, 'stamina': 128},
            'Next (124 Atk, 105.8 Def, 125 HP)': {
                'attack': 124, 'defense': 105.8, 'stamina': 125},
        },
        'Ultra': {
            'Atk (168.7 Atk, 129 Def, 167 HP)': {
                'attack': 168.7, 'defense': 129, 'stamina': 167},
        },
    },
    'Corviknight': {
        'Great': {
            'Annihilape 1-1 (134.61 Def)': {
                'attack': 0, 'defense': 134.61, 'stamina': 0},
            'Cresselia (134.55 Def)': {
                'attack': 0, 'defense': 134.55, 'stamina': 0},
            'Dig Atk (110 Atk)': {
                'attack': 110, 'defense': 0, 'stamina': 0},
        },
    },
    'Lickitung': {
        'Great': {
            'General Good (96.36 Atk, 125.94 Def, 183 HP)': {
                'attack': 96.36, 'defense': 125.94, 'stamina': 183},
            'Atk Focus (97.7 Atk, 125.94 Def, 183 HP)': {
                'attack': 97.7, 'defense': 125.94, 'stamina': 183},
            'Budget (97 Atk, 125.1 Def, 181 HP)': {
                'attack': 97, 'defense': 125.1, 'stamina': 181},
        },
    },
    'Obstagoon': {
        'Great': {
            'Super Premium (115.5 Atk, 123.56 Def, 137 HP)': {
                'attack': 115.5, 'defense': 123.56, 'stamina': 137},
            'Premium (115 Atk, 123.3 Def, 135 HP)': {
                'attack': 115, 'defense': 123.3, 'stamina': 135},
            'Bulk Focus (126 Def, 137 HP)': {
                'attack': 0, 'defense': 126, 'stamina': 137},
        },
        'Ultra': {
            'Unicorn (148 Atk, 166.8 Def, 172 HP)': {
                'attack': 148, 'defense': 166.8, 'stamina': 172},
            'General Atk (146.95 Atk, 163.8 Def, 172 HP)': {
                'attack': 146.95, 'defense': 163.8, 'stamina': 172},
        },
    },
}
    
