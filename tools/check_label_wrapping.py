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

WHAT IT SEES (findings #10/#17, 2026-07-04 review)
--------------------------------------------------
The original sweep only inspected string literals / module constants passed to
`toga.Label(...)` or `.text = ...`. It was blind to f-strings and to dynamic
text, so a provably-too-wide f-string (#17) and unbounded runtime text on a
Label (#10) slipped through. This version adds:

  * Part 1 — sound width lower-bounds. A finding is raised only when a MINIMUM
    rendered width can be proven to exceed MAX_LINE (f-string placeholders
    count as 0 chars, so every such flag is a guaranteed clip). Covers
    f-strings, `text=` keyword, `A if c else B` / `x or "lit"` (per-path),
    single-assignment function locals, and same-class `self._helper()` methods
    whose returns are all resolvable.
  * Part 2 — a per-class widget-kind map (Label vs wrapping widget vs other),
    so `.text =` is judged against what the attribute actually holds.
  * Part 3 — the unbounded remainder. A `.text =`/Label site whose width can
    NOT be lower-bounded and whose target is (or may be) a Label is an offender
    by default (this is the #10 class). Suppress a genuinely-bounded one with an
    inline `# label-fits: <reason>` pragma on the site; the OK summary prints
    the pragma count so the exemption surface stays visible. Provable clips
    (Part 1) are NOT pragma-suppressible.

USAGE
-----
    python tools/check_label_wrapping.py          # scan src/gobattlekit
    python tools/check_label_wrapping.py FILE...  # scan specific files

Exit status is non-zero if any offender is found, so it can gate CI / a test.
See docs/responsive_layout_plan.md ("Horizontal clipping") for the full method.
"""
import ast
import pathlib
import sys
from collections import namedtuple

# Longest physical line we accept. The 2026-06-23 layout pass kept hand-wrapped
# lines up to ~34 chars on the dev's target; 40 flags only clear overflow while
# staying green on the accepted text. A flagged line still needs SE eyes — this
# is a tripwire for egregious clips, not a pixel-exact width model.
MAX_LINE = 40

# Calls whose result is a wrapping widget, so their text is exempt.
WRAPPING_CALLS = {"paragraph_text", "toga.MultilineTextInput"}

# Inline suppression marker for a genuinely-bounded dynamic (Part 3) site.
PRAGMA = "# label-fits"

# A resolution scope: module constants, plus the enclosing class's widget-kind
# map (`kinds`) and helper-method widths (`methods`), plus the enclosing
# function's single-assignment locals (`locals`) and local widget kinds
# (`lkinds`).
_Scope = namedtuple("_Scope", "consts kinds methods locals lkinds")


def _empty_scope(consts):
    return _Scope(consts=consts, kinds={}, methods={}, locals={}, lkinds={})


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


def _call_kind(call):
    """'label' / 'wrap' / 'other' for a widget-constructing Call."""
    name = _func_name(call)
    if name == "toga.Label":
        return "label"
    if name in WRAPPING_CALLS:
        return "wrap"
    return "other"


def _kwarg(call, name):
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _skeleton(joined):
    """Static skeleton of an f-string: constants kept, placeholders -> 0 chars.

    Every FormattedValue is rendered as "" (>= 0 chars, no guaranteed newline),
    so the longest line of the skeleton is a sound lower bound on the longest
    rendered line. Newlines can only come from the constant parts.
    """
    parts = []
    for v in joined.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            parts.append(v.value)
        else:
            parts.append("")
    return "".join(parts)


def _self_method(call):
    """Method name for a `self.<name>(...)` call, else None."""
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) \
            and f.value.id == "self":
        return f.attr
    return None


def _width(node, scope, seen=frozenset()):
    """A sound lower bound on the longest rendered physical line, or None.

    Contract: if the return value R is not None, then R > MAX_LINE means this
    expression provably clips on some reachable path, and R <= MAX_LINE means
    it is safely bounded. None means the width cannot be lower-bounded here.
    """
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return _longest_line(node.value) if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        if node.id in scope.locals:
            return _width(scope.locals[node.id], scope, seen | {node.id})
        v = scope.consts.get(node.id)
        return _longest_line(v) if v is not None else None
    if isinstance(node, ast.JoinedStr):
        return _longest_line(_skeleton(node))
    if isinstance(node, ast.IfExp):
        return _branch_width([node.body, node.orelse], scope, seen)
    if isinstance(node, ast.BoolOp):
        return _branch_width(node.values, scope, seen)
    if isinstance(node, ast.Call):
        name = _self_method(node)
        if name is not None:
            return scope.methods.get(name)   # None if unresolvable / not tracked
        return None
    return None


def _branch_width(branches, scope, seen):
    """Per-path rule for IfExp / BoolOp (see plan Part 1.3-1.4).

    All branches resolve  -> min (a flag then means EVERY path clips).
    Some branch unresolved -> only report a resolved branch that itself clips
                              (that path provably clips); otherwise unresolved.
    """
    widths = [_width(b, scope, seen) for b in branches]
    resolved = [w for w in widths if w is not None]
    if not resolved:
        return None
    if any(w is None for w in widths):
        widest = max(resolved)
        return widest if widest > MAX_LINE else None
    return min(widths)


def _direct_returns(func):
    """`return <expr>` nodes belonging to func itself (not nested funcs)."""
    out = []

    def rec(n):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(c, ast.Return) and c.value is not None:
                out.append(c)
            rec(c)

    rec(func)
    return out


def _method_widths(cls, consts):
    """Map method-name -> width bound for helper resolution.

    A method is usable as a text source only if EVERY value-return resolves;
    its bound is the max skeleton across returns (some return path renders that
    wide — treated as reachable). Otherwise the value is None (unresolvable).
    Returns are resolved with module constants only (no per-method locals),
    which is conservative.
    """
    base = _empty_scope(consts)
    result = {}
    for item in cls.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        widths = []
        ok = True
        for ret in _direct_returns(item):
            w = _width(ret.value, base)
            if w is None:
                ok = False
                break
            widths.append(w)
        result[item.name] = max(widths) if (ok and widths) else None
    return result


def _class_kinds(cls):
    """Map self-attr name -> widget kind from `self.<attr> = <call>(...)`.

    An attr assigned different kinds anywhere in the class is 'unknown'
    (conservative).
    """
    kinds = {}
    conflict = set()
    for n in ast.walk(cls):
        if not isinstance(n, ast.Assign) or not isinstance(n.value, ast.Call):
            continue
        for tgt in n.targets:
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) \
                    and tgt.value.id == "self":
                k = _call_kind(n.value)
                if tgt.attr in kinds and kinds[tgt.attr] != k:
                    conflict.add(tgt.attr)
                kinds[tgt.attr] = k
    for a in conflict:
        kinds[a] = "unknown"
    return kinds


def _func_locals(func):
    """Single-assignment locals for func: name -> value node, plus local widget
    kinds. A name assigned more than once is dropped (ambiguous -> unresolved /
    unknown kind)."""
    values = {}
    counts = {}
    kinds = {}
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name):
                    counts[tgt.id] = counts.get(tgt.id, 0) + 1
                    values[tgt.id] = stmt.value
                    if isinstance(stmt.value, ast.Call):
                        kinds[tgt.id] = _call_kind(stmt.value)
    locs = {n: v for n, v in values.items() if counts[n] == 1}
    lkinds = {n: k for n, k in kinds.items() if counts.get(n) == 1}
    return locs, lkinds


def _target_kind(obj, scope):
    """Widget kind for the object of a `<obj>.text = ...` assignment."""
    if isinstance(obj, ast.Attribute) and isinstance(obj.value, ast.Name) \
            and obj.value.id == "self":
        return scope.kinds.get(obj.attr, "unknown")
    if isinstance(obj, ast.Name):
        return scope.lkinds.get(obj.id, "unknown")
    return "unknown"


def _pragma_lines(src):
    return {i for i, line in enumerate(src.splitlines(), 1) if PRAGMA in line}


def check_file(path):
    """Return (offenders, pragma_count) for one module.

    offenders: list of (lineno, context, width, snippet). width is an int for a
    provable clip (Part 1) and None for an unbounded/dynamic Label site
    (Part 3). pragma_count: dynamic sites suppressed by `# label-fits`.
    """
    src = path.read_text()
    tree = ast.parse(src)
    consts = _module_constants(tree)
    pragma_lines = _pragma_lines(src)
    offenders = []
    pragma_count = 0

    def snippet(node):
        seg = ast.get_source_segment(src, node) or ""
        return seg.split("\n")[0][:60]

    def add(node, context, width, kind, valnode):
        nonlocal pragma_count
        lo = node.lineno
        hi = getattr(node, "end_lineno", lo)
        if kind == "unbounded" and any(l in pragma_lines for l in range(lo, hi + 1)):
            pragma_count += 1
            return
        offenders.append((lo, context, width, snippet(valnode)))

    def emit(valnode, kind, node, context, scope):
        if kind == "wrap":                      # wrapping widget — exempt
            return
        w = _width(valnode, scope)
        if w is None:
            if kind in ("label", "unknown"):    # #10 class: dynamic Label text
                add(node, context, None, "unbounded", valnode)
        elif w > MAX_LINE:                       # provable clip (not suppressible)
            add(node, context, w, "clip", valnode)

    def visit(node, scope):
        if isinstance(node, ast.ClassDef):
            scope = scope._replace(kinds=_class_kinds(node),
                                   methods=_method_widths(node, consts),
                                   locals={}, lkinds={})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            loc, lk = _func_locals(node)
            scope = scope._replace(locals={**scope.locals, **loc},
                                   lkinds={**scope.lkinds, **lk})

        if isinstance(node, ast.Call) and _func_name(node) == "toga.Label":
            val = node.args[0] if node.args else _kwarg(node, "text")
            if val is not None:
                emit(val, "label", node, "toga.Label", scope)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute) and tgt.attr == "text":
                    emit(node.value, _target_kind(tgt.value, scope),
                         node, ".text =", scope)

        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree, _empty_scope(consts))
    return offenders, pragma_count


def main(argv):
    root = pathlib.Path(__file__).resolve().parent.parent
    if argv:
        files = [pathlib.Path(a) for a in argv]
    else:
        files = sorted((root / "src/gobattlekit").rglob("*.py"))

    total = 0
    pragmas = 0
    for path in files:
        offenders, pragma_count = check_file(path)
        pragmas += pragma_count
        for lineno, context, width, snippet in offenders:
            total += 1
            rel = path.relative_to(root) if path.is_absolute() else path
            if width is None:
                print(f"{rel}:{lineno}: {context} has dynamic/unbounded text on "
                      f"a Label and may clip: {snippet!r}. Bound it with a "
                      f"'{PRAGMA}: reason' pragma or use theme.paragraph_text().")
            else:
                print(f"{rel}:{lineno}: {context} line is {width} chars "
                      f"(> {MAX_LINE}) and will clip: {snippet!r}")

    if total:
        print(f"\n{total} label site(s) may clip on a narrow phone. "
              f"Add \\n breaks, use theme.paragraph_text(), or (if provably "
              f"bounded) a '{PRAGMA}: reason' pragma.")
        return 1
    print(f"OK: no Label text over {MAX_LINE} chars/line. "
          f"({pragmas} {PRAGMA} pragma{'s' if pragmas != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
