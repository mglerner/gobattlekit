"""2026-07-04 bug hunt: the timing quiz built ranked_fast_move_ids from every
ranked mon's moveset[0] without checking the id resolves in fastmoves.

get_moves classifies energyGain==0 moves (e.g. TRANSFORM) as charged and skips
malformed moves, so a ranked moveset[0] can be absent from fastmoves on upstream
data drift; indexing it bare in _load_question would KeyError and kill/freeze the
whole quiz. The sibling quiz.py already guards this join via _quizzable.
"""
from unittest.mock import MagicMock

import pytest

from tests._toga_stub import install_toga_stub

install_toga_stub()

from gobattlekit.screens.timing_quiz import TimingQuizScreen  # noqa: E402


def _timing_data():
    """(fastmoves, chargedmoves, rankings-by-league) with one ranked mon whose
    moveset[0] ('TRANSFORM') is absent from fastmoves — the drift case."""
    fastmoves = {
        'MUD_SHOT': {'name': 'Mud Shot', 'turns': 2},
        'COUNTER': {'name': 'Counter', 'turns': 2},
        'DRAGON_BREATH': {'name': 'Dragon Breath', 'turns': 1},
    }
    charged = {'TRANSFORM': {'name': 'Transform', 'energy': 0}}
    rankings = {
        'great': [
            {'speciesId': 'a', 'moveset': ['MUD_SHOT', 'X', 'Y']},
            {'speciesId': 'ditto', 'moveset': ['TRANSFORM', 'X', 'Y']},
        ],
        'ultra': [{'speciesId': 'b', 'moveset': ['COUNTER', 'X', 'Y']}],
        'master': [{'speciesId': 'c', 'moveset': ['DRAGON_BREATH', 'X', 'Y']}],
    }
    return fastmoves, charged, rankings


def test_unknown_moveset_id_filtered_out(monkeypatch):
    fastmoves, charged, rankings = _timing_data()
    monkeypatch.setattr(
        'gobattlekit.screens.timing_quiz.get_moves',
        lambda: (fastmoves, charged))
    monkeypatch.setattr(
        'gobattlekit.screens.timing_quiz.get_rankings',
        lambda league: rankings[league])

    s = TimingQuizScreen(MagicMock())
    s._ensure_data()

    assert 'TRANSFORM' not in s.ranked_fast_move_ids
    # every retained id resolves in fastmoves (no bare-index KeyError)
    assert all(mid in s.fastmoves for mid in s.ranked_fast_move_ids)
    assert set(s.ranked_fast_move_ids) == {'MUD_SHOT', 'COUNTER', 'DRAGON_BREATH'}


def test_empty_pool_takes_normal_error_path(monkeypatch):
    """If the filter empties the pool, _load_question raises IndexError (caught
    by show_timing_quiz's try/except -> error screen) rather than KeyError."""
    fastmoves = {'MUD_SHOT': {'name': 'Mud Shot', 'turns': 2}}
    rankings = {
        'great': [{'speciesId': 'ditto', 'moveset': ['TRANSFORM', 'X', 'Y']}],
        'ultra': [],
        'master': [],
    }
    monkeypatch.setattr(
        'gobattlekit.screens.timing_quiz.get_moves',
        lambda: (fastmoves, {'TRANSFORM': {'energy': 0}}))
    monkeypatch.setattr(
        'gobattlekit.screens.timing_quiz.get_rankings',
        lambda league: rankings[league])

    s = TimingQuizScreen(MagicMock())
    s._ensure_data()
    assert s.ranked_fast_move_ids == []
    s._prev_timing_pair = None
    with pytest.raises(IndexError):
        s._load_question()
