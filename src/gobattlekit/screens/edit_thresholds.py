#!/usr/bin/env python
"""
Edit Thresholds screen — add, view, and delete user-defined IV thresholds.
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.user_thresholds import (
    load_user_thresholds, add_threshold, delete_threshold, clear_all_thresholds,
    get_all_species
)
from ..data.iv_checker import get_pokemon_index
from ..data.thresholds import EVOLUTION_LINES


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
        self._filtered_species = []
        # Form state
        self._selected_species = None
        self._selected_league = "Great"
        self._form_name = self.FORM_DEFAULTS['name']
        self._form_atk = self.FORM_DEFAULTS['atk']
        self._form_def = self.FORM_DEFAULTS['def']
        self._form_sta = self.FORM_DEFAULTS['sta']
        self._form_onlytop = self.FORM_DEFAULTS['onlytop']
        # stores (species, league, name) of entry being edited, or
        # None for new entry
        self._editing_original = None
        self._clear_all_pending = False

    def _ensure_species_list(self):
        if self._all_species is None:
            try:
                pokemon_index = get_pokemon_index()
                self._all_species = get_all_species(pokemon_index)
            except Exception as e:
                print(f"Could not load species list: {e}")
                self._all_species = []
        return self._all_species

    def build(self):
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        self.container.add(toga.Label(
            "My Thresholds",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10)
        ))

        top_row = toga.Box(style=Pack(direction=ROW, margin_bottom=12))
        top_row.add(toga.Button(
            "Clear All",
            on_press=self._confirm_clear_all,
            style=Pack(flex=1, height=44, margin_right=4)
        ))
        top_row.add(toga.Button(
            "← My IV Checker",
            on_press=lambda w: self.app.show_user_iv_checker(),
            style=Pack(flex=1, height=44, margin_left=4)
        ))
        self.container.add(top_row)

        self.container.add(toga.Button(
            "Add Threshold",
            on_press=self._show_add_form,
            style=Pack(height=48, font_size=16, margin_bottom=12)
        ))

        self.container.add(toga.Button(
            "Import from Text",
            on_press=self._show_import_screen,
            style=Pack(height=48, font_size=16, margin_bottom=8)
        ))
        
        self.content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(content=self.content_box, style=Pack(flex=1))
        self.container.add(scroll)

        self._show_threshold_list()
        return self.container

    # ------------------------------------------------------------------
    # Threshold list view
    # ------------------------------------------------------------------

    def _show_threshold_list(self):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

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
                "No user thresholds yet. Tap 'Add Threshold' to get started.",
                style=Pack(font_size=14, text_align="center", margin_top=20)
            ))
            return

        for species in sorted(thresholds.keys()):
            self.content_box.add(toga.Label(
                species,
                style=Pack(font_size=16, font_weight="bold",
                           margin_top=12, margin_bottom=4)
            ))
            for league_label in sorted(thresholds[species].keys()):
                self.content_box.add(toga.Label(
                    f"  {league_label} League",
                    style=Pack(font_size=13, margin_bottom=2)
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
                        style=Pack(flex=1, font_size=13)
                        ))
                    row.add(toga.Button(
                        "✎",
                        on_press=self._make_edit_handler(species, league_label, name, t),
                        style=Pack(width=44, height=36)
                        ))
                    row.add(toga.Button(
                        "⧉",
                        on_press=self._make_duplicate_handler(species, league_label, name, t),
                        style=Pack(width=44, height=36)
                    ))
                    row.add(toga.Button(
                        "📤",
                        on_press=self._make_share_handler(species, league_label, name, t),
                        style=Pack(width=44, height=36)
                    ))
                    row.add(toga.Button(
                        "✕",
                        on_press=self._make_delete_handler(species, league_label, name),
                        style=Pack(width=44, height=36)
                        ))
                    self.content_box.add(row)

    def _make_delete_handler(self, species, league, name):
        def handler(widget):
            delete_threshold(species, league, name)
            self._show_threshold_list()
        return handler

    def _make_duplicate_handler(self, species, league, name, t):
        def handler(widget):
            self._editing_original = None  # not editing, creating new
            self._selected_species = species
            self._selected_league = league.replace(" League", "")
            self._form_name = self.FORM_DEFAULTS['name']  # force user to enter new name
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
        """Pre-fill form with existing threshold values for editing."""
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

        self.content_box.add(toga.Button(
            "← Cancel",
            on_press=lambda w: self._show_threshold_list(),
            style=Pack(height=44, margin_bottom=12)
        ))

        # League — inline buttons, no keyboard needed


        self.content_box.add(toga.Label(
            "League:",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        league_row = toga.Box(style=Pack(direction=ROW, margin_bottom=4))
        for league in ("Great", "Ultra", "Master"):
            btn = toga.Button(
                league,
                on_press=self._make_league_btn_handler(league),
                style=Pack(flex=1, height=40, margin=2)
            )
            league_row.add(btn)
        self.content_box.add(league_row)
        self.league_value_label = toga.Label(
            f"Selected: {self._selected_league}",
            style=Pack(font_size=13, text_align="center", margin_bottom=12)
        )
        self.content_box.add(self.league_value_label)


        # Each field is a row with label + value + arrow button
        self._add_field_row("Species:", self._selected_species or "tap to select",
                            self._show_species_picker)
        self._add_field_row("Name:", self._form_name or "tap to enter",
                            lambda w: self._show_text_entry("Name", "name"))
        self._add_field_row("Attack:", self._form_atk,
                            lambda w: self._show_text_entry("Min Attack (0=any)", "atk"))
        self._add_field_row("Defense:", self._form_def,
                            lambda w: self._show_text_entry("Min Defense (0=any)", "def"))
        self._add_field_row("Stamina:", self._form_sta,
                            lambda w: self._show_text_entry("Min Stamina (0=any)", "sta"))
        self._add_field_row("Only top N:", self._form_onlytop,
                            lambda w: self._show_text_entry("Only top N (0=all)", "onlytop"))

        # Save button
        self.content_box.add(toga.Button(
            "Save Threshold",
            on_press=self._save_threshold,
            style=Pack(height=48, font_size=16, margin_top=16)
        ))

        self.form_error = toga.Label(
            "",
            style=Pack(font_size=13, text_align="center", margin_top=8)
        )
        self.content_box.add(self.form_error)

    def _add_field_row(self, label, value, handler):
        """Add a label + value + arrow button row to the form."""
        row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        row.add(toga.Label(
            label,
            style=Pack(width=90, font_size=14)
        ))
        row.add(toga.Label(
            str(value),
            style=Pack(flex=1, font_size=14)
        ))
        row.add(toga.Button(
            "→",
            on_press=handler,
            style=Pack(width=44, height=40)
        ))
        self.content_box.add(row)

    def _make_league_btn_handler(self, league):
        def handler(widget):
            self._selected_league = league
            # Update the league label directly without rebuilding whole form
            self.league_value_label.text = f"Selected: {self._selected_league}"
        return handler

    # ------------------------------------------------------------------
    # Text entry screen
    # ------------------------------------------------------------------

    def _show_text_entry(self, prompt, field):
        """Show a single-field text entry screen for the given field."""
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self.content_box.add(toga.Button(
            "← Back to Form",
            on_press=lambda w: self._show_add_form(),
            style=Pack(height=44, margin_bottom=16)
        ))

        self.content_box.add(toga.Label(
            prompt,
            style=Pack(font_size=18, font_weight="bold",
                       text_align="center", margin_bottom=16)
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
            style=Pack(height=48, font_size=16)
        ))

    def _save_text_entry(self, widget):
        """Save the text entry value and return to form."""
        value = self._entry_input.value.strip()
        setattr(self, f"_form_{self._entry_field}", value)
        self._show_add_form()

    # ------------------------------------------------------------------
    # Species picker
    # ------------------------------------------------------------------

    def _show_species_picker(self, widget=None):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self._ensure_species_list()
        self._filtered_species = list(self._all_species)

        self.content_box.add(toga.Button(
            "← Back to Form",
            on_press=self._show_add_form,
            style=Pack(height=44, margin_bottom=8)
        ))

        self.content_box.add(toga.Label(
            "Type to search:",
            style=Pack(font_size=14, margin_bottom=4)
        ))
        self.species_search = toga.TextInput(
            placeholder="e.g. Medicham",
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
        for species in self._filtered_species[:50]:
            self.species_list_box.add(toga.Button(
                species,
                on_press=self._make_species_selector(species),
                style=Pack(height=40, font_size=14, margin_bottom=2)
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
            self.form_error.text = "Please enter a threshold name."
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

        # If editing, delete the original entry first
        if self._editing_original:
            orig_species, orig_league, orig_name = self._editing_original
            delete_threshold(orig_species, orig_league, orig_name)
            # Also delete from pre-evos if applicable
            for final, line in EVOLUTION_LINES.items():
                if final == orig_species:
                    for pre_evo in line[:-1]:
                        delete_threshold(pre_evo, orig_league, orig_name)
                    break
            self._editing_original = None        

        add_threshold(self._selected_species, league, name,
                      attack, defense, stamina, onlytop)

        self._show_threshold_list()

    # ------------------------------------------------------------------
    # Edit threshold
    # ------------------------------------------------------------------

    def _format_threshold(self, species, league, name, t):
        """Format a threshold as human-readable shareable text."""
        lines = [
            "GoBattleKit Threshold v1",
            f"Species: {species}",
            f"League: {league.replace(' League', '')}",
            f"Name: {name}",
            f"Attack: {t.get('attack', 0)}",
            f"Defense: {t.get('defense', 0)}",
            f"Stamina: {t.get('stamina', 0)}",
            f"OnlyTop: {t.get('onlytop', 0)}",
        ]
        return "\n".join(lines)

    def _parse_threshold(self, text):
        """Parse a threshold from human-readable text.

        Returns (species, league, name, t) or raises ValueError with a message.
        """
        lines = [l.strip() for l in text.strip().splitlines()]
        if not lines or lines[0] != "GoBattleKit Threshold v1":
            raise ValueError("Not a valid GoBattleKit threshold.")

        data = {}
        for line in lines[1:]:
            if ':' not in line:
                continue
            key, _, value = line.partition(':')
            data[key.strip()] = value.strip()

        required = ('Species', 'League', 'Name', 'Attack', 'Defense', 'Stamina', 'OnlyTop')
        for field in required:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        species = data['Species']
        # Validate species exists in gamemaster
        try:
            from .iv_checker import get_pokemon_index
            pokemon_index = get_pokemon_index()
            if species not in pokemon_index:
                raise ValueError(f"Unknown species: {species}")
        except ImportError:
            pass

        league = data['League'].capitalize()
        name = data['Name']
        if not name:
            raise ValueError("Name cannot be empty.")

        try:
            attack = float(data['Attack'])
            defense = float(data['Defense'])
            stamina = int(float(data['Stamina']))
            onlytop = int(float(data['OnlyTop']))
        except ValueError:
            raise ValueError("Invalid stat values.")

        t = {'attack': attack, 'defense': defense, 'stamina': stamina}
        if onlytop > 0:
            t['onlytop'] = onlytop

        return species, league, name, t

    def _show_share_screen(self, species, league, name, t):
        """Show a screen with the threshold formatted as shareable text."""
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self.content_box.add(toga.Button(
            "← Threshold List",
            on_press=lambda w: self._show_threshold_list(),
            style=Pack(height=44, margin_bottom=12)
        ))

        self.content_box.add(toga.Label(
            "Long-press to select and copy:",
            style=Pack(font_size=14, margin_bottom=8)
        ))

        text = self._format_threshold(species, league, name, t)
        self.content_box.add(toga.MultilineTextInput(
            value=text,
            readonly=True,
            style=Pack(flex=1, font_size=14)
        ))


    def _show_import_screen(self, widget=None):
        for child in list(self.content_box.children):
            self.content_box.remove(child)

        self.content_box.add(toga.Button(
            "← Threshold List",
            on_press=lambda w: self._show_threshold_list(),
            style=Pack(height=44, margin_bottom=12)
        ))

        self.content_box.add(toga.Button(
            "Import",
            on_press=self._do_import,
            style=Pack(height=48, font_size=16, margin_bottom=8)
        ))

        self._import_error = toga.Label(
            "",
            style=Pack(font_size=13, text_align="center", margin_bottom=8)
        )
        self.content_box.add(self._import_error)

        self.content_box.add(toga.Label(
            "Paste a GoBattleKit threshold:",
            style=Pack(font_size=14, margin_bottom=8)
        ))

        self._import_input = toga.MultilineTextInput(
            placeholder="GoBattleKit Threshold v1\nSpecies: ...",
            style=Pack(flex=1, font_size=14, color="white")
        )
        self.content_box.add(self._import_input)
        
    def _do_import(self, widget):
        """Validate and import a pasted threshold."""
        text = self._import_input.value.strip()
        if not text:
            self._import_error.text = "Please paste a threshold first."
            return
        try:
            species, league, name, t = self._parse_threshold(text)
            add_threshold(species, league, name,
                          t['attack'], t['defense'], t['stamina'],
                          t.get('onlytop', 0))
            # Auto-add pre-evolutions
            for final, line in EVOLUTION_LINES.items():
                if final == species:
                    for pre_evo in line[:-1]:
                        add_threshold(pre_evo, league, name,
                                      t['attack'], t['defense'], t['stamina'],
                                      t.get('onlytop', 0))
                    break
            self._show_threshold_list()
        except ValueError as e:
            self._import_error.text = str(e)    
