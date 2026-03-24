#!/usr/bin/env python
"""
Home screen — league selection.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT,
    btn_primary, btn_secondary, btn_league
)


class HomeScreen:
    def __init__(self, app):
        self.app = app

    def build(self):
        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            "GoBattleKit",
            style=Pack(font_size=32, font_weight="bold",
                       margin_bottom=20, text_align="center",
                       color=COLOR_ACCENT)
        ))

        container.add(toga.Label(
            "Move Count Quizzes",
            style=Pack(font_size=22, font_weight="bold",
                       text_align="center", margin_bottom=8,
                       color=COLOR_TEXT_LIGHT)
        ))
        for league, label in (
            ("great",  "Great League (1500 CP)"),
            ("ultra",  "Ultra League (2500 CP)"),
            ("master", "Master League"),
        ):
            container.add(toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=btn_primary(height=60, font_size=18)
            ))

        container.add(toga.Label(
            "Type Effectiveness Quiz",
            style=Pack(font_size=22, font_weight="bold",
                       text_align="center", margin_bottom=8, margin_top=16,
                       color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "Type Quiz",
            on_press=self._start_type_quiz,
            style=btn_primary(height=60, font_size=18)
        ))

        container.add(toga.Label(
            "IV Analysis",
            style=Pack(font_size=22, font_weight="bold",
                       text_align="center", margin_bottom=8, margin_top=16,
                       color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "IV Checker",
            on_press=self._start_iv_checker,
            style=btn_primary(height=60, font_size=18, margin_bottom=8)
        ))
        container.add(toga.Button(
            "My IV Checker",
            on_press=self._start_user_iv_checker,
            style=btn_primary(height=60, font_size=18)
        ))

        container.add(toga.Button(
            "About",
            on_press=lambda w: self.app.show_about(),
            style=btn_secondary(height=44, margin_bottom=0)
        ))

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
