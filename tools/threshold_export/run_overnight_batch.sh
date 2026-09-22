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
EXPORT_DIR=/Users/mglerner/coding/gobattlekit/tools/threshold_export
PYRUN="pyenv exec python"
export PYENV_VERSION=3.13.12

# BATCH_DATE override lets a post-midnight resume keep writing into the
# original night's dir (and honoring its .done markers).
STAMP=${BATCH_DATE:-$(date +%Y%m%d)}
OUT_ROOT=$SIM/userdata/threshold_batch/$STAMP
mkdir -p "$OUT_ROOT"
LOG=$OUT_ROOT/batch.log

# Roster = the GL dives in gopvpsim's own registry, one entry per species,
# in registry order (pool rank, most important first).
#
# DERIVED, 2026-09-22, from gopvpsim -- do NOT hand-edit species in or out.
# Regenerate after any gopvpsim pool/registry change with:
#
#   cd "$(cat tools/threshold_export/sibling_path)" && .venv/bin/python -c "
#   import sys; sys.path.insert(0,'scripts')
#   import dive_registry as dr
#   gl=[d for d in dr.all_dives() if d['league']=='great']
#   for flag,name in ((False,'BASE'),(True,'SHADOW')):
#       seen=[]
#       for d in gl:
#           if bool(d.get('shadow'))==flag and d['species'] not in seen:
#               seen.append(d['species'])
#       print(name+'_DIVES=('); print('  '+' '.join('\"%s\"'%s for s in seen)); print(')')"
#
# Drift this replaced (2026-09-22): the arrays still carried 9 base + 5
# shadow species the registry dropped (Lickilicky, Seaking, Dragonair,
# Shelgon, Sliggoo, Stunfisk (Galarian), Seismitoad, Sealeo, Sylveon;
# shadow Kingdra, Dragonair, Shelgon, Sealeo, Drapion) and were missing
# 32 base + 10 shadow the registry has -- including Diggersby, shadow
# Charjabug, the shadow Forretress volt-switch page and Oinkologne
# (Female). 46 entries -> 74, so the full batch is now ~1.6x the dives
# it was; use the STOP file if a night has to end early.
#
# ONE PAGE PER SPECIES, and the registry does not always agree. These
# scripts key everything -- the .done marker, the output dir, and the
# export's blob glob -- on the species name, and deep_dive.py's replay
# blobs are named by species too, with no moveset in the filename. So a
# species with more than one registry page cannot be represented here.
# Only FORRETRESS is in that position: the registry has volt-switch AND
# bug-bite pages for both the base and the shadow form. This roster runs
# the VOLT-SWITCH page (see DIVE_EXTRA_ARGS below); the two bug-bite
# pages, forretress-bug-bite-great-league and
# forretress-shadow-bug-bite-great-league, are NOT covered by this batch.
BASE_DIVES=(
  "Melmetal" "Altaria" "Cramorant" "Tinkaton" "Mimikyu" "Corviknight"
  "Corsola (Galarian)" "Florges" "Ninetales" "Quagsire" "Araquanid"
  "Clodsire" "Marowak" "Stunfisk" "Vigoroth" "Jellicent" "Empoleon"
  "Fearow" "Mantine" "Snorlax" "Umbreon" "Feraligatr" "Annihilape"
  "Azumarill" "Deoxys (Defense)" "Electrode (Hisuian)" "Rillaboom"
  "Sableye" "Lapras" "Charjabug" "Malamar" "Furret" "Guzzlord"
  "Carbink" "Dondozo" "Hippowdon" "Mandibuzz" "Morpeko (Full Belly)"
  "Forretress" "Medicham" "Jumpluff" "Kingdra" "Blastoise" "Diggersby"
  "Thievul" "Sableye (Mega)" "Malamar (Mega)" "Oinkologne (Female)"
  "Aegislash (Shield)" "Aegislash (Blade)" "Ninetales (Alolan)"
  "Spidops" "Toxapex" "Turtonator" "Cradily" "Wartortle" "Bombirdier"
)
# Shadow forms with their own registry page. Sableye now has BOTH forms
# in the registry (it was shadow-only here); Drapion has neither.
SHADOW_DIVES=(
  "Ninetales" "Altaria" "Corviknight" "Quagsire" "Sableye" "Empoleon"
  "Araquanid" "Vigoroth" "Annihilape" "Snorlax" "Malamar" "Charjabug"
  "Forretress" "Hydreigon" "Feraligatr" "Hippowdon" "Cradily"
)

# Moveset pins, copied from the registry entries' own extra_args. Without
# these the dive runs PvPoke's default moveset and produces a page that is
# not the registry's page at all -- silently, since the filenames match.
# Keyed by tag (slug() output, plus _shadow for a shadow form).
DIVE_EXTRA_ARGS=(
  "forretress|--fast VOLT_SWITCH --charged SAND_TOMB,ROCK_TOMB"
  "forretress_shadow|--fast VOLT_SWITCH --charged SAND_TOMB,ROCK_TOMB"
  "oinkologne_female|--charged BODY_SLAM,TRAILBLAZE"
  "aegislash_shield|--fast AEGISLASH_CHARGE_PSYCHO_CUT --charged SHADOW_BALL,GYRO_BALL"
  "aegislash_blade|--fast PSYCHO_CUT --charged SHADOW_BALL,GYRO_BALL"
  "cradily|--fast ACID --charged GRASS_KNOT,ROCK_TOMB"
)

# bash 3.2 (macOS /bin/bash) has no associative arrays -- linear scan.
extra_args_for() {
  local t=$1 e
  for e in "${DIVE_EXTRA_ARGS[@]}"; do
    if [ "${e%%|*}" = "$t" ]; then echo "${e#*|}"; return 0; fi
  done
}

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
  # Registry moveset pins, if this page has any. Unquoted on purpose: the
  # stored value is a flag string that must split into separate argv words.
  local ea; ea=$(extra_args_for "$tag")
  [ -n "$ea" ] && flags+=($ea)

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
