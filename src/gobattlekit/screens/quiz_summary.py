#!/usr/bin/env python
"""
Quiz summary screen — shown after a quiz ends.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    btn_nav, card_box
)


class QuizSummaryScreen:
    """Summary screen shown after completing a quiz."""

    def __init__(self, app):
        self.app = app

    def build(self, stats):
        container = toga.Box(style=CONTAINER)

        # Title
        league = stats.get('league', '')
        if league in ('great', 'ultra', 'master'):
            title = f"{league.capitalize()} League Complete!"
        elif league == 'timing':
            title = "Move Timing Complete!"
        elif league == 'type':
            title = "Type Effectiveness Complete!"
        else:
            title = "Quiz Complete!"

        container.add(toga.Label(
            title,
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=20,
                       color=COLOR_ACCENT)
        ))

        score = stats.get('score', 0)
        max_score = stats.get('max_score', 0)
        pct = int(100 * score / max_score) if max_score > 0 else 0
        max_streak = stats.get('max_streak', 0)

        # Main score card
        score_card = toga.Box(style=card_box(margin_bottom=12))
        score_card.add(toga.Label(
            "Final Score",
            style=Pack(font_size=14, font_weight="bold",
                       margin_bottom=4, color=COLOR_YELLOW)
        ))
        score_card.add(toga.Label(
            f"{score} / {max_score} ({pct}%)",
            style=Pack(font_size=22, font_weight="bold",
                       color=COLOR_TEXT_LIGHT)
        ))
        container.add(score_card)

        # Streak card
        streak_card = toga.Box(style=card_box(margin_bottom=12))
        streak_card.add(toga.Label(
            "Best Streak",
            style=Pack(font_size=14, font_weight="bold",
                       margin_bottom=4, color=COLOR_YELLOW)
        ))
        streak_card.add(toga.Label(
            f"🔥 {max_streak} in a row",
            style=Pack(font_size=18, color=COLOR_TEXT_LIGHT)
        ))
        container.add(streak_card)

        # Breakdown card — move count quiz only. Shown when EITHER question
        # type was answered: gating on first_charge_total alone hid the
        # sequence stats for sessions that happened to serve only sequence
        # questions (SQ2).
        fc_correct = stats.get('first_charge_correct', 0)
        fc_total = stats.get('first_charge_total', 0)
        seq_correct = stats.get('sequence_correct', 0)
        seq_total = stats.get('sequence_total', 0)
        if fc_total > 0 or seq_total > 0:
            breakdown_card = toga.Box(style=card_box(margin_bottom=12))
            breakdown_card.add(toga.Label(
                "Question Breakdown",
                style=Pack(font_size=14, font_weight="bold",
                           margin_bottom=8, color=COLOR_YELLOW)
            ))
            if fc_total > 0:
                breakdown_card.add(toga.Label(
                    f"First charge move: {fc_correct} / {fc_total}",
                    style=Pack(font_size=15, margin_bottom=4,
                               color=COLOR_TEXT_LIGHT)
                ))
            if seq_total > 0:
                breakdown_card.add(toga.Label(
                    f"Sequence: {seq_correct} / {seq_total}",
                    style=Pack(font_size=15, color=COLOR_TEXT_LIGHT)
                ))
            container.add(breakdown_card)

        # Back to Home
        container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44)
        ))

        # Scroll-wrap so the bottom control stays reachable on small phones;
        # inert (no scroll) when the content already fits.
        return toga.ScrollContainer(
            content=container,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

