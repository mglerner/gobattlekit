#!/usr/bin/env python
"""
Main Toga application for GoBattleKit.
"""
import locale
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
from .screens.type_quiz import TypeQuizScreen
from .screens.iv_checker import IVCheckerScreen


class GoBattleKit(toga.App):
    def startup(self):
        """Set up the application."""
        from .data.fetcher import NoDataError
        try:
            self.home_screen = HomeScreen(self)
            self.quiz_screen = QuizScreen(self)
            self.type_quiz_screen = TypeQuizScreen(self)
            self.iv_checker_screen = IVCheckerScreen(self)
            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = self.home_screen.build()
            self.main_window.show()
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

    def on_open_document(self, url):
        """Handle a CSV file opened from another app (e.g. PokeGenie)."""
        self.iv_checker_screen.load_csv(url)
        self.show_iv_checker()

    def show_quiz(self, league):
        """Switch to the move count quiz screen for the given league."""
        self.main_window.content = self.quiz_screen.build(league)

    def show_type_quiz(self):
        """Switch to the type effectiveness quiz screen."""
        self.main_window.content = self.type_quiz_screen.build()

    def show_iv_checker(self):
        """Switch to the IV checker screen."""
        self.main_window.content = self.iv_checker_screen.build()

    def show_home(self):
        """Switch back to the home screen."""
        self.main_window.content = self.home_screen.build()


def main():
    return GoBattleKit("GoBattleKit", "com.mglerner.gobattlekit")
