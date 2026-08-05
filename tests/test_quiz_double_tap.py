"""SQ6 regression: a duplicate tap on an answer must be a no-op.

Buttons disable synchronously, but a touch event already queued natively still
fires, so _check_answer could re-enter after the question resolved: double
score and a second advance task orphaning the first. commit 52dba70 added the
_question_over guard; this pins it for all three quizzes (device checklist
"Rapid double-tap an answer -- no double score, no skipped question").
"""
import asyncio
from types import SimpleNamespace

from unittest.mock import MagicMock

import pytest

from tests._toga_stub import install_toga_stub

install_toga_stub()

from gobattlekit.screens.quiz import QuizScreen  # noqa: E402
from gobattlekit.screens.timing_quiz import TimingQuizScreen  # noqa: E402
from gobattlekit.screens.type_quiz import TypeQuizScreen  # noqa: E402


@pytest.fixture
def advance_tasks(monkeypatch):
    """Collect (and close) the advance coroutines instead of scheduling them.

    There is no running loop in a unit test, so asyncio.create_task would
    raise; the collected list is also the "did the question advance twice?"
    counter.
    """
    tasks = []

    def fake_create_task(coro):
        coro.close()
        tasks.append(coro)
        return SimpleNamespace(done=lambda: True, cancel=lambda: None)

    monkeypatch.setattr(asyncio, "create_task", fake_create_task)
    return tasks


def _wire_common(s, right_answer):
    s.score = 0
    s.max_score = 0
    s.attempts = 0
    s.streak = 0
    s.max_streak = 0
    s._question_over = False
    s.right_answer = right_answer
    s.answer_buttons = {}
    s.score_label = SimpleNamespace(text="")
    s.feedback_label = SimpleNamespace(text="")
    return s


def test_move_count_quiz_double_tap_scores_once(advance_tasks):
    s = _wire_common(QuizScreen(MagicMock()), 4)
    s.question_type = 'first'
    s.first_charge_correct = 0
    s.first_charge_total = 0
    s.sequence_correct = 0
    s.sequence_total = 0
    s.fast_id = 'F'
    s.charged_id = 'C'
    s.fastmoves = {'F': {'name': 'Fast', 'energyGain': 10}}
    s.chargedmoves = {'C': {'name': 'Charged', 'energy': 50}}
    s.fast_name = 'Fast'
    s.charged_name = 'Charged'

    handler = s._make_answer_handler(4)
    handler(None)
    handler(None)  # queued duplicate tap

    assert s.score == 3
    assert s.max_score == 3
    assert s.first_charge_correct == 1
    assert s.max_streak == 1
    assert len(advance_tasks) == 1


def test_timing_quiz_double_tap_scores_once(advance_tasks):
    s = _wire_common(TimingQuizScreen(MagicMock()), (2, 3))

    handler = s._make_answer_handler((2, 3))
    handler(None)
    handler(None)  # queued duplicate tap

    assert s.score == 3
    assert s.max_score == 3
    assert s.max_streak == 1
    assert len(advance_tasks) == 1


def test_type_quiz_double_tap_scores_once(advance_tasks):
    s = _wire_common(TypeQuizScreen(MagicMock()), 'neutral')

    handler = s._make_answer_handler('neutral')
    handler(None)
    handler(None)  # queued duplicate tap

    assert s.score == 1
    assert s.max_score == 1
    assert s.max_streak == 1
    assert len(advance_tasks) == 1
