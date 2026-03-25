#!/usr/bin/env python
"""
Help screen — topic list and per-topic help content.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..platform import ON_ANDROID, ON_IOS
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    btn_primary, btn_secondary, btn_back, btn_nav, card_box
)

TOPICS = [
    "Getting Started",
    "PvP IV Checker",
    "My PvP IV Targets",
    "Move Count Quizzes",
    "Optimal Move Timing Quiz",
    "Type Effectiveness Quiz",
]

HELP_CONTENT = {
    "Getting Started": [
        ("", "GoBattleKit helps you prepare for Pokemon GO PvP battles. It has two main features: quizzes to help you learn move timing and type matchups, and an IV checker to find your best PvP Pokemon."),
        ("", "To use the IV checker, you'll need the free PokeGenie app to export your Pokemon as a CSV file."),
    ],
    "PvP IV Checker": [
        ("", "The PvP IV Checker checks your Pokemon against a curated list of targets for Great, Ultra, and Master League."),
        ("How to use", "Export your Pokemon from PokeGenie (tap the export button and share to GoBattleKit on iOS, or use Import on Android)."),
        ("Results", "Results show each Pokemon's IVs, CP, and stats. SP (stat product) measures overall PvP performance - higher is better."),
    ],
    "My PvP IV Targets": [
        ("", "Set your own IV targets to check your Pokemon against. For example, add Medicham with a minimum Attack of 105 to find your best Great League Medicham candidates."),
        ("Adding a target", "Tap Edit My Targets -> Add Target, choose a species and league, set minimum stats (0 means any), and tap Save Target. Make sure you import your PokeGenie CSV to see results. Your CSV is remembered between sessions, so you only need to import it once - results update automatically when you add or change targets."),
        ("Target buttons", "Each target has four buttons:\n✎ Edit - modify the target's stats or name\n⧉ Duplicate - copy the target as a starting point for a new one\n📤 Share - export the target as text to share with friends\n✕ Delete - remove the target"),
        ("Import from Text", "Lets you paste a target shared by someone else. This is useful for importing targets from the PvP community - for example, if a content creator publishes their recommended IV floors, you can paste them directly into GoBattleKit."),
    ],
    "Move Count Quizzes": [
        ("", "Practice counting how many fast moves it takes to charge a move."),
        ("Question types", "There are two question types: single charge (how many fast moves to reach the first charge move) and sequence (how many fast moves to reach each of the first 4 charge moves, accounting for leftover energy)."),
        ("Scoring", "You can score up to 3 points per question - more points for fewer attempts."),
    ],
    "Optimal Move Timing Quiz": [
        ("", "In PvP, throwing your charge move at the right time minimizes the free turns you give your opponent. The optimal timing depends on your fast move's turn count vs your opponent's."),
        ("", "This quiz helps you learn those patterns."),
        ("Learn more", "For a detailed explanation, watch this video: https://www.youtube.com/watch?v=UA41fzcAb8A"),
    ],
    "Type Effectiveness Quiz": [
        ("", "Practice type matchups - super effective, not very effective, neutral, and double resisted."),
    ],
}


class HelpScreen:
    """Help screen with topic list and per-topic content."""

    def __init__(self, app):
        self.app = app

    def build(self, topic=None, back_screen=None):
        """Build the help screen.
        
        If topic is given, show that topic directly.
        back_screen is a callable to return to the calling screen.
        """
        self._back_screen = back_screen
        if topic:
            return self._build_topic(topic)
        return self._build_topic_list()

    def _build_topic_list(self):
        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            "Help",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=16,
                       color=COLOR_ACCENT)
        ))

        for topic in TOPICS:
            container.add(toga.Button(
                topic,
                on_press=self._make_topic_handler(topic),
                style=btn_secondary(height=48, font_size=16)
            ))

        container.add(toga.Button(
            "← Back",
            on_press=self._go_back,
            style=btn_nav(height=44)
        ))

        return container

    def _build_topic(self, topic):
        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            topic,
            style=Pack(font_size=22, font_weight="bold",
                       text_align="center", margin_bottom=16,
                       color=COLOR_ACCENT)
        ))

        content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(
            content=content_box,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        sections = HELP_CONTENT.get(topic, [])
        for heading, body in sections:
            card = toga.Box(style=card_box(margin_bottom=12))
            if heading:
                card.add(toga.Label(
                    heading,
                    style=Pack(font_size=14, font_weight="bold",
                               margin_bottom=4, color=COLOR_YELLOW)
                ))
            card.add(toga.Label(
                body,
                style=Pack(font_size=14, color=COLOR_TEXT_LIGHT)
            ))
            content_box.add(card)

            # If body contains a URL, add a button to open it
            if "https://" in body:
                url = [w for w in body.split() if w.startswith("https://")][0]
                content_box.add(toga.Button(
                    "Watch on YouTube",
                    on_press=lambda w, u=url: self._open_url(u),
                    style=btn_primary(height=44, font_size=14)
                ))

        container.add(scroll)

        nav_row = toga.Box(style=Pack(direction=ROW, margin_top=8))
        nav_row.add(toga.Button(
            "← Topics",
            on_press=lambda w: self.app.show_help(),
            style=btn_back(height=44)
        ))
        nav_row.add(toga.Button(
            "← Back",
            on_press=self._go_back,
            style=btn_nav(height=44)
        ))
        container.add(nav_row)

        return container

    def _make_topic_handler(self, topic):
        def handler(widget):
            self.app.show_help(topic=topic)
        return handler

    def _go_back(self, widget):
        if self._back_screen:
            self._back_screen()
        else:
            self.app.show_home()

    def _open_url(self, url):
        if ON_ANDROID:
            try:
                from java import jclass
                Intent = jclass('android.content.Intent')
                Uri = jclass('android.net.Uri')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                self.app._impl.native.startActivity(intent)
            except Exception as e:
                print(f"Could not open URL on Android: {e}")
        else:
            import webbrowser
            webbrowser.open(url)
            
