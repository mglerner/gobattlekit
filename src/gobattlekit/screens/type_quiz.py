#!/usr/bin/env python
"""
Type effectiveness quiz screen.
"""
import random
import asyncio
import toga
from toga.style import Pack
from ..data.effectiveness import effectiveness, effectiveness_to_words
from ..theme import COLOR_TEXT_LIGHT, answer_color_gradient
from .quiz_base import QuizScreenBase

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


class TypeQuizScreen(QuizScreenBase):
    """Quiz screen for type effectiveness questions."""

    def build(self):
        self._cancel_advance_task()
        self.league = 'type'
        self.score = 0
        self.max_score = 0
        self.streak = 0
        self.max_streak = 0
        self._load_question()

        return self._build_scaffold(80, 18)

    def _build_extras(self):
        self.emoji_label = toga.Label(
            "",
            style=Pack(font_size=36, text_align="center", margin_bottom=16,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.emoji_label)

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

    def _check_answer(self, chosen):
        if self._question_over:
            return
        self._question_over = True
        self._disable_buttons()
        if chosen == self.right_answer:
            self.score += 1
            self.max_score += 1
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
            self._refresh_score()
            self.feedback_label.text = "✅ Correct!"
        else:
            self.streak = 0
            self.max_score += 1
            self._refresh_score()
            self.feedback_label.text = f"❌ The answer was {self.right_answer}."
            self._highlight_correct_button()
        self._advance_task = asyncio.create_task(self._advance_question())
