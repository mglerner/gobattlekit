#!/usr/bin/env python
"""
Reusable intro/onboarding screen shown before a feature.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.preferences import get_pref, set_pref
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    COLOR_SECONDARY_BTN, COLOR_NAV,
    btn_primary, btn_nav, card_box
)


# Intro content for each feature.
# Each entry: (pref_key, title, list of (heading, body) paragraphs)
INTROS = {
    "move_count_quiz": (
        "Move Count Quiz",
        [
            ("", "Practice counting how many fast moves it takes to "
             "reach a charge move in PvP."),
            ("How it works", "You'll be shown a Pokémon's fast move and "
             "charge move, and asked how many fast moves are needed. "
             "Some questions ask about the first charge move; others "
             "ask for a sequence of the first several."),
            ("Scoring", "Each question is worth up to 3 points — you "
             "get 3 for a correct first attempt, 2 for second, and 1 "
             "for third. You have 3 attempts per question."),
        ],
    ),
    "timing_quiz": (
        "Optimal Move Timing",
        [
            ("", "In PvP, throwing your charge move at the right time "
             "minimizes free turns you give your opponent."),
            ("How it works", "You'll be shown your fast move's turn count "
             "and your opponent's, and asked how many fast moves to throw "
             "before using your charge move."),
            ("Scoring", "Same as the move count quiz: up to 3 points per "
             "question, with 3 attempts allowed."),
        ],
    ),
    "type_quiz": (
        "Type Effectiveness",
        [
            ("", "Practice type matchups from Pokémon GO PvP."),
            ("How it works", "You'll be shown an attacking type and a "
             "defending type (or type pair), and asked whether the attack "
             "is super effective, not very effective, neutral, or double "
             "resisted."),
            ("Scoring", "Each question is worth 1 point — you get one "
             "attempt per question, so answer carefully!"),
        ],
    ),
    "iv_checker": (
        "PvP IV Checker",
        [
            ("", "Check your Pokémon against curated PvP IV targets for "
             "Great, Ultra, and Master League."),
            ("Getting your data in", "You can import a CSV export from "
             "PokeGenie (requires iVision subscription), or enter "
             "Pokémon one at a time using manual entry."),
            ("Reading results", "Tap a species to see which of your "
             "Pokémon meet the targets. SP (stat product) measures "
             "overall PvP performance. Rank shows how an IV combination "
             "compares to all 4096 possibilities."),
        ],
    ),
    "user_iv_checker": (
        "My PvP IV Targets",
        [
            ("", "Set your own custom IV targets and check your Pokémon "
             "against them."),
            ("Getting started", "Tap 'Edit My Targets' to create targets. "
             "Choose a species, league, and minimum stats. Then import a "
             "PokeGenie CSV or enter Pokémon manually to see results."),
            ("Sharing", "You can share targets with friends using the "
             "export button, and import targets others have shared."),
        ],
    ),
}


class IntroScreen:
    """Reusable intro screen shown before a feature."""

    def __init__(self, app):
        self.app = app

    def build(self, feature_key, on_continue):
        """Build the intro screen.

        feature_key: key into INTROS dict
        on_continue: callable to invoke when the user taps "Let's go!"
        """
        self._feature_key = feature_key
        self._on_continue = on_continue

        title, sections = INTROS[feature_key]

        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            title,
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=16,
                       color=COLOR_ACCENT)
        ))

        content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(
            content=content_box,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        for heading, body in sections:
            card = toga.Box(style=card_box(margin_bottom=12))
            if heading:
                card.add(toga.Label(
                    heading,
                    style=Pack(font_size=14, font_weight="bold",
                               margin_bottom=4, color=COLOR_YELLOW)
                ))
            lines = body.count('\n') + len(body) // 35 + 2
            card.add(toga.MultilineTextInput(
                value=body,
                readonly=True,
                style=Pack(font_size=14, color=COLOR_TEXT_LIGHT,
                           height=max(70, lines * 24))
            ))
            content_box.add(card)

        container.add(scroll)

        self._skip_next_time = False
        self._toggle_btn = toga.Button(
            "☐ Don't show this again",
            on_press=self._toggle_skip,
            style=Pack(height=40, font_size=13, margin_bottom=8,
                       background_color=COLOR_SECONDARY_BTN,
                       color=COLOR_TEXT_LIGHT)
        )
        container.add(self._toggle_btn)

        container.add(toga.Button(
            "Let's go!",
            on_press=self._continue,
            style=btn_primary(height=52, font_size=18, margin_bottom=8)
        ))

        container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44)
        ))

        return container

    def _toggle_skip(self, widget):
        self._skip_next_time = not self._skip_next_time
        pref_key = f"skip_intro_{self._feature_key}"
        if self._skip_next_time:
            self._toggle_btn.text = "☑ Don't show this again"
            set_pref(pref_key, True)
        else:
            self._toggle_btn.text = "☐ Don't show this again"
            set_pref(pref_key, False)

    def _continue(self, widget):
        self._on_continue()
