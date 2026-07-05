"""2026-07-04 bug hunt: the streak 🔥 in the score header stayed displayed after
a streak was broken by a non-final wrong attempt.

On a wrong-but-not-final attempt, _check_answer zeroed self.streak but never
refreshed score_label, so the flame lingered until the question finally
resolved. Both the move-count quiz and the timing quiz shared the bug.
"""
from types import SimpleNamespace

from unittest.mock import MagicMock

from tests._toga_stub import install_toga_stub

install_toga_stub()

from gobattlekit.screens.timing_quiz import TimingQuizScreen  # noqa: E402
from gobattlekit.screens.quiz import QuizScreen  # noqa: E402

FLAME = "\U0001F525"


def test_timing_quiz_flame_clears_on_non_final_wrong():
    s = TimingQuizScreen(MagicMock())
    s.score = 6
    s.total = 6
    s.streak = 3
    s.max_streak = 3
    s.attempts = 0
    s._question_over = False
    s.right_answer = (2, 3)
    s.score_label = SimpleNamespace(text=f"Score: 6 / 6 {FLAME}3")
    s.feedback_label = SimpleNamespace(text="")

    s._check_answer(None)  # wrong, first (non-final) attempt

    assert s.streak == 0
    assert FLAME not in s.score_label.text


def test_move_count_quiz_flame_clears_on_non_final_wrong():
    s = QuizScreen(MagicMock())
    s.score = 6
    s.max_score = 6
    s.streak = 3
    s.max_streak = 3
    s.attempts = 0
    s._question_over = False
    s.right_answer = 4
    s.score_label = SimpleNamespace(text=f"Score: 6 / 6 {FLAME}3")
    s.feedback_label = SimpleNamespace(text="")

    s._check_answer(999)  # wrong, first (non-final) attempt

    assert s.streak == 0
    assert FLAME not in s.score_label.text
