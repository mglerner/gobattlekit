#!/usr/bin/env python
"""
User IV checker screen — same as IV checker but uses user-defined thresholds.
"""
import pathlib

import toga
from toga.style import Pack
from .iv_checker import IVCheckerScreen
from ..data.user_thresholds import load_user_thresholds
from ..theme import COLOR_TEXT_LIGHT, btn_primary, btn_help

NO_TARGETS_MESSAGE = "No user IV targets defined.\nTap 'Edit My Targets' to add some."
GETTING_STARTED = (
    "To get started:\n1. Tap 'Edit My Targets'\n2. Tap 'Add Target'\n"
    "3. Choose a species and\nset minimum stats\n4. Tap 'Save Target'"
)


class UserIVCheckerScreen(IVCheckerScreen):
    """IV checker screen using user-defined thresholds.

    Everything (build, species list, matching) is the base screen's; only
    the hooks below differ.
    """

    SCREEN_TITLE = "My PvP IV Targets"

    # User-store specs with no explicit 'class' resolve to 'user', so the
    # SIM filter in the inherited _get_thresholds never hides them.
    THRESHOLD_STORE = 'user'

    def _get_thresholds_raw(self):
        return load_user_thresholds()

    def _extra_top_widgets(self):
        return [toga.Button(
            "Edit My Targets",
            on_press=lambda w: self.app.show_edit_thresholds(),
            style=btn_primary(height=48, font_size=16)
        )]

    def _add_bottom_buttons(self):
        # No IV Credits button here — these targets are the user's own.
        self.container.add(toga.Button(
            "?  Help",
            on_press=lambda w: self.app.show_help(
                topic="My PvP IV Targets",
                back_screen=lambda: self.app.show_user_iv_checker(skip_intro=True),
                back_label="← My PvP IV Targets"
            ),
            style=btn_help()
        ))

    def _no_targets_message(self):
        return f"No targets defined for {self.league.capitalize()} League."

    def _show_getting_started(self):
        self.results_box.add(toga.Label(
            GETTING_STARTED,
            style=Pack(font_size=14, text_align="center",
                       margin_top=20, color=COLOR_TEXT_LIGHT)
        ))

    def _store_is_empty(self):
        # The RAW store, so "no targets yet" only shows when the store is
        # truly empty — not when the SIM filter merely hid everything.
        return not self._get_thresholds_raw()

    def _pre_list_empty_state(self):
        if not self._store_is_empty():
            return False
        self._show_getting_started()
        return True

    def _pre_check_empty_state(self):
        if not self._store_is_empty():
            return False
        # The CSV is still loaded — show its name; only the targets are
        # missing. Don't clear the file label here.
        # csv_path is always a fixed cache filename (<= 20 chars)
        self.status_label_file.text = pathlib.Path(self.csv_path).name  # label-fits: fixed cache filename
        self._show_clear_btn(True)
        self.status_label_stats.text = NO_TARGETS_MESSAGE
        for child in list(self.results_box.children):
            self.results_box.remove(child)
        self._show_getting_started()
        return True
