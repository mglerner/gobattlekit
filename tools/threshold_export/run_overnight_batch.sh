#!/bin/bash
# Overnight threshold batch: full-config deep dives for the GL roster,
# each followed immediately by the threshold exporter (TOML + parity
# vectors + expert-vs-rederived verification).
#
# Usage:   ./run_overnight_batch.sh            # run / resume
#          touch <out_root>/STOP               # graceful stop between dives
#
# Resumable: each completed dive drops a .done marker under the batch
# dir; re-running skips completed dives. Engine/scripts must not change
# mid-batch (cache coherence — see pogo-simulator cache notes).
set -u

# Sibling gopvpsim checkout — SINGLE SOURCE OF TRUTH in ./sibling_path (edit
# that one file to repoint, e.g. on the pogo-simulator -> gopvpsim rename).
SIM=$(cat "$(dirname "$0")/sibling_path")
EXPORT_DIR=/Users/mglerner/coding/MGLPoGo/gobattlekit/tools/threshold_export
PYRUN="pyenv exec python"
export PYENV_VERSION=3.13.12

# BATCH_DATE override lets a post-midnight resume keep writing into the
# original night's dir (and honoring its .done markers).
STAMP=${BATCH_DATE:-$(date +%Y%m%d)}
OUT_ROOT=$SIM/userdata/threshold_batch/$STAMP
mkdir -p "$OUT_ROOT"
LOG=$OUT_ROOT/batch.log

# Roster order = current GL meta rank (most important first), so a
# truncated night still covers the core. Aegislash forms last.
BASE_DIVES=(
  "Lickilicky" "Altaria" "Empoleon" "Jellicent" "Quagsire"
  "Corsola (Galarian)" "Tinkaton" "Ninetales" "Seaking" "Azumarill"
  "Forretress" "Feraligatr" "Guzzlord" "Mantine" "Malamar" "Kingdra"
  "Corviknight" "Fearow" "Dragonair" "Medicham" "Shelgon" "Sliggoo"
  "Jumpluff" "Stunfisk (Galarian)" "Seismitoad" "Clodsire" "Furret"
  "Lapras" "Sealeo" "Spidops" "Florges" "Sylveon"
  "Aegislash (Shield)" "Aegislash (Blade)"
)
# Shadow variants that are independently GL-meta-relevant. Sableye and
# Drapion run shadow-only (base form is not meta).
SHADOW_DIVES=(
  "Altaria" "Empoleon" "Quagsire" "Ninetales" "Forretress" "Feraligatr"
  "Kingdra" "Dragonair" "Sableye" "Shelgon" "Sealeo" "Drapion"
)

slug() { echo "$1" | tr '[:upper:]' '[:lower:]' | tr -d '()' | sed 's/  */_/g'; }

say() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

run_dive() {
  local species=$1 shadow=$2
  local s; s=$(slug "$species")
  local tag=$s; [ "$shadow" = yes ] && tag="${s}_shadow"
  local done_f=$OUT_ROOT/$tag.done

  if [ -f "$OUT_ROOT/STOP" ]; then say "STOP file present — halting."; exit 0; fi
  if [ -f "$done_f" ]; then say "skip $tag (done)"; return 0; fi

  local flags=()
  [ "$shadow" = yes ] && flags+=(--shadow)

  say "DIVE $tag starting"
  local t0=$SECONDS
  ( cd "$SIM" && $PYRUN scripts/deep_dive.py "$species" --league great \
      --opponents-file opponent_pools/gl_top50_plus_cs.txt \
      --top-movesets 3 --opp-ivs both --bait both --reference auto \
      --html "$OUT_ROOT/html/$tag/index.html" --interactive --standalone \
      --mirror-slayer --mirror-slayer-metric all --mirror-slayer-rounds 4 \
      --mirror-slayer-pool 30 --mirror-slayer-show 20 --split-movesets \
      --reserve-cpus 1 ${flags[@]+"${flags[@]}"} ) >>"$LOG" 2>&1
  local rc=$?
  local mins=$(( (SECONDS - t0) / 60 ))
  if [ $rc -ne 0 ]; then say "DIVE $tag FAILED rc=$rc after ${mins}m (continuing)"; return 1; fi
  say "DIVE $tag done in ${mins}m"

  # Export: newest matching blob -> app TOML + parity vectors + verification.
  # deep_dive.py names blobs with non-alphanumerics collapsed to '_'
  # (e.g. "Corsola (Galarian)" -> Corsola_Galarian), so match by turning
  # every non-alphanumeric run in the species into a glob '*'.
  local gp="${species//[^A-Za-z0-9]/*}"
  local pat="*${gp}*replay.pkl.gz"; [ "$shadow" = yes ] && pat="*${gp}*shadow*replay.pkl.gz"
  local blob; blob=$(ls -t "$SIM"/userdata/replay/$pat 2>/dev/null | head -1)
  local toml=$SIM/thresholds/$s.toml
  [ "$shadow" = yes ] && [ -f "$SIM/thresholds/${s}_shadow.toml" ] && toml=$SIM/thresholds/${s}_shadow.toml
  if [ -n "$blob" ]; then
    local targs=()
    [ -f "$toml" ] && targs=(--thresholds "$toml")
    ( cd "$EXPORT_DIR" && $PYRUN export_thresholds.py "$blob" ${targs[@]+"${targs[@]}"} \
        --curation curation.toml --out "$OUT_ROOT/export" ) >>"$LOG" 2>&1 \
      && say "EXPORT $tag ok" || say "EXPORT $tag FAILED (dive kept; re-export later)"
  else
    say "EXPORT $tag SKIPPED: no replay blob found"
  fi
  touch "$done_f"
}

total=$(( ${#BASE_DIVES[@]} + ${#SHADOW_DIVES[@]} ))
say "Batch start: $total dives -> $OUT_ROOT (top-movesets 3, full anchors/slayer)"
n=0
for sp in "${BASE_DIVES[@]}";  do n=$((n+1)); say "--- $n/$total"; run_dive "$sp" no;  done
for sp in "${SHADOW_DIVES[@]}"; do n=$((n+1)); say "--- $n/$total"; run_dive "$sp" yes; done

say "Batch complete. Exports in $OUT_ROOT/export; verification reports: $(ls "$OUT_ROOT"/export/*_verification.md 2>/dev/null | wc -l | tr -d ' ')"
echo BATCH_COMPLETE
