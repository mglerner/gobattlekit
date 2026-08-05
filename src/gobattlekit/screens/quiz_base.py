#!/usr/bin/env python
"""
Shared scaffolding for the quiz screens (move-count, timing, type).

Holds the chrome all three build identically (score header, fixed-height
question box, feedback line, answer area, End Quiz button) plus the
answer/advance plumbing. Each screen keeps its own question generation,
scoring rules and answer-button layout.
"""
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..platform import ON_ANDROID
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_BG, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_nav, answer_color_gradient
)

MAX_ATTEMPTS = 3
POINTS = {1: 3, 2: 2, 3: 1}

# Android needs more room for the same question text.
QUESTION_HEIGHT = 160 if ON_ANDROID else 120


def build_two_column_answers(button_box, answers, make_handler, font_size=14):
    """Fill button_box with a two-column answer grid.

    answers is a list of (value, label) pairs laid out left/right alternating;
    the returned dict is keyed by the answer VALUE so highlight lookup can't
    desync from button layout.
    """
    left_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
    right_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_left=4))
    cols_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
    cols_row.add(left_col)
    cols_row.add(right_col)
    button_box.add(cols_row)

    buttons = {}
    total_rows = (len(answers) + 1) // 2
    for i, (key, label) in enumerate(answers):
        row_index = i // 2
        btn = toga.Button(
            label,
            on_press=make_handler(key),
            style=Pack(height=48, font_size=font_size, margin_bottom=4,
                       background_color=answer_color_gradient(total_rows, row_index),
                       color=COLOR_TEXT_LIGHT)
        )
        buttons[key] = btn
        if i % 2 == 0:
            left_col.add(btn)
        else:
            right_col.add(btn)
    return buttons


class QuizScreenBase:
    """Shared chrome and answer plumbing for the quiz screens."""

    def __init__(self, app):
        self.app = app
        self._advance_task = None

    def _build_scaffold(self, question_height, question_font_size):
        """Build the shared quiz chrome and return the ScrollContainer.

        Subclasses set up their question state (and self.league) first, then
        call this; it calls back into _build_extras, _set_question_text and
        _build_answer_buttons.
        """
        self.container = toga.Box(style=CONTAINER)

        self.score_label = toga.Label(
            self._score_text(),
            style=Pack(font_size=14, margin_bottom=10, text_align="center",
                       color=COLOR_YELLOW)
        )
        self.container.add(self.score_label)

        # NOTE: intentionally NOT using theme.paragraph_text here. Question
        # text needs a fixed height across questions of varying length so
        # the answer buttons below don't jump around between questions.
        # See DEVELOPER_NOTES "Wrapping paragraph text".
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=question_font_size, margin_bottom=20,
                       margin_left=10, margin_right=10,
                       height=question_height, flex=1,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.question_label)
        self._build_extras()
        self._set_question_text()

        self.feedback_label = toga.Label(
            "",
            style=Pack(font_size=16, margin_bottom=16, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.feedback_label)

        self.button_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self._build_answer_buttons()
        self.container.add(self.button_box)

        self.container.add(toga.Button(
            "End Quiz",
            on_press=self._end_quiz,
            style=btn_nav(height=44)
        ))

        # Scroll-wrap so the bottom controls stay reachable on small phones;
        # inert (no scroll) when the content already fits.
        return toga.ScrollContainer(
            content=self.container,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

    def _build_extras(self):
        """Hook for widgets a screen adds between question and feedback."""

    def _make_answer_handler(self, value):
        def handler(widget):
            self._check_answer(value)
        return handler

    def _highlight_correct_button(self):
        """Highlight the correct answer button in teal."""
        correct_btn = self.answer_buttons.get(self.right_answer)
        if correct_btn:
            correct_btn.style.background_color = COLOR_ACCENT

    def _disable_buttons(self):
        for btn in self.answer_buttons.values():
            btn.enabled = False

    async def _advance_question(self, delay=1.5):
        await asyncio.sleep(delay)
        self._load_question()
        self._set_question_text()
        self.feedback_label.text = ""
        self._build_answer_buttons()

    def _score_text(self):
        if self.streak > 0:
            return f"Score: {self.score} / {self.max_score} 🔥{self.streak}"
        return f"Score: {self.score} / {self.max_score}"

    def _refresh_score(self):
        self.score_label.text = self._score_text()

    def _cancel_advance_task(self):
        if self._advance_task and not self._advance_task.done():
            self._advance_task.cancel()
        self._advance_task = None

    def _extra_stats(self):
        """Per-screen breakdown counters merged into the summary stats."""
        return {}

    def _end_quiz(self, widget):
        self._cancel_advance_task()
        stats = {
            'score': self.score,
            'max_score': self.max_score,
            'max_streak': self.max_streak,
            'league': self.league,
        }
        stats.update(self._extra_stats())
        self.app.show_quiz_summary(stats)
