#!/usr/bin/env python
"""
About screen — credits and links.
"""
import webbrowser
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from ..platform import ON_ANDROID, ON_IOS, ON_MOBILE


class AboutScreen:
    """About screen with credits and links."""

    def __init__(self, app):
        self.app = app

    def build(self):
        container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        container.add(toga.Label(
            "GoBattleKit",
            style=Pack(font_size=28, font_weight="bold",
                       text_align="center", margin_bottom=4)
        ))
        container.add(toga.Label(
            "A Pokémon GO PvP companion app",
            style=Pack(font_size=14, text_align="center", margin_bottom=24)
        ))

        # Developer
        container.add(toga.Label(
            "Developer",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4)
        ))
        container.add(toga.Label(
            "Michael G. Lerner (TitanTrainers15)",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        container.add(toga.Button(
            "github.com/mglerner",
            on_press=lambda w: self._open_url("https://github.com/mglerner"),
            style=Pack(height=40, margin_bottom=16)
        ))

        # Credits
        container.add(toga.Label(
            "Credits",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=4)
        ))

        container.add(toga.Label(
            "PvPoke — game data and rankings",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        container.add(toga.Button(
            "pvpoke.com",
            on_press=lambda w: self._open_url("https://pvpoke.com"),
            style=Pack(height=40, margin_bottom=12)
        ))

        container.add(toga.Label(
            "Ryan Swag (SwagTips) - The IV OG",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        container.add(toga.Button(
            "YouTube: @SwagTips",
            on_press=lambda w: self._open_url("https://www.youtube.com/@SwagTips"),
            style=Pack(height=40, margin_bottom=12)
        ))

        container.add(toga.Label(
            "XehrFelrose's Discord - best PvP community",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        container.add(toga.Button(
            "Discord invite link",
            on_press=lambda w: self._open_url("https://discord.gg/UkCdztFf2n"),
            style=Pack(height=40, margin_bottom=16)
        ))

        # Back
        container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=Pack(height=44, margin_top=8)
        ))

        return container

    def _open_url(self, url):
        """Open a URL, handling platform differences."""
        print(f"MG Bout to open this URL: {url}")
        if ON_ANDROID:
            print("MG ON ANDROID")
            try:
                print("MG IN THE TRY")
                from java import jclass
                Intent = jclass('android.content.Intent')
                Uri = jclass('android.net.Uri')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                activity = self.app._impl.native
                activity.startActivity(intent)
                ## from toga_android.app import App
                ## print("MG about to start activity")
                ## App.app.native.startActivity(intent)
            except Exception as e:
                print(f"Could not open URL on Android: {e}")
        else:
            import webbrowser
            webbrowser.open(url)
