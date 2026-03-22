#!/usr/bin/env python
"""
IV checker screen — import PokeGenie CSV and check against thresholds.
"""
import pathlib
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from ..data.iv_checker import check_thresholds
from ..data.thresholds import DEFAULT_THRESHOLDS, EVOLUTION_LINES


class IVCheckerScreen:
    """Screen for checking Pokemon IVs against stat thresholds."""

    def __init__(self, app):
        self.app = app
        self.csv_path = None
        self.results = {}
        self.league = 'great'

    def build(self):
        """Build and return the IV checker screen content."""
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        # Title
        self.container.add(toga.Label(
            "IV Checker",
            style=Pack(font_size=24, font_weight="bold",
                       text_align="center", margin_bottom=10)
        ))

        # League selector row
        league_box = toga.Box(style=Pack(direction=ROW, margin_bottom=16))
        for league, label in (('great', 'Great'), ('ultra', 'Ultra'), ('master', 'Master')):
            btn = toga.Button(
                label,
                on_press=self._make_league_handler(league),
                style=Pack(flex=1, margin=4, height=40)
            )
            league_box.add(btn)
        self.container.add(league_box)

        # Import button
        import_btn = toga.Button(
            "Import PokeGenie CSV",
            on_press=self._import_csv,
            style=Pack(height=52, font_size=16, margin_bottom=16)
        )
        self.container.add(import_btn)

        # Status label
        self.status_label = toga.Label(
            "No CSV loaded. Export from PokeGenie and share to GoBattleKit.",
            style=Pack(font_size=14, text_align="center", margin_bottom=16)
        )
        self.container.add(self.status_label)

        # Results area — scrollable
        self.results_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        scroll = toga.ScrollContainer(content=self.results_box, style=Pack(flex=1))
        self.container.add(scroll)

        # Back button
        self.container.add(toga.Button(
            "Back to Home",
            on_press=lambda w: self.app.show_home(),
            style=Pack(margin_top=10, height=44)
        ))

        # If we already have results, show the species list
        if self.results:
            self._display_species_list()

        return self.container

    # ------------------------------------------------------------------
    # CSV loading
    # ------------------------------------------------------------------

    def load_csv(self, path):
        """Load a CSV file from the given path and run the checker."""
        self.csv_path = str(path).replace('file://', '')
        self._run_check()

    async def _import_csv(self, widget):
        """Let the user pick a CSV file manually."""
        try:
            path = await self.app.main_window.open_file_dialog(
                title="Select PokeGenie Export",
                file_types=["csv"],
            )
            if path:
                self.csv_path = str(path)
                self._run_check()
        except Exception as e:
            self.status_label.text = f"Error opening file: {e}"

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
            csv_name = pathlib.Path(self.csv_path).name
            species_count = len(self.results)
            total = sum(len(hits) for hits in self.results.values())
            self.status_label.text = (
                f"{csv_name} — {species_count} species, "
                f"{total} hit{'s' if total != 1 else ''} "
                f"in {self.league.capitalize()} League"
            )
            self._display_species_list()
        except Exception as e:
            self.status_label.text = f"Error reading CSV: {e}"

    # ------------------------------------------------------------------
    # Species list view
    # ------------------------------------------------------------------

    def _display_species_list(self):
        """Show a list of species with hits, plus a Show All option."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        if not self.results:
            self.results_box.add(toga.Label(
                "No mons hit the thresholds for this league.",
                style=Pack(font_size=14, text_align="center", margin_top=20)
            ))
            return

        # Show All button
        total = sum(len(hits) for hits in self.results.values())
        self.results_box.add(toga.Button(
            f"Show All ({total} hits)",
            on_press=lambda w: self._display_all_results(),
            style=Pack(height=48, font_size=16, margin_bottom=8)
        ))

        # One button per species
        for species in sorted(self.results.keys()):
            hits = self.results[species]
            self.results_box.add(toga.Button(
                f"{species} ({len(hits)})",
                on_press=self._make_species_handler(species),
                style=Pack(height=48, font_size=16, margin_bottom=4)
            ))

    def _make_species_handler(self, species):
        """Return a handler that shows results for a species."""
        def handler(widget):
            self._display_species_results(species)
        return handler

    # ------------------------------------------------------------------
    # Species results view (with dropdown)
    # ------------------------------------------------------------------

    def _display_species_results(self, species):
        """Show results for a species with a dropdown to filter by target."""
        for child in list(self.results_box.children):
            self.results_box.remove(child)

        hits = self.results[species]

        # Back button
        self.results_box.add(toga.Button(
            "← Back to Species List",
            on_press=lambda w: self._display_species_list(),
            style=Pack(height=44, margin_bottom=8)
        ))

        # Species title
        self.results_box.add(toga.Label(
            f"{species} — {len(hits)} hit{'s' if len(hits) != 1 else ''}",
            style=Pack(font_size=18, font_weight="bold",
                       margin_bottom=8, text_align="center")
        ))

        # Collect targets that have hits, sorted by hit count descending
        targets_with_hits = {}
        for hit in hits:
            for target in hit['matched']:
                targets_with_hits[target] = targets_with_hits.get(target, 0) + 1


        # Build target options from thresholds, not just hits
        # This ensures all targets are shown even if no mons hit them
        league_label = self.league.capitalize()
        all_targets = []
        if species in DEFAULT_THRESHOLDS and league_label in DEFAULT_THRESHOLDS[species]:
            all_targets = list(DEFAULT_THRESHOLDS[species][league_label].keys())

        # Count hits per target
        targets_with_hits = {}
        for hit in hits:
            for target in hit['matched']:
                targets_with_hits[target] = targets_with_hits.get(target, 0) + 1

        # Build options showing hit count, preserving threshold order
        target_options = [f"All targets ({len(hits)})"] + [
            f"{t} ({targets_with_hits.get(t, 0)})"
            for t in all_targets
        ]


        # Dropdown selector
        self.target_selector = toga.Selection(
            items=target_options,
            on_change=lambda w: self._refresh_hits(species, hits),
            style=Pack(margin_bottom=12)
        )
        self.results_box.add(self.target_selector)

        # Hits area — separate box so we can refresh just this part
        self.hits_box = toga.Box(style=Pack(direction=COLUMN))
        self.results_box.add(self.hits_box)

        # Show all hits initially
        self._refresh_hits(species, hits)


    def _refresh_hits(self, species, all_hits):
        """Refresh the hits display based on the current dropdown selection."""
        for child in list(self.hits_box.children):
            self.hits_box.remove(child)

        selected = self.target_selector.value
        if selected.startswith("All targets"):
            hits = all_hits
        else:
            # Strip the count suffix e.g. "General (132.8 Def, 187 HP) (3)" -> target name
            target = selected.rsplit(" (", 1)[0]
            hits = [h for h in all_hits if target in h['matched']]
        
        if not hits:
            self.hits_box.add(toga.Label(
                "No hits for this target.",
                style=Pack(font_size=14, text_align="center", margin_top=10)
            ))
            return

        for hit in hits:
            m = hit['mon']
            s = hit['stats']
            pre = f" ({hit['csv_species']})" if hit['is_pre_evo'] else ""
            iv_str = f"{m['atk_iv']}/{m['def_iv']}/{m['sta_iv']}{pre} (CP {m['cp']})"
            stat_str = (f"Atk:{s['attack']:.1f} "
                        f"Def:{s['defense']:.1f} "
                        f"Sta:{s['stamina']}")
            matched = ", ".join(hit['matched'])

            self.hits_box.add(toga.Label(
                f"  {iv_str}",
                style=Pack(font_size=14, font_weight="bold")
            ))
            self.hits_box.add(toga.Label(
                f"  {stat_str}",
                style=Pack(font_size=12)
            ))
            self.hits_box.add(toga.Label(
                f"  ✅ {matched}",
                style=Pack(font_size=12, margin_bottom=6)
            ))

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
            style=Pack(height=44, margin_bottom=12)
        ))

        for sp in sorted(self.results.keys()):
            hits = self.results[sp]
            self.results_box.add(toga.Label(
                f"{sp} ({len(hits)} hit{'s' if len(hits) != 1 else ''})",
                style=Pack(font_size=16, font_weight="bold",
                           margin_top=12, margin_bottom=4)
            ))
            for hit in hits:
                m = hit['mon']
                s = hit['stats']
                pre = f" ({hit['csv_species']})" if hit['is_pre_evo'] else ""
                iv_str = f"{m['atk_iv']}/{m['def_iv']}/{m['sta_iv']}{pre} (CP {m['cp']})"
                stat_str = (f"Atk:{s['attack']:.1f} "
                            f"Def:{s['defense']:.1f} "
                            f"Sta:{s['stamina']}")
                matched = ", ".join(hit['matched'])
                self.results_box.add(toga.Label(
                    f"  {iv_str}",
                    style=Pack(font_size=14, font_weight="bold")
                ))
                self.results_box.add(toga.Label(
                    f"  {stat_str}",
                    style=Pack(font_size=12)
                ))
                self.results_box.add(toga.Label(
                    f"  ✅ {matched}",
                    style=Pack(font_size=12, margin_bottom=6)
                ))

    # ------------------------------------------------------------------
    # League selection
    # ------------------------------------------------------------------

    def _make_league_handler(self, league):
        """Return a handler that switches to the given league."""
        def handler(widget):
            self.league = league
            if self.csv_path:
                self._run_check()
        return handler
