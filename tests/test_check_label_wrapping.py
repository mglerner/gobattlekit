"""Unit tests for the checker itself (tools/check_label_wrapping.py).

These pin the Parts 1-3 guarantees from docs/../fstring_checker_plan:
  * Part 1 raises a finding ONLY on a provable width lower-bound over MAX_LINE
    (f-strings, text= keyword, IfExp/BoolOp per-path, single-assign locals,
    same-class helper methods).
  * Part 2 judges `.text =` against the target widget's kind (Label vs wrapping
    vs other/unknown).
  * Part 3 makes an un-lower-boundable Label/unknown site an offender unless a
    `# label-fits` pragma bounds it, and the pragma count stays visible.

Each test writes a synthetic module to tmp_path and runs check_file on it, so
the checker is exercised as a unit, independent of the real source tree.
"""
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_TOOL = _ROOT / "tools" / "check_label_wrapping.py"

_spec = importlib.util.spec_from_file_location("check_label_wrapping", _TOOL)
_checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_checker)

MAX = _checker.MAX_LINE


def run(tmp_path, src):
    p = tmp_path / "snippet.py"
    p.write_text(src)
    return _checker.check_file(p)


# ---------------------------------------------------------------------------
# Part 1: sound width lower-bounds
# ---------------------------------------------------------------------------

def test_fstring_skeleton_over_max_is_flagged_historical_17(tmp_path):
    """The #17 offender must flag: its static skeleton is 42 chars, and
    placeholders count as 0, so it provably clips."""
    src = (
        "import toga\n"
        'x = toga.Label(f"Here are the top {len(q)} IV combinations that do:")\n'
    )
    offenders, pragmas = run(tmp_path, src)
    assert len(offenders) == 1
    lineno, context, width, snippet = offenders[0]
    assert width == 42          # skeleton width, placeholder = 0 chars
    assert pragmas == 0


def test_fstring_with_short_skeleton_not_flagged(tmp_path):
    """A long *placeholder* does not clip a short skeleton — placeholders are
    lower-bounded at 0, so this is provably safe and must NOT flag."""
    src = (
        "import toga\n"
        'x = toga.Label(f"Score: {a} / {b}")\n'   # skeleton 9 chars
    )
    offenders, _ = run(tmp_path, src)
    assert offenders == []


def test_text_keyword_form_is_checked(tmp_path):
    """toga.Label(text=<f-string>) must be seen, not only the positional arg."""
    src = (
        "import toga\n"
        'x = toga.Label(text=f"This static skeleton is definitely wider than forty {v}")\n'
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] > MAX


def test_ifexp_both_branches_clip_flags_min(tmp_path):
    """Both branches resolve and both exceed MAX -> every path clips; report the
    minimum of the two."""
    a = "A" * 45
    b = "B" * 50
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\nLONG2 = {b!r}\n'
        "x = toga.Label(LONG1 if c else LONG2)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] == 45          # min(45, 50)


def test_ifexp_one_branch_fits_not_flagged(tmp_path):
    """Both branches resolve but one fits -> min <= MAX, so the site is bounded
    and must NOT flag (soundness: we only flag when it clips on some path we can
    prove)."""
    a = "A" * 45
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\nSHORT = "short"\n'
        "x = toga.Label(LONG1 if c else SHORT)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert offenders == []


def test_ifexp_resolved_branch_clips_other_unresolved_flags(tmp_path):
    """One branch resolves and clips, the other is dynamic -> that path provably
    clips, so flag it (per-path soundness)."""
    a = "A" * 45
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\n'
        "x = toga.Label(LONG1 if c else dynamic)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] == 45


def test_ifexp_resolved_branch_fits_other_unresolved_is_unbounded(tmp_path):
    """One branch fits, the other is dynamic -> can't bound the dynamic path, so
    it is a Part-3 unbounded finding (width None), not a clip."""
    src = (
        "import toga\n"
        'x = toga.Label("short" if c else dynamic)\n'
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] is None        # unbounded, not a provable clip


def test_boolop_resolved_operand_clips_flags(tmp_path):
    """`dyn or LONG` — the literal fallback provably clips on the fallback
    path."""
    a = "A" * 45
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\n'
        "x = toga.Label(dyn or LONG1)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] == 45


def test_local_single_assignment_resolves(tmp_path):
    """A local assigned exactly once to a resolvable value is resolved."""
    a = "A" * 45
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\n'
        "def build():\n"
        "    msg = LONG1\n"
        "    return toga.Label(msg)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] == 45


def test_local_reassigned_is_unresolved(tmp_path):
    """A local assigned more than once is ambiguous -> treated as unresolved
    (Part-3 unbounded), never silently resolved to one arm."""
    a = "A" * 45
    src = (
        "import toga\n"
        f'LONG1 = {a!r}\n'
        "def build():\n"
        "    msg = 'a'\n"
        "    msg = LONG1\n"
        "    return toga.Label(msg)\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] is None


def test_helper_method_all_returns_resolvable_bounds_the_call(tmp_path):
    """self._helper() whose returns are all short f-strings resolves and fits,
    so the call site is neither a clip nor unbounded."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def _score_text(self):\n"
        "        if self.streak:\n"
        '            return f"Score: {self.score} / {self.total}"\n'
        '        return f"Score: {self.score}"\n'
        "    def build(self):\n"
        "        return toga.Label(self._score_text())\n"
    )
    offenders, _ = run(tmp_path, src)
    assert offenders == []


def test_helper_method_max_across_returns_flags_clip(tmp_path):
    """A helper with a return whose skeleton exceeds MAX flags at that width
    (max across returns is the existential lower bound)."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def _msg(self):\n"
        '        return f"{x} this static skeleton clearly exceeds forty characters!!"\n'
        "    def build(self):\n"
        "        return toga.Label(self._msg())\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] > MAX


def test_helper_method_unresolvable_return_is_unbounded(tmp_path):
    """If any return is unresolvable the helper is unusable -> unbounded."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def _msg(self):\n"
        "        return some_dynamic_value\n"
        "    def build(self):\n"
        "        return toga.Label(self._msg())\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] is None


# ---------------------------------------------------------------------------
# Part 2: widget-kind map
# ---------------------------------------------------------------------------

def test_text_assignment_to_wrapping_widget_is_exempt(tmp_path):
    """`.text =` on a paragraph_text/MultilineTextInput attribute is exempt even
    with wildly dynamic text (the widget wraps)."""
    src = (
        "import toga\n"
        "from theme import paragraph_text\n"
        "class S:\n"
        "    def build(self):\n"
        "        self.msg = paragraph_text('hi')\n"
        "    def update(self):\n"
        "        self.msg.text = whatever_dynamic\n"
    )
    offenders, _ = run(tmp_path, src)
    assert offenders == []


def test_text_assignment_to_label_is_unbounded(tmp_path):
    """The same dynamic `.text =` onto a Label attribute IS the #10 class."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def build(self):\n"
        "        self.msg = toga.Label('hi')\n"
        "    def update(self):\n"
        "        self.msg.text = whatever_dynamic\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] is None


def test_text_assignment_to_other_widget_unresolved_is_not_flagged(tmp_path):
    """A known non-Label, non-wrapping widget (Button) with dynamic text is out
    of the Label scope and must not regress into noise."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def build(self):\n"
        "        self.btn = toga.Button('x')\n"
        "    def update(self):\n"
        "        self.btn.text = whatever_dynamic\n"
    )
    offenders, _ = run(tmp_path, src)
    assert offenders == []


def test_attr_reassigned_to_conflicting_kinds_is_unknown(tmp_path):
    """An attr assigned both a Label and a Button anywhere in the class is
    'unknown' -> dynamic `.text =` is treated conservatively as unbounded."""
    src = (
        "import toga\n"
        "class S:\n"
        "    def build(self):\n"
        "        self.msg = toga.Label('hi')\n"
        "    def rebuild(self):\n"
        "        self.msg = toga.Button('x')\n"
        "    def update(self):\n"
        "        self.msg.text = whatever_dynamic\n"
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] is None


def test_unknown_kind_resolvable_long_value_is_clip(tmp_path):
    """Unknown-kind target keeps today's behavior: a resolvable over-long value
    still flags as a provable clip."""
    long_literal = "Z" * 50
    src = (
        "import toga\n"
        "def update(widget):\n"
        f'    widget.text = {long_literal!r}\n'
    )
    offenders, _ = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] == 50


# ---------------------------------------------------------------------------
# Part 3: pragma suppression + visible count
# ---------------------------------------------------------------------------

def test_pragma_suppresses_unbounded_and_is_counted(tmp_path):
    """A `# label-fits` pragma on an unbounded Label site suppresses the finding
    and increments the visible pragma count."""
    src = (
        "import toga\n"
        "def build():\n"
        "    return toga.Label(dynamic_value)  # label-fits: bounded by domain\n"
    )
    offenders, pragmas = run(tmp_path, src)
    assert offenders == []
    assert pragmas == 1


def test_pragma_does_not_suppress_provable_clip(tmp_path):
    """A pragma must NOT hide a Part-1 provable clip — those are real bugs to
    fix, not to annotate."""
    src = (
        "import toga\n"
        'x = toga.Label(f"This static skeleton is way over the forty-char {v}budget")  # label-fits: nope\n'
    )
    offenders, pragmas = run(tmp_path, src)
    assert len(offenders) == 1
    assert offenders[0][2] > MAX
    assert pragmas == 0
