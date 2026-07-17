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


class TestClearCsvDisarm:
    """An armed two-tap Clear-CSV confirm must not survive in-screen
    navigation, or a single later tap silently wipes all CSVs + manual mons."""

    def test_navigation_disarms_pending_clear(self):
        s = _screen()
        s._clear_csv(None)  # first tap arms
        assert s._clear_csv_pending is True
        s._display_species_list()  # in-screen navigation
        assert s._clear_csv_pending is False

    def test_run_check_disarms_pending_clear(self):
        s = _screen()
        s._clear_csv(None)  # first tap arms
        assert s._clear_csv_pending is True
        s._run_check()  # e.g. league button -> re-check overwrites the warning
        assert s._clear_csv_pending is False

    def test_two_consecutive_taps_still_clear(self):
        s = _screen()
        s._clear_csv(None)  # arm
        s._clear_csv(None)  # confirm -> actually deletes
        assert s._clear_csv_pending is False
        assert s.csv_path is None


class TestFormWipeOnError:
    """A manual-entry validation error must redisplay the form with what the
    user typed, not reset every field."""

    def _fill(self, s, atk, dfn, sta, cp, species='Medicham'):
        s._manual_species = species
        s._manual_atk_input = toga.TextInput(value=atk)
        s._manual_def_input = toga.TextInput(value=dfn)
        s._manual_sta_input = toga.TextInput(value=sta)
        s._manual_cp_input = toga.TextInput(value=cp)

    def test_bad_cp_preserves_typed_values(self):
        s = _screen()
        self._fill(s, '15', '15', '15', '1,500')  # comma -> ValueError gate
        s._submit_manual_entry(None)
        assert s._manual_atk == '15'
        assert s._manual_def == '15'
        assert s._manual_sta == '15'
        assert s._manual_cp == '1,500'

    def test_missing_species_preserves_typed_values(self):
        s = _screen()
        self._fill(s, '12', '13', '14', '1500', species=None)
        s._submit_manual_entry(None)
        assert s._manual_atk == '12'
        assert s._manual_def == '13'
        assert s._manual_sta == '14'
        assert s._manual_cp == '1500'


class TestIvsOnlyTargetSummary:
    """A target that only lists explicit IV spreads must not be summarized as
    'Requires: any' (which reads as 'any IVs qualify')."""

    def test_refresh_hits_summarizes_ivs_only_target(self, monkeypatch):
        s = _screen()
        target = {'ivs': [[0, 0, 0], [1, 1, 1], [2, 2, 2]]}
        s._get_thresholds = lambda: {
            'Annihilape': {'Great': {'Ape Slayer': target}}}
        s.league = 'great'
        s.hits_box = toga.Box()
        s.source_box = toga.Box()
        s.pogo_box = toga.Box()
        s._targets_without_hits = {'Ape Slayer'}
        s._target_options_raw = ['Ape Slayer']
        s._target_index = 0
        # Species absent from the index -> lightweight branch that still
        # renders the requirement summary.
        monkeypatch.setattr(
            'gobattlekit.screens.iv_checker.get_pokemon_index', dict)

        s._refresh_hits('Annihilape', [])

        joined = ' '.join(_texts(s.hits_box))
        assert '3 IV spreads' in joined
        assert 'Requires: any' not in joined


class TestNarrowPhoneLabels:
    """Dynamic labels the wrapping checker cannot see must still fit / wrap."""

    def test_qualifying_header_fits_narrow_phone(self):
        s = _screen()
        # Empty target: every spread qualifies, so the header renders its
        # worst-case count (top 100).
        s._get_thresholds = lambda: {'Azumarill': {'Great': {'Bulk': {}}}}
        s.league = 'great'
        s.hits_box = toga.Box()
        s.source_box = toga.Box()
        s.pogo_box = toga.Box()
        s._targets_without_hits = {'Bulk'}
        s._target_options_raw = ['Bulk']
        s._target_index = 0

        s._refresh_hits('Azumarill', [])

        headers = [getattr(c, 'text', '') for c in s.hits_box.children
                   if getattr(c, 'text', '').startswith('Top')]
        assert headers, "the qualifying-count header should render"
        assert all(len(h) <= 40 for h in headers), headers


class TestPogoSearchBlock:
    """_refresh_pogo_search: string, counts label, and copy wiring."""

    def _screen_for(self, targets):
        s = _screen()
        s._get_thresholds = lambda: {'Azumarill': {'Great': targets}}
        s.league = 'great'
        s.hits_box = toga.Box()
        s.source_box = toga.Box()
        s.pogo_box = toga.Box()
        s._targets_without_hits = set(targets)
        s._target_options_raw = list(targets)
        s._target_index = 0
        return s

    def test_string_and_counts_render(self, monkeypatch):
        from gobattlekit.data.search_strings import build_search_string
        s = self._screen_for({'Bulk': {'defense': 100}})

        s._refresh_hits('Azumarill', [])

        expected = build_search_string(
            'Azumarill', 'great', {'Bulk': {'defense': 100}})
        joined = ' '.join(_texts(s.pogo_box))
        assert expected['string'] in joined
        assert (f"Matches {expected['matched_count']}/4096 spreads; "
                f"{expected['qualifying_count']} qualify.") in joined
        assert 'Candidates only' in joined

    def test_copy_button_copies_the_string(self, monkeypatch):
        from gobattlekit.data.search_strings import build_search_string
        copied = []
        monkeypatch.setattr('gobattlekit.screens.iv_checker.copy_text',
                            lambda app, text: copied.append(text) or True)
        s = self._screen_for({'Bulk': {'defense': 100}})

        s._refresh_hits('Azumarill', [])

        buttons = [c for row in s.pogo_box.children
                   for c in getattr(row, 'children', [])
                   if getattr(c, 'text', '').startswith('📋')]
        assert buttons, "copy button should render"
        buttons[0].on_press(buttons[0])
        expected = build_search_string(
            'Azumarill', 'great', {'Bulk': {'defense': 100}})
        assert copied == [expected['string']]
        assert buttons[0].text == '✓ Copied'

    def test_all_targets_union_renders(self):
        # current=None (the 'All targets' cycler position) uses the union.
        s = self._screen_for({'Bulk': {'defense': 100},
                              'Atk': {'attack': 80}})
        s._target_options_raw = [None]
        s._targets_without_hits = set()

        s._refresh_hits('Azumarill', [])

        joined = ' '.join(_texts(s.pogo_box))
        assert '+azumarill&' in joined

    def test_run_check_error_uses_wrapping_widget(self, monkeypatch):
        s = _screen()
        s.csv_path = '/tmp/some.csv'

        def boom(*a, **k):
            raise ValueError(
                "int() argument must be a string, a bytes-like object or a "
                "real number, not 'NoneType'")

        monkeypatch.setattr(
            'gobattlekit.screens.iv_checker.check_thresholds', boom)

        s._run_check()  # must not raise

        wrapped = [
            c for c in s.results_box.children
            if type(c).__name__ == 'MultilineTextInput'
            and 'NoneType' in getattr(c, 'value', '')
        ]
        assert wrapped, "the CSV error must render through a wrapping widget"
