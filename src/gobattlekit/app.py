#!/usr/bin/env python
"""
Main Toga application for GoBattleKit.
"""
import os
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from .screens.home import HomeScreen
from .screens.quiz import QuizScreen
from .screens.type_quiz import TypeQuizScreen

# Fix for locale.Error on iOS real devices
os.environ["LANG"] = "en_US.UTF-8"

class GoBattleKit(toga.App):
    def startup(self):
        self.home_screen = HomeScreen(self)
        self.quiz_screen = QuizScreen(self)
        self.type_quiz_screen = TypeQuizScreen(self)
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.home_screen.build()
        self.main_window.show()

    def show_quiz(self, league):
        """Switch to the move count quiz screen for the given league."""
        self.main_window.content = self.quiz_screen.build(league)

    def show_type_quiz(self):
        """Switch to the type effectiveness quiz screen."""
        self.main_window.content = self.type_quiz_screen.build()

    def show_home(self):
        """Switch back to the home screen."""
        self.main_window.content = self.home_screen.build()


def main():
    return GoBattleKit("GoBattleKit", "com.mglerner.gobattlekit")

