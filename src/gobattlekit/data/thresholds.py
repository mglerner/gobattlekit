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
            'The Good (105.38A, 138.6D, 140HP)': {
                'attack': 105.38, 'defense': 138.6, 'stamina': 140},
            'Premium (105.87A, 138.64D, 140HP)': {
                'attack': 105.87, 'defense': 138.64, 'stamina': 140},
            'Mirror Slayer (108A)': {
                'attack': 108, 'defense': 0, 'stamina': 0},
        },
    },
    'Walrein': {
        'Great': {
            'GOD TIER (114.46A, 114.75D, 148HP)': {
                'attack': 114.46, 'defense': 114.75, 'stamina': 148},
            'Azu Slayer (112.06A, 114.75D, 151HP)': {
                'attack': 112.06, 'defense': 114.75, 'stamina': 151},
        },
        'Ultra': {
            'Mirror HP (145.28A, 145D, 201HP)': {
                'attack': 145.28, 'defense': 145, 'stamina': 201},
            'Best (147.45A, 145.3D, 197HP)': {
                'attack': 147.45, 'defense': 145.3, 'stamina': 197},
        },
    },
    'Azumarill': {
        'Great': {
            'Medi Wall (137.64D)': {
                'attack': 0, 'defense': 137.64, 'stamina': 0},
            'Min (135.78D, 192HP)': {
                'attack': 0, 'defense': 135.78, 'stamina': 192},
            'General (132.8D, 187HP)': {
                'attack': 0, 'defense': 132.8, 'stamina': 187},
        },
    },
    'Stunfisk (Galarian)': {
        'Great': {
            'High Bulk (99A, 124.75D, 174HP)': {
                'attack': 99, 'defense': 124.75, 'stamina': 174},
            'Mirror Slayer (101.79A, 127.34D)': {
                'attack': 101.79, 'defense': 127.34, 'stamina': 0},
            'Bulk Mirror (101.79A, 124.75D, 172HP)': {
                'attack': 101.79, 'defense': 124.75, 'stamina': 172},
        },
    },
    'Registeel': {
        'Great': {
            'Raid Only (186.7D, 127HP)': {
                'attack': 0, 'defense': 186.7, 'stamina': 127},
            'Trade Only (190.09D, 129HP)': {
                'attack': 0, 'defense': 190.09, 'stamina': 129},
        },
        'Ultra': {
            'Raid Only (240.5D, 165HP)': {
                'attack': 0, 'defense': 240.5, 'stamina': 165},
            'Trade Only (244.4D, 167HP)': {
                'attack': 0, 'defense': 244.4, 'stamina': 167},
        },
    },
    'Trevenant': {
        'Great': {
            'Best (124A, 105.8D, 128HP)': {
                'attack': 124, 'defense': 105.8, 'stamina': 128},
            'Next (124A, 105.8D, 125HP)': {
                'attack': 124, 'defense': 105.8, 'stamina': 125},
        },
        'Ultra': {
            'Atk (168.7A, 129D, 167HP)': {
                'attack': 168.7, 'defense': 129, 'stamina': 167},
        },
    },
    'Corviknight': {
        'Great': {
            'Anni 1-1 (134.61D)': {
                'attack': 0, 'defense': 134.61, 'stamina': 0},
            'Cresselia (134.55D)': {
                'attack': 0, 'defense': 134.55, 'stamina': 0},
            'Dig Atk (110A)': {
                'attack': 110, 'defense': 0, 'stamina': 0},
        },
    },
    'Lickitung': {
        'Great': {
            'Good (96.36A, 125.94D, 183HP)': {
                'attack': 96.36, 'defense': 125.94, 'stamina': 183},
            'Atk (97.7A, 125.94D, 183HP)': {
                'attack': 97.7, 'defense': 125.94, 'stamina': 183},
            'Budget (97A, 125.1D, 181HP)': {
                'attack': 97, 'defense': 125.1, 'stamina': 181},
        },
    },
    'Obstagoon': {
        'Great': {
            'S.Premium (115.5A, 123.56D, 137HP)': {
                'attack': 115.5, 'defense': 123.56, 'stamina': 137},
            'Premium (115A, 123.3D, 135HP)': {
                'attack': 115, 'defense': 123.3, 'stamina': 135},
            'Bulk (126D, 137HP)': {
                'attack': 0, 'defense': 126, 'stamina': 137},
        },
        'Ultra': {
            'Unicorn (148A, 166.8D, 172HP)': {
                'attack': 148, 'defense': 166.8, 'stamina': 172},
            'Gen Atk (146.95A, 163.8D, 172HP)': {
                'attack': 146.95, 'defense': 163.8, 'stamina': 172},
        },
    },
}
