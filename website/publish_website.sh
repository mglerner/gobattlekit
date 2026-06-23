#!/bin/zsh
# Publish the GoBattleKit web pages to mglerner.com.
# Run this after bumping the app version (see DEVELOPER_NOTES "Releasing").
#
# Only website/public/ is uploaded; this script and the README stay local.
#
# One-time setup: create website/.publish_env (gitignored) with your server:
#   MGLERNER_WEB_DEST="user@host:/var/www/mglerner.com"   # rsync target (web root)
#   MGLERNER_WEB_SSH="user@host"                          # optional, for the /GoBattleKit alias
set -e

here="${0:A:h}"
[[ -f "$here/.publish_env" ]] && source "$here/.publish_env"
: ${MGLERNER_WEB_DEST:?Set MGLERNER_WEB_DEST in website/.publish_env (user@host:/webroot)}

echo "Publishing website/public/ -> ${MGLERNER_WEB_DEST}"
# No --delete: this only adds/updates the GoBattleKit files, never touches the
# rest of the site.
rsync -av --no-perms "$here/public/" "${MGLERNER_WEB_DEST%/}/"

# Case alias so /GoBattleKit serves the same files as /gobattlekit.
if [[ -n "${MGLERNER_WEB_SSH:-}" ]]; then
    webpath="${MGLERNER_WEB_DEST#*:}"
    ssh "$MGLERNER_WEB_SSH" "ln -sfn gobattlekit '${webpath%/}/GoBattleKit'"
    echo "Linked /GoBattleKit -> /gobattlekit"
else
    echo "Note: set MGLERNER_WEB_SSH to auto-create the /GoBattleKit alias, or"
    echo "      run once on the server: ln -sfn gobattlekit <webroot>/GoBattleKit"
fi

echo "Done. Live at https://mglerner.com/gobattlekit/"
