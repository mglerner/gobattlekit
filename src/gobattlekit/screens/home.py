#!/usr/bin/env python
"""
Home screen — league selection.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_BG, COLOR_TEXT_LIGHT,
    COLOR_SECONDARY_BTN, COLOR_NAV,
    btn_primary, btn_secondary, label_section, btn_help,
    btn_great, btn_ultra, btn_master
)


class HomeScreen:
    def __init__(self, app):
        self.app = app

    def build(self):
        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            "GoBattleKit",
            style=Pack(font_size=32, font_weight="bold",
                       margin_bottom=16, text_align="center",
                       color=COLOR_ACCENT)
        ))

        # Scroll the menu so the About/Help row stays reachable on smaller
        # phones (the fixed layout clipped it below the iPhone 17 Pro size).
        menu = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(horizontal=False, 
            content=menu,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        menu.add(toga.Label(
            "Quizzes",
            style=label_section(margin_top=0)
        ))
        for league, label, btn_fn in (
            ("great",  "Great League Move Counts", btn_great),
            ("ultra",  "Ultra League Move Counts", btn_ultra),
            ("master", "Master League Move Counts", btn_master),
        ):
            menu.add(toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=btn_fn()
            ))

        menu.add(toga.Button(
            "Optimal Move Timing",
            on_press=lambda w: self.app.show_timing_quiz(),
            style=btn_primary(margin_top=8)
        ))

        menu.add(toga.Button(
            "Type Effectiveness",
            on_press=self._start_type_quiz,
            style=btn_primary()
        ))

        menu.add(toga.Label(
            "IV Analysis",
            style=label_section()
        ))
        menu.add(toga.Button(
            "PvP IV Checker",
            on_press=self._start_iv_checker,
            style=btn_primary()
        ))
        menu.add(toga.Button(
            "My PvP IV Targets",
            on_press=self._start_user_iv_checker,
            style=btn_primary()
        ))

        container.add(scroll)

        bottom_row = toga.Box(style=Pack(direction=ROW, margin_top=8))
        bottom_row.add(toga.Button(
            "About",
            on_press=lambda w: self.app.show_about(),
            style=Pack(flex=1, height=44, margin_right=4,
                       background_color=COLOR_SECONDARY_BTN,
                       color=COLOR_TEXT_LIGHT)
        ))
        bottom_row.add(toga.Button(
            "Help",
            on_press=lambda w: self.app.show_help(),
            style=btn_help(flex=1, margin_bottom=0)
        ))
        container.add(bottom_row)
        
        return container

    def _make_league_handler(self, league):
        def handler(widget):
            self.app.show_quiz(league)
        return handler

    def _start_type_quiz(self, widget):
        self.app.show_type_quiz()

    def _start_iv_checker(self, widget):
        self.app.show_iv_checker()

    def _start_user_iv_checker(self, widget):
        self.app.show_user_iv_checker()
