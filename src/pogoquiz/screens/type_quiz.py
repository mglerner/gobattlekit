#!/usr/bin/env python
"""
Type effectiveness quiz screen.
"""
import random
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.effectiveness import effectiveness, effectiveness_to_words

MAX_ATTEMPTS = 1


class TypeQuizScreen:
    """Quiz screen for type effectiveness questions."""

    def __init__(self, app):
        self.app = app

    def build(self):
        """Build and return the type quiz screen content."""
        self.score = 0
        self.total = 0
        self._load_question()

        # --- Outer container ---
        self.container = toga.Box(style=Pack(direction=COLUMN, padding=20, flex=1))

        # Score bar
        self.score_label = toga.Label(
            self._score_text(),
            style=Pack(font_size=14, padding_bottom=10, text_align="center")
        )
        self.container.add(self.score_label)

        # Question text
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=18, padding_bottom=20,
                       padding_left=10, padding_right=10,
                       height=80, flex=1)
        )
        self.container.add(self.question_label)
        self._set_question_text()

        # Feedback label
        self.feedback_label = toga.Label(
            "",
            style=Pack(font_size=16, padding_bottom=16, text_align="center")
        )
        self.container.add(self.feedback_label)

        # Answer buttons — one per effectiveness category
        self.button_box = toga.Box(style=Pack(direction=COLUMN, padding_bottom=10))
        self._build_answer_buttons()
        self.container.add(self.button_box)

        # End quiz button
        end_btn = toga.Button(
            "End Quiz",
            on_press=self._end_quiz,
            style=Pack(padding_top=30, height=44)
        )
        self.container.add(end_btn)

        return self.container

    # ------------------------------------------------------------------
    # Question loading
    # ------------------------------------------------------------------

    def _load_question(self):
        """Pick a random attacker and defender type."""
        types = list(effectiveness.keys())
        self.attacker = random.choice(types)
        self.defender = random.choice(types)
        self.right_answer = effectiveness_to_words[
            effectiveness[self.attacker][self.defender]
        ]

    def _set_question_text(self):
        """Set the question label text."""
        self.question_label.value = (
            f"How effective is {self.attacker} attacking against {self.defender}?"
        )

    # ------------------------------------------------------------------
    # Button construction
    # ------------------------------------------------------------------

    def _build_answer_buttons(self):
        """Build the four effectiveness answer buttons."""
        # Clear existing buttons
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        self.answer_buttons = {}
        answers = ['double resisted', 'not very effective', 'neutral', 'super effective']
        for answer in answers:
            btn = toga.Button(
                answer.capitalize(),
                on_press=self._make_answer_handler(answer),
                style=Pack(padding_bottom=8, height=52, font_size=16)
            )
            self.answer_buttons[answer] = btn
            self.button_box.add(btn)

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
        self.total += 1
        self._disable_buttons()
        if chosen == self.right_answer:
            self.score += 1
            self.score_label.text = self._score_text()
            self.feedback_label.text = "✅ Correct!"
        else:
            self.score_label.text = self._score_text()
            self.feedback_label.text = (
                f"❌ The answer was {self.right_answer}."
            )
        self.app.add_background_task(self._advance_question)

    def _disable_buttons(self):
        """Disable all answer buttons while waiting to advance."""
        for btn in self.answer_buttons.values():
            btn.enabled = False

    async def _advance_question(self, widget):
        """Pause briefly then load the next question."""
        await asyncio.sleep(1.5)
        self._load_question()
        self._set_question_text()
        self.feedback_label.text = ""
        self._build_answer_buttons()

    # ------------------------------------------------------------------
    # Score and navigation
    # ------------------------------------------------------------------

    def _score_text(self):
        """Format the running score display."""
        return f"Score: {self.score} / {self.total}"

    def _end_quiz(self, widget):
        """Show final score then return to home screen."""
        self.app.main_window.info_dialog(
            "Quiz Complete",
            f"Type Effectiveness\nFinal score: {self.score} / {self.total}"
        )
        self.app.show_home()
