#!/usr/bin/env python
"""
Main Toga application for GoBattleKit.
"""
import locale
import logging
import asyncio
import pathlib
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# iOS ships locales that Python's setlocale rejects with locale.Error.
# Toga/stdlib code calls setlocale at import/startup time, so we patch it
# here before any screen imports run. See DEVELOPER_NOTES.md.
_original_setlocale = locale.setlocale
def _safe_setlocale(category, loc=None):
    try:
        return _original_setlocale(category, loc)
    except locale.Error:
        return _original_setlocale(category, "C")
locale.setlocale = _safe_setlocale

from .screens.about import AboutScreen
from .screens.help import HelpScreen
from .screens.iv_credits import IVCreditsScreen

from .platform import ON_ANDROID, ON_IOS, ON_MOBILE

import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from .screens.home import HomeScreen
from .screens.quiz import QuizScreen
from .screens.timing_quiz import TimingQuizScreen
from .screens.type_quiz import TypeQuizScreen
from .screens.iv_checker import IVCheckerScreen
from .screens.user_iv_checker import UserIVCheckerScreen
from .screens.edit_thresholds import EditThresholdsScreen
from .screens.quiz_summary import QuizSummaryScreen
from .screens.intro import IntroScreen
from .data.preferences import get_pref

from .theme import COLOR_BG

class GoBattleKit(toga.App):

    def startup(self):
        """Set up the application."""
        from .data.fetcher import NoDataError
        self._active_screen = None
        self._poll_task = None
        try:
            self.home_screen = HomeScreen(self)
            self.about_screen = AboutScreen(self)
            self.quiz_screen = QuizScreen(self)
            self.timing_quiz_screen = TimingQuizScreen(self)
            self.type_quiz_screen = TypeQuizScreen(self)
            self.iv_checker_screen = IVCheckerScreen(self)
            self.user_iv_checker_screen = UserIVCheckerScreen(self)
            self.edit_thresholds_screen = EditThresholdsScreen(self)
            self.quiz_summary_screen = QuizSummaryScreen(self)
            self.intro_screen = IntroScreen(self)
            self.help_screen = HelpScreen(self)
            self.iv_credits_screen = IVCreditsScreen(self)
            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = self.home_screen.build()
            self._active_screen = "home"
            self.main_window.show()

            self.on_running = self._start_inbox_poll
            ## # Auto-load saved CSV if available
            ## from .data.fetcher import SAVED_CSV
            ## if SAVED_CSV.exists():
            ##     self.iv_checker_screen.load_csv(str(SAVED_CSV))
        except NoDataError as e:
            self.main_window = toga.MainWindow(title=self.formal_name)
            error_box = toga.Box(style=Pack(direction=COLUMN, margin=40))
            error_box.add(toga.Label(
                "Could not load game data",
                style=Pack(font_size=24, font_weight="bold",
                           text_align="center", margin_bottom=20)
            ))
            error_box.add(toga.Label(
                str(e),
                style=Pack(font_size=16, text_align="center")
            ))
            self.main_window.content = error_box
            self.main_window.show()

    def _start_inbox_poll(self, app):
        """on_running hook — launch the poll task and hold a reference."""
        self._poll_task = asyncio.create_task(self._poll_inbox())
        logger.info("Inbox poll task scheduled")

    async def _poll_inbox(self):
        """Poll the iOS inbox directory for CSV files shared from other apps."""
        logger.info("Inbox poll started")
        try:
            seen = set()
            # Pre-populate seen with any files already in inbox at startup
            # so we don't re-triger on files that were there before we launched
            try:
                inbox = pathlib.Path.home() / 'Documents' / 'Inbox'
                if inbox.exists():
                    seen = set(inbox.glob('*.csv'))
            except Exception:
                pass
            while True:
                await asyncio.sleep(3)
                try:
                    inbox = pathlib.Path.home() / 'Documents' / 'Inbox'
                    if inbox.exists():
                        csvs = list(inbox.glob('*.csv'))
                        new = [f for f in csvs if f not in seen]
                        if new:
                            latest = max(new, key=lambda p: p.stat().st_mtime)
                            logger.info("Inbox: new CSV found: %s", latest)
                            try:
                                self._handle_new_inbox_csv(latest)
                            finally:
                                # Delete all inbox CSVs even if dispatch raised.
                                # Done in a finally so a single bad/unparseable
                                # CSV can't make the poll re-detect and re-fail it
                                # every 3 seconds (which manifests as the IV
                                # checker screen flickering on a re-navigation
                                # loop). Deleting also lets a re-shared file with
                                # the same name be detected as new next time.
                                for f in csvs:
                                    try:
                                        f.unlink()
                                    except Exception:
                                        pass
                                seen = set()
                except Exception:
                    # asyncio.CancelledError derives from BaseException, so it
                    # correctly propagates out of this except and ends the task.
                    logger.exception("Inbox poll error")
        finally:
            logger.info("Inbox poll exited")

    def _handle_new_inbox_csv(self, latest):
        """Dispatch a newly arrived inbox CSV based on the user's current screen.

        If the user is on home or either IV checker, jump to the IV checker and
        reload. Otherwise (mid-quiz, editing thresholds, etc.) just stage the
        CSV to the cache without touching screen state — next IV navigation
        will pick it up.
        """
        from .data.fetcher import SAVED_CSV, CACHE_DIR
        foreground = self._active_screen in ("home", "iv_checker", "user_iv_checker")
        if foreground:
            self.show_iv_checker(skip_intro=True)
            self.iv_checker_screen.load_csv(str(latest))
            # The user IV checker isn't built or visible here, so calling
            # load_csv on it crashes — its widgets don't exist yet. Instead
            # invalidate its cached path so it re-reads SAVED_CSV the next
            # time the user navigates to it (same pattern as the staging
            # branch below). load_csv on iv_checker_screen above already
            # wrote the new data to SAVED_CSV.
            self.user_iv_checker_screen.csv_path = None
            return
        logger.info(
            "Inbox CSV arrived while on %s; staging without navigating",
            self._active_screen,
        )
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            src = pathlib.Path(str(latest))
            if src.resolve() != SAVED_CSV.resolve():
                shutil.copy2(src, SAVED_CSV)
        except Exception:
            logger.exception("Could not stage inbox CSV")
            return
        # Invalidate in-memory state so next navigation re-reads SAVED_CSV.
        self.iv_checker_screen.csv_path = None
        self.user_iv_checker_screen.csv_path = None

    def _show_with_intro(self, feature_key, on_continue):
        """Show intro screen if user hasn't opted out, otherwise go direct."""
        if get_pref(f"skip_intro_{feature_key}"):
            on_continue()
        else:
            self._active_screen = "intro"
            self.main_window.content = self.intro_screen.build(
                feature_key, on_continue
            )

    def show_quiz(self, league, skip_intro=False):
        """Switch to the move count quiz screen for the given league."""
        if skip_intro:
            self._active_screen = "quiz"
            self.main_window.content = self.quiz_screen.build(league)
        else:
            self._show_with_intro(
                "move_count_quiz",
                lambda: self.show_quiz(league, skip_intro=True)
            )

    def show_timing_quiz(self, skip_intro=False):
        """Switch to the move timing quiz screen."""
        if skip_intro:
            self._active_screen = "timing_quiz"
            self.main_window.content = self.timing_quiz_screen.build()
        else:
            self._show_with_intro(
                "timing_quiz",
                lambda: self.show_timing_quiz(skip_intro=True)
            )

    def show_type_quiz(self, skip_intro=False):
        """Switch to the type effectiveness quiz screen."""
        if skip_intro:
            self._active_screen = "type_quiz"
            self.main_window.content = self.type_quiz_screen.build()
        else:
            self._show_with_intro(
                "type_quiz",
                lambda: self.show_type_quiz(skip_intro=True)
            )

    def show_iv_checker(self, skip_intro=False):
        """Switch to the IV checker screen."""
        if skip_intro:
            self._active_screen = "iv_checker"
            self.main_window.content = self.iv_checker_screen.build()
            # Auto-load saved CSV if not already loaded
            from .data.fetcher import SAVED_CSV
            if not self.iv_checker_screen.csv_path and SAVED_CSV.exists():
                self.iv_checker_screen.load_csv(str(SAVED_CSV))
        else:
            self._show_with_intro(
                "iv_checker",
                lambda: self.show_iv_checker(skip_intro=True)
            )

    def show_user_iv_checker(self, skip_intro=False):
        """Switch to the user IV checker screen."""
        if skip_intro:
            self._active_screen = "user_iv_checker"
            self.main_window.content = self.user_iv_checker_screen.build()
            from .data.fetcher import SAVED_CSV
            if not self.user_iv_checker_screen.csv_path and SAVED_CSV.exists():
                self.user_iv_checker_screen.load_csv(str(SAVED_CSV))
            elif self.user_iv_checker_screen.csv_path:
                # Re-run check in case thresholds changed
                self.user_iv_checker_screen._run_check()
        else:
            self._show_with_intro(
                "user_iv_checker",
                lambda: self.show_user_iv_checker(skip_intro=True)
            )

    def show_edit_thresholds(self):
        """Switch to the edit thresholds screen."""
        self._active_screen = "edit_thresholds"
        self.main_window.content = self.edit_thresholds_screen.build()

    def show_home(self):
        """Switch back to the home screen."""
        self._active_screen = "home"
        self.main_window.content = self.home_screen.build()

    def show_about(self):
        self._active_screen = "about"
        self.main_window.content = self.about_screen.build()

    def show_help(self, topic=None, back_screen=None, back_label="← Home"):
        """Switch to the help screen."""
        self._active_screen = "help"
        self.main_window.content = self.help_screen.build(
            topic=topic, back_screen=back_screen,
            back_label=back_label
        )

    def show_quiz_summary(self,stats):
        self._active_screen = "quiz_summary"
        self.main_window.content = self.quiz_summary_screen.build(stats)

    def show_iv_credits(self, back_screen=None, back_label="← IV Checker"):
        self._active_screen = "iv_credits"
        self.main_window.content = self.iv_credits_screen.build(
            back_screen=back_screen,
            back_label=back_label
        )


def main():
    return GoBattleKit("GoBattleKit", "com.mglerner.gobattlekit")
