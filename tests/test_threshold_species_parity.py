"""Parity check: every threshold species must resolve against a REAL gamemaster.

The autouse mock_load_gamemaster fixture (conftest.py) serves a 7-mon
MINI_GAMEMASTER to the whole suite, so no other test ever verifies that the
species keys in default_thresholds.toml and SENTIMENTAL_DEFAULT_THRESHOLDS
still match a real pvpoke gamemaster's speciesName values. The matching
contract is pure string equality on display names ('Corsola (Galarian)',
'Ninetales (Shadow)', ...): an upstream speciesName rename would silently zero
out a species, because check_thresholds skips any species missing from the
index.

This test reads the cached gamemaster.json directly (bypassing the mock and the
network) and cross-checks every threshold species key. It skips cleanly when no
cache is present, so it is a no-op on CI / fresh machines.
"""
import json
import pathlib
import tomllib

import pytest

# The real cache location, independent of the fetcher.CACHE_DIR the
# isolate_app_data fixture redirects to tmp_path. Mirrors fetcher.CACHE_DIR.
GAMEMASTER_CACHE = (
    pathlib.Path.home() / "Documents" / "gobattlekit_cache" / "gamemaster.json"
)
BUNDLED_THRESHOLDS = (
    pathlib.Path(__file__).resolve().parents[1]
    / "src" / "gobattlekit" / "data" / "default_thresholds.toml"
)


def _real_species_names():
    """The set of speciesName values in the cached gamemaster.

    Built the same way get_pokemon_index() builds its keys — straight off
    each pokemon's 'speciesName', which already carries '(Shadow)' /
    '(Galarian)' / '(Female)' variants as distinct entries (no synthesis).
    """
    gm = json.loads(GAMEMASTER_CACHE.read_text())
    return {mon["speciesName"] for mon in gm["pokemon"]}


@pytest.mark.skipif(
    not GAMEMASTER_CACHE.exists(),
    reason=f"No cached gamemaster at {GAMEMASTER_CACHE}; run the app once to populate it.",
)
def test_default_threshold_species_resolve_against_real_gamemaster():
    names = _real_species_names()
    default = tomllib.loads(BUNDLED_THRESHOLDS.read_text())
    missing = sorted(s for s in default if s not in names)
    assert not missing, (
        "default_thresholds.toml species absent from the real gamemaster "
        f"(pvpoke speciesName rename?): {missing}"
    )


@pytest.mark.skipif(
    not GAMEMASTER_CACHE.exists(),
    reason=f"No cached gamemaster at {GAMEMASTER_CACHE}; run the app once to populate it.",
)
def test_sentimental_threshold_species_resolve_against_real_gamemaster():
    # Imported here (not module-scope) so the file still collects cleanly if
    # the data package import ever changes; the import itself hits no network.
    from gobattlekit.data.thresholds import SENTIMENTAL_DEFAULT_THRESHOLDS

    names = _real_species_names()
    missing = sorted(s for s in SENTIMENTAL_DEFAULT_THRESHOLDS if s not in names)
    assert not missing, (
        "SENTIMENTAL_DEFAULT_THRESHOLDS species absent from the real "
        f"gamemaster (pvpoke speciesName rename?): {missing}"
    )
