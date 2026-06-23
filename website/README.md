# Website

The public pages for GoBattleKit on mglerner.com. Deployed by rsync.

## Layout

- `public/` mirrors the web root. Only this directory is uploaded.
  - `public/gobattlekit/index.html` — landing page (the App Store marketing URL,
    `https://mglerner.com/gobattlekit/`)
  - `public/gobattlekit/privacy.html` — privacy policy (the App Store Privacy
    Policy URL)
  - `public/gobattlekit/support.html` — support page
  - `public/support.html` — redirect stub so older app builds that link to the
    old `/support.html` still land on the support page
- `publish_website.sh` — rsyncs `public/` to the server and creates the
  `/GoBattleKit` alias
- `.publish_env` — your server details (gitignored, you create it once)

## One-time setup

Create `website/.publish_env`:

```sh
MGLERNER_WEB_DEST="user@host:/path/to/webroot"   # rsync target (the web root)
MGLERNER_WEB_SSH="user@host"                      # optional, for the alias symlink
```

## Publishing

```sh
website/publish_website.sh
```

This uploads `public/` (no `--delete`, so it never touches the rest of the site)
and links `/GoBattleKit` to `/gobattlekit` so both URLs serve the same pages.

## When to run it

Run `publish_website.sh` whenever the app version is bumped, so the live pages
stay in step with a release. (Claude will remind you at version-bump time.)

## After the App Store listing is live

Set the real App Store link on the "Get GoBattleKit" button in
`public/gobattlekit/index.html`, then publish again.
