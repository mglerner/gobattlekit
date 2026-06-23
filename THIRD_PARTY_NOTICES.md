# Third-party notices

GoBattleKit uses and redistributes the following third-party work. Their
license terms are reproduced or referenced below as those licenses require.

## PvPoke

GoBattleKit downloads PvPoke's game data and rankings at runtime and derives
its evolution-line data and shadow battle-stat multipliers from PvPoke. PvPoke
is maintained by EmpoleonDynamite and is released under the MIT License.

```
MIT License

Copyright (c) 2019 pvpoke

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Bundled Python runtime dependencies

GoBattleKit ships with these libraries via BeeWare/Briefcase. Each is
distributed under a permissive license. The complete license text for every
package is included in its own `.dist-info` directory inside the app bundle.

- **Toga** and **Travertino** (BeeWare) — BSD 3-Clause License
- **Briefcase** support tooling (BeeWare) — BSD 3-Clause License
- **std-nslog** (BeeWare) — BSD 3-Clause License
- **certifi** — Mozilla Public License 2.0; bundles the Mozilla CA certificate
  list, which is provided under the same terms
- **fonttools** — MIT License
- **Pygments** — BSD 2-Clause License

## Data sources for IV thresholds

The IV target spreads bundled with GoBattleKit credit their individual sources
(GamePress, JRE47 / Pokémon GO Hub, RyanSwag, pogo-simulator, and others) in
the in-app IV Credits screen, with dates and links where available.
