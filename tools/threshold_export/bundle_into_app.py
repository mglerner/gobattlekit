#!/usr/bin/env python
"""Bundle per-species threshold exports into the app's default_thresholds.toml.

This is the "payload" step of the threshold re-dive pipeline. The exporter
(export_thresholds.py) writes one TOML per species/league into an export
directory, using a slightly different schema than the app consumes. This
tool transforms those exports into the app schema and merges them into the
bundled default_thresholds.toml that the app loads at import time.

Schema transform (per export target):

    EXPORT:  [Species.great.targets."Target Name"]
                 class/source/desc, attack/defense/stamina, (ivs)
    APP:     [Species.Great."Target Name"]
                 class/source/desc, attack/defense/stamina, (ivs)

i.e. the league name is title-cased ('great' -> 'Great') and the extra
'.targets.' path level is dropped. The per-species `sources` line is
carried through. Numeric int-vs-float types are preserved exactly (tomllib
reads them correctly; the emitter here keeps them apart).

Shadow species: the export file's in-table species name is the *base*
name (e.g. [Drapion]), but the filename carries the form
(drapion_shadow_great.toml). For *_shadow_great.toml files we append
" (Shadow)" to the species key so it lands as 'Drapion (Shadow)', matching
the app's existing naming.

Merge rules (per species):
  1. Species WITH a fresh export: replace that species' Great league with
     the export's targets and set its `sources` to the export's. Any OTHER
     leagues that species had (Ultra/Master) are preserved unchanged.
  2. Species in the current file with NO fresh export: kept verbatim.
  3. New species (export only): added wholesale (Great only).

Usage:
    python bundle_into_app.py \
        --export-dir .../export \
        [--current src/gobattlekit/data/default_thresholds.toml] \
        [--out     src/gobattlekit/data/default_thresholds.toml]

stdlib only (tomllib for reading; a small emitter here for writing).
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# Default app file location, resolved relative to this tool.
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APP_TOML = _REPO_ROOT / "src" / "gobattlekit" / "data" / "default_thresholds.toml"

# Order spec keys are emitted in: provenance first, then stat floors, then ivs.
SPEC_KEY_ORDER = ("class", "source", "desc", "attack", "defense", "stamina", "ivs")


# ---------------------------------------------------------------------------
# TOML emission (stdlib tomllib is read-only, so we write our own)
# ---------------------------------------------------------------------------

def _escape_basic(s: str) -> str:
    """Escape a string for a TOML basic (double-quoted) string.

    Keeps unicode literal (no \\u escaping) so em-dashes etc. stay readable;
    only escapes what TOML requires inside a basic string.
    """
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _is_bare_key(k: str) -> bool:
    """True if k is a TOML bare key (A-Za-z0-9_- only, non-empty)."""
    return bool(k) and all(c.isalnum() and c.isascii() or c in "_-" for c in k)


def _key(k: str) -> str:
    """Render a single TOML key segment, quoting if not bare-safe."""
    return k if _is_bare_key(k) else _escape_basic(k)


def _dotted(*segments: str) -> str:
    """Render a dotted TOML key path with per-segment quoting."""
    return ".".join(_key(s) for s in segments)


def _num(v) -> str:
    """Render an int or float preserving its type.

    int -> bare integer (e.g. 0, 138). float -> repr (round-trips exactly,
    e.g. 143.03, 145.1). A float that happens to be whole (0.0) still emits
    with a decimal point so the int/float distinction survives a reload.
    """
    if isinstance(v, bool):  # guard: bool is a subclass of int
        raise TypeError(f"unexpected bool value {v!r}")
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        r = repr(v)
        if "." not in r and "e" not in r and "E" not in r and "inf" not in r and "nan" not in r:
            r += ".0"
        return r
    raise TypeError(f"non-numeric value {v!r} ({type(v).__name__})")


def _ivs(ivs) -> str:
    """Render an ivs list as an inline array-of-arrays [[a, d, s], ...]."""
    inner = ", ".join("[" + ", ".join(_num(x) for x in triple) + "]" for triple in ivs)
    return f"[{inner}]"


def emit_app_toml(thresholds: dict, header: str | None = None) -> str:
    """Serialize the nested app-schema dict to TOML text.

    thresholds: {Species: {'sources'?: str, League: {Target: spec}}}
    Round-trips losslessly through tomllib back to the same dict.
    """
    lines: list[str] = []
    if header:
        lines.append(header.rstrip("\n"))
        lines.append("")

    for species, body in thresholds.items():
        # Species table: emit it (and any species-level scalar metadata).
        scalar_meta = {k: v for k, v in body.items() if not isinstance(v, dict)}
        lines.append(f"[{_key(species)}]")
        for k, v in scalar_meta.items():
            if isinstance(v, str):
                lines.append(f"{_key(k)} = {_escape_basic(v)}")
            else:
                lines.append(f"{_key(k)} = {_num(v)}")
        lines.append("")

        for league, targets in body.items():
            if not isinstance(targets, dict):
                continue  # already emitted as scalar metadata
            for target_name, spec in targets.items():
                lines.append(f"[{_dotted(species, league, target_name)}]")
                emitted = set()
                for key in SPEC_KEY_ORDER:
                    if key not in spec:
                        continue
                    emitted.add(key)
                    val = spec[key]
                    if key == "ivs":
                        lines.append(f"ivs = {_ivs(val)}")
                    elif isinstance(val, str):
                        lines.append(f"{_key(key)} = {_escape_basic(val)}")
                    else:
                        lines.append(f"{_key(key)} = {_num(val)}")
                # Any keys not in the canonical order (e.g. onlytop) — emit
                # them after, deterministically, so nothing is silently lost.
                for key in spec:
                    if key in emitted:
                        continue
                    val = spec[key]
                    if key == "ivs":
                        lines.append(f"ivs = {_ivs(val)}")
                    elif isinstance(val, str):
                        lines.append(f"{_key(key)} = {_escape_basic(val)}")
                    elif isinstance(val, (int, float)):
                        lines.append(f"{_key(key)} = {_num(val)}")
                    else:
                        raise TypeError(
                            f"unhandled value type for {species}/{league}/"
                            f"{target_name}/{key}: {val!r}"
                        )
                lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Export reading + schema transform
# ---------------------------------------------------------------------------

def species_key_for(path: Path, in_file_name: str) -> str:
    """Resolve the app species key for an export file.

    The export's in-table name is the base form; for *_shadow_great.toml the
    app key gets a ' (Shadow)' suffix.
    """
    name = path.name
    if name.endswith("_shadow_great.toml"):
        return f"{in_file_name} (Shadow)"
    return in_file_name


def _read_export_toml(path: Path) -> dict:
    """Parse an export TOML, tolerating unquoted species names in headers.

    The exporter may emit species table headers either as bare keys (e.g.
    ``[Corsola (Galarian)]``) or already-quoted (``["Corsola (Galarian)"]``,
    which the current exporter does). Species names with spaces/parens are NOT
    valid TOML bare keys, so for the bare form tomllib would reject the file.
    We don't own the export files, so rather than edit them we fix the headers
    in memory: quote the leading species segment when it isn't bare-safe AND
    isn't already a quoted string, leaving the rest of the dotted path (already
    correctly quoted) intact. The species name is everything up to the first
    ``.great`` boundary, or the whole bracket contents for the species table.

    Re-quoting an already-quoted header would embed literal quote chars in the
    parsed key (``'"Corsola (Galarian)"'``), so it would never match the app's
    ``'Corsola (Galarian)'`` and would silently graft a junk duplicate species.
    """
    out_lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[["):
            inner = stripped[1:-1]
            marker = ".great."
            if inner.endswith(".great"):
                species, rest = inner[: -len(".great")], ".great"
            elif marker in inner:
                idx = inner.index(marker)
                species, rest = inner[:idx], inner[idx:]
            else:
                species, rest = inner, ""
            already_quoted = len(species) >= 2 and species.startswith('"') and species.endswith('"')
            if not already_quoted and not _is_bare_key(species):
                species = _escape_basic(species)
            out_lines.append(f"[{species}{rest}]")
        else:
            out_lines.append(line)
    return tomllib.loads("\n".join(out_lines))


def transform_export(path: Path) -> tuple[str, str, dict]:
    """Read one export TOML, return (app_species_key, sources, great_targets).

    great_targets is {Target: spec} in app schema (no 'targets' level), with
    spec keys class/source/desc/attack/defense/stamina/ivs as present and
    int/float types intact.
    """
    data = _read_export_toml(path)
    if len(data) != 1:
        raise ValueError(f"{path.name}: expected exactly one species table, "
                         f"got {list(data)}")
    in_file_name = next(iter(data))
    species_body = data[in_file_name]

    sources = species_body.get("sources", "")

    # A species may export with zero qualifying targets (e.g. a form with no
    # actionable thresholds). That is a valid, if empty, export: carry its
    # sources but no Great targets.
    league_block = species_body.get("great") or {}
    targets = league_block.get("targets") or {}

    great = {}
    for target_name, spec in targets.items():
        if not isinstance(spec, dict):
            raise ValueError(f"{path.name}: target {target_name!r} is not a table")
        great[target_name] = dict(spec)  # shallow copy; values are scalars/lists

    return species_key_for(path, in_file_name), sources, great


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def bundle(export_dir: Path, current: dict) -> tuple[dict, dict]:
    """Merge fresh exports into the current app thresholds.

    Returns (merged_dict, audit) where audit describes what happened.
    """
    export_files = sorted(export_dir.glob("*_great.toml"))
    if not export_files:
        raise SystemExit(f"No *_great.toml exports found in {export_dir}")

    # Deep-ish copy of the current data so we never mutate the input.
    import copy
    merged = copy.deepcopy(current)

    updated, added = [], []
    export_species = set()

    for path in export_files:
        species, sources, great = transform_export(path)
        export_species.add(species)
        if species in merged:
            # Rule 1: replace Great, set sources, keep other leagues. An empty
            # export drops the Great league (rather than leaving a stale one).
            if great:
                merged[species]["Great"] = great
            else:
                merged[species].pop("Great", None)
            if sources:
                merged[species]["sources"] = sources
            updated.append(species)
        else:
            # Rule 3: new species, Great only (omitted if it has no targets).
            entry = {}
            if sources:
                entry["sources"] = sources
            if great:
                entry["Great"] = great
            merged[species] = entry
            added.append(species)

    # Rule 2: species in current with no fresh export are already in `merged`
    # untouched.
    preserved = [s for s in current if s not in export_species]

    # Rule 4: drop species that ended up with no targets in any league (only a
    # 'sources' stub) — e.g. Aegislash (Shield), whose config is narrative-only.
    # A targetless species is a dead row: nothing to match, nothing to show.
    dropped_empty = []
    for sp in list(merged):
        leagues = [k for k in merged[sp] if k != "sources"]
        if not any(merged[sp].get(lg) for lg in leagues):
            del merged[sp]
            dropped_empty.append(sp)

    audit = {
        "dropped_empty": sorted(dropped_empty),
        "updated": sorted(updated),
        "added": sorted(added),
        "preserved": sorted(preserved),
        "export_count": len(export_files),
    }
    return merged, audit


APP_HEADER = """\
# Bundled default IV thresholds for GoBattleKit.
#
# This file is the data source for DEFAULT_THRESHOLDS, loaded at
# import time by load_bundled_thresholds() in thresholds.py. It is a
# lossless TOML encoding of the nested-dict threshold schema.
#
# Per-species Great-league tables are (re)generated by the threshold
# re-dive pipeline and merged in by tools/threshold_export/bundle_into_app.py;
# Ultra/Master leagues and species without a fresh export are preserved
# verbatim. Re-run that tool to refresh after a new export batch rather
# than hand-editing.
#
# Schema (mirrors the nested dict the loader returns):
#   [Species]                       species table
#   sources = "..."                 optional species-level credit
#   [Species.League."Target Name"]  one table per target
#     class/source/desc = "..."     optional provenance metadata
#     attack/defense/stamina = num  stat floors (0 = don't care)
#     ivs = [[a, d, s], ...]        optional explicit IV list
#     onlytop = int                 optional rank cap\
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export-dir", required=True, type=Path,
                    help="Directory of *_great.toml export files.")
    ap.add_argument("--current", type=Path, default=DEFAULT_APP_TOML,
                    help="Current bundled app TOML to merge into "
                         "(default: the app's default_thresholds.toml).")
    ap.add_argument("--out", type=Path, default=DEFAULT_APP_TOML,
                    help="Where to write the merged TOML "
                         "(default: same as --current).")
    args = ap.parse_args(argv)

    current = tomllib.loads(args.current.read_text())
    merged, audit = bundle(args.export_dir, current)

    text = emit_app_toml(merged, header=APP_HEADER)

    # Self-check: the emitted text must reload to exactly the merged dict.
    reloaded = tomllib.loads(text)
    if reloaded != merged:
        raise SystemExit("ROUND-TRIP FAILURE: emitted TOML does not reload to "
                         "the merged dict. Refusing to write.")

    args.out.write_text(text)

    print(f"Wrote {args.out}")
    print(f"  exports merged : {audit['export_count']}")
    print(f"  updated species: {len(audit['updated'])}")
    print(f"  added species  : {len(audit['added'])}")
    print(f"  preserved (no fresh export): {audit['preserved']}")
    print(f"  total species  : {len(merged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
