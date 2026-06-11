"""Shared fixtures for data layer tests."""
import urllib.request

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
def isolate_app_data(tmp_path):
    """Tripwire: no test may touch the real app cache or the network.

    Every CACHE_DIR-derived path constant is captured at import time by its
    own module, so each one must be redirected individually — redirecting
    fetcher.CACHE_DIR alone is NOT enough (that was the TS7 trap). The
    urlopen block turns any network leak into a loud failure instead of a
    test that silently passes against live data.

    Deliberately uses its OWN MonkeyPatch instance rather than the shared
    `monkeypatch` fixture: pytest hands one instance to everything in a
    test, so a test calling monkeypatch.undo() would strip this isolation
    too and leak onto the real ~/Documents cache (it happened — a test's
    undo() overwrote the real user_thresholds.json).
    """
    from gobattlekit.data import fetcher, evolution_lines, user_thresholds, preferences

    mp = pytest.MonkeyPatch()
    cache = tmp_path / "gobattlekit_cache"
    mp.setattr(fetcher, "_parsed_cache", {})
    mp.setattr(fetcher, "CACHE_DIR", cache)
    mp.setattr(fetcher, "SAVED_CSV", cache / "pokegenie_export.csv")
    mp.setattr(fetcher, "USER_GENERATED_CSV", cache / "user_generated.csv")
    mp.setattr(evolution_lines, "CACHED_PATH", cache / "evolution_lines.json")
    mp.setattr(user_thresholds, "USER_THRESHOLDS_FILE", cache / "user_thresholds.json")
    mp.setattr(user_thresholds, "CACHE_DIR", cache)
    mp.setattr(preferences, "_PREFS_FILE", cache / "preferences.json")
    mp.setattr(preferences, "CACHE_DIR", cache)

    def _no_network(*args, **kwargs):
        raise AssertionError(
            "Test attempted real network access via urllib.request.urlopen. "
            "Mock it (see test_fetcher.py) or fix the load_gamemaster patch target."
        )

    mp.setattr(urllib.request, "urlopen", _no_network)
    try:
        yield
    finally:
        mp.undo()


@pytest.fixture(autouse=True)
def clear_rank_cache():
    """_rank_cache is keyed (species, max_level, max_cp) WITHOUT base stats,
    so a table computed with synthetic stats in one test would poison every
    later check_thresholds call for the same species — order-dependent
    failures. Clear it around every test."""
    from gobattlekit.data.iv_checker import _rank_cache
    _rank_cache.clear()
    yield
    _rank_cache.clear()


@pytest.fixture(autouse=True)
def mock_load_gamemaster():
    """Serve MINI_GAMEMASTER to every consumer of load_gamemaster.

    The name is bound by from-import in its consumers, so the patch must
    target the consumer modules' bindings, not (only) the fetcher's.
    Patching the fetcher alone leaves the real function reachable — the
    suite then runs against the live cache/network (finding TS1).
    """
    with patch('gobattlekit.data.fetcher.load_gamemaster', return_value=MINI_GAMEMASTER), \
         patch('gobattlekit.data.iv_checker.load_gamemaster', return_value=MINI_GAMEMASTER), \
         patch('gobattlekit.data.gamemaster.load_gamemaster', return_value=MINI_GAMEMASTER):
        yield
