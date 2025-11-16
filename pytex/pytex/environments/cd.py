"""Python port of KaTeX's environments/cd.js - commutative diagram environment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import wrap_fragment
from ..define_function import define_function
from ..dom_tree import DomSpan
from ..mathml_tree import MathNode
from ..parse_error import ParseError
from ..parse_node import AnyParseNode, ParseNode, assert_symbol_node_type
from ..types import BreakToken
from ..units import make_em

if TYPE_CHECKING:
    from ..parser import Parser
    from ..options import Options

# CD arrow function name mapping
CD_ARROW_FUNCTION_NAME = {
    ">": "\\\\cdrightarrow",
    "<": "\\\\cdleftarrow",
    "=": "\\\\cdlongequal",
    "A": "\\uparrow",
    "V": "\\downarrow",
    "|": "\\Vert",
    ".": "no arrow",
}


def new_cell() -> Dict[str, Any]:
    """Create an empty CD cell."""
    return {
        "type": "styling",
        "body": [],
        "mode": "math",
        "style": "display"
    }


def is_start_of_arrow(node: AnyParseNode) -> bool:
    """Check if node is start of arrow (@)."""
    return node.get("type") == "textord" and node.get("text") == "@"


def is_label_end(node: AnyParseNode, end_char: str) -> bool:
    """Check if node ends a label."""
    return ((node.get("type") == "mathord" or node.get("type") == "atom") and
            node.get("text") == end_char)


def cd_arrow(arrow_char: str, labels: List[AnyParseNode], parser: "Parser") -> AnyParseNode:
    """Create a parse tree for an arrow and its labels."""
    func_name = CD_ARROW_FUNCTION_NAME.get(arrow_char, "no arrow")

    if func_name in ("\\cdrightarrow", "\\cdleftarrow"):
        return cast(AnyParseNode, parser.call_function(func_name, [labels[0]], [labels[1]]))
    elif func_name in ("\\uparrow", "\\downarrow"):
        left_label = cast(AnyParseNode, parser.call_function("\\cdleft", [labels[0]], []))
        bare_arrow = {
            "type": "atom",
            "text": func_name,
            "mode": "math",
            "family": "rel",
        }
        sized_arrow = cast(AnyParseNode, parser.call_function("\\Big", [bare_arrow], []))
        right_label = cast(AnyParseNode, parser.call_function("\\cdright", [labels[1]], []))
        arrow_group = {
            "type": "ordgroup",
            "mode": "math",
            "body": [left_label, sized_arrow, right_label],
        }
        return cast(AnyParseNode, parser.call_function("\\cdparent", [arrow_group], []))
    elif func_name == "\\cdlongequal":
        return cast(AnyParseNode, parser.call_function("\\cdlongequal", [], []))
    elif func_name == "\\Vert":
        arrow = {"type": "textord", "text": "\\Vert", "mode": "math"}
        return cast(AnyParseNode, parser.call_function("\\Big", [arrow], []))
    else:
        return cast(AnyParseNode, {"type": "textord", "text": " ", "mode": "math"})


def parse_cd(parser: "Parser") -> ParseNode:
    """Parse a commutative diagram (CD) environment."""
    # Get the array's parse nodes with \\ temporarily mapped to \cr
    parsed_rows: List[List[AnyParseNode]] = []
    parser.gullet.begin_group()
    parser.gullet.macros.set("\\cr", "\\\\\\relax")
    parser.gullet.begin_group()

    while True:
        # Get the parse nodes for the next row
        parsed_rows.append(parser.parse_expression(False, BreakToken.DOUBLE_BACKSLASH))
        parser.gullet.end_group()
        parser.gullet.begin_group()

        next_token = parser.fetch().text
        if next_token in ("&", "\\\\"):
            parser.consume()
        elif next_token == "\\end":
            if len(parsed_rows[-1]) == 0:
                parsed_rows.pop()  # final row ended in \\
            break
        else:
            raise ParseError("Expected \\\\ or \\cr or \\end", parser.next_token)

    row: List[Dict[str, Any]] = []
    body: List[List[Dict[str, Any]]] = [row]

    # Loop through parse nodes, collecting into cells and arrows
    for i, row_nodes in enumerate(parsed_rows):
        # Start a new row
        # Create the first cell
        cell = new_cell()

        j = 0
        while j < len(row_nodes):
            if not is_start_of_arrow(row_nodes[j]):
                # If not an arrow, it goes into a cell
                cell["body"].append(row_nodes[j])
            else:
                # Parse node j is an "@", the start of an arrow
                # Push the cell into row first
                row.append(cell)

                # Now collect parse nodes into an arrow
                # The character after "@" defines the arrow type
                j += 1
                symbol = assert_symbol_node_type(row_nodes[j])
                if symbol is None:
                    raise ParseError("Expected symbol node in CD arrow.", row_nodes[j])
                arrow_char = cast(Dict[str, Any], symbol)["text"]

                # Create two empty label nodes
                labels: List[Dict[str, Any]] = [
                    {"type": "ordgroup", "mode": "math", "body": []},
                    {"type": "ordgroup", "mode": "math", "body": []},
                ]

                # Process the arrow
                if arrow_char in "=|.":
                    # These arrows don't take labels
                    pass
                elif arrow_char in "<>AV":
                    # These arrows take two optional labels
                    for label_num in range(2):
                        in_label = True
                        k = j + 1
                        while k < len(row_nodes):
                            if is_label_end(row_nodes[k], arrow_char):
                                in_label = False
                                j = k
                                break
                            if is_start_of_arrow(row_nodes[k]):
                                raise ParseError(
                                    f"Missing a {arrow_char} character to complete a CD arrow.",
                                    row_nodes[k]
                                )
                            labels[label_num]["body"].append(row_nodes[k])
                            k += 1
                        if in_label:
                            raise ParseError(
                                f"Missing a {arrow_char} character to complete a CD arrow.",
                                row_nodes[j]
                            )
                else:
                    raise ParseError('Expected one of "<>AV=|." after @', row_nodes[j])

                # Join the arrow to its labels
                arrow = cd_arrow(arrow_char, cast(List[AnyParseNode], labels), parser)

                # Wrap the arrow in styling node
                wrapped_arrow = {
                    "type": "styling",
                    "body": [arrow],
                    "mode": "math",
                    "style": "display",  # CD is always displaystyle
                }
                row.append(wrapped_arrow)
                # Create empty cell for upcoming parse nodes
                cell = new_cell()

            j += 1

        if i % 2 == 0:
            # Even-numbered rows: cell, arrow, cell, arrow, ... cell
            row.append(cell)
        else:
            # Odd-numbered rows: vert arrow, empty cell, ... vert arrow
            # Remove the empty cell at the beginning
            row.pop(0)

        row = []
        body.append(row)

    # End row group
    parser.gullet.end_group()
    # End array group defining \\
    parser.gullet.end_group()

    # Define column separation
    cols: List[Dict[str, Any]] = [{
        "type": "align",
        "align": "c",
        "pregap": 0.25,  # CD package sets \enskip between columns
        "postgap": 0.25,  # So pre and post each get half an \enskip, i.e. 0.25em
    }] * len(body[0])

    array_node: Dict[str, Any] = {
        "type": "array",
        "mode": "math",
        "body": body,
        "arraystretch": 1,
        "addJot": True,
        "rowGaps": [None],
        "cols": cols,
        "colSeparationType": "CD",
        "hLinesBeforeRow": [[]] * (len(body) + 1),
        "hskipBeforeAndAfter": False,
        "tags": None,
        "leqno": False,
    }

    return cast(ParseNode, array_node)


# CD label functions for internal use by CD environment
define_function({
    "type": "cdlabel",
    "names": ["\\\\cdleft", "\\\\cdright"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "cdlabel",
        "mode": context["parser"].mode,
        "side": context["funcName"][4:],  # Remove "\\cd" prefix
        "label": args[0],
    },
    "html_builder": lambda group, options: _cdlabel_html_builder(group, options),
    "mathml_builder": lambda group, options: _cdlabel_mathml_builder(group, options),
})

define_function({
    "type": "cdlabelparent",
    "names": ["\\\\cdparent"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "cdlabelparent",
        "mode": context["parser"].mode,
        "fragment": args[0],
    },
    "html_builder": lambda group, options: _cdlabelparent_html_builder(group, options),
    "mathml_builder": lambda group, options: _cdlabelparent_mathml_builder(group, options),
})


def _cdlabel_html_builder(group: Dict[str, Any], options: "Options") -> DomSpan:
    """Build HTML for CD label."""
    from .. import build_html as html

    new_options = options.having_style(options.style.sup())
    label = wrap_fragment(html.build_group(group["label"], new_options), options)
    label.classes.append(f"cd-label-{group['side']}")
    label.style["bottom"] = make_em(0.8 - label.depth)
    # Zero out label height & depth for proper arrow alignment
    label.height = 0
    label.depth = 0
    return cast(DomSpan, label)


def _cdlabel_mathml_builder(group: Dict[str, Any], options: "Options") -> MathNode:
    """Build MathML for CD label."""
    from .. import build_mathml as mml

    label = MathNode("mrow", [mml.build_group(group["label"], options)])
    label = MathNode("mpadded", [label])
    label.set_attribute("width", "0")
    if group["side"] == "left":
        label.set_attribute("lspace", "-1width")
    # Guess at vertical alignment
    label.set_attribute("voffset", "0.7em")
    label = MathNode("mstyle", [label])
    label.set_attribute("displaystyle", "false")
    label.set_attribute("scriptlevel", "1")
    return label


def _cdlabelparent_html_builder(group: Dict[str, Any], options: "Options") -> DomSpan:
    """Build HTML for CD label parent."""
    from .. import build_html as html

    # Wrap the vertical arrow and its labels
    parent = wrap_fragment(html.build_group(group["fragment"], options), options)
    parent.classes.append("cd-vert-arrow")
    return cast(DomSpan, parent)


def _cdlabelparent_mathml_builder(group: Dict[str, Any], options: "Options") -> MathNode:
    """Build MathML for CD label parent."""
    from .. import build_mathml as mml

    return MathNode("mrow", [mml.build_group(group["fragment"], options)])


# Export the parse function
__all__ = ["parse_cd"]
