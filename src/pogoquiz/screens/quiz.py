#!/usr/bin/env python
"""
Quiz screen — move timing questions.
"""
import random
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.gamemaster import get_moves, get_rankings, counters_to_charge

MAX_ATTEMPTS = 3
POINTS = {1: 3, 2: 2, 3: 1}  # points for correct on attempt N


class QuizScreen:
    """Quiz screen for move timing questions."""

    def __init__(self, app):
        self.app = app
        self.fastmoves, self.chargedmoves = get_moves()

    def build(self, league):
        """Build and return the quiz screen content for the given league."""
        self.league = league
        self.mons = get_rankings(league)
        self.score = 0
        self.max_score = 0
        self.attempts = 0
        self._load_question()

        # --- Outer container ---
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        # Score bar
        self.score_label = toga.Label(
            self._score_text(),
            style=Pack(font_size=14, margin_bottom=10, text_align="center")
        )
        self.container.add(self.score_label)

        # Question text — MultilineTextInput so text wraps properly
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=18, margin_bottom=20,
                       margin_left=10, margin_right=10,
                       height=120, flex=1)
        )
        self.container.add(self.question_label)

        # Set question text now that the widget exists
        self._set_question_text(self.mon_name, self.fast_name, self.charged_name)

        # Feedback label (hidden until answered)
        self.feedback_label = toga.Label(
            "",
            style=Pack(font_size=16, margin_bottom=16, text_align="center")
        )
        self.container.add(self.feedback_label)

        # Answer buttons: 1-20 + "more"
        self.button_box = toga.Box(style=Pack(direction=COLUMN))
        self._build_answer_buttons()
        self.container.add(self.button_box)

        # End quiz button
        end_btn = toga.Button(
            "End Quiz",
            on_press=self._end_quiz,
            style=Pack(margin_top=30, height=44)
        )
        self.container.add(end_btn)

        return self.container

    # ------------------------------------------------------------------
    # Question loading
    # ------------------------------------------------------------------

    def _load_question(self):
        """Pick a random mon and moveset, compute the right answer."""
        mon = random.choice(self.mons)
        self.fast_id = mon['moveset'][0]
        self.charged_id = random.choice(mon['moveset'][1:])
        self.right_answer = counters_to_charge(
            self.fast_id, self.charged_id,
            self.fastmoves, self.chargedmoves
        )
        self.fast_name = self.fastmoves[self.fast_id]['name']
        self.charged_name = self.chargedmoves[self.charged_id]['name']
        self.mon_name = mon['speciesName']
        self.attempts = 0

    # ------------------------------------------------------------------
    # Button construction
    # ------------------------------------------------------------------

    def _build_answer_buttons(self):
        """Build the 1-20 + more answer buttons in a grid, 5 per row."""
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        self.answer_buttons = {}
        answers = list(range(1, 21)) + ['more']
        row = None
        for i, val in enumerate(answers):
            if i % 5 == 0:
                row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
                self.button_box.add(row)
            btn = toga.Button(
                str(val),
                on_press=self._make_answer_handler(val),
                style=Pack(flex=1, margin=4, height=52, font_size=16)
            )
            self.answer_buttons[val] = btn
            row.add(btn)

    def _make_answer_handler(self, value):
        """Return a button handler for the given answer value."""
        def handler(widget):
            self._check_answer(value)
        return handler

    # ------------------------------------------------------------------
    # Answer checking and feedback
    # ------------------------------------------------------------------

    def _check_answer(self, chosen):
        """Handle a user's answer choice."""
        self.attempts += 1
        if chosen == self.right_answer:
            pts = POINTS.get(self.attempts, 1)
            self.score += pts
            self.max_score += 3
            self.score_label.text = self._score_text()
            self.feedback_label.text = f"✅ Correct! +{pts} point{'s' if pts != 1 else ''}"
            self._disable_buttons()
            asyncio.create_task(self._advance_question())
        else:
            if self.attempts >= MAX_ATTEMPTS:
                self.max_score += 3
                self.score_label.text = self._score_text()
                self.feedback_label.text = (
                    f"❌ The answer was {self.right_answer}."
                )
                self._disable_buttons()
                asyncio.create_task(self._advance_question())
            else:
                remaining = MAX_ATTEMPTS - self.attempts
                self.feedback_label.text = (
                    f"❌ Try again! {remaining} attempt{'s' if remaining != 1 else ''} left."
                )

    def _set_question_text(self, mon_name, fast_name, charged_name):
        """Set question text — MultilineTextInput handles wrapping automatically."""
        self.question_label.value = (
            f"How many {fast_name}s does it take "
            f"{mon_name} to charge {charged_name}?"
        )

    def _disable_buttons(self):
        """Disable all answer buttons while waiting to advance."""
        for btn in self.answer_buttons.values():
            btn.enabled = False

    async def _advance_question(self):
        """Pause briefly then load the next question."""
        await asyncio.sleep(1.5)
        self._load_question()
        self._set_question_text(self.mon_name, self.fast_name, self.charged_name)
        self.feedback_label.text = ""
        self._build_answer_buttons()

    # ------------------------------------------------------------------
    # Score and navigation
    # ------------------------------------------------------------------

    def _score_text(self):
        """Format the running score display."""
        return f"Score: {self.score} / {self.max_score}"

    async def _end_quiz(self, widget):
        """Show final score then return to home screen."""
        league_name = self.league.capitalize()
        await self.app.main_window.dialog(
            toga.InfoDialog(
                "Quiz Complete",
                f"{league_name} League\nFinal score: {self.score} / {self.max_score}"
            )
        )
        self.app.show_home()
        
