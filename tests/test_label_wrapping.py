"""Regression guard: no toga.Label text clips horizontally on a narrow phone.

Toga Labels do not auto-wrap on iOS — a line wider than the viewport clips (or
scrolls off the right inside a ScrollContainer). This was fixed by hand twice
(commits 303826e and the 2026-06-26 pass) and regressed both times because the
check was a one-off AST sweep, never enforced. This test runs the committed
sweep (tools/check_label_wrapping.py) so a new over-long Label fails here.

Fix a failure by adding "\n" breaks to the offending text, or rendering long
body text via theme.paragraph_text() instead of a Label. See
docs/responsive_layout_plan.md ("Horizontal clipping").
"""
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_TOOL = _ROOT / "tools" / "check_label_wrapping.py"

_spec = importlib.util.spec_from_file_location("check_label_wrapping", _TOOL)
_checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_checker)


def test_no_label_clips_on_narrow_phone():
    sources = sorted((_ROOT / "src/gobattlekit").rglob("*.py"))
    assert sources, "no source modules found to check"

    offenders = []
    for path in sources:
        found, _pragmas = _checker.check_file(path)
        for lineno, context, width, snippet in found:
            where = "clips" if width is not None else "is unbounded"
            offenders.append(
                f"{path.name}:{lineno}: {context} {where} ({width}): {snippet!r}"
            )

    assert not offenders, (
        f"Label text over {_checker.MAX_LINE} chars/line will clip on a narrow "
        "phone. Add \\n breaks or use theme.paragraph_text():\n  "
        + "\n  ".join(offenders)
    )
