#!/usr/bin/env python
"""
User IV checker screen — same as IV checker but uses user-defined thresholds.
"""
import toga
import sys
import pathlib
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from .iv_checker import IVCheckerScreen
from ..data.user_thresholds import load_user_thresholds
from ..data.iv_checker import check_thresholds
from ..data.thresholds import EVOLUTION_LINES

ON_ANDROID = sys.platform == 'android' or 'android' in sys.platform
ON_IOS = sys.platform == 'ios' or 'ios' in sys.platform


class UserIVCheckerScreen(IVCheckerScreen):
    """IV checker screen using user-defined thresholds."""

    def build(self):
        """Build and return the user IV checker screen content."""
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        # Title
        self.container.add(toga.Label(
            "My IV Checker",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10)
        ))

        # League selector row
        league_box = toga.Box(style=Pack(direction=ROW, margin_bottom=16))
        for league, label in (('great', 'Great'), ('ultra', 'Ultra'), ('master', 'Master')):
            btn = toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=Pack(flex=1, margin=4, height=40)
            )
            league_box.add(btn)
        self.container.add(league_box)

        # Import button — not available on iOS
        if not ON_IOS:
            import_btn = toga.Button(
                "Import PokeGenie CSV",
                on_press=self._import_csv,
                style=Pack(height=52, font_size=16, margin_bottom=8)
            )
            self.container.add(import_btn)
        

        # Edit Thresholds button
        self.container.add(toga.Button(
            "Edit My Thresholds",
            on_press=lambda w: self.app.show_edit_thresholds(),
            style=Pack(height=48, font_size=16, margin_bottom=12)
        ))

        # Status label
        initial_status = "No CSV loaded. Export from PokeGenie and share to GoBattleKit."
        csv_name_line = pathlib.Path(self.csv_path).name if self.csv_path else ""
        print(f"Dawg, my name line is {csv_name_line} and my path is {self.csv_path}")
        stats_line = ""
        if self.csv_path:
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            stats_line = (f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                          f"in {self.league.capitalize()} League")

        status_row = toga.Box(style=Pack(direction=ROW, margin_bottom=2))
        self.status_label_file = toga.Label(
            csv_name_line,
            style=Pack(flex=1, font_size=13, text_align="center")
        )
        self.clear_csv_btn = toga.Button(
            "✕",
            on_press=self._clear_csv,
            style=Pack(width=44, height=36)
        )
        self.clear_csv_btn.enabled = bool(self.csv_path)
        status_row.add(self.status_label_file)
        status_row.add(self.clear_csv_btn)
        self.container.add(status_row)

        self.status_label_stats = toga.Label(
            stats_line if stats_line else initial_status,
            style=Pack(font_size=13, text_align="center", margin_bottom=16)
        )
        self.container.add(self.status_label_stats)

        
        # Results area — scrollable
        self.results_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(content=self.results_box, style=Pack(flex=1))
        self.container.add(scroll)

        # Back button
        self.container.add(toga.Button(
            "Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=Pack(margin_top=10, height=44)
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
                self.status_label_stats.text = "No user thresholds defined. Tap 'Edit My Thresholds' to add some."
                for child in list(self.results_box.children):
                    self.results_box.remove(child)
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
