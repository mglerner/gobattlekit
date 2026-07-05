"""Screen-level regression tests for IVCheckerScreen.

2026-07-04 bug hunt (Agent C). toga is not a test dependency, so a minimal
stub is installed before importing the screen (see tests/_toga_stub.py). The
app-data isolation and load_gamemaster patch come from conftest.py autouse
fixtures.
"""
from unittest.mock import MagicMock

import pytest

from tests._toga_stub import install_toga_stub

install_toga_stub()

import toga  # noqa: E402

from gobattlekit.screens.iv_checker import IVCheckerScreen  # noqa: E402
from gobattlekit.data.fetcher import NoDataError  # noqa: E402


def _raise_no_data():
    raise NoDataError("Could not fetch data and no cache.")


def _screen():
    s = IVCheckerScreen(MagicMock())
    s.build()  # sets up results_box, back_btn, status labels, etc.
    return s


def _texts(box):
    """Flatten text/value of every widget under a box (recursing into
    ScrollContainer content and nested boxes)."""
    out = []
    for child in getattr(box, 'children', []):
        out.append(getattr(child, 'text', '') or '')
        out.append(getattr(child, 'value', '') or '')
        content = getattr(child, 'content', None)
        if content is not None:
            out.extend(_texts(content))
        if hasattr(child, 'children'):
            out.extend(_texts(child))
    return out


class TestOfflineGuard:
    """Fresh offline install (no cached gamemaster): the manual-entry flow
    must surface an error instead of a blank dead panel / silent no-op."""

    def test_species_picker_offline_shows_error_not_blank(self, monkeypatch):
        s = _screen()
        monkeypatch.setattr(
            'gobattlekit.screens.iv_checker.get_pokemon_index', _raise_no_data)

        s._show_manual_species_picker()  # must not raise

        joined = ' '.join(_texts(s.results_box))
        assert 'Could not load' in joined
        assert any(
            getattr(c, 'text', '') == '← Back to Form'
            for c in s.results_box.children
        ), "a Back to Form escape button must be rendered"

    def test_submit_offline_shows_error_not_silent(self, monkeypatch):
        s = _screen()
        s._manual_species = 'Medicham'
        s._manual_atk_input = toga.TextInput(value='15')
        s._manual_def_input = toga.TextInput(value='15')
        s._manual_sta_input = toga.TextInput(value='15')
        s._manual_cp_input = toga.TextInput(value='1500')
        monkeypatch.setattr(
            'gobattlekit.screens.iv_checker.get_pokemon_index', _raise_no_data)

        s._submit_manual_entry(None)  # must not raise, must not no-op

        assert 'Could not load' in ' '.join(_texts(s.results_box))
