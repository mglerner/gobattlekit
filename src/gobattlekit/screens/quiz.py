#!/usr/bin/env python
"""
Quiz screen — move timing questions.
"""
import random
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.gamemaster import get_moves, get_rankings, counters_to_charge, charge_sequence
from ..platform import ON_ANDROID
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_BG, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_nav, answer_color_gradient
)

MAX_ATTEMPTS = 3
POINTS = {1: 3, 2: 2, 3: 1}

QUESTION_TYPE_FIRST = 'first'
QUESTION_TYPE_SEQUENCE = 'sequence'

MAX_FIRST_STREAK = 4
MAX_SEQUENCE_STREAK = 2
FIRST_WEIGHT = 0.7


class QuizScreen:
    """Quiz screen for move timing questions."""

    def __init__(self, app):
        # No data loads here: screens are constructed during startup(), and
        # a cold/stale cache would put network fetches on the launch path
        # (iOS watchdog risk — AP2/DL4). First build() pays instead.
        self.app = app
        self.fastmoves = None
        self.chargedmoves = None
        self._advance_task = None

    def _ensure_data(self):
        if self.fastmoves is None:
            self.fastmoves, self.chargedmoves = get_moves()

    def _quizzable(self, m):
        """Only mons whose moveset can produce an answerable question:
        a resolvable positive-gain fast move, and ≥2 distinct resolvable
        charged moves with positive energy cost (an energy-0 charged move
        would make the answer 0 — no such button exists)."""
        moveset = m.get('moveset') or []
        if len(moveset) < 3:
            return False
        fast, charged = moveset[0], moveset[1:]
        if self.fastmoves.get(fast, {}).get('energyGain', 0) <= 0:
            return False
        if len(set(charged)) < 2:
            return False
        return all(self.chargedmoves.get(c, {}).get('energy', 0) > 0
                   for c in charged)

    def build(self, league):
        self._cancel_advance_task()
        self._ensure_data()
        self.league = league
        self.mons = [m for m in get_rankings(league) if self._quizzable(m)]
        self.score = 0
        self.max_score = 0
        self.attempts = 0
        self.streak = 0
        self.max_streak = 0
        self.first_charge_correct = 0
        self.first_charge_total = 0
        self.sequence_correct = 0
        self.sequence_total = 0
        self.question_type = None
        self._type_streak = 0
        self._prev_fast_turns = None
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
        question_height = 160 if ON_ANDROID else 120
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

        # Scroll-wrap so the bottom controls stay reachable on small phones;
        # inert (no scroll) when the content already fits.
        return toga.ScrollContainer(
            content=self.container,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

    def _pick_question_type(self):
        """Pick question type with weighted probability and streak limits."""
        if self.question_type is None:
            return QUESTION_TYPE_FIRST if random.random() < FIRST_WEIGHT else QUESTION_TYPE_SEQUENCE
        if self.question_type == QUESTION_TYPE_FIRST and self._type_streak >= MAX_FIRST_STREAK:
            return QUESTION_TYPE_SEQUENCE
        if self.question_type == QUESTION_TYPE_SEQUENCE and self._type_streak >= MAX_SEQUENCE_STREAK:
            return QUESTION_TYPE_FIRST
        return QUESTION_TYPE_FIRST if random.random() < FIRST_WEIGHT else QUESTION_TYPE_SEQUENCE

    def _load_question(self):
        # Guards against a natively queued duplicate tap double-resolving
        # the question (double score + orphaned advance task).
        self._question_over = False
        # Don't ask about a fast move with the same turn count twice in a row
        # (three 1-turn moves running felt repetitive). Fall back to the full
        # pool only if no other turn count is available.
        candidates = self.mons
        if self._prev_fast_turns is not None:
            varied = [m for m in self.mons
                      if self.fastmoves[m['moveset'][0]].get('turns', 1)
                      != self._prev_fast_turns]
            if varied:
                candidates = varied
        mon = random.choice(candidates)
        self.fast_id = mon['moveset'][0]
        self.charged_id = random.choice(mon['moveset'][1:])
        self.fast_name = self.fastmoves[self.fast_id]['name']
        self._prev_fast_turns = self.fastmoves[self.fast_id].get('turns', 1)
        self.charged_name = self.chargedmoves[self.charged_id]['name']
        self.mon_name = mon['speciesName']
        self.attempts = 0

        new_type = self._pick_question_type()
        if new_type == self.question_type:
            self._type_streak += 1
        else:
            self._type_streak = 1
        self.question_type = new_type

        if self.question_type == QUESTION_TYPE_FIRST:
            self.right_answer = counters_to_charge(
                self.fast_id, self.charged_id,
                self.fastmoves, self.chargedmoves
            )
        else:
            self.sequence = charge_sequence(
                self.fast_id, self.charged_id,
                self.fastmoves, self.chargedmoves,
                num_charges=4
            )
            self.right_answer = tuple(self.sequence)
            n = self.sequence[0]
            self.sequence_choices = list(set(
                (n, b1, b2, b3)
                for b1 in (n, n-1)
                for b2 in (n, n-1)
                for b3 in (n, n-1)
            ))
            self.sequence_choices.sort(reverse=True)

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        self.answer_buttons = {}

        if self.question_type == QUESTION_TYPE_FIRST:
            answers = list(range(1, 21)) + ['more']
            total_rows = (len(answers) + 3) // 4
            row = None
            for i, val in enumerate(answers):
                row_index = i // 4
                if i % 4 == 0:
                    row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
                    self.button_box.add(row)
                btn = toga.Button(
                    str(val),
                    on_press=self._make_answer_handler(val),
                    style=Pack(flex=1, margin=2, height=44, font_size=14,
                               background_color=answer_color_gradient(total_rows, row_index),
                               color=COLOR_TEXT_LIGHT)
                )
                self.answer_buttons[val] = btn
                row.add(btn)
        else:
            left_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
            right_col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_left=4))
            cols_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
            cols_row.add(left_col)
            cols_row.add(right_col)
            self.button_box.add(cols_row)

            total_rows = (len(self.sequence_choices) + 1) // 2
            for i, choice in enumerate(self.sequence_choices):
                row_index = i // 2
                label = ", ".join(str(x) for x in choice)
                btn = toga.Button(
                    label,
                    on_press=self._make_answer_handler(choice),
                    style=Pack(height=48, font_size=14, margin_bottom=4,
                               background_color=answer_color_gradient(total_rows, row_index),
                               color=COLOR_TEXT_LIGHT)
                )
                self.answer_buttons[choice] = btn
                if i % 2 == 0:
                    left_col.add(btn)
                else:
                    right_col.add(btn)

    def _make_answer_handler(self, value):
        def handler(widget):
            self._check_answer(value)
        return handler

    def _highlight_correct_button(self):
        """Highlight the correct answer button in teal."""
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
            self.max_score += 3
            if self.attempts == 1:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
            else:
                self.streak = 0
            if self.question_type == QUESTION_TYPE_FIRST:
                self.first_charge_correct += 1
                self.first_charge_total += 1
            else:
                self.sequence_correct += 1
                self.sequence_total += 1
            self.score_label.text = self._score_text()
            energy_per_fast = self.fastmoves[self.fast_id]['energyGain']
            energy_needed = self.chargedmoves[self.charged_id]['energy']
            self._highlight_correct_button()
            self.feedback_label.text = (
                f"✅ Correct! +{pts} point{'s' if pts != 1 else ''}. \n"
                f"{self.fast_name} gives {energy_per_fast} energy, \n"
                f"{self.charged_name} costs {energy_needed} energy."
            )
            self._disable_buttons()
            self._advance_task = asyncio.create_task(self._advance_question())
        else:
            self.streak = 0
            if self.attempts >= MAX_ATTEMPTS:
                self._question_over = True
                self.max_score += 3
                if self.question_type == QUESTION_TYPE_FIRST:
                    self.first_charge_total += 1
                else:
                    self.sequence_total += 1
                self.score_label.text = self._score_text()
                energy_per_fast = self.fastmoves[self.fast_id]['energyGain']
                energy_needed = self.chargedmoves[self.charged_id]['energy']
                if self.question_type == QUESTION_TYPE_SEQUENCE:
                    correct = ", ".join(str(x) for x in self.right_answer)
                    self.feedback_label.text = (
                        f"❌ The answer was {correct}.\n"
                        f"{self.fast_name} gives {energy_per_fast} energy, \n"
                        f"{self.charged_name} costs {energy_needed} energy."
                    )
                elif self.question_type == QUESTION_TYPE_FIRST:
                    self.feedback_label.text = (
                        f"❌ The answer was {self.right_answer}. \n"
                        f"{self.fast_name} gives {energy_per_fast} energy, \n"
                        f"{self.charged_name} costs {energy_needed} energy."
                    )
                self._highlight_correct_button()
                self._disable_buttons()
                self._advance_task = asyncio.create_task(self._advance_question(delay=2.5))
            else:
                # Streak was just broken; refresh so the 🔥 disappears now,
                # not only after the final attempt resolves.
                self.score_label.text = self._score_text()
                remaining = MAX_ATTEMPTS - self.attempts
                self.feedback_label.text = (
                    f"❌ Try again! {remaining} attempt{'s' if remaining != 1 else ''} left."
                )

    def _set_question_text(self):
        turns = self.fastmoves[self.fast_id].get('turns', '?')
        if self.question_type == QUESTION_TYPE_FIRST:
            self.question_label.value = (
                f"How many {self.fast_name}s ({turns} turn) does it take "
                f"{self.mon_name} to charge {self.charged_name}?"
            )
        else:
            self.question_label.value = (
                f"How many {self.fast_name}s ({turns} turn) does it take "
                f"{self.mon_name} to reach the first 4 {self.charged_name}s?"
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
            return f"Score: {self.score} / {self.max_score} 🔥{self.streak}"
        return f"Score: {self.score} / {self.max_score}"

    def _cancel_advance_task(self):
        if self._advance_task and not self._advance_task.done():
            self._advance_task.cancel()
        self._advance_task = None

    def _end_quiz(self, widget):
        self._cancel_advance_task()
        stats = {
            'score': self.score,
            'max_score': self.max_score,
            'max_streak': self.max_streak,
            'league': self.league,
            'first_charge_correct': self.first_charge_correct,
            'first_charge_total': self.first_charge_total,
            'sequence_correct': self.sequence_correct,
            'sequence_total': self.sequence_total,
        }
        self.app.show_quiz_summary(stats)
