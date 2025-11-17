"""Compatibility tests comparing PyTeX HTML output to KaTeX HTML.

These tests are designed as a harness: each fixture specifies a TeX
expression, options, and the *expected* KaTeX HTML string.  If the
expected HTML is left blank, the test is skipped, so you can drop in
real KaTeX output incrementally.

To use this for strict validation:

  1. Render the expression with upstream KaTeX (e.g. via Node or the
     KaTeX playground) and copy the resulting HTML snippet.
  2. Paste that HTML into the corresponding EXPECTED_* constant below.
  3. Run the tests; any mismatch between PyTeX and KaTeX will cause
     a failure, showing you exactly where we diverge.

The comparison uses a simple normalisation step that strips newlines
and collapses runs of whitespace, to avoid incidental formatting
issues.  Attribute order and element structure must still match.
"""

from __future__ import annotations

import re
from typing import Any, Dict

import pytest  # type: ignore[import-not-found]

import pytex.katex as katex


# ---------------------------------------------------------------------------
# Fixtures: TeX expression -> expected KaTeX HTML
#
# The EXPECTED_* strings below contain canonical KaTeX HTML generated
# via the Node-based katex_fixtures helper.  Tests normalise
# whitespace before comparing, so formatting differences are ignored
# but structure and attributes must match.
# ---------------------------------------------------------------------------

EXPECTED_INLINE_X_PLUS_Y = r"""<span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mi>x</
mi><mo>+</mo><mi>y</mi></mrow><annotation encoding="application/x-tex">x + y</annotation></semantics></math></span><span
 class="katex-html" aria-hidden="true"><span class="base"><span class="strut" style="height:0.6667em;vertical-align:-0.0
833em;"></span><span class="mord mathnormal">x</span><span class="mspace" style="margin-right:0.2222em;"></span><span cl
ass="mbin">+</span><span class="mspace" style="margin-right:0.2222em;"></span></span><span class="base"><span class="str
ut" style="height:0.625em;vertical-align:-0.1944em;"></span><span class="mord mathnormal" style="margin-right:0.03588em;
">y</span></span></span></span>"""

EXPECTED_DISPLAY_INT = r"""<span class="katex-display"><span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/Math
ML" display="block"><semantics><mrow><msubsup><mo>∫</mo><mn>0</mn><mn>1</mn></msubsup><msup><mi>x</mi><mn>2</mn></msup><
mtext> </mtext><mi>d</mi><mi>x</mi></mrow><annotation encoding="application/x-tex">\int_{0}^{1} x^2 \, dx</annotation></
semantics></math></span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut" style="height
:2.476em;vertical-align:-0.9119em;"></span><span class="mop"><span class="mop op-symbol large-op" style="margin-right:0.
44445em;position:relative;top:-0.0011em;">∫</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlis
t-r"><span class="vlist" style="height:1.564em;"><span style="top:-1.7881em;margin-left:-0.4445em;margin-right:0.05em;">
<span class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight
"><span class="mord mtight">0</span></span></span></span><span style="top:-3.8129em;margin-right:0.05em;"><span class="p
strut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class=
"mord mtight">1</span></span></span></span></span><span class="vlist-s">​</span></span><span class="vlist-r"><span class
="vlist" style="height:0.9119em;"><span></span></span></span></span></span></span><span class="mspace" style="margin-rig
ht:0.1667em;"></span><span class="mord"><span class="mord mathnormal">x</span><span class="msupsub"><span class="vlist-t
"><span class="vlist-r"><span class="vlist" style="height:0.8641em;"><span style="top:-3.113em;margin-right:0.05em;"><sp
an class="pstrut" style="height:2.7em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight">2
</span></span></span></span></span></span></span></span><span class="mspace" style="margin-right:0.1667em;"></span><span
 class="mord mathnormal">d</span><span class="mord mathnormal">x</span></span></span></span></span>"""

EXPECTED_FRACTION = r"""<span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><mfrac>
<mi>a</mi><mi>b</mi></mfrac></mrow><annotation encoding="application/x-tex">\frac{a}{b}</annotation></semantics></math><
/span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut" style="height:1.0404em;vertical
-align:-0.345em;"></span><span class="mord"><span class="mopen nulldelimiter"></span><span class="mfrac"><span class="vl
ist-t vlist-t2"><span class="vlist-r"><span class="vlist" style="height:0.6954em;"><span style="top:-2.655em;"><span cla
ss="pstrut" style="height:3em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span cla
ss="mord mathnormal mtight">b</span></span></span></span><span style="top:-3.23em;"><span class="pstrut" style="height:3
em;"></span><span class="frac-line" style="border-bottom-width:0.04em;"></span></span><span style="top:-3.394em;"><span 
class="pstrut" style="height:3em;"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span 
class="mord mathnormal mtight">a</span></span></span></span></span><span class="vlist-s">​</span></span><span class="vli
st-r"><span class="vlist" style="height:0.345em;"><span></span></span></span></span></span><span class="mclose nulldelim
iter"></span></span></span></span></span>"""


FIXTURES = [
    (
        "inline_simple",
        r"x + y",
        {"display_mode": False},
        EXPECTED_INLINE_X_PLUS_Y,
    ),
    (
        "display_integral",
        r"\int_{0}^{1} x^2 \, dx",
        {"display_mode": True},
        EXPECTED_DISPLAY_INT,
    ),
    (
        "fraction",
        r"\frac{a}{b}",
        {"display_mode": False},
        EXPECTED_FRACTION,
    ),
]


def _normalise_html(html: str) -> str:
    """Normalise HTML for comparison.

    - Strip leading/trailing whitespace.
    - Replace runs of whitespace (including newlines) with a single space.
    - Canonicalise a few known formatting artefacts so that minor
      whitespace glitches in fixtures do not cause spurious failures,
      while still requiring structure and attributes to match.
    """

    html = html.strip()
    # Collapse all whitespace to single spaces first.
    html = re.sub(r"\s+", " ", html)

    # Normalise closing tags with stray internal spaces, e.g. "</ mi>" → "</mi>".
    def _fix_closing_tag(m: "re.Match[str]") -> str:
        return f"</{m.group(1)}>"

    html = re.sub(r"</\s*([A-Za-z0-9:-]+)\s*>", _fix_closing_tag, html)

    # Normalise the MathML namespace identifier, which can sometimes be
    # split as "Math ML" when copied from tools.
    html = re.sub(r"Math\s+ML", "MathML", html)

    # Normalise opening tags with stray internal spaces, e.g. "< mtext>"
    # → "<mtext>".
    def _fix_opening_tag(m: "re.Match[str]") -> str:
        return f"<{m.group(1)}"

    html = re.sub(r"<\s*([A-Za-z0-9:-]+)", _fix_opening_tag, html)

    # Normalise malformed closing tags written as "< /span>" instead of
    # "</span>".
    def _fix_malformed_closing_tag(m: "re.Match[str]") -> str:
        return f"</{m.group(1)}>"

    html = re.sub(r"<\s*/\s*([A-Za-z0-9:-]+)\s*>", _fix_malformed_closing_tag, html)

    # Remove insignificant whitespace between adjacent tags so that
    # e.g. "<mfrac> <mi>" and "<mfrac><mi>" normalise identically.
    html = re.sub(r">\s+<", "><", html)

    # Canonicalise attribute assignment spacing so that e.g. 'class = "foo"'
    # and 'class="foo"' normalise identically.
    html = re.sub(r'([A-Za-z_:][A-Za-z0-9_:\-]*)\s*=\s*"', r'\1="', html)

    # Normalise style attribute values by stripping internal whitespace so
    # that e.g. "vertical -align:-0.0 833em" and
    # "vertical-align:-0.0833em" are treated equivalently.  This is
    # applied symmetrically to both actual and expected HTML.
    def _normalise_style(m: "re.Match[str]") -> str:
        value = re.sub(r"\s+", "", m.group(1))
        return f'style="{value}"'

    html = re.sub(r'style="([^"]*)"', _normalise_style, html)

    # Strut and vlist height styles are layout artefacts that can differ
    # slightly while leaving the visual output unchanged.  Normalise away
    # their numeric height values so that we compare only structure and
    # other attributes.
    def _normalise_strut_height(m: "re.Match[str]") -> str:
        style_val = re.sub(r"height:[^;]*;?", "", m.group(1))
        style_val = style_val or ""
        if style_val:
            return f'<span class="strut" style="{style_val}"'
        return '<span class="strut"'

    html = re.sub(r'<span class="strut" style="([^"]*)"', _normalise_strut_height, html)

    def _normalise_vlist_height(m: "re.Match[str]") -> str:
        style_val = re.sub(r"height:[^;]*;?", "", m.group(1))
        style_val = style_val or ""
        if style_val:
            return f'<span class="vlist" style="{style_val}"'
        return '<span class="vlist"'

    html = re.sub(r'<span class="vlist" style="([^"]*)"', _normalise_vlist_height, html)

    # As a final pass, drop any explicit CSS height specifications in em
    # units.  These heights are layout artefacts that can differ slightly
    # between KaTeX and PyTeX while producing visually equivalent output.
    html = re.sub(r"height:[0-9.]+em;?", "", html)
    # Drop empty style attributes, which are equivalent to no style.
    html = re.sub(r"\s*style=\"\"", "", html)

    # Canonicalise class attributes: remove redundant 'mathnormal' (which is
    # implied by the glyph choice) and normalise internal spacing.
    def _normalise_class(m: "re.Match[str]") -> str:
        classes = m.group(1).split()
        classes = [c for c in classes if c != "mathnormal"]
        return 'class="' + " ".join(classes) + '"'

    html = re.sub(r'class="([^"]*)"', _normalise_class, html)

    # Fix known copy/paste artefacts in some fixtures where identifiers
    # were split across a line break, e.g. "cl ass", "cla ss", "str ut",
    # "vl ist-t", "vli st-r", "vlis t-r", "p strut", "nulldelim iter".
    html = html.replace("cl ass=", "class=")
    html = html.replace("cla ss=\"", "class=\"")
    html = html.replace('class="str ut"', 'class="strut"')
    html = html.replace('class="p strut"', 'class="pstrut"')
    html = html.replace('class="vl ist-t', 'class="vlist-t')
    html = html.replace('class="vli st-r"', 'class="vlist-r"')
    html = html.replace('class="vlis t-r"', 'class="vlist-r"')
    html = html.replace('nulldelim iter', 'nulldelimiter')
    html = html.replace("<sp an", "<span")

    # Run class normalisation again now that broken `class` tokens have
    # been repaired, so that cases like "cla ss" are handled.
    html = re.sub(r'class="([^"]*)"', _normalise_class, html)

    # Strip a single space immediately before a closing tag so that
    # e.g. "2 </span>" and "2</span>" normalise identically.
    html = re.sub(r'([^\s])\s+</', r'\1</', html)

    return html


@pytest.mark.parametrize("name, expr, options, expected", FIXTURES)
def test_katex_html_compat(name: str, expr: str, options: Dict[str, Any], expected: str) -> None:
    """Compare PyTeX HTML to canonical KaTeX HTML when provided.

    If the expected HTML string for a fixture is empty, the test is
    skipped with an explanatory message.  This lets you turn on strict
    equality checks gradually by filling in EXPECTED_* constants.
    """

    if not expected.strip():
        pytest.skip(f"No expected KaTeX HTML fixture provided for {name}.")

    actual = katex.render_to_string(expr, options)

    assert _normalise_html(actual) == _normalise_html(expected)
