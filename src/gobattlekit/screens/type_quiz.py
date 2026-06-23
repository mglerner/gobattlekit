#!/usr/bin/env python
"""
Type effectiveness quiz screen.
"""
import random
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..data.effectiveness import effectiveness, effectiveness_to_words
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_BG, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_nav, answer_color_gradient
)

TYPE_EMOJI = {
    'normal': '⚪',
    'fire': '🔥',
    'water': '💧',
    'grass': '🌿',
    'electric': '⚡',
    'ice': '❄️',
    'fighting': '🥊',
    'poison': '☠️',
    'ground': '🏔️',
    'flying': '🦅',
    'psychic': '🔮',
    'bug': '🐛',
    'rock': '🪨',
    'ghost': '👻',
    'dragon': '🐉',
    'dark': '🌑',
    'steel': '⚙️',
    'fairy': '🧚',
}


class TypeQuizScreen:
    """Quiz screen for type effectiveness questions."""

    def __init__(self, app):
        self.app = app
        self._advance_task = None

    def build(self):
        self._cancel_advance_task()
        self.score = 0
        self.total = 0
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
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=18, margin_bottom=20,
                       margin_left=10, margin_right=10,
                       height=80, flex=1,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.question_label)
        self.emoji_label = toga.Label(
            "",
            style=Pack(font_size=36, text_align="center", margin_bottom=16,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.emoji_label)
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

    def _load_question(self):
        # Guards against a natively queued duplicate tap double-resolving
        # the question (same pattern as quiz.py).
        self._question_over = False
        types = list(effectiveness.keys())
        self.attacker = random.choice(types)
        self.defender = random.choice(types)
        self.right_answer = effectiveness_to_words[
            effectiveness[self.attacker][self.defender]
        ]

    def _set_question_text(self):
        attacker_emoji = TYPE_EMOJI.get(self.attacker, '❓')
        defender_emoji = TYPE_EMOJI.get(self.defender, '❓')
        self.question_label.value = (
            f"How effective is {self.attacker} attacking against {self.defender}?"
        )
        self.emoji_label.text = f"{attacker_emoji}  →  {defender_emoji}"

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        self.answer_buttons = {}
        answers = ['double resisted', 'not very effective', 'neutral', 'super effective']
        total_rows = len(answers)
        for i, answer in enumerate(answers):
            btn = toga.Button(
                answer.capitalize(),
                on_press=self._make_answer_handler(answer),
                style=Pack(height=52, font_size=16, margin_bottom=4,
                           background_color=answer_color_gradient(total_rows, i),
                           color=COLOR_TEXT_LIGHT)
            )
            self.answer_buttons[answer] = btn
            self.button_box.add(btn)

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
        self._question_over = True
        self._disable_buttons()
        if chosen == self.right_answer:
            self.score += 1
            self.total += 1
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
            self.score_label.text = self._score_text()
            self.feedback_label.text = "✅ Correct!"
        else:
            self.streak = 0
            self.total += 1
            self.score_label.text = self._score_text()
            self.feedback_label.text = f"❌ The answer was {self.right_answer}."
            self._highlight_correct_button()
        self._advance_task = asyncio.create_task(self._advance_question())

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
            'league': 'type',
        }
        self.app.show_quiz_summary(stats)
