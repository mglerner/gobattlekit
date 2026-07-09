# App Review information

Paste the notes below into App Store Connect under App Review Information > Notes.
No demo account is needed because the app has no login. Attach
`sample_pokegenie.csv` so the reviewer can exercise the import flow.

## Review notes

GoBattleKit has no account and no login. Everything works offline once the app
has downloaded public game data on first launch.

There are two ways to see IV results:

1. Manual entry. On the PvP IV Checker screen, tap the manual entry button and
   type in a Pokémon, its CP, and its IVs. The app shows which ranked-PvP IV
   targets that Pokémon meets.

2. CSV import. Real users export a CSV of their Pokémon from a separate app
   called PokeGenie and share it into GoBattleKit. I have attached a small
   sample as a .zip (App Store Connect does not accept .csv attachments); unzip
   it to get sample_pokegenie.csv. To test it, open the Files app, share the
   CSV, and choose GoBattleKit. The app reads the file and lists which Pokémon
   meet which targets.

The quizzes (move counts, move timing, type effectiveness) need no input and
can be opened straight from the home screen.

What leaves the device: nothing the user enters. On launch the app downloads
public Pokémon game data and PvP rankings from PvPoke over HTTPS. The CSV a user
imports and the targets they save stay on the device. There is no analytics, no
advertising, and no account system.

The app is a fan-made companion for Pokémon GO. It is not affiliated with
Niantic, Nintendo, The Pokémon Company, or PokeGenie, and the About screen says
so.
