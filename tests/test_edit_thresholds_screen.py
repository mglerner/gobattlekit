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
