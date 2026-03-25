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
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_primary, btn_nav
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

    def build(self):
        self.score = 0
        self.total = 0
        self._load_question()

        self.container = toga.Box(style=CONTAINER)

        # Score bar
        self.score_label = toga.Label(
            self._score_text(),
            style=Pack(font_size=14, margin_bottom=10, text_align="center",
                       color=COLOR_YELLOW)
        )
        self.container.add(self.score_label)

        # Question text
        self.question_label = toga.MultilineTextInput(
            value="",
            readonly=True,
            style=Pack(font_size=18, margin_bottom=20,
                       margin_left=10, margin_right=10,
                       height=80, flex=1,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.question_label)
        self._set_question_text()

        # Feedback label
        self.feedback_label = toga.Label(
            "",
            style=Pack(font_size=16, margin_bottom=16, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.feedback_label)

        # Answer buttons
        self.button_box = toga.Box(style=Pack(direction=COLUMN, margin_bottom=10))
        self._build_answer_buttons()
        self.container.add(self.button_box)

        # End quiz button
        self.container.add(toga.Button(
            "End Quiz",
            on_press=self._end_quiz,
            style=btn_nav(height=44)
        ))

        return self.container

    def _load_question(self):
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
            f"How effective is {self.attacker} attacking against {self.defender}?\n"
            f"        {attacker_emoji} → {defender_emoji}"
        )        

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        self.answer_buttons = {}
        answers = ['double resisted', 'not very effective', 'neutral', 'super effective']
        for answer in answers:
            btn = toga.Button(
                answer.capitalize(),
                on_press=self._make_answer_handler(answer),
                style=btn_primary(height=52, font_size=16)
            )
            self.answer_buttons[answer] = btn
            self.button_box.add(btn)

    def _make_answer_handler(self, value):
        def handler(widget):
            self._check_answer(value)
        return handler

    def _check_answer(self, chosen):
        self.total += 1
        self._disable_buttons()
        if chosen == self.right_answer:
            self.score += 1
            self.score_label.text = self._score_text()
            self.feedback_label.text = "✅ Correct!"
        else:
            self.score_label.text = self._score_text()
            self.feedback_label.text = f"❌ The answer was {self.right_answer}."
        asyncio.create_task(self._advance_question())

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
                f"Type Effectiveness\nFinal score: {self.score} / {self.total}"
            )
        )
        self.app.show_home()
