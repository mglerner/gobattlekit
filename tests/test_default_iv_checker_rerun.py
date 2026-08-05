"""2026-07-04 bug hunt: the default IV Checker showed stale results after a
manual entry was added on another screen.

show_user_iv_checker re-runs its check when csv_path is already set, but
show_iv_checker lacked that branch. Both checkers merge the shared
user_generated.csv, so the default checker must re-run too.
"""
from unittest.mock import MagicMock

from tests._toga_stub import install_toga_stub

install_toga_stub()

from gobattlekit.app import GoBattleKit  # noqa: E402


def _fake_app(name, csv_path):
    """A GoBattleKit with only the navigation state these tests touch
    (__init__ would build the whole toga app)."""
    app = GoBattleKit.__new__(GoBattleKit)
    app._active_screen = None
    app.main_window = MagicMock()
    setattr(app, f"{name}_screen", MagicMock(csv_path=csv_path))
    return app


def test_rerun_when_csv_path_set():
    """A manual entry added elsewhere merges into user_generated.csv;
    revisiting the default IV Checker must re-run the check to pick it up."""
    app = _fake_app("iv_checker", "/tmp/some.csv")
    app.show_iv_checker(skip_intro=True)
    app.iv_checker_screen._run_check.assert_called_once()
    # csv_path already set -> must NOT reload from SAVED_CSV.
    app.iv_checker_screen.load_csv.assert_not_called()


def test_no_rerun_when_no_csv_path():
    """Nothing loaded yet: no stale re-check to trigger."""
    app = _fake_app("iv_checker", None)
    app.show_iv_checker(skip_intro=True)
    app.iv_checker_screen._run_check.assert_not_called()


def test_matches_user_checker_behaviour():
    """The default checker's revisit branch must mirror the user checker's
    (the asymmetry was the bug; they now share one code path)."""
    app = _fake_app("user_iv_checker", "/tmp/some.csv")
    app.show_user_iv_checker(skip_intro=True)
    app.user_iv_checker_screen._run_check.assert_called_once()
