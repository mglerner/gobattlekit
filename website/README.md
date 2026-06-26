# Website

The public pages for GoBattleKit on mglerner.com. Deployed by rsync, same style
as `../../gopvpsim/scripts/publish_website.sh`.

## Layout

- `public/` is the content of `https://mglerner.com/gobattlekit/`:
  - `index.html` — landing page (the App Store marketing URL,
    `https://mglerner.com/gobattlekit/`)
  - `privacy.html` — privacy policy (the App Store Privacy Policy URL,
    `https://mglerner.com/gobattlekit/privacy.html`)
  - `support.html` — support page
- `publish_website.sh` — dry-run by default; rsyncs `public/` to the server and
  symlinks `/GoBattleKit` to `/gobattlekit`

## Publishing

```sh
website/publish_website.sh          # dry run (safe default)
website/publish_website.sh --push   # actually push
```

The destination (`mglerner.com:mglerner.com/gobattlekit/`) is hardcoded in the
script. `--delete` is scoped to that dedicated directory, so it never touches the
rest of the site.

## When to run it

Run it whenever the app version is bumped, so the live pages stay in step with a
release. (Claude will remind you at version-bump time.)

## Notes

- The old `/support.html` at the site root still works for app builds shipped
  before 1.0.0. The 1.0.0 app links to `/gobattlekit/support.html`. Retire the
  old root page by hand if you want to.
- After the App Store listing is live, set the App Store link on the "Get
  GoBattleKit" button in `public/index.html`, then publish again.
