#!/usr/bin/env python3
"""Build a repeatable ditch/keep triage HTML report from a threshold-batch
export dir.

Reads every ``*_verification.md`` in an export dir (the per-species expert
anchor checks emitted by ``export_thresholds.py``), classifies each anchor,
cross-references the current GL rankings, and writes a self-contained styled
HTML report. The keep-list (opponents kept regardless of rank) is read from
``curation.toml`` so it lives in exactly one place.

Classification per anchor:
  * MATCH                  — verdict MATCH (re-derived == expert within tol)
  * small drift (<1.0)     — DIVERGED, |re-derived - expert| < 1.0 (ship as-is)
  * big divergence (>=1.0) — DIVERGED, |delta| >= 1.0 (flag as likely artifact)
  * opponent out of top 50 — opponent rank > threshold or absent; annotated
                             KEEP-per-list (base name on keep-list) vs DITCH.
    (An anchor can be both a drift bucket AND out-of-meta; the out-of-meta
     ditch/keep list is reported separately, like the original triage.)

Stdlib only (+ tomllib). No external assets; the HTML embeds its own <style>.

Usage:
    python build_triage_report.py \
        --export <batch>/export \
        --date 2026-06-14 \
        [--rankings .../rankings-1500.json] \
        [--curation curation.toml] \
        [--out docs/threshold_pipeline/<date>_ditch_keep_triage.html]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RANKINGS = Path(
    "/Users/mglerner/coding/pvpoke/src/data/rankings/all/overall/"
    "rankings-1500.json"
)
DEFAULT_CURATION = HERE / "curation.toml"
DOCS_DIR = HERE.parent.parent / "docs" / "threshold_pipeline"

BIG_DELTA = 1.0  # >= this |delta| is a "big" divergence (likely artifact)

# expert column looks like "137.64 def" or "132.10 def + 149 hp"
EXPERT_RE = re.compile(r"(\d+\.\d+)\s*(def|atk)")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def load_keep_names(curation: Path) -> set[str]:
    try:
        cfg = tomllib.loads(curation.read_text())
        return set(cfg.get("keep_names", []))
    except OSError:
        print(f"WARNING: curation {curation} not found; keep-list empty")
        return set()


def load_ranks(path: Path) -> dict[str, int]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARNING: rankings unavailable ({path}): {e}; all opponents "
              "treated as out-of-meta")
        return {}
    return {e["speciesName"]: i + 1 for i, e in enumerate(data)}


def base_name(opponent: str) -> str:
    return opponent[: -len(" (Shadow)")] if opponent.endswith(" (Shadow)") else opponent


def parse_verification(path: Path) -> list[dict]:
    """Parse the anchor table out of one *_verification.md."""
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        anchor, opponent, expert, rederived, verdict, detail = cells
        if anchor in ("anchor", "---") or verdict not in (
                "MATCH", "DIVERGED", "OPPONENT-GONE", "UNRESOLVABLE"):
            continue
        m = EXPERT_RE.search(expert)
        expert_val = float(m.group(1)) if m else None
        stat = m.group(2) if m else ""
        try:
            red_val = float(rederived)
        except ValueError:
            red_val = None
        rows.append({
            "anchor": anchor,
            "opponent": None if opponent in ("", "—") else opponent,
            "expert": expert,
            "expert_val": expert_val,
            "stat": stat,
            "rederived": red_val,
            "verdict": verdict,
            "detail": detail,
        })
    return rows


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(row: dict) -> tuple[str, float | None]:
    """Return (bucket, delta). bucket in {match, small, big, unresolved}."""
    if row["verdict"] == "MATCH":
        return "match", 0.0
    if row["verdict"] in ("OPPONENT-GONE", "UNRESOLVABLE"):
        return "unresolved", None
    # DIVERGED
    if row["expert_val"] is None or row["rederived"] is None:
        return "unresolved", None
    delta = row["rederived"] - row["expert_val"]
    return ("big" if abs(delta) >= BIG_DELTA else "small"), delta


def species_from_filename(p: Path) -> str:
    return p.name.replace("_verification.md", "")


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

STYLE = """
:root{--ink:#1c1e21;--muted:#5f6368;--teal:#0e7c7b;--border:#e0e0e0;}
body{font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fafafa;margin:0;padding:2rem 1rem 5rem;}
main{max-width:1000px;margin:0 auto;}
h1{font-size:1.55rem;border-bottom:3px solid var(--teal);padding-bottom:.4rem;}
h2{font-size:1.2rem;color:var(--teal);margin-top:2.2rem;}
h3{margin-top:1.5rem;font-size:1.02rem;}
.card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:1rem 1.2rem;margin:1rem 0;}
table{border-collapse:collapse;width:100%;font-size:.85em;}
th,td{border:1px solid var(--border);padding:.3rem .5rem;text-align:left;}
th{background:#f0f4f4;}
.chip{color:#fff;border-radius:9px;padding:1px 7px;font-size:.72em;font-weight:600;}
.big{font-size:1.7rem;font-weight:700;}
.grid{display:flex;gap:1rem;flex-wrap:wrap;}
.stat{flex:1;min-width:130px;background:#fff;border:1px solid var(--border);border-radius:8px;padding:.8rem;text-align:center;}
.prov{background:#fff8e1;border-left:4px solid #b8860b;padding:.6rem .9rem;border-radius:4px;}
.drift td{color:#5f6368;}
.flag{background:#fff3f0;}
small{color:var(--muted);}
"""

CHIP = {
    "MATCH": "#2e7d32",
    "DIVERGED": "#b8860b",
    "OPPONENT-GONE": "#b3392f",
    "UNRESOLVABLE": "#b3392f",
}


def chip(verdict: str) -> str:
    return (f'<span class="chip" style="background:{CHIP.get(verdict, "#5f6368")}">'
            f'{html.escape(verdict)}</span>')


def esc(x) -> str:
    return html.escape(str(x))


def fmt_delta(d: float | None) -> str:
    return "—" if d is None else f"{d:+.3f}"


def build_html(date_str: str, by_species: dict[str, list[dict]],
               ranks: dict[str, int], keep_names: set[str],
               rank_threshold: int) -> str:
    counts = {"match": 0, "small": 0, "big": 0, "unresolved": 0}
    big_rows = []          # (species, row, delta)
    out_of_meta = []       # rows whose opponent is out of top N

    for species, rows in sorted(by_species.items()):
        for row in rows:
            bucket, delta = classify(row)
            row["_bucket"] = bucket
            row["_delta"] = delta
            counts[bucket] += 1
            if bucket == "big":
                big_rows.append((species, row, delta))
            opp = row["opponent"]
            if opp is not None:
                rank = ranks.get(opp)
                if rank is None or rank > rank_threshold:
                    keep = base_name(opp) in keep_names
                    out_of_meta.append({
                        "species": species, "row": row, "rank": rank,
                        "keep": keep,
                    })

    n_species = len(by_species)
    p = []
    p.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
    p.append(f"<title>Threshold Batch — Ditch/Keep Triage ({esc(date_str)})</title>")
    p.append(f"<style>{STYLE}</style></head><body><main>")
    p.append("<h1>Threshold Batch — Ditch/Keep Triage</h1>")
    p.append(f'<p><small>{esc(date_str)} · {n_species} species with parsed '
             f'expert-anchor verifications</small></p>')

    # summary cards
    p.append('<div class="grid">')
    p.append(f'<div class="stat"><div class="big" style="color:#2e7d32">'
             f'{counts["match"]}</div>MATCH<br><small>keep as-is</small></div>')
    p.append(f'<div class="stat"><div class="big" style="color:#0e7c7b">'
             f'{counts["small"]}</div>small drift &lt;{BIG_DELTA:g}<br>'
             f'<small>re-derive &amp; keep</small></div>')
    p.append(f'<div class="stat"><div class="big" style="color:#b8860b">'
             f'{counts["big"]}</div>big divergence &ge;{BIG_DELTA:g}<br>'
             f'<small>likely artifact</small></div>')
    p.append(f'<div class="stat"><div class="big" style="color:#b3392f">'
             f'{len(out_of_meta)}</div>opponent rank&gt;{rank_threshold}<br>'
             f'<small>ditch/keep</small></div>')
    if counts["unresolved"]:
        p.append(f'<div class="stat"><div class="big" style="color:#5f6368">'
                 f'{counts["unresolved"]}</div>unresolvable<br>'
                 f'<small>no claim/opponent gone</small></div>')
    p.append("</div>")

    # how to read
    p.append('<div class="card"><h2>How to read this</h2>')
    p.append(f'<p><b>MATCH</b> reproduced the expert number exactly; <b>small '
             f'drift</b> (&lt;{BIG_DELTA:g} stat point) is benign grid-notch '
             f'movement — re-derive to current numbers and ship as '
             f'<code>generated</code>. <b>Big divergence</b> (&ge;{BIG_DELTA:g}) '
             f'is almost always a data/parse artifact, not a meta shift — '
             f'inspect before shipping.</p>')
    p.append(f'<p>The genuine judgment call is the <b>{len(out_of_meta)} anchors '
             f'whose opponent has fallen out of the current top {rank_threshold}</b>: '
             f'each is annotated KEEP-per-list (on the curation keep-list) or '
             f'DITCH. Same keep-list as the exporter (<code>curation.toml</code>).</p>')
    p.append("</div>")

    # big divergences
    if big_rows:
        p.append(f'<div class="card"><h2>Big divergences (&ge;{BIG_DELTA:g}) — '
                 f'likely artifacts</h2>')
        p.append('<table><tr><th>Species</th><th>Anchor</th><th>Opponent</th>'
                 '<th>Expert</th><th>Re-derived</th><th>Δ</th><th>Detail</th></tr>')
        for species, row, delta in sorted(big_rows, key=lambda x: -abs(x[2])):
            p.append(
                f'<tr class="flag"><td>{esc(species)}</td>'
                f'<td>{esc(row["anchor"])}</td>'
                f'<td>{esc(row["opponent"] or "—")}</td>'
                f'<td>{esc(row["expert"])}</td>'
                f'<td>{esc(f"{row["rederived"]:.4f}")}</td>'
                f'<td>{fmt_delta(delta)}</td>'
                f'<td><small>{esc(row["detail"])}</small></td></tr>')
        p.append("</table></div>")

    # out of meta ditch/keep
    p.append(f'<div class="card"><h2>Opponent out of current top {rank_threshold} '
             f'— ditch/keep ({len(out_of_meta)} anchors)</h2>')
    p.append('<p>Sorted by how far the opponent fell. KEEP-per-list opponents '
             '(on the curation keep-list) survive regardless of rank.</p>')
    p.append('<table><tr><th>Species</th><th>Anchor opponent</th><th>Opp rank</th>'
             '<th>Decision</th><th>Verdict</th></tr>')

    def sort_rank(item):
        return -(item["rank"] or 10**9)
    for item in sorted(out_of_meta, key=sort_rank):
        row = item["row"]
        rank_txt = f"#{item['rank']}" if item["rank"] else "absent"
        if item["keep"]:
            decision = '<span class="chip" style="background:#2e7d32">KEEP-per-list</span>'
        else:
            decision = '<span class="chip" style="background:#b3392f">DITCH</span>'
        p.append(f'<tr><td>{esc(item["species"])}</td>'
                 f'<td>{esc(row["opponent"])}</td>'
                 f'<td>{rank_txt}</td><td>{decision}</td>'
                 f'<td>{chip(row["verdict"])}</td></tr>')
    p.append("</table></div>")

    # per-species detail
    p.append('<div class="card"><h2>Per-species detail</h2>')
    for species, rows in sorted(by_species.items()):
        if not rows:
            continue
        p.append(f"<h3>{esc(species)}</h3>")
        p.append('<table><tr><th>Anchor</th><th>Opp</th><th>Expert</th>'
                 '<th>Re-derived</th><th>Δ</th><th>Opp rank</th><th>Verdict</th></tr>')
        for row in rows:
            bucket = row["_bucket"]
            delta = row["_delta"]
            cls = ' class="flag"' if bucket == "big" else (
                ' class="drift"' if bucket == "small" else "")
            opp = row["opponent"]
            rank = ranks.get(opp) if opp else None
            rank_txt = f"#{rank}" if rank else ("—" if opp is None else "absent")
            red = f"{row['rederived']:.4f}" if row["rederived"] is not None else "—"
            p.append(f'<tr{cls}><td>{esc(row["anchor"])}</td>'
                     f'<td>{esc(opp or "—")}</td>'
                     f'<td>{esc(row["expert"])}</td>'
                     f'<td>{esc(red)}</td>'
                     f'<td>{fmt_delta(delta)}</td>'
                     f'<td>{esc(rank_txt)}</td>'
                     f'<td>{chip(row["verdict"])}</td></tr>')
        p.append("</table>")
    p.append("</div>")

    p.append("</main></body></html>")
    return "".join(p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", type=Path, required=True,
                    help="batch export dir containing *_verification.md")
    ap.add_argument("--date", required=True,
                    help="date string for the report (e.g. 2026-06-14); "
                         "no datetime is called")
    ap.add_argument("--rankings", type=Path, default=DEFAULT_RANKINGS)
    ap.add_argument("--curation", type=Path, default=DEFAULT_CURATION,
                    help="curation TOML to read the keep-list from")
    ap.add_argument("--out", type=Path, default=None,
                    help="output HTML path "
                         "(default docs/threshold_pipeline/<date>_ditch_keep_triage.html)")
    args = ap.parse_args(argv)

    keep_names = load_keep_names(args.curation)
    ranks = load_ranks(args.rankings)
    cfg = tomllib.loads(args.curation.read_text()) if args.curation.exists() else {}
    rank_threshold = int(cfg.get("rank_threshold", 50))

    files = sorted(args.export.glob("*_verification.md"))
    if not files:
        print(f"no *_verification.md found in {args.export}")
        return 1

    by_species: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        rows = parse_verification(f)
        if rows:
            by_species[species_from_filename(f)] = rows

    out = args.out or (DOCS_DIR / f"{args.date}_ditch_keep_triage.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(args.date, dict(by_species), ranks,
                              keep_names, rank_threshold))
    n_anchors = sum(len(v) for v in by_species.values())
    print(f"wrote {out}")
    print(f"  {len(by_species)} species, {n_anchors} expert anchors parsed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
