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
    CONTAINER, LABEL_TITLE, COLOR_ACCENT, COLOR_TEXT_LIGHT, COLOR_BG,
    btn_primary, btn_secondary, btn_back, btn_league, btn_icon, card_box,
    btn_nav, btn_destructive, btn_destructive_icon
)

    
class IVCheckerScreen:
    """Screen for checking Pokemon IVs against stat thresholds."""

    NO_CSV_MESSAGE = (
    "No CSV loaded. Export from PokeGenie and tap Share → GoBattleKit"
    if ON_IOS else
    "No CSV loaded. Tap 'Import PokeGenie CSV' to get started."
    )
    def __init__(self, app):
        self.app = app
        self.csv_path = None
        self.results = {}
        self.league = 'great'

    def build(self):
        """Build and return the IV checker screen content."""
        self.container = toga.Box(style=CONTAINER)

        # Title
        self.container.add(toga.Label(
            "IV Checker",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10,
                       color=COLOR_ACCENT)
        ))

        # League selector row
        league_box = toga.Box(style=Pack(direction=ROW, margin_bottom=16))
        for league, label in (('great', 'Great'), ('ultra', 'Ultra'), ('master', 'Master')):
            btn = toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=btn_league()
            )
            league_box.add(btn)
        self.container.add(league_box)

        # Import button — not available on iOS
        if not ON_IOS:
            self.container.add(toga.Button(
                "Import PokeGenie CSV",
                on_press=self._import_csv,
                style=btn_primary(height=52, font_size=16)
            ))

        # Status labels
        initial_status = self.NO_CSV_MESSAGE
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
            stats_line if stats_line else initial_status,
            style=Pack(font_size=13, text_align="center", margin_bottom=16,
                       color=COLOR_TEXT_LIGHT)
        )
        self.container.add(self.status_label_stats)

        # Results area — scrollable
        self.results_box = toga.Box(
            style=Pack(direction=COLUMN, flex=1, background_color=COLOR_BG))
        scroll = toga.ScrollContainer(content=self.results_box,
                                          style=Pack(flex=1, background_color=COLOR_BG))
        
        self.container.add(scroll)

        # Back button
        self.container.add(toga.Button(
            "← Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=btn_nav(height=44, margin_bottom=0)
        ))

        if self.results:
            self._display_species_list()

        return self.container

    # ------------------------------------------------------------------
    # CSV loading
    # ------------------------------------------------------------------

    def load_csv(self, path):
        """Load a CSV file from the given path and run the checker."""
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
        """Let the user pick a CSV file manually."""
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
        """Use Android's file picker Intent to select a CSV."""
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
        """Run the IV check against current thresholds and league."""
        if not self.csv_path:
            return
        try:
            self.results = check_thresholds(
                self.csv_path,
                DEFAULT_THRESHOLDS,
                league=self.league,
                max_level=51,
                evolution_lines=EVOLUTION_LINES,
            )
            self.status_label_file.text = pathlib.Path(self.csv_path).name
            self.clear_csv_btn.enabled = True
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
        """Show a list of species with hits, plus a Show All option."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)


        if not self.results:
            if not self.csv_path:
                self.results_box.add(toga.Label(
                    self.NO_CSV_MESSAGE,
                    style=Pack(font_size=14, text_align="center", margin_top=20,
                                   color=COLOR_TEXT_LIGHT)
                ))
            else:
                self.results_box.add(toga.Label(
                    "No Pokémon hit the thresholds\nfor this league.",
                    style=Pack(font_size=14, text_align="center", margin_top=20,
                                   flex=1, color=COLOR_TEXT_LIGHT)
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
        """Show results for a species with target cycling."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        hits = self.results[species]

        self.results_box.add(toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_back(height=44)
        ))

        self.results_box.add(toga.Label(
            f"{species} — {len(hits)} hit{'s' if len(hits) != 1 else ''}",
            style=Pack(font_size=18, font_weight="bold",
                       margin_bottom=8, text_align="center",
                       color=COLOR_ACCENT)
        ))

        all_targets = sorted({
            target for hit in hits for target in hit['matched']
        })

        targets_with_hits = {}
        for hit in hits:
            for target in hit['matched']:
                targets_with_hits[target] = targets_with_hits.get(target, 0) + 1

        self._target_index = 0
        self._target_options_raw = [None] + all_targets

        def make_cycle_handler(direction):
            def handler(widget):
                self._target_index = (self._target_index + direction) % len(self._target_options_raw)
                current = self._target_options_raw[self._target_index]
                if current is None:
                    self.target_label.text = f"All targets ({len(hits)})"
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
        """Show all results for all species without filtering."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        self.results_box.add(toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=btn_back(height=44)
        ))

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
        """Clear the loaded CSV and delete the cached file."""
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
        self.clear_csv_btn.enabled = False
        for child in list(self.results_box.children):
            self.results_box.remove(child)

    # ------------------------------------------------------------------
    # Hit display
    # ------------------------------------------------------------------

    def _add_hit_display(self, box, hit):
        """Add a card displaying a single hit to the given box."""
        m = hit['mon']
        s = hit['stats']
        pre = f" ({hit['csv_species']})" if hit['is_pre_evo'] else ""
        iv_str = f"{m['atk_iv']}/{m['def_iv']}/{m['sta_iv']}{pre} (CP {m['cp']})"
        stat_str = (f"Atk:{s['attack']:.1f} "
                    f"Def:{s['defense']:.1f} "
                    f"Sta:{s['stamina']} "
                    f"SP:{s['stat_prod']}")
        matched = ", ".join(hit['matched'])

        card = toga.Box(style=card_box())
        card.add(toga.Label(
            iv_str,
            style=Pack(font_size=14, font_weight="bold", color=COLOR_TEXT_LIGHT)
        ))
        card.add(toga.Label(
            stat_str,
            style=Pack(font_size=12, color=COLOR_TEXT_LIGHT)
        ))
        card.add(toga.Label(
            f"✅ {matched}",
            style=Pack(font_size=12, color=COLOR_ACCENT)
        ))
        box.add(card)
        
