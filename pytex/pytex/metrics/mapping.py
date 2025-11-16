#!/usr/bin/env python3

"""Convert TeX to KaTeX font mapping data into JSON.

This module replaces the legacy ``mapping.pl`` script by parsing the existing
mapping definitions and emitting the same JSON payload that downstream tools
expect.

The Perl file is treated as a static data source; no Perl interpreter is
required.  The parsed output matches the structure produced by the original
script:

    {
        "Font-Style": {
            "targetCodePoint": {
                "font": "<tex font>",
                "char": <tex char code>,
                "xshift": <int>,
                "yshift": <int>
            },
            ...
        },
        ...
    }

The conversion process mirrors the Perl implementation:

1. Parse the ``$map{...}`` blocks into an intermediate representation.
2. Reconstruct the reverse lookup organised by KaTeX font/style.
3. Expand ranges and glyph shifts to produce the final mapping.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple, Union
from typing import TypedDict


ROOT = Path(__file__).parent
DATA_FILE = ROOT / "mapping.pl"


@dataclass(frozen=True)
class Range:
    """Inclusive range of character codes."""

    start: int
    end: int

    def expand(self) -> Iterable[int]:
        return range(self.start, self.end + 1)


GlyphSource = Union[int, Range]
GlyphTarget = Union[int, Tuple[int, int, int]]
MappingEntry = Tuple[GlyphSource, GlyphTarget]


class MappingMetadata(TypedDict):
    font: str
    char: int
    xshift: int
    yshift: int


class MappingParseError(RuntimeError):
    """Raised when the legacy mapping data cannot be parsed."""


def _extract_block(text: str, start_index: int, opener: str, closer: str) -> Tuple[str, int]:
    depth = 0
    index = start_index
    while index < len(text):
        char = text[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                # Exclude the outer delimiters.
                return text[start_index + 1 : index], index + 1
        index += 1
    raise MappingParseError(f"Unclosed block starting at {start_index} for {opener}{closer}")


def _skip_ws_and_comments(text: str, index: int) -> int:
    length = len(text)
    while index < length:
        char = text[index]
        if char in " \t\r\n":
            index += 1
            continue
        if char == "#":
            while index < length and text[index] != "\n":
                index += 1
            continue
        break
    return index


def _parse_number(fragment: str, index: int) -> Tuple[int, int]:
    match = re.match(r"-?(?:0x[0-9A-Fa-f]+|\d+)", fragment[index:])
    if not match:
        raise MappingParseError(f"Expected number at position {index}: {fragment[index:index+20]!r}")
    token = match.group(0)
    base = 16 if token.lower().startswith("0x") else 10
    value = int(token, base)
    return value, index + len(token)


def _parse_value(fragment: str, index: int) -> Tuple[Union[int, Tuple[int, ...]], int]:
    index = _skip_ws_and_comments(fragment, index)
    if index >= len(fragment):
        raise MappingParseError("Unexpected end of fragment while parsing value")

    if fragment[index] == "[":
        items: List[int] = []
        index += 1
        while True:
            index = _skip_ws_and_comments(fragment, index)
            if index >= len(fragment):
                raise MappingParseError("Unterminated array literal")
            if fragment[index] == "]":
                index += 1
                break
            number, index = _parse_number(fragment, index)
            items.append(number)
            index = _skip_ws_and_comments(fragment, index)
            if index < len(fragment) and fragment[index] == ",":
                index += 1
        return tuple(items), index

    value, index = _parse_number(fragment, index)
    return value, index


def _parse_entry_pairs(fragment: str) -> List[MappingEntry]:
    entries: List[MappingEntry] = []
    index = 0
    length = len(fragment)

    while True:
        index = _skip_ws_and_comments(fragment, index)
        if index >= length:
            break

        left, index = _parse_value(fragment, index)
        index = _skip_ws_and_comments(fragment, index)
        if fragment[index : index + 2] != "=>":
            raise MappingParseError(f"Expected '=>' after left value at position {index}")
        index += 2

        right, index = _parse_value(fragment, index)
        entries.append((_normalize_source(left), _normalize_target(right)))

        index = _skip_ws_and_comments(fragment, index)
        if index < length and fragment[index] == ",":
            index += 1

    return entries


def _normalize_source(raw: Union[int, Tuple[int, ...]]) -> GlyphSource:
    if isinstance(raw, int):
        return raw
    if len(raw) != 2:
        raise MappingParseError(f"Source ranges must contain exactly 2 values, found {raw}")
    return Range(raw[0], raw[1])


def _normalize_target(raw: Union[int, Tuple[int, ...]]) -> GlyphTarget:
    if isinstance(raw, int):
        return raw
    if len(raw) != 3:
        raise MappingParseError(f"Glyph target adjustments require 3 values, found {raw}")
    return raw[0], raw[1], raw[2]


def _parse_map_definitions(content: str) -> Dict[str, Dict[str, List[MappingEntry]]]:
    map_data: Dict[str, Dict[str, List[MappingEntry]]] = {}
    block_pattern = re.compile(r"\$map\{([^}]+)\}\s*=\s*\{", re.MULTILINE)
    search_index = 0

    while True:
        match = block_pattern.search(content, search_index)
        if not match:
            break
        cmfont = match.group(1).strip()
        block_start = match.end() - 1  # position of the opening brace
        block_body, next_index = _extract_block(content, block_start, "{", "}")
        map_data[cmfont] = _parse_font_block(block_body)
        search_index = next_index

    if not map_data:
        raise MappingParseError("No mapping definitions found in mapping.pl")

    return map_data


def _parse_font_block(body: str) -> Dict[str, List[MappingEntry]]:
    fonts: Dict[str, List[MappingEntry]] = {}
    entry_pattern = re.compile(r'"([^\"]+)"\s*=>\s*\[', re.MULTILINE)
    search_index = 0

    while True:
        match = entry_pattern.search(body, search_index)
        if not match:
            break
        mjfont = match.group(1)
        list_start = match.end() - 1
        list_body, next_index = _extract_block(body, list_start, "[", "]")
        fonts[mjfont] = _parse_entry_pairs(list_body)
        search_index = next_index

    return fonts


def _family_and_style(font_descriptor: str) -> Tuple[str, str]:
    if "-" in font_descriptor:
        family, style = font_descriptor.split("-", 1)
        style = style or "Regular"
    else:
        family, style = font_descriptor, "Regular"
    return family, style


def _expand_entries(cmfont: str, entries: Sequence[MappingEntry]) -> Iterator[Tuple[int, MappingMetadata]]:
    for source, target in entries:
        if isinstance(source, Range):
            sources = list(source.expand())
        else:
            sources = [source]

        for offset, tex_char in enumerate(sources):
            if isinstance(target, tuple):
                base_code, xshift, yshift = target
                code_point = base_code + offset
            else:
                code_point = target + offset
                xshift = 0
                yshift = 0

            yield code_point, {
                "font": cmfont,
                "char": tex_char,
                "xshift": xshift,
                "yshift": yshift,
            }


def _build_mapping(map_data: Dict[str, Dict[str, List[MappingEntry]]]) -> Dict[str, Dict[int, MappingMetadata]]:
    reverse: Dict[str, Dict[str, List[MappingEntry]]] = {}
    for cmfont, font_map in map_data.items():
        for descriptor, entries in font_map.items():
            family, style = _family_and_style(descriptor)
            fontname = f"{family}-{style}"
            reverse.setdefault(fontname, {}).setdefault(cmfont, []).extend(entries)

    output: Dict[str, Dict[int, MappingMetadata]] = {}
    for mjfont, cmfonts in reverse.items():
        font_output = output.setdefault(mjfont, {})
        for cmfont, entries in cmfonts.items():
            for code_point, metadata in _expand_entries(cmfont, entries):
                if code_point in font_output:
                    previous = font_output[code_point]
                    raise MappingParseError(
                        "Duplicate mapping for "
                        f"{mjfont} code point {code_point:#x}: {previous} vs {metadata}"
                    )
                font_output[code_point] = metadata

    return output


def load_mapping() -> Dict[str, Dict[int, MappingMetadata]]:
    content = DATA_FILE.read_text(encoding="utf-8")
    map_data = _parse_map_definitions(content)
    return _build_mapping(map_data)


def main() -> None:
    mapping = load_mapping()
    json.dump(mapping, sys.stdout, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    main()
