"""Shared fixtures for data layer tests."""
import pytest
from unittest.mock import patch


# Minimal gamemaster with a few real pokemon for testing.
# Base stats sourced from PvPoke for Azumarill and Registeel.
MINI_GAMEMASTER = {
    'pokemon': [
        {
            'speciesId': 'azumarill',
            'speciesName': 'Azumarill',
            'baseStats': {'atk': 112, 'def': 152, 'hp': 225},
            'family': {
                'id': 'marill',
                'parent': 'marill',
                'evolutions': [],
            },
        },
        {
            'speciesId': 'marill',
            'speciesName': 'Marill',
            'baseStats': {'atk': 37, 'def': 93, 'hp': 172},
            'family': {
                'id': 'marill',
                'parent': None,
                'evolutions': ['azumarill'],
            },
        },
        {
            'speciesId': 'registeel',
            'speciesName': 'Registeel',
            'baseStats': {'atk': 143, 'def': 285, 'hp': 190},
            'family': {
                'id': 'registeel',
                'parent': None,
                'evolutions': [],
            },
        },
    ],
    'moves': [
        # Fast moves (energyGain != 0)
        {
            'moveId': 'BUBBLE',
            'name': 'Bubble',
            'type': 'water',
            'power': 7,
            'energyGain': 11,
            'cooldown': 3,
        },
        {
            'moveId': 'LOCK_ON',
            'name': 'Lock-On',
            'type': 'normal',
            'power': 1,
            'energyGain': 5,
            'cooldown': 1,
        },
        {
            'moveId': 'MUD_SHOT',
            'name': 'Mud Shot',
            'type': 'ground',
            'power': 3,
            'energyGain': 9,
            'cooldown': 2,
        },
        # Charged moves (energyGain == 0)
        {
            'moveId': 'ICE_BEAM',
            'name': 'Ice Beam',
            'type': 'ice',
            'power': 90,
            'energy': 55,
            'energyGain': 0,
            'cooldown': 0,
        },
        {
            'moveId': 'PLAY_ROUGH',
            'name': 'Play Rough',
            'type': 'fairy',
            'power': 90,
            'energy': 60,
            'energyGain': 0,
            'cooldown': 0,
        },
        {
            'moveId': 'FOCUS_BLAST',
            'name': 'Focus Blast',
            'type': 'fighting',
            'power': 150,
            'energy': 75,
            'energyGain': 0,
            'cooldown': 0,
        },
        {
            'moveId': 'ZAP_CANNON',
            'name': 'Zap Cannon',
            'type': 'electric',
            'power': 150,
            'energy': 80,
            'energyGain': 0,
            'cooldown': 0,
        },
    ],
}


@pytest.fixture
def mini_gamemaster():
    """A minimal gamemaster dict for testing without network."""
    return MINI_GAMEMASTER


@pytest.fixture(autouse=True)
def mock_load_gamemaster():
    """Patch load_gamemaster globally so tests never hit the network."""
    with patch('gobattlekit.data.fetcher.load_gamemaster', return_value=MINI_GAMEMASTER):
        yield
