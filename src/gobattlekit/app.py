#!/usr/bin/env python
"""
Main Toga application for GoBattleKit.
"""
import locale
import logging
import asyncio
import pathlib
import shutil
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# iOS ships locales that Python's setlocale rejects with locale.Error.
# Toga/stdlib code calls setlocale at import/startup time, so we patch it
# here before any screen imports run. See DEVELOPER_NOTES.md.
_original_setlocale = locale.setlocale
_LocaleError = locale.Error  # bound early: the param below shadows the module
def _safe_setlocale(category, locale=None):
    # Keyword name matches the stdlib signature so callers using
    # setlocale(cat, locale=...) don't get an unexpected-keyword TypeError.
    try:
        return _original_setlocale(category, locale)
    except _LocaleError:
        return _original_setlocale(category, "C")
locale.setlocale = _safe_setlocale

from .screens.about import AboutScreen
from .screens.help import HelpScreen
from .screens.iv_credits import IVCreditsScreen

from .platform import ON_IOS

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
        self._active_screen = None
        self._poll_task = None
        self._loop_running = False
        self.on_running = self._on_running
        self.main_window = toga.MainWindow(title=self.formal_name)
        self._try_init()
        self.main_window.show()

    def _on_running(self, app):
        self._loop_running = True
        if self._active_screen is not None:
            self._start_inbox_poll(app)

    def _try_init(self):
        """Build all screens and show home; on ANY failure show a
        recoverable error screen.

        Catching only NoDataError here turned every other startup failure
        (e.g. unexpected data-shape errors) into an unhandled crash loop.
        """
        try:
            # One-time migration: drop targets written by the (removed)
            # import-path pre-evo propagation — they shadowed the correct
            # evolution-line mapping and never matched (SI2).
            from .data.user_thresholds import prune_propagated_pre_evos
            from .data.thresholds import EVOLUTION_LINES
            if prune_propagated_pre_evos(EVOLUTION_LINES):
                logger.info("Pruned propagated pre-evolution user targets")
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
            self.main_window.content = self.home_screen.build()
            self._active_screen = "home"
            if self._loop_running:
                # Retry after the app was already running — the on_running
                # hook has fired, start the poll directly.
                self._start_inbox_poll(self)
        except Exception as e:
            logger.exception("Startup failed")
            self._show_startup_error(e)

    def _show_startup_error(self, exc):
        from .data.fetcher import NoDataError
        from .theme import paragraph_text, btn_primary
        if isinstance(exc, NoDataError):
            title = "Could not load game data"
            body = str(exc)
        else:
            title = "Something went wrong"
            body = (f"GoBattleKit hit an unexpected error while starting "
                    f"up:\n\n{exc}\n\nTap Try Again — if this keeps "
                    f"happening, reinstalling the app may help.")
        error_box = toga.Box(style=Pack(direction=COLUMN, margin=40))
        error_box.add(toga.Label(
            title,
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=20)
        ))
        # paragraph_text, not Label: Labels never wrap (DEVELOPER_NOTES)
        # and these messages are full sentences.
        error_box.add(paragraph_text(body, font_size=16))
        error_box.add(toga.Button(
            "Try Again",
            on_press=lambda w: self._try_init(),
            style=btn_primary(height=48, font_size=16, margin_top=20)
        ))
        self.main_window.content = error_box

    def _start_inbox_poll(self, app):
        """Launch the poll task (once) and hold a reference."""
        if self._poll_task is not None:
            return
        if not ON_IOS:
            # The Documents/Inbox share mechanism is iOS-only; on desktop
            # this loop would watch (and delete CSVs from!) the user's real
            # ~/Documents/Inbox.
            logger.info("Inbox poll skipped (not iOS)")
            return
        self._poll_task = asyncio.create_task(self._poll_inbox())
        logger.info("Inbox poll task scheduled")

    async def _poll_inbox(self):
        """Poll the iOS inbox directory for CSV files shared from other apps."""
        logger.info("Inbox poll started")
        try:
            # NOTE: do NOT pre-seed with files already in the inbox. When a
            # share LAUNCHES the app (cold start), iOS places the file in
            # Documents/Inbox before startup() runs — pre-seeding silently
            # swallowed exactly that share (AP1). Anything sitting in the
            # inbox is either a fresh share or a leftover from a crash;
            # both should be imported.
            seen = set()
            while True:
                await asyncio.sleep(3)
                try:
                    inbox = pathlib.Path.home() / 'Documents' / 'Inbox'
                    if inbox.exists():
                        # suffix.lower(): a shared '.CSV' must match too.
                        csvs = [f for f in inbox.iterdir()
                                if f.suffix.lower() == '.csv']
                        # Skip files modified within the last second — iOS
                        # may still be copying them in; they're picked up
                        # on the next tick.
                        now = time.time()
                        ready = [f for f in csvs
                                 if now - f.stat().st_mtime > 1.0]
                        new = [f for f in ready if f not in seen]
                        if new:
                            # PokeGenie exports are full snapshots, so when
                            # several arrive in one tick the newest
                            # supersedes the rest — but say so in the log
                            # instead of discarding them silently (AP6).
                            latest = max(new, key=lambda p: p.stat().st_mtime)
                            if len(new) > 1:
                                logger.warning(
                                    "Inbox: %d new CSVs in one tick; importing "
                                    "newest (%s), discarding %s",
                                    len(new), latest.name,
                                    [f.name for f in new if f != latest],
                                )
                            logger.info("Inbox: new CSV found: %s", latest)
                            try:
                                self._handle_new_inbox_csv(latest)
                            finally:
                                # Delete the processed inbox CSVs even if
                                # dispatch raised. Done in a finally so a
                                # single bad/unparseable CSV can't make the
                                # poll re-detect and re-fail it every 3
                                # seconds (which manifests as the IV checker
                                # screen flickering on a re-navigation
                                # loop). Deleting also lets a re-shared file
                                # with the same name be detected as new next
                                # time. A file whose unlink FAILS stays in
                                # 'seen' so it can't resurrect that loop.
                                for f in ready:
                                    try:
                                        f.unlink()
                                    except Exception:
                                        logger.exception(
                                            "Could not delete inbox CSV %s", f)
                                seen = {f for f in ready if f.exists()}
                except Exception:
                    # asyncio.CancelledError derives from BaseException, so it
                    # correctly propagates out of this except and ends the task.
                    logger.exception("Inbox poll error")
        finally:
            logger.info("Inbox poll exited")

    def _handle_new_inbox_csv(self, latest):
        """Dispatch a newly arrived inbox CSV based on the user's current screen.

        Always stage the CSV to the cache and invalidate both IV screens'
        in-memory state FIRST; then, if the user is on home or either IV
        checker, navigate so the screen's auto-load picks up the new file
        (one parse — the old flow navigated first, auto-loading the stale
        export, then re-parsed the new one). Mid-quiz or editing, just
        stage — the next IV navigation picks it up.
        """
        from .data.fetcher import SAVED_CSV, CACHE_DIR
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            src = pathlib.Path(str(latest))
            if src.resolve() != SAVED_CSV.resolve():
                shutil.copy2(src, SAVED_CSV)
        except Exception:
            logger.exception("Could not stage inbox CSV")
            return
        self.iv_checker_screen.csv_path = None
        self.user_iv_checker_screen.csv_path = None

        if self._active_screen == "user_iv_checker":
            # Refresh in place — don't yank the user to the default checker.
            self.show_user_iv_checker(skip_intro=True)
        elif self._active_screen in ("home", "iv_checker"):
            self.show_iv_checker(skip_intro=True)
        else:
            logger.info(
                "Inbox CSV arrived while on %s; staged without navigating",
                self._active_screen,
            )

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
            try:
                # Quiz data loads lazily on first build (AP2); a cold cache
                # with no network surfaces here, not at startup.
                self.main_window.content = self.quiz_screen.build(league)
            except Exception as e:
                logger.exception("Quiz build failed")
                self._show_startup_error(e)
        else:
            self._show_with_intro(
                "move_count_quiz",
                lambda: self.show_quiz(league, skip_intro=True)
            )

    def show_timing_quiz(self, skip_intro=False):
        """Switch to the move timing quiz screen."""
        if skip_intro:
            self._active_screen = "timing_quiz"
            try:
                self.main_window.content = self.timing_quiz_screen.build()
            except Exception as e:
                logger.exception("Timing quiz build failed")
                self._show_startup_error(e)
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
