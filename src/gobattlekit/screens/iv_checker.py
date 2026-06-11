#!/usr/bin/env python
"""
IV checker screen — import PokeGenie CSV and check against thresholds.
"""
import logging
import shutil
import pathlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.iv_checker import (
    check_thresholds, get_pokemon_index, cp_to_level, append_user_generated,
    compute_rank_table, ivs_to_stats, LEAGUE_CAPS
)
from ..data.thresholds import DEFAULT_THRESHOLDS, EVOLUTION_LINES
from ..data.fetcher import CACHE_DIR, SAVED_CSV, USER_GENERATED_CSV, get_csv_path
from ..platform import ON_ANDROID, ON_IOS, ON_MOBILE
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_YELLOW, COLOR_BG,
    btn_primary, btn_secondary, btn_back, btn_league, btn_icon, card_box,
    btn_nav, btn_destructive, btn_destructive_icon, btn_help,
    show_widget, hide_widget, paragraph_text,
)

logger = logging.getLogger(__name__)


class IVCheckerScreen:
    """Screen for checking Pokemon IVs against stat thresholds."""

    NO_CSV_MESSAGE = "No Pokémon data loaded."

    def __init__(self, app):
        self.app = app
        self.csv_path = None
        self.results = {}
        self.league = 'great'
        self._manual_species = None
        self._manual_atk = '0'
        self._manual_def = '0'
        self._manual_sta = '0'
        self._manual_cp = ''
        self._clear_csv_pending = False

    def _get_thresholds(self):
        return DEFAULT_THRESHOLDS

    def build(self):
        self._clear_csv_pending = False
        self.container = toga.Box(style=CONTAINER)

        self.container.add(toga.Label(
            "IV Checker",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10,
                       color=COLOR_ACCENT)
        ))

        league_box = toga.Box(style=Pack(direction=ROW, margin_bottom=16))
        for league, label in (('great', 'Great'), ('ultra', 'Ultra'), ('master', 'Master')):
            btn = toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=btn_league()
            )
            league_box.add(btn)
        self.container.add(league_box)

        if not ON_IOS:
            self.container.add(toga.Button(
                "Import PokeGenie CSV",
                on_press=self._import_csv,
                style=btn_primary(height=52, font_size=16)
            ))

        status_row = toga.Box(style=Pack(direction=ROW, margin_bottom=2, height=36))
        self.status_label_file = toga.Label(
            pathlib.Path(self.csv_path).name if self.csv_path else "",
            style=Pack(flex=1, font_size=13, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.clear_csv_btn = toga.Button(
            "✕",
            on_press=self._clear_csv,
            style=btn_destructive_icon()
        )
        self._show_clear_btn(bool(self.csv_path))
        status_row.add(self.status_label_file)
        status_row.add(self.clear_csv_btn)
        self.container.add(status_row)

        self.status_label_stats = toga.Label(
            self._stats_line() if self.csv_path else self.NO_CSV_MESSAGE,
            style=Pack(font_size=13, text_align="center", margin_bottom=4,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.status_label_stats)

        self.results_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=COLOR_BG))
        scroll = toga.ScrollContainer(content=self.results_box,
                                      style=Pack(flex=1, background_color=COLOR_BG))
        self.container.add(scroll)

        self.back_btn = toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        )
        hide_widget(self.back_btn)
        self.container.add(self.back_btn)

        help_row = toga.Box(style=Pack(direction=ROW))
        help_row.add(toga.Button(
            "? Help",
            on_press=lambda w: self.app.show_help(
                topic="PvP IV Checker",
                back_screen=lambda: self.app.show_iv_checker(skip_intro=True),
                back_label="← PvP IV Checker"
            ),
            style=btn_help(flex=1, margin_right=2)
        ))
        help_row.add(toga.Button(
            "IV Credits",
            on_press=lambda w: self.app.show_iv_credits(
                back_screen=lambda: self.app.show_iv_checker(skip_intro=True),
                back_label="← IV Checker"
            ),
            style=btn_help(flex=1, margin_left=2)
        ))
        self.container.add(help_row)

        self.container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44, margin_bottom=0)
        ))

        path = get_csv_path()
        if path and not self.csv_path:
            self.csv_path = path
            self._run_check()
        else:
            self._display_species_list()

        return self.container

    def _stats_line(self):
        species_count = len([s for s in self.results if self.results[s]])
        total = sum(len(hits) for hits in self.results.values())
        return (f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                f"in {self.league.capitalize()} League")

    def _show_clear_btn(self, visible):
        if visible:
            show_widget(self.clear_csv_btn, height=32, width=44)
        else:
            hide_widget(self.clear_csv_btn)

    def _show_back_btn(self, visible):
        if visible:
            show_widget(self.back_btn, height=44)
        else:
            hide_widget(self.back_btn)

    # ------------------------------------------------------------------
    # PokeGenie import help
    # ------------------------------------------------------------------

    def _has_pokegenie_csv(self):
        return SAVED_CSV.exists()

    def _show_pokegenie_help(self, widget):
        """Show instructions for importing from PokeGenie."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(False)

        if ON_IOS:
            steps = (
                "1. Open PokeGenie (requires iVision subscription)\n"
                "2. Tap the export/share button in PokeGenie\n"
                "3. Choose 'Share' and select GoBattleKit\n"
                "4. Your CSV will be imported automatically"
            )
        else:
            steps = (
                "1. Open PokeGenie (requires iVision subscription)\n"
                "2. Export your Pokémon data as a CSV file\n"
                "3. Come back here and tap 'Import PokeGenie CSV'\n"
                "4. Select the exported CSV file"
            )

        self.results_box.add(toga.Label(
            "Importing from PokeGenie",
            style=Pack(font_size=18, font_weight="bold",
                       margin_bottom=8, text_align="center",
                       color=COLOR_ACCENT)
        ))

        self.results_box.add(paragraph_text(steps, font_size=14, margin_bottom=12))

        self.results_box.add(toga.Label(
            "Note: CSV export requires PokeGenie's iVision subscription. "
            "Without iVision, you can enter Pokémon manually instead.",
            style=Pack(font_size=13, margin_bottom=12,
                       color=COLOR_TEXT_LIGHT)
        ))

        if not ON_IOS:
            self.results_box.add(toga.Button(
                "Import PokeGenie CSV",
                on_press=self._import_csv,
                style=btn_primary(height=48, font_size=16)
            ))

        self.results_box.add(toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        ))

    # ------------------------------------------------------------------
    # Manual entry
    # ------------------------------------------------------------------

    def _show_manual_entry(self, error=None):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(False)

        form_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(
            content=form_box,
            style=Pack(flex=1),
            horizontal=False,
            vertical=True,
        )
        self.results_box.add(scroll)

        form_box.add(toga.Label(
            "Enter Pokémon details:",
            style=Pack(font_size=16, font_weight="bold",
                       margin_bottom=8, color=COLOR_ACCENT)
        ))

        if error:
            form_box.add(toga.Label(
                error,
                style=Pack(font_size=13, text_align="center",
                           margin_bottom=8, color=COLOR_TEXT_LIGHT)
            ))

        species_row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        species_row.add(toga.Label(
            "Species:",
            style=Pack(width=90, font_size=14, color=COLOR_TEXT_LIGHT)
        ))
        species_row.add(toga.Label(
            self._manual_species or "tap to select",
            style=Pack(flex=1, font_size=14, color=COLOR_ACCENT)
        ))
        species_row.add(toga.Button(
            "→",
            on_press=lambda w: self._save_manual_inputs_and_pick_species(),
            style=btn_icon()
        ))
        form_box.add(species_row)

        iv_row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        iv_row.add(toga.Label(
            "IVs:",
            style=Pack(width=50, font_size=14, color=COLOR_TEXT_LIGHT)
        ))
        for label, attr in [("Atk", '_manual_atk'), ("Def", '_manual_def'), ("HP", '_manual_sta')]:
            col = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_right=4))
            col.add(toga.Label(
                label,
                style=Pack(font_size=12, text_align="center", color=COLOR_TEXT_LIGHT)
            ))
            current = getattr(self, attr, '0')
            inp = toga.TextInput(
                value=str(current),
                style=Pack(font_size=14)
            )
            setattr(self, f'{attr}_input', inp)
            col.add(inp)
            iv_row.add(col)
        form_box.add(iv_row)

        cp_row = toga.Box(style=Pack(direction=ROW, margin_bottom=8))
        cp_row.add(toga.Label(
            "CP:",
            style=Pack(width=50, font_size=14, color=COLOR_TEXT_LIGHT)
        ))
        self._manual_cp_input = toga.TextInput(
            value=str(self._manual_cp),
            style=Pack(flex=1, font_size=14)
        )
        cp_row.add(self._manual_cp_input)
        form_box.add(cp_row)

        form_box.add(toga.Button(
            "Check this Pokémon",
            on_press=self._submit_manual_entry,
            style=btn_primary(height=48, font_size=16)
        ))

        form_box.add(toga.Button(
            "← Cancel",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        ))

    def _save_manual_inputs_and_pick_species(self):
        self._manual_atk = self._manual_atk_input.value.strip() or '0'
        self._manual_def = self._manual_def_input.value.strip() or '0'
        self._manual_sta = self._manual_sta_input.value.strip() or '0'
        self._manual_cp = self._manual_cp_input.value.strip() or ''
        self._show_manual_species_picker()

    def _show_manual_species_picker(self):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        pokemon_index = get_pokemon_index()
        self._manual_all_species = sorted(pokemon_index.keys())
        self._manual_filtered = list(self._manual_all_species)

        self._manual_search = toga.TextInput(
            placeholder="Type to search (e.g. Medicham)",
            on_change=self._filter_manual_species,
            style=Pack(margin_bottom=8)
        )
        self.results_box.add(self._manual_search)

        self._manual_species_list_box = toga.Box(style=Pack(direction=COLUMN))
        scroll = toga.ScrollContainer(
            content=self._manual_species_list_box,
            style=Pack(flex=1),
            horizontal=False,
            vertical=True,
        )
        self.results_box.add(scroll)
        self._rebuild_manual_species_list()

        self.results_box.add(toga.Button(
            "← Back to Form",
            on_press=lambda w: self._show_manual_entry(),
            style=btn_nav(height=44)
        ))

    def _filter_manual_species(self, widget):
        query = self._manual_search.value.strip().lower()
        if query:
            self._manual_filtered = [
                s for s in self._manual_all_species if query in s.lower()
            ]
        else:
            self._manual_filtered = list(self._manual_all_species)
        self._rebuild_manual_species_list()

    def _rebuild_manual_species_list(self):
        for child in list(self._manual_species_list_box.children):
            self._manual_species_list_box.remove(child)
        for species in self._manual_filtered[:50]:
            self._manual_species_list_box.add(toga.Button(
                species,
                on_press=self._make_manual_species_handler(species),
                style=btn_secondary(height=40, font_size=14, margin_bottom=2)
            ))

    def _make_manual_species_handler(self, species):
        def handler(widget):
            self._manual_species = species
            self._show_manual_entry()
        return handler

    def _submit_manual_entry(self, widget):
        species = self._manual_species
        if not species:
            self._show_manual_entry(error="Please select a species.")
            return

        try:
            atk_iv = int(self._manual_atk_input.value.strip())
            def_iv = int(self._manual_def_input.value.strip())
            sta_iv = int(self._manual_sta_input.value.strip())
            cp = int(self._manual_cp_input.value.strip())
        except ValueError:
            self._show_manual_entry(error="Please enter valid numbers for IVs and CP.")
            return

        if not (0 <= atk_iv <= 15 and 0 <= def_iv <= 15 and 0 <= sta_iv <= 15):
            self._show_manual_entry(error="IVs must be between 0 and 15.")
            return

        if cp <= 0:
            self._show_manual_entry(error="Please enter a valid CP.")
            return

        self._manual_atk = atk_iv
        self._manual_def = def_iv
        self._manual_sta = sta_iv
        self._manual_cp = cp

        pokemon_index = get_pokemon_index()
        if species not in pokemon_index:
            self._show_manual_entry(error=f"Could not find base stats for {species}.")
            return

        base = pokemon_index[species]
        level = cp_to_level(cp, atk_iv, def_iv, sta_iv,
                             base['atk'], base['def'], base['hp'])
        if level is None:
            self._show_manual_entry(
                error=f"Could not find a level matching CP {cp} for those IVs. "
                      f"Please check your values."
            )
            return

        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            append_user_generated(
                str(USER_GENERATED_CSV),
                species, atk_iv, def_iv, sta_iv, cp, level
            )
        except Exception as e:
            self._show_manual_entry(error=f"Could not save: {e}")
            return

        self._manual_species = None
        self._manual_atk = '0'
        self._manual_def = '0'
        self._manual_sta = '0'
        self._manual_cp = ''

        if not self.csv_path:
            self.csv_path = str(USER_GENERATED_CSV)

        self._run_check()

    # ------------------------------------------------------------------
    # CSV loading
    # ------------------------------------------------------------------

    def load_csv(self, path):
        self._clear_csv_pending = False
        src_path = str(path).replace('file://', '')
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            src = pathlib.Path(src_path)
            if src.resolve() != SAVED_CSV.resolve():
                shutil.copy2(src, SAVED_CSV)
            self.csv_path = str(SAVED_CSV)
        except Exception as e:
            logger.exception("Could not save CSV to cache")
            self.csv_path = None
            if hasattr(self, 'status_label_file'):
                self.status_label_file.text = ""
                self._show_clear_btn(False)
                self.status_label_stats.text = f"Could not load CSV: {e}"
            return
        self._run_check()

    async def _import_csv(self, widget):
        if ON_ANDROID:
            self._import_csv_android()
        else:
            try:
                path = await self.app.main_window.open_file_dialog(
                    title="Select PokeGenie Export",
                    file_types=["csv"],
                )
                if path:
                    self.load_csv(str(path))
            except Exception as e:
                self.status_label_file.text = ""
                self.status_label_stats.text = f"Error opening file: {e}"

    def _import_csv_android(self):
        try:
            from java import jclass
            Intent = jclass('android.content.Intent')
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("text/comma-separated-values")
            intent.addCategory(Intent.CATEGORY_OPENABLE)

            def on_complete(result_code, result):
                try:
                    if result and result.getData():
                        uri = result.getData()
                        CACHE_DIR.mkdir(exist_ok=True, parents=True)
                        dest = CACHE_DIR / 'pokegenie_import.csv'
                        ContentResolver = self.app._impl.native.getContentResolver()
                        stream = ContentResolver.openInputStream(uri)
                        try:
                            ByteArrayOutputStream = jclass('java.io.ByteArrayOutputStream')
                            baos = ByteArrayOutputStream()
                            buf = bytearray(4096)
                            while True:
                                n = stream.read(buf)
                                if n < 0:
                                    break
                                baos.write(buf, 0, n)
                            data = bytes(baos.toByteArray())
                            dest.write_bytes(data)
                        finally:
                            stream.close()
                        self.load_csv(str(dest))
                    else:
                        logger.info("Android file picker: no file selected")
                except Exception as e:
                    logger.exception("Android CSV import callback error")
                    self.status_label_file.text = ""
                    self.status_label_stats.text = f"Error importing: {e}"

            self.app._impl.start_activity(intent, on_complete=on_complete)

        except Exception as e:
            logger.exception("Android CSV import error")
            self.status_label_file.text = ""
            self.status_label_stats.text = f"Error importing: {e}"

    def _run_check(self):
        if not self.csv_path:
            self._display_species_list()
            return
        try:
            self.results = check_thresholds(
                self.csv_path,
                self._get_thresholds(),
                league=self.league,
                max_level=51,
                evolution_lines=EVOLUTION_LINES,
                include_empty=True,
            )
            self.status_label_file.text = pathlib.Path(self.csv_path).name
            self._show_clear_btn(True)
            self.status_label_stats.text = self._stats_line()
            self._display_species_list()
        except Exception as e:
            self.status_label_file.text = ""
            self._show_clear_btn(False)
            self.status_label_stats.text = f"Error reading CSV: {e}"

    # ------------------------------------------------------------------
    # Species list view
    # ------------------------------------------------------------------

    def _display_species_list(self):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(False)

        thresholds = self._get_thresholds()
        league_label = self.league.capitalize()

        all_target_species = sorted([
            s for s in thresholds
            if league_label in thresholds.get(s, {})
        ])

        if not all_target_species:
            self.results_box.add(toga.Label(
                "No targets defined for this league.",
                style=Pack(font_size=14, text_align="center", margin_top=20,
                           color=COLOR_TEXT_LIGHT)
            ))
            return

        total = sum(len(hits) for hits in self.results.values())
        if total > 0:
            self.results_box.add(toga.Button(
                f"Show All ({total} hits)",
                on_press=lambda w: self._display_all_results(),
                style=btn_primary(height=48, font_size=16)
            ))

        self.results_box.add(toga.Button(
            "✏️ Enter a Pokémon manually",
            on_press=lambda w: self._show_manual_entry(),
            style=btn_secondary(height=44, font_size=14)
        ))

        if not self._has_pokegenie_csv():
            self.results_box.add(toga.Button(
                "Import from PokeGenie",
                on_press=self._show_pokegenie_help,
                style=btn_secondary(height=44, font_size=14)
            ))

        for species in all_target_species:
            hits = self.results.get(species, [])
            self.results_box.add(toga.Button(
                f"{species} ({len(hits)})",
                on_press=self._make_species_handler(species),
                style=btn_secondary(height=48, font_size=16)
            ))

    def _make_species_handler(self, species):
        def handler(widget):
            self._display_species_results(species)
        return handler

    # ------------------------------------------------------------------
    # Species results view
    # ------------------------------------------------------------------

    def _display_species_results(self, species):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(True)

        hits = self.results.get(species, [])
        league_label = self.league.capitalize()

        self.results_box.add(toga.Label(
            f"{species} — {len(hits)} hit{'s' if len(hits) != 1 else ''}",
            style=Pack(font_size=18, font_weight="bold",
                       margin_bottom=8, text_align="center",
                       color=COLOR_ACCENT)
        ))

        thresholds = self._get_thresholds()
        all_targets = sorted(
            thresholds.get(species, {}).get(league_label, {}).keys()
        )

        targets_with_hits = {}
        for hit in hits:
            for target in hit['matched']:
                targets_with_hits[target] = targets_with_hits.get(target, 0) + 1

        targets_without_hits = [t for t in all_targets if t not in targets_with_hits]

        self._targets_without_hits = set(targets_without_hits)

        # Build the list of target options to cycle through.
        # If there are hits, include "All targets" as the first option.
        # If there are no hits, skip "All targets" and start on the first
        # specific target so qualifying IVs are shown immediately.
        if hits:
            self._target_options_raw = [None] + sorted(targets_with_hits.keys()) + targets_without_hits
        else:
            self._target_options_raw = targets_without_hits or [None]
        self._target_index = 0

        def _target_label_text(target):
            if target is None:
                return f"All targets ({len(hits)})"
            elif target in self._targets_without_hits:
                return f"{target} (0)"
            else:
                return f"{target} ({targets_with_hits.get(target, 0)})"

        def make_cycle_handler(direction):
            def handler(widget):
                self._target_index = (self._target_index + direction) % len(self._target_options_raw)
                current = self._target_options_raw[self._target_index]
                self.target_label.text = _target_label_text(current)
                self._refresh_hits(species, hits)
            return handler

        initial_target = self._target_options_raw[self._target_index]
        target_row = toga.Box(style=Pack(direction=ROW, margin_bottom=12))
        target_row.add(toga.Button("◀", on_press=make_cycle_handler(-1),
                                   style=btn_icon(width=44, height=44)))
        self.target_label = toga.Label(
            _target_label_text(initial_target),
            style=Pack(flex=1, text_align="center", font_size=14,
                       color=COLOR_TEXT_LIGHT)
        )
        target_row.add(self.target_label)
        target_row.add(toga.Button("▶", on_press=make_cycle_handler(1),
                                   style=btn_icon(width=44, height=44)))
        self.results_box.add(target_row)

        self.hits_box = toga.Box(style=Pack(direction=COLUMN))
        self.results_box.add(self.hits_box)
        self._refresh_hits(species, hits)

    def _refresh_hits(self, species, all_hits):
        for child in list(self.hits_box.children):
            self.hits_box.remove(child)

        current = self._target_options_raw[self._target_index]
        league_label = self.league.capitalize()

        # Empty target — show qualifying IV combinations
        if current is not None and current in self._targets_without_hits:
            thresholds = self._get_thresholds()
            target = thresholds.get(species, {}).get(league_label, {}).get(current, {})
            parts = []
            if target.get('attack', 0):
                parts.append(f"{target['attack']}A")
            if target.get('defense', 0):
                parts.append(f"{target['defense']}D")
            if target.get('stamina', 0):
                parts.append(f"{target['stamina']}S")
            if target.get('onlytop', 0):
                parts.append(f"top{target['onlytop']}")
            req_str = ', '.join(parts) if parts else 'any'

            pokemon_index = get_pokemon_index()
            if species in pokemon_index:
                base = pokemon_index[species]
                max_cp = LEAGUE_CAPS.get(self.league, 1500.99)
                max_level = 51

                rank_table = compute_rank_table(
                    species,
                    base['atk'], base['def'], base['hp'],
                    max_level=max_level, max_cp=max_cp,
                )

                qualifying = []
                for (a, d, s), rank in rank_table.items():
                    stats = ivs_to_stats(
                        a, d, s, start_level=1,
                        base_atk=base['atk'], base_def=base['def'],
                        base_sta=base['hp'],
                        max_level=max_level, max_cp=max_cp,
                    )
                    if stats is None:
                        continue
                    if not (stats['attack'] >= target.get('attack', 0) and
                            stats['defense'] >= target.get('defense', 0) and
                            stats['stamina'] >= target.get('stamina', 0)):
                        continue
                    if 'ivs' in target and not any(
                        tuple(iv) == (a, d, s) for iv in target['ivs']
                    ):
                        continue
                    if 'onlytop' in target and rank > target['onlytop']:
                        continue
                    qualifying.append((rank, a, d, s, stats))

                # Sort by rank, truncate to top 100.
                qualifying.sort(key=lambda x: x[0])
                qualifying = qualifying[:100]
                # qualifying.sort(key=lambda x: (-x[1], -x[2], -x[3]))  # atk desc, def desc, sta desc

                self.hits_box.add(toga.Label(
                    f"Requires: {req_str}",
                    style=Pack(font_size=12, margin_bottom=4,
                               color=COLOR_TEXT_LIGHT)
                ))
                self.hits_box.add(toga.Label(
                    "None of your mons meet this target.",
                    style=Pack(font_size=13, font_weight="bold",
                               margin_bottom=2, color=COLOR_YELLOW)
                ))
                self.hits_box.add(toga.Label(
                    f"Here are the top {len(qualifying)} IV combinations that do:",
                    style=Pack(font_size=13, font_weight="bold",
                               margin_bottom=8, color=COLOR_YELLOW)
                ))

                for rank, a, d, s, stats in qualifying:
                    card = toga.Box(style=card_box(margin_bottom=4))
                    card.add(toga.Label(
                        f"{a}/{d}/{s}  CP:{stats['cp']}  Rank:#{rank}",
                        style=Pack(font_size=13, font_weight="bold",
                                   color=COLOR_TEXT_LIGHT)
                    ))
                    card.add(toga.Label(
                        f"Atk:{stats['attack']:.2f}  Def:{stats['defense']:.2f}  "
                        f"HP:{stats['stamina']}  SP:{stats['stat_prod']}",
                        style=Pack(font_size=12, color=COLOR_TEXT_LIGHT)
                    ))
                    self.hits_box.add(card)
            else:
                self.hits_box.add(toga.Label(
                    f"No Pokémon meets this target\nRequires: {req_str}",
                    style=Pack(font_size=14, color=COLOR_TEXT_LIGHT)
                ))
            return

        hits = all_hits if current is None else [
            h for h in all_hits if current in h['matched']
        ]

        if not hits:
            self.hits_box.add(toga.Label(
                "No hits for this target.",
                style=Pack(font_size=14, text_align="center", margin_top=10,
                           color=COLOR_TEXT_LIGHT)
            ))
            if not self.csv_path:
                self.hits_box.add(toga.Button(
                    "✏️ Enter a Pokémon manually",
                    on_press=lambda w: self._show_manual_entry(),
                    style=btn_secondary(height=44, font_size=14)
                ))
            return

        hits = sorted(hits, key=lambda h: h['stats']['stat_prod'], reverse=True)
        for hit in hits:
            self._add_hit_display(self.hits_box, hit)

    # ------------------------------------------------------------------
    # Show all results view
    # ------------------------------------------------------------------

    def _display_all_results(self):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(True)

        for sp in sorted(self.results.keys()):
            hits = self.results[sp]
            if not hits:
                continue
            self.results_box.add(toga.Label(
                f"{sp} ({len(hits)} hit{'s' if len(hits) != 1 else ''})",
                style=Pack(font_size=16, font_weight="bold",
                           margin_top=12, margin_bottom=4,
                           color=COLOR_ACCENT)
            ))
            hits = sorted(hits, key=lambda h: h['stats']['stat_prod'], reverse=True)
            for hit in hits:
                self._add_hit_display(self.results_box, hit)

    # ------------------------------------------------------------------
    # League selection
    # ------------------------------------------------------------------

    def _make_league_handler(self, league):
        def handler(widget):
            self.league = league
            if self.csv_path:
                self._run_check()
            else:
                self._display_species_list()
        return handler

    # ------------------------------------------------------------------
    # Clear CSV
    # ------------------------------------------------------------------

    def _clear_csv(self, widget):
        # Two-tap confirm (same pattern as Edit Targets' Clear All): this
        # permanently deletes BOTH the imported PokeGenie CSV and all
        # manually entered Pokémon, so one stray tap must not be enough.
        if not self._clear_csv_pending:
            self._clear_csv_pending = True
            self.status_label_stats.text = (
                "Tap ✕ again to delete the imported CSV and all manually "
                "entered Pokémon."
            )
            return
        self._clear_csv_pending = False
        self.csv_path = None
        self.results = {}
        try:
            if SAVED_CSV.exists():
                SAVED_CSV.unlink()
            if USER_GENERATED_CSV.exists():
                USER_GENERATED_CSV.unlink()
        except Exception:
            logger.exception("Could not delete cached CSV")
        self.status_label_file.text = ""
        self.status_label_stats.text = self.NO_CSV_MESSAGE
        self._show_clear_btn(False)
        self._show_back_btn(False)
        self._display_species_list()

    # ------------------------------------------------------------------
    # Hit display
    # ------------------------------------------------------------------

    def _add_hit_display(self, box, hit):
        m = hit['mon']
        s = hit['stats']
        pre = f" ({hit['csv_species']})" if hit['is_pre_evo'] else ""
        iv_str = f"{m['atk_iv']}/{m['def_iv']}/{m['sta_iv']}{pre} (CP {m['cp']})"
        line1 = (f"Atk:{s['attack']:.2f} "
                 f"Def:{s['defense']:.2f} "
                 f"HP:{s['stamina']}")
        line2 = f"SP:{s['stat_prod']}  Rank:#{s.get('rank', '?')}"

        card = toga.Box(style=card_box())
        card.add(toga.Label(
            iv_str,
            style=Pack(font_size=14, font_weight="bold", color=COLOR_TEXT_LIGHT)
        ))
        card.add(toga.Label(
            line1,
            style=Pack(font_size=12, color=COLOR_TEXT_LIGHT)
        ))
        card.add(toga.Label(
            line2,
            style=Pack(font_size=12, color=COLOR_TEXT_LIGHT)
        ))
        for target in hit['matched']:
            card.add(toga.Label(
                f"✅ {target}",
                style=Pack(font_size=12, color=COLOR_ACCENT)
            ))
        box.add(card)
