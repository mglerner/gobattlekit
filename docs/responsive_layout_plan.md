# Responsive layout plan

GoBattleKit is iPhone-only, portrait, iOS 13+. The layout was tuned on an
iPhone 17 Pro (~852pt tall content). Real users span iPhone SE (4.7", 667pt,
~600pt usable after chrome) up to Pro Max (~956pt). The App Store also needs
screenshots at multiple device sizes. Goal: (a) never clip on the smallest
supported phone, (b) make reasonable use of larger screens, without changing how
the dev's phone renders.

## Strategy: scroll safety-net, not runtime scaling

The fix is a `toga.ScrollContainer` around the root of each screen that can
overflow. A ScrollContainer is **inert when content fits**: no scroll thumb, no
behavior change, pixel-identical layout. So the 17 Pro is unchanged, and the SE
gets a reachable bottom button instead of a clipped one. "Using larger screens"
is automatic — content just fits with no scroll.

We deliberately did NOT add runtime device-size font scaling. It is technically
feasible (`app.screens[0].size` / `main_window.size` are populated by the time
`startup()` runs), but those APIs return the FULL `UIScreen.mainScreen.bounds` —
they do NOT subtract the ~90-140pt of nav bar + safe-area/home-indicator insets.
The only accurate content height (`main_window._impl.container.height`) is
private and valid only after native layout. A ScrollContainer is a layout
*invariant* — correct regardless of exact screen/content height, no magic
numbers — which is strictly safer than trusting an inset-blind height to drive a
font scale, especially given Toga's finickiness about wrapping and the app's
fixed-height `paragraph_text()` helper.

## What was implemented (2026-06-23)

Eight screens (home, about, help, intro, iv_credits, iv_checker,
user_iv_checker, edit_thresholds) were ALREADY wrapped in ScrollContainers. The
four quiz/summary screens had a plain `toga.Box(style=CONTAINER)` root and no
scroll, and were the only overflow suspects:

| Screen          | SE risk (pre-fix)           | Worst-case height |
| --------------- | --------------------------- | ----------------- |
| timing_quiz.py  | HIGH                        | ~642pt            |
| quiz.py         | HIGH (first-charge variant) | ~578pt            |
| type_quiz.py    | LOW / MEDIUM (SE-1)         | ~534pt            |
| quiz_summary.py | LOW                         | ~360pt + spacer   |

Each had its final `return self.container` changed to a
`toga.ScrollContainer(content=self.container, style=Pack(flex=1,
background_color=COLOR_BG))`. The inner `CONTAINER`-styled box (margin=20) stays
as edge padding — we do NOT add a second outer box, which would double the
margin. `quiz_summary.py` also had its `flex=1` spacer Box removed, since a flex
spacer inside a scroll expands pointlessly and would defeat scrolling (the Back
button now sits directly under the cards instead of pinned to the bottom — the
one cosmetically-visible change on a large screen, worth an eyeball).

Timed-quiz safety (the explicit worry): SAFE. The dynamic handlers
(`_highlight_correct_button`, `_disable_buttons`, the asyncio `_advance_question`
rebuild of `button_box`) operate on widget references captured at build() time,
NOT on the root box's tree position, so re-parenting the root inside a
ScrollContainer is invisible to them. The fixed `height=` on each
`question_label` (which keeps the answer buttons from jumping between questions)
is untouched.

## What was deliberately left

- **No runtime font scaling / `UI_SCALE` constant.** The dominant SE overflow
  comes from INLINE `Pack()` heights in the quiz screens (question-box
  160/120/80, answer buttons h48/52) that bypass theme.py entirely, so a central
  constant would not move the screens that matter while touching ~11 helpers. It
  is real groundwork if active large-screen scaling is ever wanted, but it is not
  a fix and was not worth the surface area now.
- **No active large-screen "fill."** Fonts/spacing are not grown to fill a Pro
  Max. Large screens are handled passively (content fits, no scroll).
- **`paragraph_text()` narrow-width robustness** — a separate follow-up (below);
  the affected screens already scroll, so it is low priority.

## paragraph_text() heuristic (known sharp edge, follow-up)

`theme.paragraph_text()` sets a FIXED height on a read-only MultilineTextInput
using `_PARAGRAPH_CHARS_PER_LINE` tuned at the dev's WIDE width. On a narrower
SE, real wrap is FEWER chars/line, so the formula can UNDER-estimate height and
truncate long bodies. Safe follow-up: add a narrow-width cpl column or derive cpl
from an assumed narrow width; leave the harmless wide-screen over-estimate alone.
Low priority because every screen using `paragraph_text` already scrolls. Keep it
in its OWN commit (it changes fixed heights app-wide and needs SE + 17 Pro eyes).

## Screenshot process (App Store)

1. Build for the simulator via `./prepare_ios.sh`.
2. Capture on the required device classes: an SE-class (smallest), a mid 6.1",
   and a Pro Max (largest). Boot each in the iOS Simulator, run, and screenshot
   Home + a representative quiz + IV checker + About.
3. On the SE, walk each quiz to the bottom and confirm the End Quiz / nav buttons
   are reachable (scroll engages).
4. On the Pro Max, confirm no scroll thumb appears on the quizzes (inert = fits).

## The dials to turn later

- **Active large-screen scaling:** revisit the `UI_SCALE` groundwork only if you
  want fonts/spacing to grow on big phones. It would need threading through
  theme.py helpers AND the inline quiz heights, gated off a startup device-class
  check (accepting the inset-blind `window.size` caveat).
- **paragraph_text cpl:** narrow the chars-per-line table if any long body
  truncates on an SE.
