"""Utility to regenerate pytex.macros_data from KaTeX's macros.js.

This script parses KaTeX's macros.js from the KaTeX sources stored in
archive.tgz (pytex/archive/src/macros.js inside the tarball) and emits a Python
module defining a single global:

    MACROS_DATA: Dict[str, str]

The keys are macro names as seen by the parser; the values are either:

- a macro body string (for simple string macros), or
- the literal string "<function macro>" for macros that are implemented
  manually in pytex.macros, or
- the literal string "<unparsed macro>" for complex function-style
  macros that are not yet ported.

Usage (from the pytex project root):

    poetry run python -m pytex.generate_macros_data > pytex/macros_data.py

As with generate_symbols_data, this script is intended as a small,
re-runnable tool to keep the Python data in sync with KaTeX's source,
not something used at runtime.
"""

from __future__ import annotations

import pprint
import re
import tarfile
from pathlib import Path

_JS_STRING_RE = re.compile(r"^(['\"])(.*)\1$", re.DOTALL)


def _parse_js_string_literal(src: str) -> str | None:
    """Parse a restricted JS string literal into a Python str.

    Returns None if *src* is not a simple quoted literal.
    """

    text = src.strip()
    m = _JS_STRING_RE.match(text)
    if not m:
        return None
    _quote, body = m.groups()
    result_chars: list[str] = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            result_chars.append(ch)
            i += 1
            continue

        # Escape sequence
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
                # Keep sequence literally on parse error
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


def _split_args(arg_src: str) -> list[str]:
    """Split a defineMacro argument list into individual argument strings.

    This is a minimal JS argument splitter that understands strings and
    balanced (), [], {}. It is sufficient for KaTeX's defineMacro calls.
    """

    args: list[str] = []
    buf: list[str] = []
    stack: list[str] = []
    in_string: str | None = None
    escape = False

    for ch in arg_src:
        if in_string is not None:
            buf.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ("'", '"', "`"):
                in_string = ch
                buf.append(ch)
            elif ch in "([{":
                stack.append(ch)
                buf.append(ch)
            elif ch in ")]}":
                if stack:
                    stack.pop()
                buf.append(ch)
            elif ch == "," and not stack:
                arg = "".join(buf).strip()
                if arg:
                    args.append(arg)
                buf = []
            else:
                buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        args.append(tail)
    return args


def _extract_define_macro_calls(src: str) -> list[tuple[str, str]]:
    """Extract (name_src, body_src) pairs from macros.js source.

    *name_src* and *body_src* are raw JS expressions for the first two
    defineMacro arguments; both still need to be parsed.
    """

    calls: list[tuple[str, str]] = []
    needle = "defineMacro"
    i = 0
    n = len(src)

    while True:
        idx = src.find(needle, i)
        if idx == -1:
            break

        # Find the opening parenthesis
        j = idx + len(needle)
        while j < n and src[j].isspace():
            j += 1
        if j >= n or src[j] != "(":
            i = j
            continue

        # Walk until the matching closing parenthesis
        depth = 1
        in_string: str | None = None
        escape = False
        k = j + 1
        while k < n and depth > 0:
            ch = src[k]
            if in_string is not None:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == in_string:
                    in_string = None
            else:
                if ch in ("'", '"', "`"):
                    in_string = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            k += 1

        inner = src[j + 1 : k - 1]
        args = _split_args(inner)
        if len(args) >= 2:
            name_src = args[0].strip()
            body_src = args[1].strip()
            calls.append((name_src, body_src))

        i = k

    return calls


# Macros with dedicated Python implementations in pytex.macros.
_FUNCTION_MACROS = {
    "\\noexpand",
    "\\expandafter",
    "\\@firstoftwo",
    "\\@secondoftwo",
    "\\@ifnextchar",
    "\\TextOrMath",
    "\\char",
    "\\dots",
    "\\dotso",
    "\\dotsc",
    "\\cdots",
}


def _parse_macros_js(src_text: str) -> dict[str, str]:
    """Parse KaTeX's macros.js into a MACROS_DATA-style dict.

    For each defineMacro(name, value) call we:

    - parse *name* as a JS string literal to get the macro name; and
    - attempt to parse *value* as a simple string literal.

    If *value* is a function expression (or otherwise not a simple
    literal), we record either "<function macro>" (for macros that have
    Python implementations) or "<unparsed macro>".
    """

    macros: dict[str, str] = {}

    for name_src, body_src in _extract_define_macro_calls(src_text):
        name = _parse_js_string_literal(name_src)
        if name is None:
            continue

        candidate = body_src.strip()
        body: str | None

        is_function = (
            candidate.startswith("function")
            or "=>" in candidate
        )

        if is_function:
            body = None
        else:
            body = _parse_js_string_literal(candidate)

        if body is None:
            if name in _FUNCTION_MACROS:
                macros[name] = "<function macro>"
            else:
                macros[name] = "<unparsed macro>"
        else:
            macros[name] = body

    return macros


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    archive = root / "archive.tgz"

    if not archive.is_file():  # pragma: no cover - environment/config error
        raise SystemExit(f"Could not find KaTeX archive at {archive}")

    with tarfile.open(archive, "r:gz") as tf:
        member = next(
            (m for m in tf.getmembers() if m.name.endswith("/src/macros.js")),
            None,
        )
        if member is None:
            raise SystemExit("Could not find src/macros.js inside archive.tgz")
        extracted = tf.extractfile(member)
        if extracted is None:
            raise SystemExit("Could not read src/macros.js from archive.tgz")
        src_text = extracted.read().decode("utf8")

    macros = _parse_macros_js(src_text)
    macros = dict(sorted(macros.items(), key=lambda kv: kv[0]))

    print("# Auto-generated from KaTeX src/macros.js - DO NOT EDIT BY HAND")
    print("MACROS_DATA = ", end="")
    pprint.pprint(macros, sort_dicts=False)


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()
