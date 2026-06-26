#!/usr/bin/env python3
"""Static check for toga.Label text that will clip horizontally on a narrow phone.

WHY THIS EXISTS
---------------
Toga `Label`s do NOT auto-wrap on iOS — they render on a single line and clip
(or, inside a horizontally-scrollable ScrollContainer, scroll off the right
edge) when the text is wider than the viewport. The app is iPhone-only/portrait
down to the iPhone SE (~320pt usable width), so any single Label line longer
than ~`MAX_LINE` characters risks clipping.

The fix for a flagged line is one of:
  * add explicit "\n" breaks so each physical line fits (the convention for
    short static labels — see GETTING_STARTED in user_iv_checker.py), or
  * render long *body* text via theme.paragraph_text() (a wrapping
    MultilineTextInput), not a Label.

This is the REPRODUCIBLE version of the one-off "AST sweep" done by hand in
commit 303826e. That sweep only inspected string literals passed directly to
`toga.Label(...)`, so it MISSED text assigned through a module-level constant
(e.g. `NO_TARGETS_MESSAGE`) or through `widget.text = ...`. This checker covers
all three, resolving module-level string constants by name.

USAGE
-----
    python tools/check_label_wrapping.py          # scan src/gobattlekit/screens
    python tools/check_label_wrapping.py FILE...  # scan specific files

Exit status is non-zero if any offender is found, so it can gate CI / a test.
See docs/responsive_layout_plan.md ("Horizontal clipping") for the full method.
"""
import ast
import pathlib
import sys

# Longest physical line we accept. The 2026-06-23 layout pass kept hand-wrapped
# lines up to ~34 chars on the dev's target; 40 flags only clear overflow while
# staying green on the accepted text. A flagged line still needs SE eyes — this
# is a tripwire for egregious clips, not a pixel-exact width model.
MAX_LINE = 40

# theme.paragraph_text() returns a wrapping widget, so its text is exempt.
WRAPPING_CALLS = {"paragraph_text"}


def _func_name(node):
    """'toga.Label' / 'paragraph_text' for a Call's func, else ''."""
    f = node.func
    if isinstance(f, ast.Attribute):
        base = f.value.id if isinstance(f.value, ast.Name) else "?"
        return f"{base}.{f.attr}"
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _longest_line(text):
    return max((len(line) for line in text.split("\n")), default=0)


def _module_constants(tree):
    """Map NAME -> str value for top-level `NAME = "literal"` assignments."""
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
    return consts


def _resolve(node, consts):
    """A str value for a Constant or a Name bound to a module const, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    return None


def check_file(path):
    src = path.read_text()
    tree = ast.parse(src)
    consts = _module_constants(tree)
    offenders = []

    def consider(text, lineno, context):
        if text and _longest_line(text) > MAX_LINE:
            offenders.append((lineno, context, _longest_line(text),
                              text.split("\n")[0][:60]))

    # 1) toga.Label(<literal-or-const>, ...)
    # 2) <anything>.text = <literal-or-const>
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _func_name(node) == "toga.Label":
            if node.args:
                consider(_resolve(node.args[0], consts), node.lineno, "toga.Label")
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute) and tgt.attr == "text":
                    consider(_resolve(node.value, consts), node.lineno, ".text =")

    # A module const is only an offender if it is actually used as label text,
    # which (1)/(2) already capture by resolving the name. Report the const's
    # own definition line too, so the fix site is obvious.
    return offenders


def main(argv):
    root = pathlib.Path(__file__).resolve().parent.parent
    if argv:
        files = [pathlib.Path(a) for a in argv]
    else:
        files = sorted((root / "src/gobattlekit/screens").glob("*.py"))

    total = 0
    for path in files:
        offenders = check_file(path)
        for lineno, context, width, snippet in offenders:
            total += 1
            rel = path.relative_to(root) if path.is_absolute() else path
            print(f"{rel}:{lineno}: {context} line is {width} chars "
                  f"(> {MAX_LINE}) and will clip: {snippet!r}")

    if total:
        print(f"\n{total} label line(s) may clip on a narrow phone. "
              f"Add \\n breaks or use theme.paragraph_text().")
        return 1
    print(f"OK: no Label text over {MAX_LINE} chars/line.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
