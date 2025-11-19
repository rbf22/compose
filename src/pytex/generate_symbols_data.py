"""Utility to regenerate pytex.symbols_data from KaTeX's symbols.js.

This script parses KaTeX's symbols.js (from archive.tgz under
pytex/archive/src/symbols.js) and emits a Python
module defining four globals compatible with the current runtime:

- symbols: Dict[Mode, Dict[str, Dict[str, Optional[str]]]]
- ligatures: Dict[str, bool]
- ATOMS: Dict[str, int]
- NON_ATOMS: Dict[str, int]

Usage (from the pytex project root):

    poetry run python -m pytex.generate_symbols_data > pytex/pytex/symbols_data_generated.py

This script is an intermediate tool: it focuses on faithfully porting the
explicit defineSymbol(...) calls in symbols.js.  It does not attempt to
simulate every wide-character loop at the end of symbols.js; those can be
added later if needed.  The existing symbols_data.py file is left
untouched; consumers are expected to opt-in to any newly generated module
explicitly.
"""

from __future__ import annotations

import pprint
import re
import tarfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Simple JS helpers
# ---------------------------------------------------------------------------

_MODE_MAP = {"math": "math", "text": "text"}
_FONT_MAP = {"main": "main", "ams": "ams"}
_GROUP_MAP = {
    "accent": "accent-token",
    "bin": "bin",
    "close": "close",
    "inner": "inner",
    "mathord": "mathord",
    "op": "op-token",
    "open": "open",
    "punct": "punct",
    "rel": "rel",
    "spacing": "spacing",
    "textord": "textord",
}


_DEFINE_RE = re.compile(
    r"defineSymbol\(\s*"  # function name
    r"([a-zA-Z]+)\s*,\s*"  # mode identifier (math/text)
    r"([a-zA-Z]+)\s*,\s*"  # font identifier (main/ams)
    r"([a-zA-Z]+)\s*,\s*"  # group identifier (accent/bin/...)
    r"([^,]+?)\s*,\s*"     # replace argument (string literal or null)
    r"([^,]+?)"              # name argument (string literal or identifier)
    r"(?:\s*,\s*(true|false))?"  # optional acceptUnicodeChar
    r"\s*\);",
)

_JS_STRING_RE = re.compile(r"^(['\"])(.*)\1$", re.DOTALL)


def _parse_js_string_literal(src: str) -> str | None:
    """Parse a restricted JS string literal into a Python str.

    Returns None if *src* is not a simple quoted literal.
    """

    m = _JS_STRING_RE.match(src.strip())
    if not m:
        return None
    _quote, body = m.groups()
    result_chars = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            result_chars.append(ch)
            i += 1
            continue

        # Handle escape sequence
        i += 1
        if i >= len(body):
            result_chars.append("\\")
            break
        esc = body[i]

        if esc == "u" and i + 4 < len(body):
            # Unicode escape \uXXXX
            hex_digits = body[i + 1 : i + 5]
            try:
                codepoint = int(hex_digits, 16)
            except ValueError:
                # Fallback: keep sequence literally
                result_chars.append("\\u" + hex_digits)
            else:
                result_chars.append(chr(codepoint))
            i += 5
            continue

        if esc in {"\\", "'", '"'}:
            result_chars.append(esc)
            i += 1
            continue

        if esc == "n":
            result_chars.append("\n")
        elif esc == "r":
            result_chars.append("\r")
        elif esc == "t":
            result_chars.append("\t")
        else:
            # Unknown/unused escape – keep the escaped char
            result_chars.append(esc)
        i += 1

    return "".join(result_chars)


# ---------------------------------------------------------------------------
# Core parsing
# ---------------------------------------------------------------------------


def _parse_symbols_js(src_text: str) -> dict[str, dict[str, dict[str, str | None]]]:
    """Parse KaTeX's symbols.js into a nested symbols dict.

    The returned structure is:

        {mode: {name: {"font": str, "group": str, "replace": Optional[str]}}}
    """

    symbols: dict[str, dict[str, dict[str, str | None]]] = {
        "math": {},
        "text": {},
    }

    for line in src_text.splitlines():
        if "defineSymbol(" not in line:
            continue

        m = _DEFINE_RE.search(line)
        if not m:
            continue

        mode_id, font_id, group_id, replace_src, name_src, accept_src = m.groups()

        mode = _MODE_MAP.get(mode_id)
        font = _FONT_MAP.get(font_id)
        group = _GROUP_MAP.get(group_id)
        if mode is None or font is None or group is None:
            # Unknown identifier – ignore conservatively.
            continue

        replace_src = replace_src.strip()
        if replace_src == "null":
            replace: str | None = None
        else:
            replace = _parse_js_string_literal(replace_src)

        name = _parse_js_string_literal(name_src.strip())
        if name is None:
            # Non-literal name (e.g. loop variable) – skip for now.
            continue

        entry: dict[str, str | None] = {
            "font": font,
            "group": group,
            "replace": replace,
        }
        symbols[mode][name] = entry

        accept = accept_src == "true"
        if accept and replace is not None and replace not in symbols[mode]:
            # Unicode-accepting alias
            symbols[mode][replace] = entry

    return symbols


def _default_atoms() -> dict[str, int]:
    """Return ATOMS map mirroring KaTeX's symbols.js."""

    return {
        "bin": 1,
        "close": 1,
        "inner": 1,
        "open": 1,
        "punct": 1,
        "rel": 1,
    }


def _default_non_atoms() -> dict[str, int]:
    """Return NON_ATOMS map mirroring KaTeX's symbols.js."""

    return {
        "accent-token": 1,
        "mathord": 1,
        "op-token": 1,
        "spacing": 1,
        "textord": 1,
    }


def _default_ligatures() -> dict[str, bool]:
    """Return ligatures map from the bottom of symbols.js."""

    return {
        "--": True,
        "---": True,
        "``": True,
        "''": True,
    }


def _surrogate_pair_to_codepoint(high: int, low: int) -> int:
    return ((high - 0xD800) << 10) + (low - 0xDC00) + 0x10000


def _add_loop_built_symbols(symbols: dict[str, dict[str, dict[str, str | None]]]) -> None:
    math_text_symbols = "0123456789/@.\""
    for ch in math_text_symbols:
        symbols["math"][ch] = {"font": "main", "group": "textord", "replace": ch}

    text_symbols = '0123456789!@*()-=+";:?/.,'
    for ch in text_symbols:
        symbols["text"][ch] = {"font": "main", "group": "textord", "replace": ch}

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    for ch in letters:
        symbols["math"][ch] = {"font": "main", "group": "mathord", "replace": ch}
        symbols["text"][ch] = {"font": "main", "group": "textord", "replace": ch}

    high = 0xD835

    def _define(mode: str, group: str, replace: str, name: str) -> None:
        symbols[mode][name] = {"font": "main", "group": group, "replace": replace}

    def _cp(low: int) -> int:
        return _surrogate_pair_to_codepoint(high, low)

    for i, ch in enumerate(letters):
        wide = chr(_cp(0xDC00 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDC34 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDC68 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDD04 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDD6C + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDDA0 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDDD4 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDE08 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDE70 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        if i < 26:
            wide = chr(_cp(0xDD38 + i))
            _define("math", "mathord", ch, wide)
            _define("text", "textord", ch, wide)

            wide = chr(_cp(0xDC9C + i))
            _define("math", "mathord", ch, wide)
            _define("text", "textord", ch, wide)

    wide_k = chr(_cp(0xDD5C))
    _define("math", "mathord", "k", wide_k)
    _define("text", "textord", "k", wide_k)

    for i in range(10):
        ch = str(i)

        wide = chr(_cp(0xDFCE + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDFE2 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDFEC + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

        wide = chr(_cp(0xDFF6 + i))
        _define("math", "mathord", ch, wide)
        _define("text", "textord", ch, wide)

    extra_latin = "\u00d0\u00de\u00fe"
    for ch in extra_latin:
        _define("math", "mathord", ch, ch)
        _define("text", "textord", ch, ch)


def _normalise_symbols(symbols: dict[str, dict[str, dict[str, str | None]]]) -> dict[str, dict[str, dict[str, str | None]]]:
    """Return a copy of *symbols* with modes and keys sorted for stability."""

    normalised: dict[str, dict[str, dict[str, str | None]]] = {}
    for mode in sorted(symbols.keys()):
        inner = symbols[mode]
        normalised[mode] = {name: inner[name] for name in sorted(inner.keys())}
    return normalised


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    archive = root / "archive.tgz"

    if not archive.is_file():  # pragma: no cover - environment/config error
        raise SystemExit(f"Could not find KaTeX archive at {archive}")

    with tarfile.open(archive, "r:gz") as tf:
        member = next(
            (m for m in tf.getmembers() if m.name.endswith("/src/symbols.js")),
            None,
        )
        if member is None:
            raise SystemExit("Could not find src/symbols.js inside archive.tgz")
        extracted = tf.extractfile(member)
        if extracted is None:
            raise SystemExit("Could not read src/symbols.js from archive.tgz")
        src_text = extracted.read().decode("utf8")

    symbols = _parse_symbols_js(src_text)
    _add_loop_built_symbols(symbols)
    atoms = _default_atoms()
    non_atoms = _default_non_atoms()
    ligatures = _default_ligatures()

    symbols = _normalise_symbols(symbols)

    print("# Auto-generated from KaTeX src/symbols.js - DO NOT EDIT BY HAND")
    print("symbols = ", end="")
    pprint.pprint(symbols, sort_dicts=False)
    print()
    print("ligatures = ", end="")
    pprint.pprint(ligatures, sort_dicts=True)
    print()
    print("ATOMS = ", end="")
    pprint.pprint(atoms, sort_dicts=True)
    print()
    print("NON_ATOMS = ", end="")
    pprint.pprint(non_atoms, sort_dicts=True)


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()
