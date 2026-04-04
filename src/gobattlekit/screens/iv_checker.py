#!/usr/bin/env python
"""
IV checker screen — import PokeGenie CSV and check against thresholds.
"""
import shutil
import pathlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.iv_checker import check_thresholds
from ..data.thresholds import DEFAULT_THRESHOLDS, EVOLUTION_LINES
from ..platform import ON_ANDROID, ON_IOS, ON_MOBILE
from ..theme import (
    CONTAINER, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_BG,
    btn_primary, btn_secondary, btn_back, btn_league, btn_icon, card_box,
    btn_nav, btn_destructive, btn_destructive_icon, btn_help
)


class IVCheckerScreen:
    """Screen for checking Pokemon IVs against stat thresholds."""

    NO_CSV_MESSAGE = "No CSV loaded."
    CSV_INSTRUCTIONS = (
        "Share CSV from PokeGenie → GoBattleKit"
        if ON_IOS else
        "Tap 'Import PokeGenie CSV' to get started."
    )

    def __init__(self, app):
        self.app = app
        self.csv_path = None
        self.results = {}
        self.league = 'great'

    def _get_thresholds(self):
        """Return the thresholds dict for this screen. Override in subclasses."""
        return DEFAULT_THRESHOLDS

    def build(self):
        """Build and return the IV checker screen content."""
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

        csv_name_line = pathlib.Path(self.csv_path).name if self.csv_path else ""
        stats_line = ""
        if self.csv_path:
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            stats_line = (f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                          f"in {self.league.capitalize()} League")

        status_row = toga.Box(style=Pack(direction=ROW, margin_bottom=2, height=36))
        self.status_label_file = toga.Label(
            csv_name_line,
            style=Pack(flex=1, font_size=13, text_align="center",
                       color=COLOR_TEXT_LIGHT)
        )
        self.clear_csv_btn = toga.Button(
            "✕",
            on_press=self._clear_csv,
            style=btn_destructive_icon()
        )
        self.clear_csv_btn.enabled = bool(self.csv_path)
        status_row.add(self.status_label_file)
        status_row.add(self.clear_csv_btn)
        self.container.add(status_row)

        self.status_label_stats = toga.Label(
            stats_line if stats_line else self.NO_CSV_MESSAGE,
            style=Pack(font_size=13, text_align="center", margin_bottom=4,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.status_label_stats)

        self.csv_instructions_label = toga.Label(
            "" if self.csv_path else self.CSV_INSTRUCTIONS,
            style=Pack(font_size=13, text_align="center", margin_bottom=12,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.csv_instructions_label)

        self.results_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=COLOR_BG))
        scroll = toga.ScrollContainer(content=self.results_box,
                                      style=Pack(flex=1, background_color=COLOR_BG))
        self.container.add(scroll)

        # Dynamic back button
        self.back_btn = toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_nav(height=44)
        )
        self.back_btn.enabled = False
        self.back_btn.style.height = 2
        self.back_btn.style.margin_bottom = 0
        self.container.add(self.back_btn)

        self.container.add(toga.Button(
            "? Help",
            on_press=lambda w: self.app.show_help(
                topic="PvP IV Checker",
                back_screen=lambda: self.app.show_iv_checker(),
                back_label="← PvP IV Checker"
            ),
            style=btn_help()
        ))

        self.container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44, margin_bottom=0)
        ))

        if self.results:
            self._display_species_list()

        return self.container

    def _show_back_btn(self, visible):
        self.back_btn.enabled = visible
        self.back_btn.style.height = 44 if visible else 2
        self.back_btn.style.margin_bottom = 0

    # ------------------------------------------------------------------
    # CSV loading
    # ------------------------------------------------------------------

    def load_csv(self, path):
        from ..data.fetcher import CACHE_DIR, SAVED_CSV
        self.csv_path = str(path).replace('file://', '')
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            src = pathlib.Path(self.csv_path)
            if src.resolve() != SAVED_CSV.resolve():
                shutil.copy2(src, SAVED_CSV)
        except Exception as e:
            print(f"Could not save CSV to cache: {e}")
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
                        from ..data.fetcher import CACHE_DIR
                        CACHE_DIR.mkdir(exist_ok=True, parents=True)
                        dest = CACHE_DIR / 'pokegenie_import.csv'
                        ContentResolver = self.app._impl.native.getContentResolver()
                        stream = ContentResolver.openInputStream(uri)
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
                        stream.close()
                        self.load_csv(str(dest))
                    else:
                        print("Android file picker: no file selected")
                except Exception as e:
                    print(f"Android CSV import callback error: {e}")
                    self.status_label_file.text = ""
                    self.status_label_stats.text = f"Error importing: {e}"

            self.app._impl.start_activity(intent, on_complete=on_complete)

        except Exception as e:
            print(f"Android CSV import error: {e}")
            self.status_label_file.text = ""
            self.status_label_stats.text = f"Error importing: {e}"

    def _run_check(self):
        if not self.csv_path:
            return
        try:
            self.results = check_thresholds(
                self.csv_path,
                DEFAULT_THRESHOLDS,
                league=self.league,
                max_level=51,
                evolution_lines=EVOLUTION_LINES,
                include_empty=True,
            )
            self.status_label_file.text = pathlib.Path(self.csv_path).name
            self.clear_csv_btn.enabled = True
            self.csv_instructions_label.text = ""
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            self.status_label_stats.text = (
                f"{species_count} species, {total} hit{'s' if total != 1 else ''} "
                f"in {self.league.capitalize()} League"
            )
            self._display_species_list()
        except Exception as e:
            self.status_label_file.text = ""
            self.clear_csv_btn.enabled = False
            self.status_label_stats.text = f"Error reading CSV: {e}"

    # ------------------------------------------------------------------
    # Species list view
    # ------------------------------------------------------------------

    def _display_species_list(self):
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self._show_back_btn(False)

        if not self.results:
            if not self.csv_path:
                self.results_box.add(toga.Label(
                    self.NO_CSV_MESSAGE,
                    style=Pack(font_size=14, text_align="center", margin_top=20,
                               color=COLOR_TEXT_LIGHT)
                ))
            else:
                self.results_box.add(toga.Label(
                    "No Pokémon hit the thresholds for this league.",
                    style=Pack(font_size=14, text_align="center", margin_top=20,
                               color=COLOR_TEXT_LIGHT)
                ))
            return

        total = sum(len(hits) for hits in self.results.values())
        self.results_box.add(toga.Button(
            f"Show All ({total} hits)",
            on_press=lambda w: self._display_all_results(),
            style=btn_primary(height=48, font_size=16)
        ))

        for species in sorted(self.results.keys()):
            hits = self.results[species]
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

        # Get all targets for this species
        thresholds = self._get_thresholds()
        all_targets = sorted(
            thresholds.get(species, {}).get(league_label, {}).keys()
        )

        # Split into targets with hits and targets without
        targets_with_hits = {}
        for hit in hits:
            for target in hit['matched']:
                targets_with_hits[target] = targets_with_hits.get(target, 0) + 1

        targets_without_hits = [t for t in all_targets if t not in targets_with_hits]

        # target_options: None (all), then targets with hits, then empty targets
        self._target_index = 0
        self._target_options_raw = [None] + sorted(targets_with_hits.keys()) + targets_without_hits
        self._targets_without_hits = set(targets_without_hits)

        def make_cycle_handler(direction):
            def handler(widget):
                self._target_index = (self._target_index + direction) % len(self._target_options_raw)
                current = self._target_options_raw[self._target_index]
                if current is None:
                    self.target_label.text = f"All targets ({len(hits)})"
                elif current in self._targets_without_hits:
                    self.target_label.text = f"{current} (0)"
                else:
                    count = targets_with_hits.get(current, 0)
                    self.target_label.text = f"{current} ({count})"
                self._refresh_hits(species, hits)
            return handler

        target_row = toga.Box(style=Pack(direction=ROW, margin_bottom=12))
        target_row.add(toga.Button("◀", on_press=make_cycle_handler(-1),
                                   style=btn_icon(width=44, height=44)))
        self.target_label = toga.Label(
            f"All targets ({len(hits)})",
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

        # Empty target card
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
            card = toga.Box(style=card_box())
            card.add(toga.Label(
                "No Pokémon meets this target",
                style=Pack(font_size=14, font_weight="bold",
                           color=COLOR_TEXT_LIGHT)
            ))
            card.add(toga.Label(
                f"Requires: {req_str}",
                style=Pack(font_size=12, color=COLOR_TEXT_LIGHT)
            ))
            self.hits_box.add(card)
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
        return handler

    # ------------------------------------------------------------------
    # Clear CSV
    # ------------------------------------------------------------------

    def _clear_csv(self, widget):
        from ..data.fetcher import SAVED_CSV
        self.csv_path = None
        self.results = {}
        try:
            if SAVED_CSV.exists():
                SAVED_CSV.unlink()
        except Exception as e:
            print(f"Could not delete cached CSV: {e}")
        self.status_label_file.text = ""
        self.status_label_stats.text = self.NO_CSV_MESSAGE
        self.csv_instructions_label.text = self.CSV_INSTRUCTIONS
        self.clear_csv_btn.enabled = False
        self._show_back_btn(False)
        for child in list(self.results_box.children):
            self.results_box.remove(child)

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
                 f"Sta:{s['stamina']}")
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
