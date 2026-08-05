#!/usr/bin/env python
"""
Move timing quiz screen — optimal charge move timing based on fast move matchups.
"""
import random
import asyncio
from ..data.gamemaster import (
    get_moves, get_rankings,
    OPTIMAL_TIMING, ALL_TIMING_PATTERNS, format_timing_pattern,
)
from .quiz_base import (
    MAX_ATTEMPTS, POINTS, QUESTION_HEIGHT,
    QuizScreenBase, build_two_column_answers
)

# Target frequency of "doesn't matter" answers. The natural ranked move pool is
# ~50% doesn't-matter (2-turn moves dominate and (2,2) is None), which feels
# repetitive; we re-roll the move pair to hit this rate instead. Chosen
# independently per question, so it leaks nothing about any single answer.
DM_RATE = 0.30
_MAX_SAMPLE_TRIES = 50


class TimingQuizScreen(QuizScreenBase):
    """Quiz screen for optimal move timing questions."""

    def __init__(self, app):
        # No data loads here — this constructor previously did FOUR
        # potential network fetches (gamemaster + three leagues' rankings)
        # on the startup path (AP2/DL4). First build() pays instead.
        super().__init__(app)
        self.fastmoves = None
        self.ranked_fast_move_ids = None

    def _ensure_data(self):
        if self.fastmoves is None:
            self.fastmoves, _ = get_moves()
            all_mons = []
            for league in ('great', 'ultra', 'master'):
                all_mons.extend(get_rankings(league))
            # Keep only ids that actually resolve in get_moves' fast-move
            # dict. Rankings and the gamemaster are fetched independently and
            # get_moves classifies energyGain==0 moves (e.g. TRANSFORM) as
            # charged, so a ranked moveset[0] can be absent from fastmoves on
            # upstream data drift; indexing it bare later would KeyError. The
            # sibling quiz.py guards the same join via _quizzable.
            self.ranked_fast_move_ids = list({
                mon['moveset'][0]
                for mon in all_mons
                if mon.get('moveset') and mon['moveset'][0] in self.fastmoves
            })

    def build(self):
        self._cancel_advance_task()
        self._ensure_data()
        self.league = 'timing'
        self.score = 0
        self.max_score = 0
        self.attempts = 0
        self.streak = 0
        self.max_streak = 0
        self._prev_timing_pair = None
        self._load_question()

        return self._build_scaffold(QUESTION_HEIGHT, 13)

    def _load_question(self):
        # Guards against a natively queued duplicate tap double-resolving
        # the question (same pattern as quiz.py).
        self._question_over = False
        self.attempts = 0

        # Decide the answer category up front so "doesn't matter" lands ~DM_RATE
        # of the time (the natural pool is ~50%), then sample a move pair to
        # match it. Bounded re-roll; fall back to the last draw if exhausted.
        want_dm = random.random() < DM_RATE
        prev_pair = self._prev_timing_pair
        for _ in range(_MAX_SAMPLE_TRIES):
            your_id = random.choice(self.ranked_fast_move_ids)
            their_id = random.choice(self.ranked_fast_move_ids)
            your_t = min(self.fastmoves[your_id].get('turns', 1), 5)
            their_t = min(self.fastmoves[their_id].get('turns', 1), 5)
            right = OPTIMAL_TIMING.get((your_t, their_t), None)
            # Unordered turn-pair: (2,3) and (3,2) are the same matchup, so the
            # same combo won't appear back-to-back. The turns are shown in the
            # question, so unlike the doesn't-matter rate this leaks nothing.
            pair = (min(your_t, their_t), max(your_t, their_t))
            if (right is None) == want_dm and pair != prev_pair:
                break

        self._prev_timing_pair = pair
        self.your_fast_name = self.fastmoves[your_id]['name']
        self.their_fast_name = self.fastmoves[their_id]['name']
        self.your_turns = self.fastmoves[your_id].get('turns', 1)
        self.their_turns = self.fastmoves[their_id].get('turns', 1)
        self.right_answer = right

        self.timing_choices = list(ALL_TIMING_PATTERNS)

    def _build_answer_buttons(self):
        for child in list(self.button_box.children):
            self.button_box.remove(child)

        pattern_choices = [p for p in self.timing_choices if p is not None]

        # "Doesn't matter" (None) is the last answer in the same 2-col grid —
        # shortened from "Timing doesn't matter" so it fits a half-width cell.
        answers = [(p, format_timing_pattern(p)) for p in pattern_choices]
        answers.append((None, "Doesn't matter"))

        self.answer_buttons = build_two_column_answers(
            self.button_box, answers, self._make_answer_handler, font_size=13
        )

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
            self._refresh_score()
            self.feedback_label.text = f"✅ Correct! +{pts} point{'s' if pts != 1 else ''}"
            self._highlight_correct_button()
            self._disable_buttons()
            self._advance_task = asyncio.create_task(self._advance_question())
        else:
            self.streak = 0
            if self.attempts >= MAX_ATTEMPTS:
                self._question_over = True
                self.max_score += 3
                self._refresh_score()
                correct_str = format_timing_pattern(self.right_answer)
                self.feedback_label.text = f"❌ The answer was: {correct_str}."
                self._highlight_correct_button()
                self._disable_buttons()
                self._advance_task = asyncio.create_task(self._advance_question(delay=2.5))
            else:
                # Streak was just broken; refresh so the 🔥 disappears now,
                # not only after the final attempt resolves.
                self._refresh_score()
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
