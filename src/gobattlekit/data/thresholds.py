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

    # New from RS_INFO
    'Noctowl': ['Hoothoot', 'Noctowl'],
    'Chesnaught': ['Chespin', 'Quilladin', 'Chesnaught'],
    'Greninja': ['Froakie', 'Frogadier', 'Greninja'],
    'Toxapex': ['Mareanie', 'Toxapex'],
    'Toxicroak': ['Croagunk', 'Toxicroak'],
    'Froslass': ['Snorunt', 'Froslass'],
    'Decidueye': ['Rowlet', 'Dartrix', 'Decidueye'],
    'Annihilape': ['Mankey', 'Primeape', 'Annihilape'],
    'Tapu Fini': ['Tapu Fini'],
    'Slowbro': ['Slowpoke', 'Slowbro'],
    'Slowbro (Galarian)': ['Slowpoke (Galarian)', 'Slowbro (Galarian)'],
    'Slowking (Galarian)': ['Slowpoke (Galarian)', 'Slowking (Galarian)'],
    'Deoxys (Defense)': ['Deoxys (Defense)'],
    'Linoone (Galarian)': ['Zigzagoon (Galarian)', 'Linoone (Galarian)'],
    'Marowak (Alolan)': ['Cubone', 'Marowak (Alolan)'],
    'Sandslash (Alolan)': ['Sandshrew (Alolan)', 'Sandslash (Alolan)'],
    'Golem (Alolan)': ['Geodude (Alolan)', 'Graveler (Alolan)', 'Golem (Alolan)'],
}

DEFAULT_THRESHOLDS = {
    'Jumpluff': {
        'Great': {
            'Top SP (157.31D)': {
                'attack': 0, 'defense': 157.31, 'stamina': 0, 'onlytop': 12},
            'Atk+Def (97.6A, 156.3D)': {
                'attack': 97.6, 'defense': 156.3, 'stamina': 0},
            'Atk+Bulk (97.6A, 150D, 151HP)': {
                'attack': 97.6, 'defense': 150, 'stamina': 151},
        },
    },
    'Walrein': {
        'Great': {
            'GOD TIER (114.46A, 114.75D, 148HP)': {
                'attack': 114.46, 'defense': 114.75, 'stamina': 148},
            'Azu Slayer (112.06A, 114.75D, 151HP)': {
                'attack': 112.06, 'defense': 114.75, 'stamina': 151},
            'All Atk BPs (114.46A, 113D, 148HP)': {
                'attack': 114.46, 'defense': 113, 'stamina': 148},
        },
        'Ultra': {
            'Mirror HP (145.28A, 145D, 201HP)': {
                'attack': 145.28, 'defense': 145, 'stamina': 201},
            'Mirror Def (145.28A, 147D, 199HP)': {
                'attack': 145.28, 'defense': 147, 'stamina': 199},
            'Best (147.45A, 145.3D, 197HP)': {
                'attack': 147.45, 'defense': 145.3, 'stamina': 197},
        },
        'Master': {
            'Best (15A, 15D, 15HP)': {
                'attack': 15, 'defense': 15, 'stamina': 15},
            'Good (15A, 14D, 13HP)': {
                'attack': 15, 'defense': 14, 'stamina': 13},
            'Min (13A, 12D, 12HP)': {
                'attack': 13, 'defense': 12, 'stamina': 12},
        },
    },
    'Deoxys (Defense)': {
        'Great': {
            'Best (101.95A, 221D, 98HP)': {
                'attack': 101.95, 'defense': 221, 'stamina': 98},
            'Lanturn BPs (101.95A, 220.18D, 95HP)': {
                'attack': 101.95, 'defense': 220.18, 'stamina': 95},
            'SwagMan+ (100.78A, 220.18D, 95HP)': {
                'attack': 100.78, 'defense': 220.18, 'stamina': 95},
            'Mirror (100.78A, 98HP)': {
                'attack': 100.78, 'defense': 0, 'stamina': 98},
        },
        'Ultra': {
            'BB Umb (132.81A, 284D, 122HP)': {
                'attack': 132.81, 'defense': 284, 'stamina': 122},
            'Regi+TF (132.28A, 126HP)': {
                'attack': 132.28, 'defense': 0, 'stamina': 126},
            'Umb+TF+Regi (131.8A, 126HP)': {
                'attack': 131.8, 'defense': 0, 'stamina': 126},
            'Atk BP (132.28A)': {
                'attack': 132.28, 'defense': 0, 'stamina': 0},
        },
    },
    'Venusaur': {
        'Great': {
            'Fross Slay+Def (122.5A, 121.13D, 122HP)': {
                'attack': 122.5, 'defense': 121.13, 'stamina': 122},
            'Fross Slay+OKDef (122.5A, 117.88D, 122HP)': {
                'attack': 122.5, 'defense': 117.88, 'stamina': 122},
            'Big Bulk (121.13D, 123HP)': {
                'attack': 0, 'defense': 121.13, 'stamina': 123},
            'Shadow Bulk (120.46D, 122HP)': {
                'attack': 0, 'defense': 120.46, 'stamina': 122},
        },
        'Ultra': {
            'GFisk Slay (159.2A, 157.25D, 152HP)': {
                'attack': 159.2, 'defense': 157.25, 'stamina': 152},
            'Huge Def (160.82D, 156HP)': {
                'attack': 0, 'defense': 160.82, 'stamina': 156},
            'R1 Bulk (158.05D, 156HP)': {
                'attack': 0, 'defense': 158.05, 'stamina': 156},
            'Shadow Blend (161.59A, 155.28D, 153HP)': {
                'attack': 161.59, 'defense': 155.28, 'stamina': 153},
        },
    },
    'Dewgong': {
        'Great': {
            'MaxDef Umb (102.89A, 131.7D)': {
                'attack': 102.89, 'defense': 131.7, 'stamina': 0},
            'R1Umb Bulk (101.79A, 136.81D, 150HP)': {
                'attack': 101.79, 'defense': 136.81, 'stamina': 150},
            'R1Umb+Def (101.79A, 138.28D, 150HP)': {
                'attack': 101.79, 'defense': 138.28, 'stamina': 150},
        },
    },
    'Sandslash': {
        'Great': {
            'General (121A, 120D)': {
                'attack': 121, 'defense': 120, 'stamina': 0},
        },
    },
    'Sandslash (Alolan)': {
        'Great': {
            'Hi Atk (115.31A, 128.92D, 119HP)': {
                'attack': 115.31, 'defense': 128.92, 'stamina': 119},
            'Super Hi Atk (118.24A, 127.59D, 118HP)': {
                'attack': 118.24, 'defense': 127.59, 'stamina': 118},
        },
        'Ultra': {
            'Def Focus (149.14A, 173.07D)': {
                'attack': 149.14, 'defense': 173.07, 'stamina': 0},
            'Atk Focus (154.26A, 168D)': {
                'attack': 154.26, 'defense': 168, 'stamina': 0},
        },
    },
    'Whimsicott': {
        'Great': {
            'Mod Atk (121.26A, 132.25D)': {
                'attack': 121.26, 'defense': 132.25, 'stamina': 0},
            'Slight Atk (119.47A, 132.25D)': {
                'attack': 119.47, 'defense': 132.25, 'stamina': 0},
            'A9 Slay (121.87A, 132.25D)': {
                'attack': 121.87, 'defense': 132.25, 'stamina': 0},
            'Licki Slay (122.81A, 132.25D)': {
                'attack': 122.81, 'defense': 132.25, 'stamina': 0},
        },
    },
    'Swampert': {
        'Great': {
            'Def (110D)': {
                'attack': 0, 'defense': 110, 'stamina': 0},
            'Atk (121.6A, 108D)': {
                'attack': 121.6, 'defense': 108, 'stamina': 0},
        },
    },
    'Registeel': {
        'Great': {
            'Raid Only (186.7D, 127HP)': {
                'attack': 0, 'defense': 186.7, 'stamina': 127},
            'Trade (190.09D, 129HP)': {
                'attack': 0, 'defense': 190.09, 'stamina': 129},
            'Trade+ (191.97D, 129HP)': {
                'attack': 0, 'defense': 191.97, 'stamina': 129},
        },
        'Ultra': {
            'Raid Only (240.5D, 165HP)': {
                'attack': 0, 'defense': 240.5, 'stamina': 165},
            'Trade (244.4D, 167HP)': {
                'attack': 0, 'defense': 244.4, 'stamina': 167},
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
            'Slight Atk (92A, 132.8D, 187HP)': {
                'attack': 92, 'defense': 132.8, 'stamina': 187},
        },
    },
    'Araquanid': {
        'Great': {
            'S-Drap Atk (99.02A)': {
                'attack': 99.02, 'defense': 0, 'stamina': 0},
            'Hi Viggy Atk (99.2A)': {
                'attack': 99.2, 'defense': 0, 'stamina': 0},
            'Best Walrus Atk (99.93A)': {
                'attack': 99.93, 'defense': 0, 'stamina': 0},
            'DD Def Min (163.77D)': {
                'attack': 0, 'defense': 163.77, 'stamina': 0},
            'DD Def Max (165.21D)': {
                'attack': 0, 'defense': 165.21, 'stamina': 0},
            'HP Min (134HP)': {
                'attack': 0, 'defense': 0, 'stamina': 134},
            'HP Max (136HP)': {
                'attack': 0, 'defense': 0, 'stamina': 136},
            'General (99.2A, 165.2D, 134HP)': {
                'attack': 99.2, 'defense': 165.2, 'stamina': 134},
        },
    },
    'Golem (Alolan)': {
        'Great': {
            'General (124.79A)': {
                'attack': 124.79, 'defense': 0, 'stamina': 0},
            'Min (123.93A)': {
                'attack': 123.93, 'defense': 0, 'stamina': 0},
            'Best (126A, 118D)': {
                'attack': 126, 'defense': 118, 'stamina': 0},
        },
    },
    'Marowak (Alolan)': {
        'Great': {
            'S-AWak MinAtk (110.5A, 141.49D)': {
                'attack': 110.5, 'defense': 141.49, 'stamina': 0},
            'S-AWak HiAtk (111.85A, 141.49D)': {
                'attack': 111.85, 'defense': 141.49, 'stamina': 0},
        },
    },
    'Linoone (Galarian)': {
        'Great': {
            'Swamp/Cash (112.87A, 144HP)': {
                'attack': 112.87, 'defense': 0, 'stamina': 144},
            'Drap CMP (114A, 144HP)': {
                'attack': 114, 'defense': 0, 'stamina': 144},
            'Diggers (110.11D, 144HP)': {
                'attack': 0, 'defense': 110.11, 'stamina': 144},
            'SwagAtk (111.14D, 144HP)': {
                'attack': 0, 'defense': 111.14, 'stamina': 144},
            'Best (114A, 111.14D, 144HP)': {
                'attack': 114, 'defense': 111.14, 'stamina': 144},
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
            'Gen Atk+ (147.89A, 163.8D, 172HP)': {
                'attack': 147.89, 'defense': 163.8, 'stamina': 172},
            'Mirror (149.1A, 172D, 172HP)': {
                'attack': 149.1, 'defense': 172, 'stamina': 172},
            'Bulk (166.8D, 174HP)': {
                'attack': 0, 'defense': 166.8, 'stamina': 174},
        },
    },
    'Medicham': {
        'Great': {
            'The Good (105.38A, 138.6D, 140HP)': {
                'attack': 105.38, 'defense': 138.6, 'stamina': 140},
            'Premium (105.87A, 138.64D, 140HP)': {
                'attack': 105.87, 'defense': 138.64, 'stamina': 140},
            'BB (105.38A, 140.3D, 142HP)': {
                'attack': 105.38, 'defense': 140.3, 'stamina': 142},
            'Mirror Slay (108A, 137.64D)': {
                'attack': 108, 'defense': 137.64, 'stamina': 0},
        },
    },
    'Dedenne': {
        'Great': {
            'Basic (123.17A, 109D, 133HP)': {
                'attack': 123.17, 'defense': 109, 'stamina': 133},
            'Scrafty (123.17A, 109.86D, 133HP)': {
                'attack': 123.17, 'defense': 109.86, 'stamina': 133},
            'Atk+ (124.59A, 109D, 133HP)': {
                'attack': 124.59, 'defense': 109, 'stamina': 133},
            'Best (124.59A, 109.86D, 133HP)': {
                'attack': 124.59, 'defense': 109.86, 'stamina': 133},
            'Bulk (109.86D, 133HP)': {
                'attack': 0, 'defense': 109.86, 'stamina': 133},
        },
    },
    'Dunsparce': {
        'Great': {
            'Basic Bulk (110.63D, 185HP)': {
                'attack': 0, 'defense': 110.63, 'stamina': 185},
            'Premium Bulk (111.14D, 186HP)': {
                'attack': 0, 'defense': 111.14, 'stamina': 186},
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
            'Min Bulk (99A, 124.75D, 172HP)': {
                'attack': 99, 'defense': 124.75, 'stamina': 172},
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
    'Toxapex': {
        'Great': {
            'Hi Bulk (226.73D, 118HP)': {
                'attack': 0, 'defense': 226.73, 'stamina': 118},
            'Mirror/HP (219D, 121HP)': {
                'attack': 0, 'defense': 219, 'stamina': 121},
            'Licki Slay (93A, 118HP)': {
                'attack': 93, 'defense': 0, 'stamina': 118},
        },
    },
    'Toxicroak': {
        'Great': {
            'General (136A, 92.51D, 131HP)': {
                'attack': 136, 'defense': 92.51, 'stamina': 131},
            'Discord (136.6A, 88.57D, 134HP)': {
                'attack': 136.6, 'defense': 88.57, 'stamina': 134},
            'Bork (136.6A, 82D, 134HP)': {
                'attack': 136.6, 'defense': 82, 'stamina': 134},
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
    'Noctowl': {
        'Great': {
            'Slight Atk (104.23A, 118.27D, 171HP)': {
                'attack': 104.23, 'defense': 118.27, 'stamina': 171},
            'Azu Slay (105.2A, 117.58D, 168HP)': {
                'attack': 105.2, 'defense': 117.58, 'stamina': 168},
            'A9 Slay (106.36A, 172HP)': {
                'attack': 106.36, 'defense': 0, 'stamina': 172},
        },
    },
    'Chesnaught': {
        'Great': {
            'Bulk (122.21D, 127HP)': {
                'attack': 0, 'defense': 122.21, 'stamina': 127},
            'Fross Slay (121.89A, 117.7D, 125HP)': {
                'attack': 121.89, 'defense': 117.7, 'stamina': 125},
            'Fross Slay Def (121.89A, 122.21D, 122HP)': {
                'attack': 121.89, 'defense': 122.21, 'stamina': 122},
        },
    },
    'Altaria': {
        'Great': {
            'Trev Slay (102.97A, 149.02D, 139HP)': {
                'attack': 102.97, 'defense': 149.02, 'stamina': 139},
            'Bulk+Trev (101.95A, 151.63D, 139HP)': {
                'attack': 101.95, 'defense': 151.63, 'stamina': 139},
            'Bulk (153.95D, 139HP)': {
                'attack': 0, 'defense': 153.95, 'stamina': 139},
        },
    },
    'Cofagrigus': {
        'Great': {
            'General (109A, 162D, 106HP)': {
                'attack': 109, 'defense': 162, 'stamina': 106},
            'Best (111.32A, 164.56D, 106HP)': {
                'attack': 111.32, 'defense': 164.56, 'stamina': 106},
        },
        'Ultra': {
            'General (145.21A, 208D, 138HP)': {
                'attack': 145.21, 'defense': 208, 'stamina': 138},
        },
    },
    'Runerigus': {
        'Great': {
            'General (109A, 162D, 106HP)': {
                'attack': 109, 'defense': 162, 'stamina': 106},
            'Best (111.32A, 164.56D, 106HP)': {
                'attack': 111.32, 'defense': 164.56, 'stamina': 106},
        },
        'Ultra': {
            'General (145.21A, 208D, 138HP)': {
                'attack': 145.21, 'defense': 208, 'stamina': 138},
        },
    },
    'Slowbro': {
        'Great': {
            'Bulk (118.4D, 144HP)': {
                'attack': 0, 'defense': 118.4, 'stamina': 144},
        },
    },
    'Slowbro (Galarian)': {
        'Great': {
            'Mirror (118.48A, 108.83D, 144HP)': {
                'attack': 118.48, 'defense': 108.83, 'stamina': 144},
            'Bulk (109D, 146HP)': {
                'attack': 0, 'defense': 109, 'stamina': 146},
            'General (110A, 100D, 144HP)': {
                'attack': 110, 'defense': 100, 'stamina': 144},
        },
    },
    'Slowking (Galarian)': {
        'Great': {
            'Mirror Slay (116.7A, 117.5D, 138HP)': {
                'attack': 116.7, 'defense': 117.5, 'stamina': 138},
        },
    },
    'Tapu Fini': {
        'Great': {
            'Beat Medi (153.91D, 110HP)': {
                'attack': 0, 'defense': 153.91, 'stamina': 110},
            'General (153.91D, 107HP)': {
                'attack': 0, 'defense': 153.91, 'stamina': 107},
            'Thrift (153.91D, 105HP)': {
                'attack': 0, 'defense': 153.91, 'stamina': 105},
        },
        'Ultra': {
            'Hi HP (198.9D, 142HP)': {
                'attack': 0, 'defense': 198.9, 'stamina': 142},
            'Poli+Auro (147.59A, 198.9D, 139HP)': {
                'attack': 147.59, 'defense': 198.9, 'stamina': 139},
            'A9 Atk (149.39A, 198.9D, 139HP)': {
                'attack': 149.39, 'defense': 198.9, 'stamina': 139},
            'General (198.9D, 139HP)': {
                'attack': 0, 'defense': 198.9, 'stamina': 139},
        },
    },
    'Greninja': {
        'Great': {
            'Bulk (99.61D, 115HP)': {
                'attack': 0, 'defense': 99.61, 'stamina': 115},
            'Azu Slay (140.08A, 99.36D, 111HP)': {
                'attack': 140.08, 'defense': 99.36, 'stamina': 111},
            'Hi Atk (139.04A)': {
                'attack': 139.04, 'defense': 0, 'stamina': 0},
            'V.Hi Atk (143.3A)': {
                'attack': 143.3, 'defense': 0, 'stamina': 0},
            'Max Atk (144.6A)': {
                'attack': 144.6, 'defense': 0, 'stamina': 0},
        },
        'Ultra': {
            'Bulk (130.62D, 149HP)': {
                'attack': 0, 'defense': 130.62, 'stamina': 149},
            'Bulk+ (132.53D, 149HP)': {
                'attack': 0, 'defense': 132.53, 'stamina': 149},
        },
    },
    'Dubwool': {
        'Great': {
            'Hi Bulk (141.6D, 128HP)': {
                'attack': 0, 'defense': 141.6, 'stamina': 128},
        },
        'Ultra': {
            'Nearly Hundo (178.3D, 160HP)': {
                'attack': 0, 'defense': 178.3, 'stamina': 160},
        },
    },
    'Quagsire': {
        'Great': {
            'Non-Shadow (112D, 163HP)': {
                'attack': 0, 'defense': 112, 'stamina': 163},
            'Shadow Bulk (112.68D, 163HP)': {
                'attack': 0, 'defense': 112.68, 'stamina': 163},
            'Shadow Atk (110A, 110.26D, 163HP)': {
                'attack': 110, 'defense': 110.26, 'stamina': 163},
            'Carbink Slay (111.89A, 108D, 162HP)': {
                'attack': 111.89, 'defense': 108, 'stamina': 162},
        },
    },
    'Clodsire': {
        'Great': {
            'Bulk1 (119.51D, 212HP)': {
                'attack': 0, 'defense': 119.51, 'stamina': 212},
            'Bulk2 (121.23D, 210HP)': {
                'attack': 0, 'defense': 121.23, 'stamina': 210},
            'Atk (96.5A, 117D, 199HP)': {
                'attack': 96.5, 'defense': 117, 'stamina': 199},
            'Top 20 (all stats)': {
                'attack': 0, 'defense': 0, 'stamina': 0, 'onlytop': 20},
        },
    },
    'Charjabug': {
        'Great': {
            'Mirror (116.27A, 136.09D, 120HP)': {
                'attack': 116.27, 'defense': 136.09, 'stamina': 120},
            'Mirror CMP (114.51A, 136.09D, 124HP)': {
                'attack': 114.51, 'defense': 136.09, 'stamina': 124},
        },
    },
    'Froslass': {
        'Great': {
            'Premium CMP (121.6A, 113D, 131HP)': {
                'attack': 121.6, 'defense': 113, 'stamina': 131},
            'General Bulk (113D, 131HP)': {
                'attack': 0, 'defense': 113, 'stamina': 131},
            'Hi Atk (123.12A, 113D, 127HP)': {
                'attack': 123.12, 'defense': 113, 'stamina': 127},
        },
    },
    'Decidueye': {
        'Great': {
            'General (115.29D, 118HP)': {
                'attack': 0, 'defense': 115.29, 'stamina': 118},
            'General LoDef (113.7D, 120HP)': {
                'attack': 0, 'defense': 113.7, 'stamina': 120},
            'Astonish (115.52D, 118HP)': {
                'attack': 0, 'defense': 115.52, 'stamina': 118},
            'Astonish HiAtk (127.61A, 115.52D, 118HP)': {
                'attack': 127.61, 'defense': 115.52, 'stamina': 118},
            'Astonish HiDef (116D, 118HP)': {
                'attack': 0, 'defense': 116, 'stamina': 118},
            'Astonish HiHP (113.7D, 120HP)': {
                'attack': 0, 'defense': 113.7, 'stamina': 120},
            'Leafage Atk (127.61A, 115.29D, 118HP)': {
                'attack': 127.61, 'defense': 115.29, 'stamina': 118},
            'Leafage+Poli (127.61A, 115.29D, 119HP)': {
                'attack': 127.61, 'defense': 115.29, 'stamina': 119},
            'Leafage+Zong (127.61A, 113.7D, 118HP)': {
                'attack': 127.61, 'defense': 113.7, 'stamina': 118},
            'Leafage+Dnair (127.61A, 116.71D, 118HP)': {
                'attack': 127.61, 'defense': 116.71, 'stamina': 118},
        },
    },
    'Lanturn': {
        'Great': {
            'General Bulk (105.5D, 196HP)': {
                'attack': 0, 'defense': 105.5, 'stamina': 196},
            'Premium Bulk (106.04D, 192HP)': {
                'attack': 0, 'defense': 106.04, 'stamina': 192},
        },
    },
    'Annihilape': {
        'Great': {
            'General (122.94A, 106.17D, 136HP)': {
                'attack': 122.94, 'defense': 106.17, 'stamina': 136},
            'Licki Slay (127.23A, 102.26D, 132HP)': {
                'attack': 127.23, 'defense': 102.26, 'stamina': 132},
            'Licki Slay Bulk (127.23A, 102.55D, 132HP)': {
                'attack': 127.23, 'defense': 102.55, 'stamina': 132},
        },
        'Ultra': {
            'General (159.7A, 134.5D, 178HP)': {
                'attack': 159.7, 'defense': 134.5, 'stamina': 178},
        },
    },
    'Goodra': {
        'Great': {
            'Swag (135.72D, 117HP)': {
                'attack': 0, 'defense': 135.72, 'stamina': 117},
            'Swag Licki (122A, 125.2D, 115HP)': {
                'attack': 122, 'defense': 125.2, 'stamina': 115},
        },
    },
    'Carbink': {
        'Great': {
            'Premium Bulk (81.38A, 247.67D, 128HP)': {
                'attack': 81.38, 'defense': 247.67, 'stamina': 128},
            'Slight Atk (85.81A, 239.06D, 124HP)': {
                'attack': 85.81, 'defense': 239.06, 'stamina': 124},
            'General (82.83A, 246D, 124HP)': {
                'attack': 82.83, 'defense': 246, 'stamina': 124},
        },
    },
    'Corviknight': {
        'Great': {
            'Anni 1-1 (134.61D)': {
                'attack': 0, 'defense': 134.61, 'stamina': 0},
            'Carbink (130.7D)': {
                'attack': 0, 'defense': 130.7, 'stamina': 0},
            'Cresselia (134.55D)': {
                'attack': 0, 'defense': 134.55, 'stamina': 0},
            'G-Cors (130.34D)': {
                'attack': 0, 'defense': 130.34, 'stamina': 0},
            'Mandi (132.17D)': {
                'attack': 0, 'defense': 132.17, 'stamina': 0},
            'Dig Atk (110A)': {
                'attack': 110, 'defense': 0, 'stamina': 0},
            'Drap Atk (111.4A)': {
                'attack': 111.4, 'defense': 0, 'stamina': 0},
            'S-ASlash Atk (124A)': {
                'attack': 124, 'defense': 0, 'stamina': 0},
            'Pex Atk (112.54A)': {
                'attack': 112.54, 'defense': 0, 'stamina': 0},
            'Azu 1-1 Atk (108.75A)': {
                'attack': 108.75, 'defense': 0, 'stamina': 0},
        },
    },
}
