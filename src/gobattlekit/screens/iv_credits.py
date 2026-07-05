#!/usr/bin/env python
"""
IV Credits screen — attribution for default IV targets.
"""
import re
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.thresholds import DEFAULT_THRESHOLDS
from ..links import open_url
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    btn_primary, btn_nav, card_box, paragraph_text,
)

VIDEO_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


class IVCreditsScreen:
    """Screen showing attribution for default IV targets."""

    def __init__(self, app):
        self.app = app
        self._back_screen = None
        self._back_label = "← Back"

    def build(self, back_screen=None, back_label="← Back"):
        self._back_screen = back_screen
        self._back_label = back_label

        container = toga.Box(style=CONTAINER)

        container.add(toga.Label(
            "IV Target Credits",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=16,
                       color=COLOR_ACCENT)
        ))

        container.add(toga.Label(
            "Sources for the default\nPvP IV targets:",
            style=Pack(font_size=13, text_align="center", margin_bottom=12,
                       color=COLOR_TEXT_LIGHT)
        ))

        content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(
            content=content_box,
            style=Pack(flex=1, background_color=COLOR_BG)
        )

        for species in sorted(DEFAULT_THRESHOLDS.keys()):
            sources = DEFAULT_THRESHOLDS[species].get('sources')
            if not sources:
                # Pipeline species carry per-target 'source' strings
                # instead of a species-level credit — collect the
                # distinct ones so they're credited too.
                per_target = []
                for targets in DEFAULT_THRESHOLDS[species].values():
                    if not isinstance(targets, dict):
                        continue
                    for t in targets.values():
                        src = t.get('source') if isinstance(t, dict) else None
                        if src and src not in per_target:
                            per_target.append(src)
                sources = '; '.join(per_target)
            if not sources:
                continue

            videos = VIDEO_PATTERN.findall(sources)
            clean_text = VIDEO_PATTERN.sub('', sources).strip()

            card = toga.Box(style=card_box(margin_bottom=12))
            card.add(toga.Label(
                species,  # label-fits: Pokemon species name (<= ~20 chars)
                style=Pack(font_size=14, font_weight="bold",
                           margin_bottom=4, color=COLOR_YELLOW)
            ))
            if clean_text:
                card.add(paragraph_text(clean_text, font_size=13))
            for label, url in videos:
                card.add(toga.Button(
                    label,
                    on_press=lambda w, u=url: self._open_url(u),
                    style=btn_primary(height=40, font_size=13, margin_bottom=4)
                ))
            content_box.add(card)

        container.add(scroll)

        container.add(toga.Button(
            self._back_label,
            on_press=self._go_back,
            style=btn_nav(height=44)
        ))

        return container

    def _go_back(self, widget):
        if self._back_screen:
            self._back_screen()
        else:
            self.app.show_iv_checker(skip_intro=True)

    def _open_url(self, url):
        open_url(self.app, url)
