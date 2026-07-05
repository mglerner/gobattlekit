"""Screen-level regression tests for EditThresholdsScreen.

toga is not a test dependency (see test_provenance.py), so we install a
minimal stub into sys.modules BEFORE importing the screen. The stub only
models the tiny slice of the toga widget API the screen touches (add /
remove children, .text, .value, .style attribute get/set). It is installed
only when the real toga is absent, so a machine that has toga still uses it.
"""
import sys
import types

import pytest
from unittest.mock import MagicMock


def _install_toga_stub():
    if 'toga' in sys.modules:
        return

    toga = types.ModuleType('toga')
    style = types.ModuleType('toga.style')
    pack = types.ModuleType('toga.style.pack')

    class Pack:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __getattr__(self, name):
            # Unset style attributes (e.g. width when only height was given)
            # read as None, matching how the screen probes widget.style.
            return None

    pack.COLUMN = 'column'
    pack.ROW = 'row'
    style.Pack = Pack
    style.pack = pack
    toga.style = style

    class _Widget:
        def __init__(self, *args, **kwargs):
            self.style = kwargs.get('style')
            self.on_press = kwargs.get('on_press')
            self.on_change = kwargs.get('on_change')
            self.enabled = True
            self.placeholder = kwargs.get('placeholder', '')
            self.readonly = kwargs.get('readonly', False)
            self.text = args[0] if args else kwargs.get('text', '')
            self.value = kwargs.get('value', '')

    class Box(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.children = []

        def add(self, *children):
            self.children.extend(children)

        def remove(self, child):
            self.children.remove(child)

    class ScrollContainer(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.content = k.get('content')

    class Label(_Widget):
        pass

    class Button(_Widget):
        pass

    class TextInput(_Widget):
        pass

    class MultilineTextInput(_Widget):
        pass

    toga.Box = Box
    toga.ScrollContainer = ScrollContainer
    toga.Label = Label
    toga.Button = Button
    toga.TextInput = TextInput
    toga.MultilineTextInput = MultilineTextInput

    sys.modules['toga'] = toga
    sys.modules['toga.style'] = style
    sys.modules['toga.style.pack'] = pack


_install_toga_stub()

from gobattlekit.screens.edit_thresholds import EditThresholdsScreen  # noqa: E402
from gobattlekit.data.user_thresholds import (  # noqa: E402
    add_threshold, load_user_thresholds,
)


@pytest.fixture
def screen():
    s = EditThresholdsScreen(MagicMock())
    s.build()
    return s


def _widget_texts(box):
    """Flatten the text/value of every widget in a box."""
    out = []
    for child in box.children:
        out.append(getattr(child, 'text', '') or '')
        out.append(getattr(child, 'value', '') or '')
    return out


class TestOfflineSpeciesPicker:
    def test_species_picker_offline_shows_error_not_crash(self, screen, monkeypatch):
        """Offline first launch: get_pokemon_index raises, _all_species stays
        None. Opening the picker must render the stored error + a Back button,
        not crash on list(None)."""
        from gobattlekit.data.fetcher import NoDataError

        def boom():
            raise NoDataError("Could not fetch data and no cache.")

        monkeypatch.setattr(
            'gobattlekit.screens.edit_thresholds.get_pokemon_index', boom)

        screen._show_add_form()
        # Must not raise.
        screen._show_species_picker()

        # Retry-on-next-visit semantics preserved.
        assert screen._all_species is None
        joined = ' '.join(_widget_texts(screen.content_box))
        assert 'Could not load species list' in joined


class TestFloorValidation:
    """The edit form must reject the same non-finite / negative floors the
    paste-import validator rejects, instead of silently storing a
    match-everything (negative), match-nothing (NaN), or Save-dead (inf)
    target."""

    def test_negative_floor_rejected(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Bulky'
        screen._form_atk = '-92'
        screen._save_threshold(None)
        assert load_user_thresholds() == {}
        assert screen.form_error.text

    def test_nan_floor_rejected(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Bulky'
        screen._form_def = 'nan'
        screen._save_threshold(None)
        assert load_user_thresholds() == {}
        assert screen.form_error.text

    def test_inf_stamina_rejected_no_crash(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Bulky'
        screen._form_sta = 'inf'
        # Must not raise OverflowError.
        screen._save_threshold(None)
        assert load_user_thresholds() == {}
        assert screen.form_error.text

    def test_inf_onlytop_rejected_no_crash(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Bulky'
        screen._form_onlytop = 'inf'
        screen._save_threshold(None)
        assert load_user_thresholds() == {}
        assert screen.form_error.text

    def test_valid_floor_still_saves(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Bulky'
        screen._form_def = '143.0'
        screen._form_sta = '138'
        screen._save_threshold(None)
        data = load_user_thresholds()
        assert data['Azumarill']['Great']['Bulky']['defense'] == 143.0


class TestSilentOverwrite:
    """Add/duplicate/rename must not silently clobber a different existing
    target with the same (species, league, name); editing in place is
    exempt. First collision arms a confirm, a second Save replaces."""

    def test_add_same_name_requires_confirm(self, screen):
        add_threshold('Azumarill', 'Great', 'Default', 92.0, 0, 0)
        screen._show_add_form()
        screen._editing_original = None
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Default'
        screen._form_def = '135'

        # First save: warned, original untouched.
        screen._save_threshold(None)
        data = load_user_thresholds()
        assert data['Azumarill']['Great']['Default']['attack'] == 92.0
        assert screen.form_error.text

        # Second save: overwrite confirmed.
        screen._save_threshold(None)
        data = load_user_thresholds()
        entry = data['Azumarill']['Great']['Default']
        assert entry.get('attack', 0) == 0
        assert entry['defense'] == 135.0

    def test_edit_in_place_no_confirm(self, screen):
        add_threshold('Azumarill', 'Great', 'Bulky', 0, 143.0, 138)
        screen._edit_threshold('Azumarill', 'Great', 'Bulky',
                               {'attack': 0, 'defense': 143.0, 'stamina': 138})
        screen._form_def = '150'
        screen._save_threshold(None)
        data = load_user_thresholds()
        assert data['Azumarill']['Great']['Bulky']['defense'] == 150.0

    def test_rename_to_existing_requires_confirm(self, screen):
        add_threshold('Azumarill', 'Great', 'A', 0, 143.0, 138)
        add_threshold('Azumarill', 'Great', 'B', 0, 100.0, 120)
        screen._edit_threshold('Azumarill', 'Great', 'A',
                               {'attack': 0, 'defense': 143.0, 'stamina': 138})
        screen._form_name = 'B'

        # First save: warned; both entries intact.
        screen._save_threshold(None)
        data = load_user_thresholds()
        assert 'A' in data['Azumarill']['Great']
        assert data['Azumarill']['Great']['B']['defense'] == 100.0
        assert screen.form_error.text

        # Second save: replace confirmed.
        screen._save_threshold(None)
        data = load_user_thresholds()
        assert 'A' not in data['Azumarill']['Great']
        assert data['Azumarill']['Great']['B']['defense'] == 143.0

    def test_add_new_unique_name_saves_immediately(self, screen):
        screen._show_add_form()
        screen._selected_species = 'Azumarill'
        screen._selected_league = 'Great'
        screen._form_name = 'Fresh'
        screen._form_def = '120'
        screen._save_threshold(None)
        assert 'Fresh' in load_user_thresholds()['Azumarill']['Great']


class TestImportErrorWrapping:
    """Import/validator error text is arbitrary length; it must render
    through a wrapping widget, not a clipping toga.Label."""

    def test_import_error_uses_wrapping_widget(self, screen):
        screen._show_import_screen()
        screen._import_input.value = (
            '{"Azumarill": {"Great": {"My Target": {"ivs": [[1, 2]]}}}}')
        screen._do_import(None)

        kids = screen._import_error.children
        assert kids, "an error should be rendered"
        w = kids[0]
        # Routed through paragraph_text (a wrapping MultilineTextInput), not a
        # clipping Label.
        assert type(w).__name__ == 'MultilineTextInput'
        assert 'triples' in w.value
