#!/usr/bin/env python
"""
Move timing quiz screen — optimal charge move timing based on fast move matchups.
"""
import random
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.gamemaster import (
    get_moves, get_rankings,
    OPTIMAL_TIMING, ALL_TIMING_PATTERNS, format_timing_pattern,
)
from ..platform import ON_ANDROID
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    COLOR_SECONDARY_BTN,
    answer_color_gradient,
    btn_nav
)

MAX_ATTEMPTS = 3
POINTS = {1: 3, 2: 2, 3: 1}


class TimingQuizScreen:
    """Quiz screen for optimal move timing questions."""

    def __init__(self, app):
        self.app = app
        self.fastmoves, _ = get_moves()
        self._advance_task = None
        all_mons = []
        for league in ('great', 'ultra', 'master'):
            all_mons.extend(get_rankings(league))
        self.ranked_fast_move_ids = list({
            mon['moveset'][0]
            for mon in all_mons
            if mon.get('moveset')
        })

    def build(self):
        self._cancel_advance_task()
        self.score = 0
        self.total = 0
        self.attempts = 0
        self.streak = 0
        self.max_streak = 0
        self._load_question()

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
        question_height = 200 if ON_ANDROID else 160
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=18, margin_bottom=20,
                       margin_left=10, margin_right=10,
                       height=question_height, flex=1,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.question_label)
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

        return self.container

    def _load_question(self):
        # Guards against a natively queued duplicate tap double-resolving
        # the question (same pattern as quiz.py).
        self._question_over = False
        self.attempts = 0
        your_id = random.choice(self.ranked_fast_move_ids)
        their_id = random.choice(self.ranked_fast_move_ids)
        self.your_fast_name = self.fastmoves[your_id]['name']
        self.their_fast_name = self.fastmoves[their_id]['name']
        self.your_turns = self.fastmoves[your_id].get('turns', 1)
        self.their_turns = self.fastmoves[their_id].get('turns', 1)

        your_t = min(self.your_turns, 5)
        their_t = min(self.their_turns, 5)
        self.right_answer = OPTIMAL_TIMING.get((your_t, their_t), None)

        self.timing_choices = list(ALL_TIMING_PATTERNS)

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)
        self.answer_buttons = {}

        pattern_choices = [p for p in self.timing_choices if p is not None]

        left_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
        right_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_left=4))
        cols_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
        cols_row.add(left_col)
        cols_row.add(right_col)
        self.button_box.add(cols_row)

        total_rows = ((len(pattern_choices) + 1) // 2) + 1
        for i, pattern in enumerate(pattern_choices):
            row_index = i // 2
            label = format_timing_pattern(pattern)
            btn = toga.Button(
                label,
                on_press=self._make_answer_handler(pattern),
                style=Pack(height=48, font_size=13, margin_bottom=4,
                           background_color=answer_color_gradient(total_rows, row_index),
                           color=COLOR_TEXT_LIGHT)
            )
            # Keyed by the pattern VALUE (like quiz.py keys by answer), so
            # highlight lookup can't desync from button layout.
            self.answer_buttons[pattern] = btn
            if i % 2 == 0:
                left_col.add(btn)
            else:
                right_col.add(btn)

        tdm_btn = toga.Button(
            "Timing doesn't matter",
            on_press=self._make_answer_handler(None),
            style=Pack(height=48, font_size=13, margin_bottom=4,
                       background_color=answer_color_gradient(total_rows, total_rows - 1),
                       color=COLOR_TEXT_LIGHT)
        )
        self.answer_buttons[None] = tdm_btn
        self.button_box.add(tdm_btn)

    def _make_answer_handler(self, pattern):
        def handler(widget):
            self._check_answer(pattern)
        return handler

    def _highlight_correct_button(self):
        """Highlight the correct answer button in teal."""
        # Buttons are keyed by pattern value (None = "Timing doesn't
        # matter"), so this is a direct lookup.
        correct_btn = self.answer_buttons.get(self.right_answer)
        if correct_btn:
            correct_btn.style.background_color = COLOR_ACCENT

    def _check_answer(self, chosen):
        if self._question_over:
            return
        self.attempts += 1
        if chosen == self.right_answer:
            self._question_over = True
            pts = POINTS.get(self.attempts, 1)
            self.score += pts
            self.total += 3
            if self.attempts == 1:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
            else:
                self.streak = 0
            self.score_label.text = self._score_text()
            self.feedback_label.text = f"✅ Correct! +{pts} point{'s' if pts != 1 else ''}"
            self._highlight_correct_button()
            self._disable_buttons()
            self._advance_task = asyncio.create_task(self._advance_question())
        else:
            self.streak = 0
            if self.attempts >= MAX_ATTEMPTS:
                self._question_over = True
                self.total += 3
                self.score_label.text = self._score_text()
                correct_str = format_timing_pattern(self.right_answer)
                self.feedback_label.text = f"❌ The answer was: {correct_str}."
                self._highlight_correct_button()
                self._disable_buttons()
                self._advance_task = asyncio.create_task(self._advance_question(delay=2.5))
            else:
                remaining = MAX_ATTEMPTS - self.attempts
                self.feedback_label.text = (
                    f"❌ Try again! {remaining} attempt{'s' if remaining != 1 else ''} left."
                )

    def _set_question_text(self):
        self.question_label.value = (
            f"You're using {self.your_fast_name} ({self.your_turns} turn). "
            f"Your opponent is using {self.their_fast_name} ({self.their_turns} turn). "
            f"What's the most optimal timing to throw your charge move?"
        )

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
            return f"Score: {self.score} / {self.total} 🔥{self.streak}"
        return f"Score: {self.score} / {self.total}"

    def _cancel_advance_task(self):
        if self._advance_task and not self._advance_task.done():
            self._advance_task.cancel()
        self._advance_task = None

    def _end_quiz(self, widget):
        self._cancel_advance_task()
        stats = {
            'score': self.score,
            'max_score': self.total,
            'max_streak': self.max_streak,
            'league': 'timing',
        }
        self.app.show_quiz_summary(stats)
