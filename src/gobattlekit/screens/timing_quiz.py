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
    CONTAINER, COLOR_TEXT_LIGHT, COLOR_YELLOW,
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
        # Build set of fast move IDs used by ranked mons across all leagues
        all_mons = []
        for league in ('great', 'ultra', 'master'):
            all_mons.extend(get_rankings(league))
        self.ranked_fast_move_ids = list({
            mon['moveset'][0]
            for mon in all_mons
            if mon.get('moveset')
        })

    def build(self):
        self.score = 0
        self.total = 0
        self.attempts = 0
        self._load_question()

        self.container = toga.Box(style=CONTAINER)

        self.score_label = toga.Label(
            self._score_text(),
            style=Pack(font_size=14, margin_bottom=10, text_align="center",
                       color=COLOR_YELLOW)
        )
        self.container.add(self.score_label)

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

        self.button_box = toga.Box(style=Pack(direction=COLUMN), flex=1)
        self._build_answer_buttons()
        self.container.add(self.button_box)

        self.container.add(toga.Button(
            "End Quiz",
            on_press=self._end_quiz,
            style=btn_nav(height=44)
        ))

        return self.container

    # ------------------------------------------------------------------
    # Question loading
    # ------------------------------------------------------------------

    def _load_question(self):
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
        #random.shuffle(self.timing_choices)

    # ------------------------------------------------------------------
    # Button construction
    # ------------------------------------------------------------------

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)
        self.answer_buttons = {}

        # Separate out "timing doesn't matter" (None) from the rest
        pattern_choices = [p for p in self.timing_choices if p is not None]

        left_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
        right_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_left=4))
        cols_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
        cols_row.add(left_col)
        cols_row.add(right_col)
        self.button_box.add(cols_row)

        # ceil(9/2) = 5 + 1 for the doesn't matter button
        total_rows = ((len(pattern_choices) + 1) // 2) + 1  
        for i, pattern in enumerate(pattern_choices):
            row_index = i // 2  # same color for both buttons in a row
            label = format_timing_pattern(pattern)
            btn = toga.Button(
                label,
                on_press=self._make_answer_handler(pattern),
                style=Pack(height=48, font_size=13, margin_bottom=4,
                           background_color=answer_color_gradient(total_rows, row_index),
                           color=COLOR_TEXT_LIGHT)
            )        
            self.answer_buttons[i] = btn
            if i % 2 == 0:
                left_col.add(btn)
            else:
                right_col.add(btn)

        # "Timing doesn't matter" as full-width button at the bottom
        tdm_btn = toga.Button(
            "Timing doesn't matter",
            on_press=self._make_answer_handler(None),
            style=Pack(height=48, font_size=13, margin_bottom=4,
                       background_color=answer_color_gradient(total_rows,total_rows),
                       color=COLOR_TEXT_LIGHT)
        )
        self.answer_buttons[len(pattern_choices)] = tdm_btn
        self.button_box.add(tdm_btn)    

    def _make_answer_handler(self, pattern):
        def handler(widget):
            self._check_answer(pattern)
        return handler

    # ------------------------------------------------------------------
    # Answer checking
    # ------------------------------------------------------------------

    def _check_answer(self, chosen):
        self.attempts += 1
        if chosen == self.right_answer:
            pts = POINTS.get(self.attempts, 1)
            self.score += pts
            self.total += 3
            self.score_label.text = self._score_text()
            self.feedback_label.text = f"✅ Correct! +{pts} point{'s' if pts != 1 else ''}"
            self._disable_buttons()
            asyncio.create_task(self._advance_question())
        else:
            if self.attempts >= MAX_ATTEMPTS:
                self.total += 3
                self.score_label.text = self._score_text()
                correct_str = format_timing_pattern(self.right_answer)
                self.feedback_label.text = f"❌ The answer was: {correct_str}."
                self._disable_buttons()
                asyncio.create_task(self._advance_question())
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

    async def _advance_question(self):
        await asyncio.sleep(1.5)
        self._load_question()
        self._set_question_text()
        self.feedback_label.text = ""
        self._build_answer_buttons()

    def _score_text(self):
        return f"Score: {self.score} / {self.total}"

    async def _end_quiz(self, widget):
        await self.app.main_window.dialog(
            toga.InfoDialog(
                "Quiz Complete",
                f"Move Timing\nFinal score: {self.score} / {self.total}"
            )
        )
        self.app.show_home()
