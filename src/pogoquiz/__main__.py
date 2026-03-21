#!/usr/bin/env python
import locale
_original_setlocale = locale.setlocale
def _safe_setlocale(category, loc=None):
    try:
        return _original_setlocale(category, loc)
    except locale.Error:
        return _original_setlocale(category, "C")
locale.setlocale = _safe_setlocale

from pogoquiz.app import main
main().main_loop()

