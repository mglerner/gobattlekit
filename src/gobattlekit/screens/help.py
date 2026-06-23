#!/usr/bin/env python
"""
Help screen — topic list and per-topic help content.
"""
import re
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..links import open_url
from ..data.preferences import get_pref, set_pref
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    COLOR_SECONDARY_BTN, COLOR_NAV,
    btn_primary, btn_secondary, btn_nav, card_box, paragraph_text,
)

INTRO_PREF_KEYS = [
    "skip_intro_move_count_quiz",
    "skip_intro_timing_quiz",
    "skip_intro_type_quiz",
    "skip_intro_iv_checker",
    "skip_intro_user_iv_checker",
]

TOPICS = [
    "Getting Started",
    "PvP IV Checker",
    "My PvP IV Targets",
    "Move Count Quizzes",
    "Optimal Move Timing Quiz",
    "Type Effectiveness Quiz",
]

VIDEO_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

HELP_CONTENT = {
    "Getting Started": [
        ("", "GoBattleKit helps you prepare for Pokemon GO PvP battles. It has two main features: quizzes to help you learn move timing and type matchups, and an IV checker to find your best PvP Pokemon."),
        ("IV Checker", "The IV checker lets you find Pokémon that meet PvP IV targets. You can import a CSV from PokeGenie, or enter Pokémon manually one at a time."),
        ("PokeGenie import", "To import from PokeGenie, you need PokeGenie's iVision subscription. With iVision, tap the export button in PokeGenie and share the CSV to GoBattleKit. Your CSV is remembered between sessions."),
        ("Manual entry", "If you don't have iVision, you can enter Pokémon manually. Tap 'Enter a Pokémon manually' on the IV Checker screen, pick a species, enter IVs and CP, and tap Check. Results are saved and remembered between sessions."),
    ],
    "PvP IV Checker": [
        ("", "The PvP IV Checker checks your Pokémon against a curated list of targets for Great, Ultra, and Master League."),
        ("PokeGenie import", "Export your Pokémon from PokeGenie and share to GoBattleKit on iOS, or use Import on Android. Note: CSV export requires PokeGenie's iVision subscription."),
        ("Manual entry", "No iVision? Tap 'Enter a Pokémon manually' to add Pokémon one at a time. Enter the species, IVs (0-15 each), and CP. GoBattleKit will calculate the level and check against targets. Manually entered Pokémon are saved between sessions."),
        ("Results", "Results show each Pokémon's IVs, CP, and stats. SP (stat product) measures overall PvP performance - higher is better. Rank shows how this IV combination compares to all 4096 possible combinations for that species."),
        ("👑 and 🏆 badges", "A 👑 means the spread is efficient: no other IV spread beats it on Attack, Defense, and Stamina at once, so it is one of the best possible for that Pokémon. A 🏆 means that among the matching Pokémon you own, this one is not beaten on all three stats by any of your others, but a better spread exists that you have not caught. A Pokémon with no badge is beaten on every stat by one of your own that you see here, so it is a safe candidate to transfer. The 👑/🏆 efficient-IV idea comes from orgodemir's PvP IV webapp."),
        ("Pre-evolutions", "If you import a Frigibax, it is checked against Baxcalibur's targets and labelled with the pre-evolution in parentheses, like \"7/15/5 (Frigibax)\". A Pokémon you have not evolved yet still shows up under the final form it would become. One that can evolve into more than one final form, like an Eevee, is checked against each of them."),
        ("Cycling targets", "On a species' results, the ◀ and ▶ arrows move through that species' targets. \"All targets\" shows every match; a single target shows only the Pokémon that meet it. If you pick a target none of your Pokémon meet, GoBattleKit lists the top IV spreads that would, so you know what to hunt for."),
        ("Expert vs SIM targets", "Most default targets are hand-tuned by PvP experts. Targets marked SIM come from automated battle-simulation pipelines instead — useful, but less battle-tested. The 'SIM targets' button on the species list shows or hides them; hidden SIM targets are also left out of the hit counts. On the species list, a species whose league targets are all simulated shows a [SIM] tag, and a matched simulated target is labelled SIM on the result card."),
    ],
    "My PvP IV Targets": [
        ("", "Set your own IV targets to check your Pokémon against. For example, add Medicham with a minimum Attack of 105 to find your best Great League Medicham candidates."),
        ("Adding a target", "Tap Edit My Targets → Add Target, choose a species and league, set minimum stats (0 means any), and tap Save Target. Make sure a CSV is imported or Pokémon are entered manually to see results. Your data is remembered between sessions."),
        ("👑 and 🏆 badges", "Your matching Pokémon show the same 👑 and 🏆 badges as the PvP IV Checker: 👑 marks an efficient spread (one of the best possible for that Pokémon), 🏆 marks the best of what you own that no other of yours beats on all three stats, and no badge means another of your Pokémon beats it on every stat. See the PvP IV Checker help for the full explanation."),
        ("Target buttons", "Each target has four buttons:\n✎ Edit - modify the target's stats or label\n⧉ Duplicate - copy the target as a starting point for a new one\n📤 Share - export the target as text to share with friends\n✕ Delete - remove the target"),
        ("Import from Text", "Lets you paste a target shared by someone else, or a \"Copy for IV scanner\" snippet from a deep-dive page. This is useful for importing targets from the PvP community."),
        ("PokeGenie note", "Importing a CSV from PokeGenie requires the iVision subscription. Alternatively, use manual entry to add Pokémon one at a time."),
    ],
    "Move Count Quizzes": [
        ("", "Practice counting how many fast moves it takes to charge a move."),
        ("Question types", "There are two question types: single charge (how many fast moves to reach the first charge move) and sequence (how many fast moves to reach each of the first 4 charge moves, accounting for leftover energy)."),
        ("Scoring", "You can score up to 3 points per question — more points for fewer attempts. Your current streak of first-attempt correct answers is shown with 🔥 in the score display."),
    ],
    "Optimal Move Timing Quiz": [
        ("", "In PvP, throwing your charge move at the right time minimizes the free turns you give your opponent. The optimal timing depends on your fast move's turn count vs your opponent's."),
        ("", "This quiz helps you learn those patterns."),
        ("Learn more", "For a detailed explanation of optimal move timing, watch XehrFelrose's video.[Watch on YouTube](https://www.youtube.com/watch?v=UA41fzcAb8A)"),
    ],
    "Type Effectiveness Quiz": [
        ("", "Practice type matchups - super effective, not very effective, neutral, and double resisted."),
    ],
}

class HelpScreen:
    """Help screen with topic list and per-topic content."""

    def __init__(self, app):
        self.app = app
        self._back_screen = None
        self._back_label = "← Home"

    def build(self, topic=None, back_screen=None, back_label="← Home"):
        """Build the help screen.

        If topic is given, show that topic directly.
        back_screen is a callable to return to the calling screen.
        back_label is the text for the back button.
        """
        self._back_screen = back_screen
        self._back_label = back_label
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

        topic_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        for topic in TOPICS:
            topic_box.add(toga.Button(
                topic,
                on_press=self._make_topic_handler(topic),
                style=btn_secondary(height=48, font_size=16)
            ))
        container.add(topic_box)

        any_skipped = any(get_pref(k) for k in INTRO_PREF_KEYS)
        self._reset_intro_btn = toga.Button(
            "Reset intro screens",
            on_press=self._reset_intros,
            style=btn_secondary(height=44, font_size=14, margin_bottom=8)
        )
        if not any_skipped:
            from ..theme import hide_widget
            hide_widget(self._reset_intro_btn)
        container.add(self._reset_intro_btn)

        container.add(toga.Button(
            self._back_label,
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
        scroll = toga.ScrollContainer(horizontal=False, 
            content=content_box,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        sections = HELP_CONTENT.get(topic, [])
        for heading, body in sections:
            videos = VIDEO_PATTERN.findall(body)
            clean_body = VIDEO_PATTERN.sub('', body).strip()

            card = toga.Box(style=card_box(margin_bottom=12))
            if heading:
                card.add(toga.Label(
                    heading,
                    style=Pack(font_size=14, font_weight="bold",
                               margin_bottom=4, color=COLOR_YELLOW)
                ))
            card.add(paragraph_text(clean_body, font_size=14))
            for label, url in videos:
                card.add(toga.Button(
                    label,
                    on_press=lambda w, u=url: self._open_url(u),
                    style=btn_primary(height=44, font_size=14, margin_bottom=4)
                ))
            content_box.add(card)

        container.add(scroll)

        nav_row = toga.Box(style=Pack(direction=ROW, margin_top=8))
        nav_row.add(toga.Button(
            "← Topics",
            on_press=lambda w: self.app.show_help(
                back_screen=self._back_screen,
                back_label=self._back_label
            ),
            style=Pack(flex=1, height=44, margin_right=4,
                       background_color=COLOR_SECONDARY_BTN,
                       color=COLOR_TEXT_LIGHT)
        ))
        nav_row.add(toga.Button(
            self._back_label,
            on_press=self._go_back,
            style=Pack(flex=1, height=44, margin_left=4,
                       background_color=COLOR_NAV,
                       color=COLOR_TEXT_LIGHT)
        ))
        container.add(nav_row)

        return container

    def _make_topic_handler(self, topic):
        def handler(widget):
            self.app.show_help(topic=topic, back_screen=self._back_screen,
                               back_label=self._back_label)
        return handler

    def _reset_intros(self, widget):
        for key in INTRO_PREF_KEYS:
            set_pref(key, False)
        self._reset_intro_btn.text = "Intro screens reset ✓"
        self._reset_intro_btn.enabled = False

    def _go_back(self, widget):
        if self._back_screen:
            self._back_screen()
        else:
            self.app.show_home()

    def _open_url(self, url):
        open_url(self.app, url)
