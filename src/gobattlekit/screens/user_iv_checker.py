#!/usr/bin/env python
"""
User IV checker screen — same as IV checker but uses user-defined thresholds.
"""
import logging
import pathlib

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from .iv_checker import IVCheckerScreen
from ..data.user_thresholds import load_user_thresholds
from ..data.iv_checker import check_thresholds
from ..data.thresholds import EVOLUTION_LINES
from ..data.fetcher import SAVED_CSV, USER_GENERATED_CSV, get_csv_path, CACHE_DIR
from ..platform import ON_IOS
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_BG,
    btn_primary, btn_secondary, btn_nav, btn_league, btn_icon,
    btn_destructive, btn_destructive_icon, btn_help,
    show_widget, hide_widget
)

logger = logging.getLogger(__name__)

NO_TARGETS_MESSAGE = "No user IV targets defined.\nTap 'Edit My Targets' to add some."
GETTING_STARTED = (
    "To get started:\n1. Tap 'Edit My Targets'\n2. Tap 'Add Target'\n"
    "3. Choose a species and\nset minimum stats\n4. Tap 'Save Target'"
)


class UserIVCheckerScreen(IVCheckerScreen):
    """IV checker screen using user-defined thresholds."""

    # User-store specs with no explicit 'class' resolve to 'user', so the
    # SIM filter in the inherited _get_thresholds never hides them.
    THRESHOLD_STORE = 'user'

    def _get_thresholds_raw(self):
        return load_user_thresholds()

    def build(self):
        self._clear_csv_pending = False
        self.container = toga.Box(style=CONTAINER)

        self.container.add(toga.Label(
            "My PvP IV Targets",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10,
                       color=COLOR_ACCENT)
        ))

        league_box = toga.Box(style=Pack(direction=ROW, margin_bottom=16))
        for league, label in (('great', 'Great'), ('ultra', 'Ultra'), ('master', 'Master')):
            league_box.add(toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=btn_league()
            ))
        self.container.add(league_box)

        if not ON_IOS:
            self.container.add(toga.Button(
                "Import PokeGenie CSV",
                on_press=self._import_csv,
                style=btn_primary(height=52, font_size=16)
            ))

        self.container.add(toga.Button(
            "Edit My Targets",
            on_press=lambda w: self.app.show_edit_thresholds(),
            style=btn_primary(height=48, font_size=16)
        ))

        status_row = toga.Box(style=Pack(direction=ROW, margin_bottom=2, height=36))
        self.status_label_file = toga.Label(
            # label-fits: csv_path is always a fixed cache filename (<= 20 chars)
            pathlib.Path(self.csv_path).name if self.csv_path else "",
            style=Pack(flex=1, font_size=13, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.clear_csv_btn = toga.Button(
            "✕",
            on_press=self._clear_csv,
            style=btn_destructive_icon()
        )
        self._show_clear_btn(bool(self.csv_path))
        status_row.add(self.status_label_file)
        status_row.add(self.clear_csv_btn)
        self.container.add(status_row)

        self.status_label_stats = toga.Label(
            # label-fits: _stats_line() (inherited) skeleton ~25 chars; NO_CSV_MESSAGE 24
            self._stats_line() if self.csv_path else self.NO_CSV_MESSAGE,
            style=Pack(font_size=13, text_align="center", margin_bottom=4,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.status_label_stats)

        self.results_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=COLOR_BG))
        scroll = toga.ScrollContainer(content=self.results_box,
                                      style=Pack(flex=1, background_color=COLOR_BG))
        self.container.add(scroll)

        self.back_btn = toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        )
        hide_widget(self.back_btn)
        self.container.add(self.back_btn)

        self.container.add(toga.Button(
            "?  Help",
            on_press=lambda w: self.app.show_help(
                topic="My PvP IV Targets",
                back_screen=lambda: self.app.show_user_iv_checker(skip_intro=True),
                back_label="← My PvP IV Targets"
            ),
            style=btn_help()
        ))

        self.container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44)
        ))

        path = get_csv_path()
        if path and not self.csv_path:
            self.csv_path = path
            self._run_check()
        else:
            self._display_species_list()

        return self.container

    def _display_species_list(self):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(False)

        # Through the chokepoint, so SIM-hidden targets disappear here
        # too; the GETTING_STARTED check uses the raw store so "no
        # targets yet" only shows when the store is truly empty.
        user_thresholds = self._get_thresholds()
        league_label = self.league.capitalize()

        if not self._get_thresholds_raw():
            self.results_box.add(toga.Label(
                GETTING_STARTED,
                style=Pack(font_size=14, text_align="center",
                           margin_top=20, color=COLOR_TEXT_LIGHT)
            ))
            return

        all_target_species = sorted([
            s for s in user_thresholds
            if league_label in user_thresholds.get(s, {})
        ])

        if not all_target_species:
            self.results_box.add(toga.Label(
                f"No targets defined for {league_label} League.",
                style=Pack(font_size=14, text_align="center",
                           margin_top=20, color=COLOR_TEXT_LIGHT)
            ))
            return

        total = sum(len(hits) for hits in self.results.values())
        if total > 0:
            self.results_box.add(toga.Button(
                f"Show All ({total} hits)",
                on_press=lambda w: self._display_all_results(),
                style=btn_primary(height=48, font_size=16)
            ))

        self.results_box.add(toga.Button(
            "✏️ Enter a Pokémon manually",
            on_press=lambda w: self._show_manual_entry(),
            style=btn_secondary(height=44, font_size=14)
        ))

        if not self._has_pokegenie_csv():
            self.results_box.add(toga.Button(
                "Import from PokeGenie",
                on_press=self._show_pokegenie_help,
                style=btn_secondary(height=44, font_size=14)
            ))

        for species in all_target_species:
            hits = self.results.get(species, [])
            self.results_box.add(toga.Button(
                f"{species} ({len(hits)})",
                on_press=self._make_species_handler(species),
                style=btn_secondary(height=48, font_size=16)
            ))

    def _run_check(self):
        if not self.csv_path:
            self._display_species_list()
            return
        try:
            # Matching reads through the SIM-filter chokepoint so hidden
            # generated targets never produce hits (counts must agree
            # with the display).
            user_thresholds = self._get_thresholds()
            if not self._get_thresholds_raw():
                # CSV is still loaded — show its name; only the targets
                # are missing. Don't clear the file label here.
                # csv_path is always a fixed cache filename (<= 20 chars)
                self.status_label_file.text = pathlib.Path(self.csv_path).name  # label-fits: fixed cache filename
                self._show_clear_btn(True)
                self.status_label_stats.text = NO_TARGETS_MESSAGE
                for child in list(self.results_box.children):
                    self.results_box.remove(child)
                self.results_box.add(toga.Label(
                    GETTING_STARTED,
                    style=Pack(font_size=14, text_align="center",
                               margin_top=20, color=COLOR_TEXT_LIGHT)
                ))
                return

            # Manual entries count alongside the loaded CSV (SI1) — same
            # merge as the base class's _run_check.
            paths = [self.csv_path]
            if (USER_GENERATED_CSV.exists()
                    and str(USER_GENERATED_CSV) != self.csv_path):
                paths.append(str(USER_GENERATED_CSV))
            self.results = check_thresholds(
                paths,
                user_thresholds,
                league=self.league,
                max_level=51,
                evolution_lines=EVOLUTION_LINES,
                include_empty=True,
            )
            # csv_path is always a fixed cache filename (<= 20 chars)
            self.status_label_file.text = pathlib.Path(self.csv_path).name  # label-fits: fixed cache filename
            self._show_clear_btn(True)
            # _stats_line() (inherited) skeleton is ~25 chars
            self.status_label_stats.text = self._stats_line()  # label-fits: inherited _stats_line ~25 chars
            self._display_species_list()
        except Exception as e:
            logger.exception("check_thresholds failed")
            self.status_label_file.text = ""
            self._show_clear_btn(False)
            self.status_label_stats.text = f"Error: {e}"
            # Don't leave the previous check's hits on screen next to an
            # error claiming the read failed.
            self.results = {}
            self._display_species_list()
