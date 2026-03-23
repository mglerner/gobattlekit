#!/usr/bin/env python
"""
Home screen — league selection.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN


class HomeScreen:
    """Home screen with league selection buttons."""

    def __init__(self, app):
        self.app = app

    def build(self):
        """Build and return the home screen content."""
        container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        title = toga.Label(
            "GoBattleKit",
            style=Pack(font_size=32, font_weight="bold", margin_bottom=10,
                       text_align="center")
        )
        container.add(title)
        ## subtitle = toga.Label(
        ##     "Choose a quiz to begin",
        ##     style=Pack(font_size=16, margin_bottom=20, text_align="center")
        ## )
        ## container.add(subtitle)

        # Move count quizzes by league
        league_label = toga.Label(
            "Move Count Quizzes",
            style=Pack(font_size=22, margin_bottom=8, text_align="center")
        )
        container.add(league_label)

        for league, label in (
            ("great",  "Great League (1500 CP)"),
            ("ultra",  "Ultra League (2500 CP)"),
            ("master", "Master League"),
        ):
            btn = toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=Pack(margin_bottom=12, height=60, font_size=18)
            )
            container.add(btn)

        # Divider label
        type_label = toga.Label(
            "Type Effectiveness Quiz",
            style=Pack(font_size=22, margin_top=16, margin_bottom=8,
                       text_align="center")
        )
        container.add(type_label)

        type_btn = toga.Button(
            "Type Quiz",
            on_press=self._start_type_quiz,
            style=Pack(margin_bottom=12, height=60, font_size=18)
        )
        container.add(type_btn)

        iv_label = toga.Label(
            "IV Analysis",
            style=Pack(font_size=22, margin_top=16, margin_bottom=8,
                       text_align="center")
        )
        container.add(iv_label)
        iv_btn = toga.Button(
            "IV Checker",
            on_press=self._start_iv_checker,
            style=Pack(margin_bottom=8, height=60, font_size=18)
        )
        container.add(iv_btn)
        my_iv_btn = toga.Button(
            "My IV Checker",
            on_press=self._start_user_iv_checker,
            style=Pack(margin_bottom=12, height=60, font_size=18)
        )
        container.add(my_iv_btn)

        container.add(toga.Button(
            "About",
            on_press=lambda w: self.app.show_about(),
            style=Pack(margin_top=16, height=44)
        ))

        return container

    def _make_league_handler(self, league):
        """Return a button handler for the given league."""
        def handler(widget):
            self.app.show_quiz(league)
        return handler

    def _start_type_quiz(self, widget):
        """Switch to the type effectiveness quiz screen."""
        self.app.show_type_quiz()
        
    def _start_iv_checker(self, widget):
        """Switch to the IV checker screen."""
        self.app.show_iv_checker()

    def _start_user_iv_checker(self, widget):
        """Switch to the user IV checker screen."""
        self.app.show_user_iv_checker()        
