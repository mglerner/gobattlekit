#!/usr/bin/env python
"""
App-wide theme constants for GoBattleKit.
Colors and reusable Pack styles.
"""
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# ------------------------------------------------------------------
# Colors
# ------------------------------------------------------------------
COLOR_PRIMARY = "#1a3a5c"       # dark navy — background, primary text
COLOR_BG = "#000000"            # black background .. maybe a bad idea for light mode
COLOR_ACCENT = "#00BCD4"        # teal — primary action buttons
COLOR_ACCENT_DARK = "#0097A7"   # darker teal — pressed/secondary accent
COLOR_YELLOW = "#FFCC00"        # yellow — highlights, scores
COLOR_TEXT_LIGHT = "#FFFFFF"    # white text on dark backgrounds
COLOR_TEXT_DARK = "#1a3a5c"     # dark text on light/teal backgrounds
COLOR_DESTRUCTIVE = "#E53935"   # red — delete, clear all
COLOR_CARD_BG = "#0d2a42"       # slightly lighter than primary — card backgrounds
COLOR_SECONDARY_BTN = "#2a4a6c" # slightly lighter navy — secondary buttons
COLOR_NAV = "#0d5c4a"           # dark teal-green — navigation buttons
COLOR_HELP = "#5c3d8f"          # purple — help buttons

# ------------------------------------------------------------------
# Button styles
# ------------------------------------------------------------------

def btn_primary(height=50, font_size=16, margin_bottom=18):
    """Primary action button — teal background."""
    return Pack(
        height=height,
        font_size=font_size,
        margin_bottom=margin_bottom,
        background_color=COLOR_ACCENT,
        color=COLOR_TEXT_DARK,
    )

def btn_secondary(height=44, font_size=14, margin_bottom=8):
    """Secondary action button — dark navy background."""
    return Pack(
        height=height,
        font_size=font_size,
        margin_bottom=margin_bottom,
        background_color=COLOR_SECONDARY_BTN,
        color=COLOR_TEXT_LIGHT,
    )

def btn_destructive(height=44, font_size=14, margin_bottom=8):
    """Destructive action button — red background."""
    return Pack(
        height=height,
        font_size=font_size,
        margin_bottom=margin_bottom,
        background_color=COLOR_DESTRUCTIVE,
        color=COLOR_TEXT_LIGHT,
    )

def btn_destructive_icon(width=44, height=32):
    """Small destructive icon button (✕)."""
    return Pack(
        width=width,
        height=height,
        background_color=COLOR_DESTRUCTIVE,
        color=COLOR_TEXT_LIGHT,
    )

def btn_league(margin=4, height=40):
    """League selector button."""
    return Pack(
        flex=1,
        margin=margin,
        height=height,
        background_color=COLOR_SECONDARY_BTN,
        color=COLOR_TEXT_LIGHT,
    )

def btn_back(height=44, margin_bottom=8):
    """Back/navigation button."""
    return Pack(
        height=height,
        margin_bottom=margin_bottom,
        background_color=COLOR_SECONDARY_BTN,
        color=COLOR_TEXT_LIGHT,
    )

def btn_icon(width=44, height=36):
    """Small icon button (✕, ✎, ⧉, 📤, →)."""
    return Pack(
        width=width,
        height=height,
        background_color=COLOR_SECONDARY_BTN,
        color=COLOR_TEXT_LIGHT,
    )


def btn_nav(height=44, font_size=14, margin_bottom=0):
    """Navigation button — distinct from primary and secondary."""
    return Pack(
        height=height,
        font_size=font_size,
        margin_bottom=margin_bottom,
        background_color=COLOR_NAV,
        color=COLOR_TEXT_LIGHT,
    )


def btn_quiz_answer(height=44, font_size=14):
    """Quiz answer button — full width within its row."""
    return Pack(
        flex=1,
        margin=2,
        height=height,
        font_size=font_size,
        background_color=COLOR_SECONDARY_BTN,
        color=COLOR_TEXT_LIGHT,
    )

def btn_help(height=44, font_size=14, margin_bottom=8):
    """Help button — distinct purple color."""
    return Pack(
        height=height,
        font_size=font_size,
        margin_bottom=margin_bottom,
        background_color=COLOR_HELP,
        color=COLOR_TEXT_LIGHT,
    )

# ------------------------------------------------------------------
# Label styles
# ------------------------------------------------------------------

LABEL_TITLE = Pack(
    font_size=24,
    font_weight="bold",
    text_align="center",
    margin_bottom=10,
)

LABEL_SECTION = Pack(
    font_size=22,
    font_weight="bold",
    text_align="center",
    margin_bottom=8,
)

LABEL_BODY = Pack(font_size=14)

LABEL_SMALL = Pack(font_size=12)

LABEL_STATUS = Pack(font_size=13, text_align="center", margin_bottom=2)

def label_section(margin_top=8, margin_bottom=8):
    """Section header label style."""
    return Pack(
        font_size=22,
        font_weight="bold",
        text_align="center",
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        color=COLOR_TEXT_LIGHT,
    )

# ------------------------------------------------------------------
# Card style — for hit results
# ------------------------------------------------------------------

def card_box(margin_bottom=8):
    """A subtle card box for hit results."""
    return Pack(
        direction=COLUMN,
        background_color=COLOR_CARD_BG,
        margin_bottom=margin_bottom,
        padding=8,
    )

# ------------------------------------------------------------------
# Container styles
# ------------------------------------------------------------------

CONTAINER = Pack(direction=COLUMN, margin=20, flex=1, background_color=COLOR_BG)
