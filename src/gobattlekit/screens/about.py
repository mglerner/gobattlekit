#!/usr/bin/env python
"""
About screen — credits and links.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..platform import ON_ANDROID
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_secondary, btn_nav, btn_help
)


class AboutScreen:
    """About screen with credits and links."""

    def __init__(self, app):
        self.app = app

    def build(self):
        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            "GoBattleKit",
            style=Pack(font_size=28, font_weight="bold",
                       text_align="center", margin_bottom=4,
                       color=COLOR_ACCENT)
        ))
        container.add(toga.Label(
            "A Pokémon GO PvP companion app",
            style=Pack(font_size=14, text_align="center", margin_bottom=24,
                       color=COLOR_TEXT_LIGHT)
        ))

        # Developer
        container.add(toga.Label(
            "Developer",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        container.add(toga.Label(
            "Michael G. Lerner (TitanTrainers15)",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "github.com/mglerner",
            on_press=lambda w: self._open_url("https://github.com/mglerner"),
            style=btn_secondary(height=40, margin_bottom=16)
        ))

        # Credits
        container.add(toga.Label(
            "Credits",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        container.add(toga.Label(
            "PvPoke — game data and rankings",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "pvpoke.com",
            on_press=lambda w: self._open_url("https://pvpoke.com"),
            style=btn_secondary(height=40, margin_bottom=12)
        ))
        container.add(toga.Label(
            "Ryan Swag (SwagTips) - The IV OG",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "YouTube: @SwagTips",
            on_press=lambda w: self._open_url("https://www.youtube.com/@SwagTips"),
            style=btn_secondary(height=40, margin_bottom=12)
        ))
        container.add(toga.Label(
            "XehrFelrose's Discord - best PvP community",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        container.add(toga.Button(
            "Discord invite link",
            on_press=lambda w: self._open_url("https://discord.gg/UkCdztFf2n"),
            style=btn_secondary(height=40, margin_bottom=16)
        ))


        # Support
        container.add(toga.Label(
            "Support Development",
            style=Pack(font_size=16, font_weight="bold", margin_top=16, margin_bottom=4,
                       color=COLOR_YELLOW)
        ))
        if ON_ANDROID:
            container.add(toga.Button(
                "Tip jar — Venmo @mglerner",
                on_press=lambda w: self._open_url("https://venmo.com/u/mglerner"),
                style=btn_secondary(height=40, margin_bottom=16)
            ))
        else:
            container.add(toga.Button(
                "Support via mglerner.com",
                on_press=lambda w: self._open_url("http://mglerner.com/support.html"),
                style=btn_secondary(height=40, margin_bottom=16)
            ))        

            container.add(toga.Button(
                "← Back to Home",
                on_press=lambda w: self.app.show_home(),
                style=btn_nav(height=44)
            ))

        container.add(toga.Button(
            "Help",
            on_press=lambda w: self.app.show_help(
                back_screen=lambda: self.app.show_about()
            ),
            style=btn_help()
        ))

        return container

    def _open_url(self, url):
        """Open a URL, handling platform differences."""
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
