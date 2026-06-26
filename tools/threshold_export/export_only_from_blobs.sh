#!/bin/bash
# Export-only pass: re-derive app thresholds from the NEWEST existing replay
# blob per roster species, with NO deep_dive re-simulation (blobs are locked).
# Mirrors run_overnight_batch.sh's export block (lines 80-90) but uses the
# gopvpsim venv interpreter and excludes shadow blobs when exporting a base
# form (the batch relied on a fresh non-shadow blob being newest; we don't
# create one, so we must filter).
set -u
SIM=/Users/mglerner/coding/MGLPoGo/gopvpsim
EXPORT_DIR=/Users/mglerner/coding/MGLPoGo/gobattlekit/tools/threshold_export
PY=$SIM/.venv/bin/python
OUT=$SIM/userdata/threshold_batch/20260626/export
mkdir -p "$OUT"
LOG=$SIM/userdata/threshold_batch/20260626/export_only.log
: > "$LOG"

BASE_DIVES=(
  "Lickilicky" "Altaria" "Empoleon" "Jellicent" "Quagsire"
  "Corsola (Galarian)" "Tinkaton" "Ninetales" "Seaking" "Azumarill"
  "Forretress" "Feraligatr" "Guzzlord" "Mantine" "Malamar" "Kingdra"
  "Corviknight" "Fearow" "Dragonair" "Medicham" "Shelgon" "Sliggoo"
  "Jumpluff" "Stunfisk (Galarian)" "Seismitoad" "Clodsire" "Furret"
  "Lapras" "Sealeo" "Spidops" "Florges" "Sylveon"
  "Aegislash (Shield)" "Aegislash (Blade)"
)
SHADOW_DIVES=(
  "Altaria" "Empoleon" "Quagsire" "Ninetales" "Forretress" "Feraligatr"
  "Kingdra" "Dragonair" "Sableye" "Shelgon" "Sealeo" "Drapion"
)

slug() { echo "$1" | tr '[:upper:]' '[:lower:]' | tr -d '()' | sed 's/  */_/g'; }

export_one() {
  local species=$1 shadow=$2
  local s; s=$(slug "$species")
  local tag=$s; [ "$shadow" = yes ] && tag="${s}_shadow"
  local gp="${species//[^A-Za-z0-9]/*}"
  # Require the league suffix so a recent ULTRA/MASTER sweep can't poison the
  # pick (the batch relied on a fresh GL blob being newest; we don't make one).
  # "*_great.replay.pkl.gz" also excludes "_great_shadow" for base forms.
  local pat="*${gp}*_great.replay.pkl.gz"; [ "$shadow" = yes ] && pat="*${gp}*_great_shadow.replay.pkl.gz"
  local blob; blob=$(ls -t "$SIM"/userdata/replay/$pat 2>/dev/null | head -1)
  if [ -z "$blob" ]; then echo "SKIP   $tag : no blob" | tee -a "$LOG"; return 0; fi
  local toml=$SIM/thresholds/$s.toml
  [ "$shadow" = yes ] && [ -f "$SIM/thresholds/${s}_shadow.toml" ] && toml=$SIM/thresholds/${s}_shadow.toml
  local targs=(); [ -f "$toml" ] && targs=(--thresholds "$toml")
  echo "EXPORT $tag <- $(basename "$blob")" | tee -a "$LOG"
  ( cd "$EXPORT_DIR" && "$PY" export_thresholds.py "$blob" ${targs[@]+"${targs[@]}"} \
      --curation curation.toml --out "$OUT" ) >>"$LOG" 2>&1 \
    && echo "  ok   $tag" || echo "  FAIL $tag (see $LOG)"
}

for sp in "${BASE_DIVES[@]}";  do export_one "$sp" no;  done
for sp in "${SHADOW_DIVES[@]}"; do export_one "$sp" yes; done
echo "DONE. exports in $OUT"
ls "$OUT"/*.toml 2>/dev/null | wc -l | xargs echo "toml files:"
