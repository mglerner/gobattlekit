#!/usr/bin/env bash
# Publish website/public/ to mglerner.com/gobattlekit/.
#
# Run this after bumping the app version (see DEVELOPER_NOTES "TestFlight Notes")
# so the live pages stay in step with a release.
#
# Flow:
#   1. Verify no em/en-dashes in the pages (Michael's house style; aborts on a
#      hit unless --skip-verify).
#   2. rsync website/public/ to mglerner.com:mglerner.com/gobattlekit/ with
#      --delete, so anything removed locally is also removed on the server.
#   3. Symlink /GoBattleKit -> /gobattlekit on the server so both URLs serve the
#      same pages.
#
# Default is dry-run. Pass --push to actually send the files.
#
# Usage:
#     website/publish_website.sh                 # dry run (safe default)
#     website/publish_website.sh --push          # actually push
#     website/publish_website.sh --push --skip-verify

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${SCRIPT_DIR}/public/"
DEST="mglerner.com:mglerner.com/gobattlekit/"
SSH_HOST="mglerner.com"

PUSH=false
SKIP_VERIFY=false
for arg in "$@"; do
  case "$arg" in
    --push) PUSH=true ;;
    --skip-verify) SKIP_VERIFY=true ;;
    *) echo "error: unknown arg '$arg'" >&2; exit 2 ;;
  esac
done

if [ ! -d "$SRC" ]; then
  echo "error: $SRC does not exist" >&2
  exit 1
fi

if [ "$SKIP_VERIFY" = true ]; then
  echo "Skipping em/en-dash check (--skip-verify)."
else
  echo "Checking for em/en-dashes..."
  if hits=$(grep -rlE '—|–' "$SRC"); then
    echo "error: em/en-dash found (use ASCII hyphens, or --skip-verify):" >&2
    echo "$hits" >&2
    exit 1
  fi
  echo
fi

if [ "$PUSH" = true ]; then
  echo "Pushing ${SRC} -> ${DEST}"
  rsync -avzh --delete "$SRC" "$DEST"
  echo
  echo "Linking /GoBattleKit -> /gobattlekit"
  ssh "$SSH_HOST" "ln -sfn gobattlekit mglerner.com/GoBattleKit"
  echo
  echo "Done. Live at https://mglerner.com/gobattlekit/"
else
  echo "Dry run (pass --push to actually push)"
  echo "Source: ${SRC}"
  echo "Dest:   ${DEST}"
  echo
  rsync -avzhn --delete "$SRC" "$DEST"
  echo
  echo "(dry run - nothing was sent; pass --push to publish)"
fi
