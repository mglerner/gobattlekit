#!/usr/bin/env python
"""
About screen — credits and links.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..platform import ON_ANDROID
from ..links import open_url
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_BG, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_secondary, btn_nav, btn_help, paragraph_text
)


class AboutScreen:
    """About screen with credits and links."""

    def __init__(self, app):
        self.app = app

    def build(self):
        container = toga.Box(style=CONTAINER)

        # Fixed title; the credits/support/disclaimer scroll between it and
        # the nav buttons so nothing clips on smaller phones.
        container.add(toga.Label(
            "GoBattleKit",
            style=Pack(font_size=28, font_weight="bold",
                       text_align="center", margin_bottom=4,
                       color=COLOR_ACCENT)
        ))
        container.add(toga.Label(
            "A Pokémon GO PvP companion app",
            style=Pack(font_size=14, text_align="center", margin_bottom=16,
                       color=COLOR_TEXT_LIGHT)
        ))

        content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(
            content=content,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        # Developer
        content.add(toga.Label(
            "Developer",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        content.add(toga.Label(
            "Michael G. Lerner (TitanTrainers15)",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        content.add(toga.Button(
            "github.com/mglerner",
            on_press=lambda w: self._open_url("https://github.com/mglerner"),
            style=btn_secondary(height=40, margin_bottom=16)
        ))

        # Credits
        content.add(toga.Label(
            "Credits",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        content.add(toga.Label(
            "Game data and rankings: PvPoke by EmpoleonDynamite (MIT license)",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        content.add(toga.Button(
            "pvpoke.com",
            on_press=lambda w: self._open_url("https://pvpoke.com"),
            style=btn_secondary(height=40, margin_bottom=12)
        ))
        content.add(toga.Label(
            "Ryan Swag (SwagTips) - The IV OG",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        content.add(toga.Button(
            "YouTube: @SwagTips",
            on_press=lambda w: self._open_url("https://www.youtube.com/@SwagTips"),
            style=btn_secondary(height=40, margin_bottom=12)
        ))
        content.add(toga.Label(
            "XehrFelrose's Discord - best PvP community",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        content.add(toga.Button(
            "Discord invite link",
            on_press=lambda w: self._open_url("https://discord.gg/UkCdztFf2n"),
            style=btn_secondary(height=40, margin_bottom=16)
        ))
        content.add(toga.Label(
            "🏆/👑 efficient-IV badges inspired by orgodemir's PvP IV webapp",
            style=Pack(font_size=14, margin_bottom=16, color=COLOR_TEXT_LIGHT)
        ))


        # Support
        content.add(toga.Label(
            "Support Development",
            style=Pack(font_size=16, font_weight="bold", margin_top=16, margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        if ON_ANDROID:
            content.add(toga.Button(
                "Tip jar — Venmo @mglerner",
                on_press=lambda w: self._open_url("https://venmo.com/u/mglerner"),
                style=btn_secondary(height=40, margin_bottom=16)
            ))
        else:
            content.add(toga.Button(
                "Support via mglerner.com",
                on_press=lambda w: self._open_url("https://mglerner.com/gobattlekit/support.html"),
                style=btn_secondary(height=40, margin_bottom=16)
            ))

        # Trademark / affiliation disclaimer
        content.add(toga.Label(
            "Legal",
            style=Pack(font_size=16, font_weight="bold", margin_top=16,
                       margin_bottom=4, color=COLOR_YELLOW)
        ))
        content.add(paragraph_text(
            "GoBattleKit is an unofficial fan project. It is not affiliated "
            "with, endorsed, sponsored, or approved by Niantic, Nintendo, The "
            "Pokémon Company, Game Freak, or PokeGenie. Pokémon and Pokémon GO "
            "are trademarks of their respective owners.",
            font_size=12, margin_bottom=8,
        ))

        container.add(scroll)

        container.add(toga.Button(
            "? Help",
            on_press=lambda w: self.app.show_help(
                back_screen=lambda: self.app.show_about()
            ),
            style=btn_help()
        ))

        container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44)
        ))


        return container

    def _open_url(self, url):
        open_url(self.app, url)
