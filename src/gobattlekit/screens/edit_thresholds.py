#!/usr/bin/env python
"""
Edit Thresholds screen — add, view, and delete user-defined IV thresholds.
"""
import logging
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.user_thresholds import (
    load_user_thresholds, add_threshold, delete_threshold,
    replace_threshold, clear_all_thresholds, parse_threshold_json,
    parse_threshold_text, format_threshold_text, import_threshold_entries,
    get_all_species
)
from ..data.iv_checker import get_pokemon_index
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW,
    btn_primary, btn_secondary, btn_back, btn_nav, btn_league,
    btn_destructive, btn_icon, btn_destructive_icon, card_box,
    btn_help, show_widget, hide_widget, paragraph_text
)

logger = logging.getLogger(__name__)


class EditThresholdsScreen:
    """Screen for managing user-defined IV thresholds."""

    FORM_DEFAULTS = {
        'name': 'Default',
        'atk': '0.0',
        'def': '0.0',
        'sta': '0',
        'onlytop': '0',
    }

    def __init__(self, app):
        self.app = app
        self._all_species = None
        self._species_list_error = None
        self._filtered_species = []
        self._selected_species = None
        self._selected_league = "Great"
        self._form_name = self.FORM_DEFAULTS['name']
        self._form_atk = self.FORM_DEFAULTS['atk']
        self._form_def = self.FORM_DEFAULTS['def']
        self._form_sta = self.FORM_DEFAULTS['sta']
        self._form_onlytop = self.FORM_DEFAULTS['onlytop']
        self._editing_original = None
        self._clear_all_pending = False
        self._clear_all_btn = None

    def _reset_clear_all_state(self):
        """Reset the clear-all confirmation state (flag AND button label —
        an armed 'Tap again to confirm' must not survive navigation, or a
        single later tap wipes all targets)."""
        self._clear_all_pending = False
        if self._clear_all_btn is not None:
            self._clear_all_btn.text = "Clear All"

    def _ensure_species_list(self):
        if self._all_species is None:
            try:
                pokemon_index = get_pokemon_index()
                self._all_species = get_all_species(pokemon_index)
                self._species_list_error = None
            except Exception as e:
                logger.exception("Could not load species list")
                # Leave _all_species as None so the next visit RETRIES —
                # caching [] here turned one transient failure (e.g. first
                # launch offline) into a permanently empty picker.
                self._species_list_error = str(e)
                return []
        return self._all_species

    def _set_outer_buttons_enabled(self, enabled):
        """Enable/disable and show/hide the outer buttons."""
        for btn in [self._clear_all_btn, self._add_target_btn,
                    self._import_text_btn, self._help_btn]:
            if enabled:
                show_widget(btn, height=48, margin_bottom=8)
            else:
                hide_widget(btn)

    def build(self):
        self.container = toga.Box(style=CONTAINER)

        self.container.add(toga.Label(
            "My IV Targets",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10,
                       color=COLOR_ACCENT)
        ))

        top_row = toga.Box(style=Pack(direction=ROW, margin_bottom=12))
        self._clear_all_btn = toga.Button(
            "Clear All",
            on_press=self._confirm_clear_all,
            style=btn_destructive()
        )
        top_row.add(self._clear_all_btn)
        self.container.add(top_row)

        self._add_target_btn = toga.Button(
            "Add Target",
            on_press=self._show_add_form,
            style=btn_primary(height=48, font_size=16)
        )
        self.container.add(self._add_target_btn)

        self._import_text_btn = toga.Button(
            "Import from Text 📥",
            on_press=self._show_import_screen,
            style=btn_secondary(height=48, font_size=16)
        )
        self.container.add(self._import_text_btn)

        self._help_btn = toga.Button(
            "? Help",
            on_press=lambda w: self.app.show_help(
                topic="My PvP IV Targets",
                back_screen=lambda: self.app.show_edit_thresholds(),
                back_label="← Edit My Targets"
            ),
            style=btn_help()
        )
        self.container.add(self._help_btn)

        self.content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(content=self.content_box, style=Pack(flex=1))
        self.container.add(scroll)

        self.container.add(toga.Button(
            "← My IV Checker",
            on_press=lambda w: self.app.show_user_iv_checker(skip_intro=True),
            style=btn_nav(height=44)
        ))

        self._reset_clear_all_state()
        self._show_threshold_list()
        return self.container

    # ------------------------------------------------------------------
    # Threshold list view
    # ------------------------------------------------------------------

    def _show_threshold_list(self):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(True)
        self._reset_clear_all_state()

        self._selected_species = None
        self._selected_league = "Great"
        self._form_name = self.FORM_DEFAULTS['name']
        self._form_atk = self.FORM_DEFAULTS['atk']
        self._form_def = self.FORM_DEFAULTS['def']
        self._form_sta = self.FORM_DEFAULTS['sta']
        self._form_onlytop = self.FORM_DEFAULTS['onlytop']
        self._editing_original = None

        thresholds = load_user_thresholds()

        if not thresholds:
            self.content_box.add(toga.Label(
                "No user targets yet. Tap 'Add Target' to get started.",
                style=Pack(font_size=14, text_align="center", margin_top=20,
                           color=COLOR_TEXT_LIGHT)
            ))
            return

        for species in sorted(thresholds.keys()):
            self.content_box.add(toga.Label(
                species,
                style=Pack(font_size=16, font_weight="bold",
                           margin_top=12, margin_bottom=4,
                           color=COLOR_ACCENT)
            ))
            for league_label in sorted(thresholds[species].keys()):
                self.content_box.add(toga.Label(
                    f"  {league_label} League",
                    style=Pack(font_size=13, margin_bottom=2,
                               color=COLOR_YELLOW)
                ))
                for name in sorted(thresholds[species][league_label].keys()):
                    t = thresholds[species][league_label][name]
                    parts = []
                    if t.get('attack', 0): parts.append(f"{t['attack']}A")
                    if t.get('defense', 0): parts.append(f"{t['defense']}D")
                    if t.get('stamina', 0): parts.append(f"{t['stamina']}S")
                    if t.get('onlytop', 0): parts.append(f"top{t['onlytop']}")
                    stat_str = ', '.join(parts) if parts else 'any'

                    row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
                    row.add(toga.Label(
                        f"    {name} ({stat_str})",
                        style=Pack(flex=1, font_size=13, color=COLOR_TEXT_LIGHT)
                    ))
                    row.add(toga.Button(
                        "✎",
                        on_press=self._make_edit_handler(species, league_label, name, t),
                        style=btn_icon()
                    ))
                    row.add(toga.Button(
                        "⧉",
                        on_press=self._make_duplicate_handler(species, league_label, name, t),
                        style=btn_icon()
                    ))
                    row.add(toga.Button(
                        "📤",
                        on_press=self._make_share_handler(species, league_label, name, t),
                        style=btn_icon()
                    ))
                    row.add(toga.Button(
                        "✕",
                        on_press=self._make_delete_handler(species, league_label, name),
                        style=btn_destructive_icon()
                    ))
                    self.content_box.add(row)

    def _make_delete_handler(self, species, league, name):
        def handler(widget):
            delete_threshold(species, league, name)
            self._show_threshold_list()
        return handler

    def _make_duplicate_handler(self, species, league, name, t):
        def handler(widget):
            self._editing_original = None
            self._selected_species = species
            self._selected_league = league.replace(" League", "")
            self._form_name = self.FORM_DEFAULTS['name']
            self._form_atk = str(t.get('attack', 0))
            self._form_def = str(t.get('defense', 0))
            self._form_sta = str(t.get('stamina', 0))
            self._form_onlytop = str(t.get('onlytop', 0))
            self._show_add_form()
        return handler

    def _make_share_handler(self, species, league, name, t):
        def handler(widget):
            self._show_share_screen(species, league, name, t)
        return handler

    def _confirm_clear_all(self, widget):
        if not self._clear_all_pending:
            self._clear_all_pending = True
            widget.text = "Tap again to confirm"
        else:
            self._clear_all_pending = False
            widget.text = "Clear All"
            clear_all_thresholds()
            self._show_threshold_list()

    # ------------------------------------------------------------------
    # Threshold editing
    # ------------------------------------------------------------------

    def _make_edit_handler(self, species, league, name, t):
        def handler(widget):
            self._edit_threshold(species, league, name, t)
        return handler

    def _edit_threshold(self, species, league, name, t):
        self._editing_original = (species, league, name)
        self._selected_species = species
        self._selected_league = league.replace(" League", "")
        self._form_name = name
        self._form_atk = str(t.get('attack', 0))
        self._form_def = str(t.get('defense', 0))
        self._form_sta = str(t.get('stamina', 0))
        self._form_onlytop = str(t.get('onlytop', 0))
        self._show_add_form()

    # ------------------------------------------------------------------
    # Add threshold form
    # ------------------------------------------------------------------

    def _show_add_form(self, widget=None):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(False)

        self.content_box.add(toga.Button(
            "Save Target",
            on_press=self._save_threshold,
            style=btn_primary(height=48, font_size=16)
        ))

        self.form_error = toga.Label(
            "",
            style=Pack(font_size=13, text_align="center", margin_top=8,
                       color=COLOR_YELLOW)
        )
        self.content_box.add(self.form_error)

        self.content_box.add(toga.Label(
            "League:",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        league_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
        for league in ("Great", "Ultra", "Master"):
            league_row.add(toga.Button(
                league,
                on_press=self._make_league_btn_handler(league),
                style=btn_league()
            ))
        self.content_box.add(league_row)
        self.league_value_label = toga.Label(
            f"Selected: {self._selected_league}",
            style=Pack(font_size=13, text_align="center", margin_bottom=12,
                       color=COLOR_YELLOW)
        )
        self.content_box.add(self.league_value_label)

        self._add_field_row("Species:", self._selected_species or "tap to select",
                            self._show_species_picker)
        self._add_field_row("Label:", self._form_name or "tap to enter",
                            lambda w: self._show_text_entry("Label", "name"))

        # Compact IV row — Atk, Def, Sta on one line
        self.content_box.add(toga.Label(
            "Min stats (0 = any):",
            style=Pack(font_size=14, margin_bottom=4, color=COLOR_TEXT_LIGHT)
        ))
        iv_row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        for label, form_attr, entry_prompt, entry_field in [
            ("Atk", '_form_atk', "Min Attack (0=any)", "atk"),
            ("Def", '_form_def', "Min Defense (0=any)", "def"),
            ("HP",  '_form_sta', "Min HP (0=any)", "sta"),
        ]:
            col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
            col.add(toga.Label(
                label,
                style=Pack(font_size=12, text_align="center", color=COLOR_TEXT_LIGHT)
            ))
            value = getattr(self, form_attr, '0')
            col.add(toga.Label(
                str(value),
                style=Pack(font_size=14, text_align="center", color=COLOR_ACCENT)
            ))
            prompt = entry_prompt
            field = entry_field
            col.add(toga.Button(
                "→",
                on_press=lambda w, p=prompt, f=field: self._show_text_entry(p, f),
                style=btn_icon()
            ))
            iv_row.add(col)
        self.content_box.add(iv_row)

        self._add_field_row("Only top N:", self._form_onlytop,
                            lambda w: self._show_text_entry("Only top N (0=all)", "onlytop"))

        self.content_box.add(toga.Button(
            "← Cancel",
            on_press=lambda w: self._show_threshold_list(),
            style=btn_nav(height=44)
        ))

    def _add_field_row(self, label, value, handler):
        row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        row.add(toga.Label(
            label,
            style=Pack(width=90, font_size=14, color=COLOR_TEXT_LIGHT)
        ))
        row.add(toga.Label(
            str(value),
            style=Pack(flex=1, font_size=14, color=COLOR_ACCENT)
        ))
        row.add(toga.Button(
            "→",
            on_press=handler,
            style=btn_icon()
        ))
        self.content_box.add(row)

    def _make_league_btn_handler(self, league):
        def handler(widget):
            self._selected_league = league
            self.league_value_label.text = f"Selected: {self._selected_league}"
        return handler

    # ------------------------------------------------------------------
    # Text entry screen
    # ------------------------------------------------------------------

    def _show_text_entry(self, prompt, field):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(False)

        self.content_box.add(toga.Label(
            prompt,
            style=Pack(font_size=18, font_weight="bold",
                       text_align="center", margin_bottom=16,
                       color=COLOR_ACCENT)
        ))

        self._entry_field = field
        current = getattr(self, f"_form_{field}", "")
        self._entry_input = toga.TextInput(
            placeholder=self.FORM_DEFAULTS.get(field, '0'),
            style=Pack(font_size=18, margin_bottom=16)
        )
        self._entry_input.value = current
        self.content_box.add(self._entry_input)

        self.content_box.add(toga.Button(
            "Done",
            on_press=self._save_text_entry,
            style=btn_primary(height=48, font_size=16)
        ))

        self.content_box.add(toga.Button(
            "← Back to Form",
            on_press=lambda w: self._show_add_form(),
            style=btn_nav(height=44)
        ))

    def _save_text_entry(self, widget):
        value = self._entry_input.value.strip()
        setattr(self, f"_form_{self._entry_field}", value)
        self._show_add_form()

    # ------------------------------------------------------------------
    # Species picker
    # ------------------------------------------------------------------

    def _show_species_picker(self, widget=None):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(False)
        self._ensure_species_list()
        self._filtered_species = list(self._all_species)

        self.species_search = toga.TextInput(
            placeholder="Type to search (e.g. Medicham)",
            on_change=self._filter_species,
            style=Pack(margin_bottom=8)
        )
        self.content_box.add(self.species_search)

        self.species_list_box = toga.Box(style=Pack(direction=COLUMN))
        scroll = toga.ScrollContainer(
            content=self.species_list_box,
            style=Pack(flex=1)
        )
        self.content_box.add(scroll)
        self._rebuild_species_list()

        self.content_box.add(toga.Button(
            "← Back to Form",
            on_press=self._show_add_form,
            style=btn_nav(height=44)
        ))

    def _filter_species(self, widget):
        query = self.species_search.value.strip().lower()
        if query:
            self._filtered_species = [
                s for s in self._all_species
                if query in s.lower()
            ]
        else:
            self._filtered_species = list(self._all_species)
        self._rebuild_species_list()

    def _rebuild_species_list(self):
        for child in list(self.species_list_box.children):
            self.species_list_box.remove(child)
        if not self._all_species and self._species_list_error:
            # paragraph_text — exception text is arbitrary-length and
            # Labels never wrap.
            self.species_list_box.add(paragraph_text(
                f"Could not load species list: {self._species_list_error}",
                font_size=13,
            ))
            return
        for species in self._filtered_species[:50]:
            self.species_list_box.add(toga.Button(
                species,
                on_press=self._make_species_selector(species),
                style=btn_secondary(height=40, font_size=14, margin_bottom=2)
            ))

    def _make_species_selector(self, species):
        def handler(widget):
            self._selected_species = species
            self._show_add_form()
        return handler

    # ------------------------------------------------------------------
    # Save threshold
    # ------------------------------------------------------------------

    def _save_threshold(self, widget):
        if not self._selected_species:
            self.form_error.text = "Please select a species."
            return

        name = self._form_name.strip()
        if not name:
            self.form_error.text = "Please enter a target name."
            return

        try:
            attack = float(self._form_atk or 0)
            defense = float(self._form_def or 0)
            stamina = int(float(self._form_sta or 0))
            onlytop = int(float(self._form_onlytop or 0))
        except (ValueError, TypeError):
            self.form_error.text = "Invalid stat values — use numbers only."
            return

        league = self._selected_league

        if self._editing_original:
            orig_species, orig_league, orig_name = self._editing_original
            # Single transaction: a failed save leaves the original intact
            # instead of losing it between a delete-save and an add-save.
            ok = replace_threshold(orig_species, orig_league, orig_name,
                                   self._selected_species, league, name,
                                   attack, defense, stamina, onlytop)
            if not ok:
                self.form_error.text = ("Could not save changes — your "
                                        "original target is unchanged.")
                return
            self._editing_original = None
            self._show_threshold_list()
            return

        add_threshold(self._selected_species, league, name,
                      attack, defense, stamina, onlytop)

        self._show_threshold_list()

    # ------------------------------------------------------------------
    # Share/Import
    # ------------------------------------------------------------------

    def _format_threshold(self, species, league, name, t):
        return format_threshold_text(species, league, name, t)

    def _check_species_known(self, entries):
        """Best-effort species validation against the gamemaster.

        A fetcher failure here must not crash the import (it previously
        escaped the ValueError handler) — offline imports proceed
        unvalidated rather than failing.
        """
        try:
            from ..data.iv_checker import get_pokemon_index
            pokemon_index = get_pokemon_index()
        except Exception:
            logger.warning("Could not load species list; importing unvalidated")
            return
        for species, _league, _name, _spec in entries:
            if species not in pokemon_index:
                raise ValueError(f"Unknown species: {species}")

    def _show_share_screen(self, species, league, name, t):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(False)

        self.content_box.add(toga.Label(
            "Long-press to select and copy:",
            style=Pack(font_size=14, margin_bottom=8, color=COLOR_TEXT_LIGHT)
        ))

        text = self._format_threshold(species, league, name, t)
        self.content_box.add(toga.MultilineTextInput(
            value=text,
            readonly=True,
            style=Pack(flex=1, font_size=14)
        ))

        self.content_box.add(toga.Button(
            "← Target List",
            on_press=lambda w: self._show_threshold_list(),
            style=btn_nav(height=44)
        ))

    def _show_import_screen(self, widget=None):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._set_outer_buttons_enabled(False)

        self.content_box.add(toga.Button(
            "Import",
            on_press=self._do_import,
            style=btn_primary(height=48, font_size=16, margin_bottom=8)
        ))

        self._import_error = toga.Label(
            "",
            style=Pack(font_size=13, text_align="center", margin_bottom=8,
                       color=COLOR_YELLOW)
        )
        self.content_box.add(self._import_error)

        self.content_box.add(toga.Label(
            "Paste a shared target or scanner JSON:",
            style=Pack(font_size=14, margin_bottom=8, color=COLOR_TEXT_LIGHT)
        ))

        self._import_input = toga.MultilineTextInput(
            placeholder='GoBattleKit Threshold v1\nSpecies: ...\n— or —\n{"Azumarill": {"Great": ...}}',
            style=Pack(flex=1, font_size=14, color="white")
        )
        self.content_box.add(self._import_input)

        self.content_box.add(toga.Button(
            "← Target List",
            on_press=lambda w: self._show_threshold_list(),
            style=btn_nav(height=44)
        ))

    def _do_import(self, widget):
        text = self._import_input.value.strip()
        if not text:
            self._import_error.text = "Please paste a target first."
            return
        try:
            # Two paste formats: scanner JSON from pogo-simulator's dive
            # pages ("Copy for IV scanner", possibly several targets per
            # fragment) and the v1 share text. No pre-evo propagation in
            # either: check_thresholds maps pre-evos to their final form
            # via evolution_lines on its own, and stored pre-evo copies
            # actively shadowed that path (SI2; same block was removed
            # from the save path in c5fe1a8).
            if text.startswith('{'):
                entries = parse_threshold_json(text)
            else:
                entries = [parse_threshold_text(text)]
            self._check_species_known(entries)
            import_threshold_entries(entries)
            self._show_threshold_list()
        except ValueError as e:
            self._import_error.text = str(e)
            
