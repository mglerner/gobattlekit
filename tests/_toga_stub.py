"""Minimal toga stub for screen/navigation tests.

toga is not a test dependency (see test_provenance.py), so screen-level tests
install this stub into sys.modules before importing the screens. It models
only the slice of the toga widget API the screens touch. Installed only when
the real toga is absent, so a machine that has toga still uses it.
"""
import sys
import types


def install_toga_stub():
    if 'toga' in sys.modules:
        return

    toga = types.ModuleType('toga')
    style = types.ModuleType('toga.style')
    pack = types.ModuleType('toga.style.pack')

    class Pack:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __getattr__(self, name):
            return None

    pack.COLUMN = 'column'
    pack.ROW = 'row'
    pack.CENTER = 'center'
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

    class InfoDialog(_Widget):
        pass

    class MainWindow(_Widget):
        pass

    class App:
        def __init__(self, *a, **k):
            pass

    toga.Box = Box
    toga.ScrollContainer = ScrollContainer
    toga.Label = Label
    toga.Button = Button
    toga.TextInput = TextInput
    toga.MultilineTextInput = MultilineTextInput
    toga.InfoDialog = InfoDialog
    toga.MainWindow = MainWindow
    toga.App = App

    sys.modules['toga'] = toga
    sys.modules['toga.style'] = style
    sys.modules['toga.style.pack'] = pack
