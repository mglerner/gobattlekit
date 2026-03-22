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
            'Top SP (157D)': {
                'attack': 0, 'defense': 157.31, 'stamina': 0, 'onlytop': 12},
            'Atk+Def (97.6A, 156D)': {
                'attack': 97.6, 'defense': 156.3, 'stamina': 0},
            'Atk+Bulk (97.6A, 150D, 151S)': {
                'attack': 97.6, 'defense': 150, 'stamina': 151},
        },
    },
    'Walrein': {
        'Great': {
            'GOD (114A, 114D, 148S)': {
                'attack': 114.46, 'defense': 114.75, 'stamina': 148},
            'Azu (112A, 114D, 151S)': {
                'attack': 112.06, 'defense': 114.75, 'stamina': 151},
            'All BPs (114A, 113D, 148S)': {
                'attack': 114.46, 'defense': 113, 'stamina': 148},
        },
        'Ultra': {
            'Mirror HP (145A, 145D, 201S)': {
                'attack': 145.28, 'defense': 145, 'stamina': 201},
            'Mirror Def (145A, 147D, 199S)': {
                'attack': 145.28, 'defense': 147, 'stamina': 199},
            'Best (147A, 145D, 197S)': {
                'attack': 147.45, 'defense': 145.3, 'stamina': 197},
        },
        'Master': {
            'Best (15/15/15)': {
                'attack': 15, 'defense': 15, 'stamina': 15},
            'Good (15/14/13)': {
                'attack': 15, 'defense': 14, 'stamina': 13},
            'Min (13/12/12)': {
                'attack': 13, 'defense': 12, 'stamina': 12},
        },
    },
    'Deoxys (Defense)': {
        'Great': {
            'Best (102A, 221D, 98S)': {
                'attack': 101.95, 'defense': 221, 'stamina': 98},
            'Lanturn (102A, 220D, 95S)': {
                'attack': 101.95, 'defense': 220.18, 'stamina': 95},
            'SwagMan (101A, 220D, 95S)': {
                'attack': 100.78, 'defense': 220.18, 'stamina': 95},
            'Mirror (101A, 98S)': {
                'attack': 100.78, 'defense': 0, 'stamina': 98},
        },
        'Ultra': {
            'BB Umb (133A, 284D, 122S)': {
                'attack': 132.81, 'defense': 284, 'stamina': 122},
            'Regi+TF (132A, 126S)': {
                'attack': 132.28, 'defense': 0, 'stamina': 126},
            'Umb+TF (132A, 126S)': {
                'attack': 131.8, 'defense': 0, 'stamina': 126},
            'Atk BP (132A)': {
                'attack': 132.28, 'defense': 0, 'stamina': 0},
        },
    },
    'Venusaur': {
        'Great': {
            'Fross+Def (122A, 121D, 122S)': {
                'attack': 122.5, 'defense': 121.13, 'stamina': 122},
            'Fross+OK (122A, 118D, 122S)': {
                'attack': 122.5, 'defense': 117.88, 'stamina': 122},
            'Big Bulk (121D, 123S)': {
                'attack': 0, 'defense': 121.13, 'stamina': 123},
            'S-Bulk (120D, 122S)': {
                'attack': 0, 'defense': 120.46, 'stamina': 122},
        },
        'Ultra': {
            'GFisk (159A, 157D, 152S)': {
                'attack': 159.2, 'defense': 157.25, 'stamina': 152},
            'Hi Def (161D, 156S)': {
                'attack': 0, 'defense': 160.82, 'stamina': 156},
            'R1 Bulk (158D, 156S)': {
                'attack': 0, 'defense': 158.05, 'stamina': 156},
            'S-Blend (162A, 155D, 153S)': {
                'attack': 161.59, 'defense': 155.28, 'stamina': 153},
        },
    },
    'Dewgong': {
        'Great': {
            'MaxDef (103A, 132D)': {
                'attack': 102.89, 'defense': 131.7, 'stamina': 0},
            'R1Umb (102A, 137D, 150S)': {
                'attack': 101.79, 'defense': 136.81, 'stamina': 150},
            'R1+Def (102A, 138D, 150S)': {
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
            'Hi Atk (115A, 129D, 119S)': {
                'attack': 115.31, 'defense': 128.92, 'stamina': 119},
            'Max Atk (118A, 128D, 118S)': {
                'attack': 118.24, 'defense': 127.59, 'stamina': 118},
        },
        'Ultra': {
            'Def (149A, 173D)': {
                'attack': 149.14, 'defense': 173.07, 'stamina': 0},
            'Atk (154A, 168D)': {
                'attack': 154.26, 'defense': 168, 'stamina': 0},
        },
    },
    'Whimsicott': {
        'Great': {
            'Mod Atk (121A, 132D)': {
                'attack': 121.26, 'defense': 132.25, 'stamina': 0},
            'Slight Atk (119A, 132D)': {
                'attack': 119.47, 'defense': 132.25, 'stamina': 0},
            'A9 (122A, 132D)': {
                'attack': 121.87, 'defense': 132.25, 'stamina': 0},
            'Licki (123A, 132D)': {
                'attack': 122.81, 'defense': 132.25, 'stamina': 0},
        },
    },
    'Swampert': {
        'Great': {
            'Def (110D)': {
                'attack': 0, 'defense': 110, 'stamina': 0},
            'Atk (122A, 108D)': {
                'attack': 121.6, 'defense': 108, 'stamina': 0},
        },
    },
    'Registeel': {
        'Great': {
            'Raid (187D, 127S)': {
                'attack': 0, 'defense': 186.7, 'stamina': 127},
            'Trade (190D, 129S)': {
                'attack': 0, 'defense': 190.09, 'stamina': 129},
            'Trade+ (192D, 129S)': {
                'attack': 0, 'defense': 191.97, 'stamina': 129},
        },
        'Ultra': {
            'Raid (241D, 165S)': {
                'attack': 0, 'defense': 240.5, 'stamina': 165},
            'Trade (244D, 167S)': {
                'attack': 0, 'defense': 244.4, 'stamina': 167},
        },
    },
    'Azumarill': {
        'Great': {
            'Medi Wall (138D)': {
                'attack': 0, 'defense': 137.64, 'stamina': 0},
            'Min (136D, 192S)': {
                'attack': 0, 'defense': 135.78, 'stamina': 192},
            'General (133D, 187S)': {
                'attack': 0, 'defense': 132.8, 'stamina': 187},
            'Slight Atk (92A, 133D, 187S)': {
                'attack': 92, 'defense': 132.8, 'stamina': 187},
        },
    },
    'Araquanid': {
        'Great': {
            'S-Drap (99A)': {
                'attack': 99.02, 'defense': 0, 'stamina': 0},
            'Viggy (99.2A)': {
                'attack': 99.2, 'defense': 0, 'stamina': 0},
            'Walrus (99.9A)': {
                'attack': 99.93, 'defense': 0, 'stamina': 0},
            'Def Min (164D)': {
                'attack': 0, 'defense': 163.77, 'stamina': 0},
            'Def Max (165D)': {
                'attack': 0, 'defense': 165.21, 'stamina': 0},
            'HP Min (134S)': {
                'attack': 0, 'defense': 0, 'stamina': 134},
            'HP Max (136S)': {
                'attack': 0, 'defense': 0, 'stamina': 136},
            'General (99A, 165D, 134S)': {
                'attack': 99.2, 'defense': 165.2, 'stamina': 134},
        },
    },
    'Golem (Alolan)': {
        'Great': {
            'General (125A)': {
                'attack': 124.79, 'defense': 0, 'stamina': 0},
            'Min (124A)': {
                'attack': 123.93, 'defense': 0, 'stamina': 0},
            'Best (126A, 118D)': {
                'attack': 126, 'defense': 118, 'stamina': 0},
        },
    },
    'Marowak (Alolan)': {
        'Great': {
            'S-Min (111A, 141D)': {
                'attack': 110.5, 'defense': 141.49, 'stamina': 0},
            'S-Hi (112A, 141D)': {
                'attack': 111.85, 'defense': 141.49, 'stamina': 0},
        },
    },
    'Linoone (Galarian)': {
        'Great': {
            'Swamp (113A, 144S)': {
                'attack': 112.87, 'defense': 0, 'stamina': 144},
            'Drap (114A, 144S)': {
                'attack': 114, 'defense': 0, 'stamina': 144},
            'Dig (110D, 144S)': {
                'attack': 0, 'defense': 110.11, 'stamina': 144},
            'SwagAtk (111D, 144S)': {
                'attack': 0, 'defense': 111.14, 'stamina': 144},
            'Best (114A, 111D, 144S)': {
                'attack': 114, 'defense': 111.14, 'stamina': 144},
        },
    },
    'Obstagoon': {
        'Great': {
            'S.Prem (116A, 124D, 137S)': {
                'attack': 115.5, 'defense': 123.56, 'stamina': 137},
            'Prem (115A, 123D, 135S)': {
                'attack': 115, 'defense': 123.3, 'stamina': 135},
            'Bulk (126D, 137S)': {
                'attack': 0, 'defense': 126, 'stamina': 137},
        },
        'Ultra': {
            'Unicorn (148A, 167D, 172S)': {
                'attack': 148, 'defense': 166.8, 'stamina': 172},
            'Gen (147A, 164D, 172S)': {
                'attack': 146.95, 'defense': 163.8, 'stamina': 172},
            'Gen+ (148A, 164D, 172S)': {
                'attack': 147.89, 'defense': 163.8, 'stamina': 172},
            'Mirror (149A, 172D, 172S)': {
                'attack': 149.1, 'defense': 172, 'stamina': 172},
            'Bulk (167D, 174S)': {
                'attack': 0, 'defense': 166.8, 'stamina': 174},
        },
    },
    'Medicham': {
        'Great': {
            'Good (105A, 139D, 140S)': {
                'attack': 105.38, 'defense': 138.6, 'stamina': 140},
            'Prem (106A, 139D, 140S)': {
                'attack': 105.87, 'defense': 138.64, 'stamina': 140},
            'BB (105A, 140D, 142S)': {
                'attack': 105.38, 'defense': 140.3, 'stamina': 142},
            'Mirror (108A, 138D)': {
                'attack': 108, 'defense': 137.64, 'stamina': 0},
        },
    },
    'Dedenne': {
        'Great': {
            'Basic (123A, 109D, 133S)': {
                'attack': 123.17, 'defense': 109, 'stamina': 133},
            'Scrafty (123A, 110D, 133S)': {
                'attack': 123.17, 'defense': 109.86, 'stamina': 133},
            'Atk+ (125A, 109D, 133S)': {
                'attack': 124.59, 'defense': 109, 'stamina': 133},
            'Best (125A, 110D, 133S)': {
                'attack': 124.59, 'defense': 109.86, 'stamina': 133},
            'Bulk (110D, 133S)': {
                'attack': 0, 'defense': 109.86, 'stamina': 133},
        },
    },
    'Dunsparce': {
        'Great': {
            'Bulk (111D, 185S)': {
                'attack': 0, 'defense': 110.63, 'stamina': 185},
            'Prem Bulk (111D, 186S)': {
                'attack': 0, 'defense': 111.14, 'stamina': 186},
        },
    },
    'Stunfisk (Galarian)': {
        'Great': {
            'Hi Bulk (99A, 125D, 174S)': {
                'attack': 99, 'defense': 124.75, 'stamina': 174},
            'Mirror (102A, 127D)': {
                'attack': 101.79, 'defense': 127.34, 'stamina': 0},
            'Bulk Mirror (102A, 125D, 172S)': {
                'attack': 101.79, 'defense': 124.75, 'stamina': 172},
            'Min Bulk (99A, 125D, 172S)': {
                'attack': 99, 'defense': 124.75, 'stamina': 172},
        },
    },
    'Lickitung': {
        'Great': {
            'Good (96A, 126D, 183S)': {
                'attack': 96.36, 'defense': 125.94, 'stamina': 183},
            'Atk (98A, 126D, 183S)': {
                'attack': 97.7, 'defense': 125.94, 'stamina': 183},
            'Budget (97A, 125D, 181S)': {
                'attack': 97, 'defense': 125.1, 'stamina': 181},
        },
    },
    'Toxapex': {
        'Great': {
            'Hi Bulk (227D, 118S)': {
                'attack': 0, 'defense': 226.73, 'stamina': 118},
            'Mirror (219D, 121S)': {
                'attack': 0, 'defense': 219, 'stamina': 121},
            'Licki (93A, 118S)': {
                'attack': 93, 'defense': 0, 'stamina': 118},
        },
    },
    'Toxicroak': {
        'Great': {
            'General (136A, 93D, 131S)': {
                'attack': 136, 'defense': 92.51, 'stamina': 131},
            'Discord (137A, 89D, 134S)': {
                'attack': 136.6, 'defense': 88.57, 'stamina': 134},
            'Bork (137A, 82D, 134S)': {
                'attack': 136.6, 'defense': 82, 'stamina': 134},
        },
    },
    'Trevenant': {
        'Great': {
            'Best (124A, 106D, 128S)': {
                'attack': 124, 'defense': 105.8, 'stamina': 128},
            'Next (124A, 106D, 125S)': {
                'attack': 124, 'defense': 105.8, 'stamina': 125},
        },
        'Ultra': {
            'Atk (169A, 129D, 167S)': {
                'attack': 168.7, 'defense': 129, 'stamina': 167},
        },
    },
    'Noctowl': {
        'Great': {
            'Slight Atk (104A, 118D, 171S)': {
                'attack': 104.23, 'defense': 118.27, 'stamina': 171},
            'Azu (105A, 118D, 168S)': {
                'attack': 105.2, 'defense': 117.58, 'stamina': 168},
            'A9 (106A, 172S)': {
                'attack': 106.36, 'defense': 0, 'stamina': 172},
        },
    },
    'Chesnaught': {
        'Great': {
            'Bulk (122D, 127S)': {
                'attack': 0, 'defense': 122.21, 'stamina': 127},
            'Fross (122A, 118D, 125S)': {
                'attack': 121.89, 'defense': 117.7, 'stamina': 125},
            'Fross Def (122A, 122D, 122S)': {
                'attack': 121.89, 'defense': 122.21, 'stamina': 122},
        },
    },
    'Altaria': {
        'Great': {
            'Trev (103A, 149D, 139S)': {
                'attack': 102.97, 'defense': 149.02, 'stamina': 139},
            'Bulk+Trev (102A, 152D, 139S)': {
                'attack': 101.95, 'defense': 151.63, 'stamina': 139},
            'Bulk (154D, 139S)': {
                'attack': 0, 'defense': 153.95, 'stamina': 139},
        },
    },
    'Cofagrigus': {
        'Great': {
            'General (109A, 162D, 106S)': {
                'attack': 109, 'defense': 162, 'stamina': 106},
            'Best (111A, 165D, 106S)': {
                'attack': 111.32, 'defense': 164.56, 'stamina': 106},
        },
        'Ultra': {
            'General (145A, 208D, 138S)': {
                'attack': 145.21, 'defense': 208, 'stamina': 138},
        },
    },
    'Runerigus': {
        'Great': {
            'General (109A, 162D, 106S)': {
                'attack': 109, 'defense': 162, 'stamina': 106},
            'Best (111A, 165D, 106S)': {
                'attack': 111.32, 'defense': 164.56, 'stamina': 106},
        },
        'Ultra': {
            'General (145A, 208D, 138S)': {
                'attack': 145.21, 'defense': 208, 'stamina': 138},
        },
    },
    'Slowbro': {
        'Great': {
            'Bulk (118D, 144S)': {
                'attack': 0, 'defense': 118.4, 'stamina': 144},
        },
    },
    'Slowbro (Galarian)': {
        'Great': {
            'Mirror (118A, 109D, 144S)': {
                'attack': 118.48, 'defense': 108.83, 'stamina': 144},
            'Bulk (109D, 146S)': {
                'attack': 0, 'defense': 109, 'stamina': 146},
            'General (110A, 100D, 144S)': {
                'attack': 110, 'defense': 100, 'stamina': 144},
        },
    },
    'Slowking (Galarian)': {
        'Great': {
            'Mirror (117A, 118D, 138S)': {
                'attack': 116.7, 'defense': 117.5, 'stamina': 138},
        },
    },
    'Tapu Fini': {
        'Great': {
            'Beat Medi (154D, 110S)': {
                'attack': 0, 'defense': 153.91, 'stamina': 110},
            'General (154D, 107S)': {
                'attack': 0, 'defense': 153.91, 'stamina': 107},
            'Thrift (154D, 105S)': {
                'attack': 0, 'defense': 153.91, 'stamina': 105},
        },
        'Ultra': {
            'Hi HP (199D, 142S)': {
                'attack': 0, 'defense': 198.9, 'stamina': 142},
            'Poli (148A, 199D, 139S)': {
                'attack': 147.59, 'defense': 198.9, 'stamina': 139},
            'A9 (149A, 199D, 139S)': {
                'attack': 149.39, 'defense': 198.9, 'stamina': 139},
            'General (199D, 139S)': {
                'attack': 0, 'defense': 198.9, 'stamina': 139},
        },
    },
    'Greninja': {
        'Great': {
            'Bulk (100D, 115S)': {
                'attack': 0, 'defense': 99.61, 'stamina': 115},
            'Azu (140A, 99D, 111S)': {
                'attack': 140.08, 'defense': 99.36, 'stamina': 111},
            'Hi Atk (139A)': {
                'attack': 139.04, 'defense': 0, 'stamina': 0},
            'V.Hi Atk (143A)': {
                'attack': 143.3, 'defense': 0, 'stamina': 0},
            'Max Atk (145A)': {
                'attack': 144.6, 'defense': 0, 'stamina': 0},
        },
        'Ultra': {
            'Bulk (131D, 149S)': {
                'attack': 0, 'defense': 130.62, 'stamina': 149},
            'Bulk+ (133D, 149S)': {
                'attack': 0, 'defense': 132.53, 'stamina': 149},
        },
    },
    'Dubwool': {
        'Great': {
            'Hi Bulk (142D, 128S)': {
                'attack': 0, 'defense': 141.6, 'stamina': 128},
        },
        'Ultra': {
            'Hundo (178D, 160S)': {
                'attack': 0, 'defense': 178.3, 'stamina': 160},
        },
    },
    'Quagsire': {
        'Great': {
            'Non-S (112D, 163S)': {
                'attack': 0, 'defense': 112, 'stamina': 163},
            'S-Bulk (113D, 163S)': {
                'attack': 0, 'defense': 112.68, 'stamina': 163},
            'S-Atk (110A, 110D, 163S)': {
                'attack': 110, 'defense': 110.26, 'stamina': 163},
            'Carbink (112A, 108D, 162S)': {
                'attack': 111.89, 'defense': 108, 'stamina': 162},
        },
    },
    'Clodsire': {
        'Great': {
            'Bulk1 (120D, 212S)': {
                'attack': 0, 'defense': 119.51, 'stamina': 212},
            'Bulk2 (121D, 210S)': {
                'attack': 0, 'defense': 121.23, 'stamina': 210},
            'Atk (97A, 117D, 199S)': {
                'attack': 96.5, 'defense': 117, 'stamina': 199},
            'Top 20': {
                'attack': 0, 'defense': 0, 'stamina': 0, 'onlytop': 20},
        },
    },
    'Charjabug': {
        'Great': {
            'Mirror (116A, 136D, 120S)': {
                'attack': 116.27, 'defense': 136.09, 'stamina': 120},
            'Mirror CMP (115A, 136D, 124S)': {
                'attack': 114.51, 'defense': 136.09, 'stamina': 124},
        },
    },
    'Froslass': {
        'Great': {
            'CMP (122A, 113D, 131S)': {
                'attack': 121.6, 'defense': 113, 'stamina': 131},
            'Bulk (113D, 131S)': {
                'attack': 0, 'defense': 113, 'stamina': 131},
            'Hi Atk (123A, 113D, 127S)': {
                'attack': 123.12, 'defense': 113, 'stamina': 127},
        },
    },
    'Decidueye': {
        'Great': {
            'Gen (115D, 118S)': {
                'attack': 0, 'defense': 115.29, 'stamina': 118},
            'Gen LoDef (114D, 120S)': {
                'attack': 0, 'defense': 113.7, 'stamina': 120},
            'Astonish (116D, 118S)': {
                'attack': 0, 'defense': 115.52, 'stamina': 118},
            'Asto HiAtk (128A, 116D, 118S)': {
                'attack': 127.61, 'defense': 115.52, 'stamina': 118},
            'Asto HiDef (116D, 118S)': {
                'attack': 0, 'defense': 116, 'stamina': 118},
            'Asto HiHP (114D, 120S)': {
                'attack': 0, 'defense': 113.7, 'stamina': 120},
            'Leaf Atk (128A, 115D, 118S)': {
                'attack': 127.61, 'defense': 115.29, 'stamina': 118},
            'Leaf+Poli (128A, 115D, 119S)': {
                'attack': 127.61, 'defense': 115.29, 'stamina': 119},
            'Leaf+Zong (128A, 114D, 118S)': {
                'attack': 127.61, 'defense': 113.7, 'stamina': 118},
            'Leaf+Dnair (128A, 117D, 118S)': {
                'attack': 127.61, 'defense': 116.71, 'stamina': 118},
        },
    },
    'Lanturn': {
        'Great': {
            'General (106D, 196S)': {
                'attack': 0, 'defense': 105.5, 'stamina': 196},
            'Prem (106D, 192S)': {
                'attack': 0, 'defense': 106.04, 'stamina': 192},
        },
    },
    'Annihilape': {
        'Great': {
            'Gen (123A, 106D, 136S)': {
                'attack': 122.94, 'defense': 106.17, 'stamina': 136},
            'Licki (127A, 102D, 132S)': {
                'attack': 127.23, 'defense': 102.26, 'stamina': 132},
            'Licki+ (127A, 103D, 132S)': {
                'attack': 127.23, 'defense': 102.55, 'stamina': 132},
        },
        'Ultra': {
            'Gen (160A, 135D, 178S)': {
                'attack': 159.7, 'defense': 134.5, 'stamina': 178},
        },
    },
    'Goodra': {
        'Great': {
            'Swag (136D, 117S)': {
                'attack': 0, 'defense': 135.72, 'stamina': 117},
            'Licki (122A, 125D, 115S)': {
                'attack': 122, 'defense': 125.2, 'stamina': 115},
        },
    },
    'Carbink': {
        'Great': {
            'Prem (81A, 248D, 128S)': {
                'attack': 81.38, 'defense': 247.67, 'stamina': 128},
            'Atk (86A, 239D, 124S)': {
                'attack': 85.81, 'defense': 239.06, 'stamina': 124},
            'Gen (83A, 246D, 124S)': {
                'attack': 82.83, 'defense': 246, 'stamina': 124},
        },
    },
    'Corviknight': {
        'Great': {
            'Anni (135D)': {
                'attack': 0, 'defense': 134.61, 'stamina': 0},
            'Carbink (131D)': {
                'attack': 0, 'defense': 130.7, 'stamina': 0},
            'Cress (135D)': {
                'attack': 0, 'defense': 134.55, 'stamina': 0},
            'G-Cors (130D)': {
                'attack': 0, 'defense': 130.34, 'stamina': 0},
            'Mandi (132D)': {
                'attack': 0, 'defense': 132.17, 'stamina': 0},
            'Dig (110A)': {
                'attack': 110, 'defense': 0, 'stamina': 0},
            'Drap (111A)': {
                'attack': 111.4, 'defense': 0, 'stamina': 0},
            'S-ASlash (124A)': {
                'attack': 124, 'defense': 0, 'stamina': 0},
            'Pex (113A)': {
                'attack': 112.54, 'defense': 0, 'stamina': 0},
            'Azu (109A)': {
                'attack': 108.75, 'defense': 0, 'stamina': 0},
        },
    },
}
