#!/usr/bin/env python
"""
Main Toga application for GoBattleKit.
"""
import locale
import asyncio
import pathlib
from .screens.about import AboutScreen
from .screens.help import HelpScreen
_original_setlocale = locale.setlocale
def _safe_setlocale(category, loc=None):
    try:
        return _original_setlocale(category, loc)
    except locale.Error:
        return _original_setlocale(category, "C")
locale.setlocale = _safe_setlocale

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

from .theme import COLOR_BG

class GoBattleKit(toga.App):

    def startup(self):
        """Set up the application."""
        from .data.fetcher import NoDataError
        try:
            self.home_screen = HomeScreen(self)
            self.about_screen = AboutScreen(self)
            self.quiz_screen = QuizScreen(self)
            self.timing_quiz_screen = TimingQuizScreen(self)
            self.type_quiz_screen = TypeQuizScreen(self)
            self.iv_checker_screen = IVCheckerScreen(self)
            self.user_iv_checker_screen = UserIVCheckerScreen(self)
            self.edit_thresholds_screen = EditThresholdsScreen(self)
            self.help_screen = HelpScreen(self)
            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = self.home_screen.build()
            self.main_window.show()
            self.on_running = lambda app: asyncio.create_task(self._poll_inbox(None))
            ## # Auto-load saved CSV if available
            ## from .data.fetcher import SAVED_CSV
            ## if SAVED_CSV.exists():
            ##     self.iv_checker_screen.load_csv(str(SAVED_CSV))
        except NoDataError as e:
            self.main_window = toga.MainWindow(title=self.formal_name)
            error_box = toga.Box(style=Pack(direction=COLUMN, margin=40))
            error_box.add(toga.Label(
                "No Internet Connection",
                style=Pack(font_size=24, font_weight="bold",
                           text_align="center", margin_bottom=20)
            ))
            error_box.add(toga.Label(
                str(e),
                style=Pack(font_size=16, text_align="center")
            ))
            self.main_window.content = error_box
            self.main_window.show()

    async def _poll_inbox(self, widget):
        """Poll the iOS inbox directory for CSV files shared from other apps."""
        import asyncio
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
                        print("Inbox: new CSV found:", latest)
                        # Delete all other CSVs, keep only the latest
                        for f in csvs:
                            if f != latest:
                                f.unlink()
                        seen = {latest}
                        self.show_iv_checker()
                        self.iv_checker_screen.load_csv(str(latest))
            except Exception as e:
                print("Inbox poll error:", e)            

    def show_quiz(self, league):
        """Switch to the move count quiz screen for the given league."""
        self.main_window.content = self.quiz_screen.build(league)

    def show_timing_quiz(self):
        """Switch to the move timing quiz screen."""
        self.main_window.content = self.timing_quiz_screen.build()    

    def show_type_quiz(self):
        """Switch to the type effectiveness quiz screen."""
        self.main_window.content = self.type_quiz_screen.build()

    def show_iv_checker(self):
        """Switch to the IV checker screen."""
        self.main_window.content = self.iv_checker_screen.build()
        # Auto-load saved CSV if not already loaded
        from .data.fetcher import SAVED_CSV
        if not self.iv_checker_screen.csv_path and SAVED_CSV.exists():
            self.iv_checker_screen.load_csv(str(SAVED_CSV))

    def show_user_iv_checker(self):
        """Switch to the user IV checker screen."""
        self.main_window.content = self.user_iv_checker_screen.build()
        from .data.fetcher import SAVED_CSV
        if not self.user_iv_checker_screen.csv_path and SAVED_CSV.exists():
            self.user_iv_checker_screen.load_csv(str(SAVED_CSV))
        elif self.user_iv_checker_screen.csv_path:
            # Re-run check in case thresholds changed
            self.user_iv_checker_screen._run_check()

    def show_edit_thresholds(self):
        """Switch to the edit thresholds screen."""
        self.main_window.content = self.edit_thresholds_screen.build()            

    def show_home(self):
        """Switch back to the home screen."""
        self.main_window.content = self.home_screen.build()

    def show_about(self):
        self.main_window.content = self.about_screen.build()

    def show_help(self, topic=None, back_screen=None, back_label="← Home"):
        """Switch to the help screen."""
        self.main_window.content = self.help_screen.build(
            topic=topic, back_screen=back_screen,
            back_label=back_label
        )    


def main():
    return GoBattleKit("GoBattleKit", "com.mglerner.gobattlekit")
