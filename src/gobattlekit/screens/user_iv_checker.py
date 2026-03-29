#!/usr/bin/env python
"""
User IV checker screen — same as IV checker but uses user-defined thresholds.
"""
import toga
import pathlib
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from .iv_checker import IVCheckerScreen
from ..data.user_thresholds import load_user_thresholds
from ..data.iv_checker import check_thresholds
from ..data.thresholds import EVOLUTION_LINES
from ..platform import ON_ANDROID, ON_IOS, ON_MOBILE
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_BG,
    btn_primary, btn_secondary, btn_back, btn_nav, btn_league, btn_icon,
    btn_destructive, btn_destructive_icon, btn_help
)

NO_TARGETS_MESSAGE = "No user IV targets defined. Tap 'Edit My Targets' to add some."
GETTING_STARTED = (
    "To get started:\n1. Tap 'Edit My Targets'\n2. Tap 'Add Target'\n"
    "3. Choose a species and\nset minimum stats\n4. Tap 'Save Target'\n"
    "5. Make sure a PokeGenie\nCSV is imported"
)


class UserIVCheckerScreen(IVCheckerScreen):
    """IV checker screen using user-defined thresholds."""

    def build(self):
        """Build and return the user IV checker screen content."""
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

        csv_name_line = pathlib.Path(self.csv_path).name if self.csv_path else ""
        stats_line = ""
        if self.csv_path:
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            stats_line = (f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                          f"in {self.league.capitalize()} League")

        status_row = toga.Box(style=Pack(direction=ROW, margin_bottom=2, height=36))
        self.status_label_file = toga.Label(
            csv_name_line,
            style=Pack(flex=1, font_size=13, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.clear_csv_btn = toga.Button(
            "✕",
            on_press=self._clear_csv,
            style=btn_destructive_icon()
        )
        self.clear_csv_btn.enabled = bool(self.csv_path)
        status_row.add(self.status_label_file)
        status_row.add(self.clear_csv_btn)
        self.container.add(status_row)

        self.status_label_stats = toga.Label(
            stats_line if stats_line else self.NO_CSV_MESSAGE,
            style=Pack(font_size=13, text_align="center", margin_bottom=4,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.status_label_stats)

        self.results_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=COLOR_BG))
        scroll = toga.ScrollContainer(content=self.results_box,
                                      style=Pack(flex=1, background_color=COLOR_BG))
        self.container.add(scroll)

        if not load_user_thresholds():
            self.results_box.add(toga.Label(
                GETTING_STARTED,
                style=Pack(font_size=14, text_align="center",
                           margin_top=20, color=COLOR_TEXT_LIGHT)
            ))
        elif not self.csv_path:
            self.results_box.add(toga.Label(
                "Share CSV from PokeGenie → GoBattleKit" if ON_IOS else "Tap 'Import PokeGenie CSV' to get started.",
                style=Pack(font_size=14, text_align="center",
                           margin_top=20, color=COLOR_TEXT_LIGHT)
            ))

        # Dynamic back button — hidden on species list, shown on detail views
        self.back_btn = toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        )
        self.back_btn.enabled = False
        self.back_btn.style.height = 2
        self.back_btn.style.margin_bottom = 0
        self.container.add(self.back_btn)

        self.container.add(toga.Button(
            "?  Help",
            on_press=lambda w: self.app.show_help(
                topic="My PvP IV Targets",
                back_screen=lambda: self.app.show_user_iv_checker(),
                back_label="← My PvP IV Targets"
            ),
            style=btn_help()
        ))

        self.container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44)
        ))

        if self.results:
            self._display_species_list()

        return self.container

    def _run_check(self):
        """Run the IV check against user thresholds."""
        if not self.csv_path:
            return
        try:
            user_thresholds = load_user_thresholds()
            if not user_thresholds:
                self.status_label_file.text = ""
                self.clear_csv_btn.enabled = False
                self.status_label_stats.text = NO_TARGETS_MESSAGE
                for child in list(self.results_box.children):
                    self.results_box.remove(child)
                self.results_box.add(toga.Label(
                    GETTING_STARTED,
                    style=Pack(font_size=14, text_align="center",
                               margin_top=20, color=COLOR_TEXT_LIGHT)
                ))
                return

            self.results = check_thresholds(
                self.csv_path,
                user_thresholds,
                league=self.league,
                max_level=51,
                evolution_lines=EVOLUTION_LINES,
            )
            self.status_label_file.text = pathlib.Path(self.csv_path).name
            self.clear_csv_btn.enabled = True
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            self.status_label_stats.text = (
                f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                f"in {self.league.capitalize()} League"
            )
            self._display_species_list()
        except Exception as e:
            self.status_label_file.text = ""
            self.clear_csv_btn.enabled = False
            self.status_label_stats.text = f"Error: {e}"
