"""Python port of KaTeX's environments/array.js - array and matrix environments."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union, Dict, Any, cast

from ..build_common import make_fragment, make_line_span, make_span, make_v_list
from ..define_environment import define_environment
from ..mathml_tree import MathNode
from ..parse_error import ParseError
from ..parse_node import assert_node_type, assert_symbol_node_type, check_symbol_node_type
from ..style import Style
from ..token import Token
from ..units import calculate_size, make_em
from ..utils import deflt

if TYPE_CHECKING:
    from ..parser import Parser
    from ..parse_node import ParseNode, OrdgroupParseNode, AccentTokenParseNode
    from ..options import Options

# Type definitions
AlignSpec = Union[
    Dict[str, str],  # {"type": "separator", "separator": "|"}
    Dict[str, Any],  # {"type": "align", "align": "c", "pregap": float, "postgap": float}
]

ColSeparationType = str  # "align" | "alignat" | "gather" | "small" | "CD"


def get_hlines(parser: Parser) -> List[bool]:
    """Get horizontal lines (\hline, \hdashline) info."""
    hline_info = []
    parser.consume_spaces()

    nxt = parser.fetch().text
    if nxt == "\\relax":
        parser.consume()
        parser.consume_spaces()
        nxt = parser.fetch().text

    while nxt in ("\\hline", "\\hdashline"):
        parser.consume()
        hline_info.append(nxt == "\\hdashline")
        parser.consume_spaces()
        nxt = parser.fetch().text

    return hline_info


def validate_ams_environment_context(context) -> None:
    """Validate that AMS environments are used in display mode."""
    settings = context["parser"].settings
    if not settings.display_mode:
        raise ParseError(f"{{{context['envName']}}} can be used only in display mode.")


def get_auto_tag(name: str) -> Optional[bool]:
    """Get auto-tagging behavior for environment name."""
    if "ed" not in name:
        return "*" not in name
    return None


def d_cell_style(env_name: str) -> str:
    """Get cell style for environment (display or text)."""
    return "display" if env_name.startswith("d") else "text"


def parse_array(
    parser: Parser,
    config: Dict[str, Any],
    style: str,
) -> ParseNode:
    """Parse array environment with rows and columns."""
    parser.gullet.begin_group()

    if not config.get("singleRow"):
        parser.gullet.macros.set("\\cr", "\\\\\\relax")

    # Get arraystretch
    arraystretch = config.get("arraystretch")
    if arraystretch is None:
        stretch = parser.gullet.expand_macro_as_text("\\arraystretch")
        if stretch is None:
            arraystretch = 1
        else:
            arraystretch = float(stretch)
            if not arraystretch or arraystretch < 0:
                raise ParseError(f"Invalid \\arraystretch: {stretch}")

    parser.gullet.begin_group()

    row = []
    body = [row]
    row_gaps = []
    h_lines_before_row = []

    tags = [] if config.get("autoTag") is not None else None

    def begin_row():
        if config.get("autoTag"):
            parser.gullet.macros.set("\\@eqnsw", "1", True)

    def end_row():
        if tags is not None:
            if parser.gullet.macros.get("\\df@tag"):
                tags.append(parser.subparse([Token("\\df@tag")]))
                parser.gullet.macros.set("\\df@tag", None, True)
            else:
                tags.append(bool(config.get("autoTag")) and
                          parser.gullet.macros.get("\\@eqnsw") == "1")

    begin_row()
    h_lines_before_row.append(get_hlines(parser))

    while True:
        # Parse each cell in its own group (namespace)
        cell = parser.parse_expression(False, "\\end" if config.get("singleRow") else "\\\\")
        parser.gullet.end_group()
        parser.gullet.begin_group()

        cell = {
            "type": "ordgroup",
            "mode": parser.mode,
            "body": cell,
        }
        if style:
            cell = {
                "type": "styling",
                "mode": parser.mode,
                "style": style,
                "body": [cell],
            }
        row.append(cell)

        next_token = parser.fetch().text
        if next_token == "&":
            if config.get("maxNumCols") and len(row) == config["maxNumCols"]:
                if config.get("singleRow") or config.get("colSeparationType"):
                    raise ParseError("Too many tab characters: &", parser.next_token)
                else:
                    parser.settings.report_nonstrict("textEnv",
                        "Too few columns specified in the {array} column argument.")
            parser.consume()
        elif next_token == "\\end":
            end_row()
            # Arrays terminate newlines with `\crcr` which consumes a `\cr` if
            # the last line is empty.  However, AMS environments keep the
            # empty row if it's the only one.
            # NOTE: Currently, `cell` is the last item added into `row`.
            if (len(row) == 1 and cell["type"] == "styling" and
                len(cell["body"][0]["body"]) == 0 and
                (len(body) > 1 or not config.get("emptySingleRow"))):
                body.pop()
            if len(h_lines_before_row) < len(body) + 1:
                h_lines_before_row.append([])
            break
        elif next_token == "\\\\":
            parser.consume()
            # Parse optional size argument [size]
            size = parser.parse_size_group(True) if parser.gullet.future().text != " " else None
            row_gaps.append(size["value"] if size else None)
            end_row()

            # Check for \hline(s) following the row separator
            h_lines_before_row.append(get_hlines(parser))
            row = []
            body.append(row)
            begin_row()
        else:
            raise ParseError("Expected & or \\\\ or \\cr or \\end", parser.next_token)

    parser.gullet.end_group()
    parser.gullet.end_group()

    return {
        "type": "array",
        "mode": parser.mode,
        "addJot": config.get("addJot"),
        "arraystretch": arraystretch,
        "body": body,
        "cols": config.get("cols"),
        "rowGaps": row_gaps,
        "hskipBeforeAndAfter": config.get("hskipBeforeAndAfter"),
        "hLinesBeforeRow": h_lines_before_row,
        "colSeparationType": config.get("colSeparationType"),
        "tags": tags,
        "leqno": config.get("leqno"),
    }


def html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for array environments."""
    from .. import build_html as html
    from ..parse_node import ArrayParseNode
    from typing import cast

    array_group = cast(ArrayParseNode, group)

    nr = len(array_group["body"])
    h_lines_before_row = array_group["hLinesBeforeRow"]
    nc = 0
    body = [None] * nr
    hlines = []

    rule_thickness = max(options.font_metrics().get("arrayRuleWidth", 0.04),
                        options.min_rule_thickness)

    # Horizontal spacing
    pt = 1 / options.font_metrics().get("ptPerEm", 10)
    arraycolsep = 5 * pt  # default value

    if array_group.get("colSeparationType") == "small":
        local_multiplier = options.having_style(Style.SCRIPT).size_multiplier
        arraycolsep = 0.2778 * (local_multiplier / options.size_multiplier)

    # Vertical spacing
    baselineskip = calculate_size({"number": 3, "unit": "ex"}, options) \
                   if array_group.get("colSeparationType") == "CD" else 12 * pt
    jot = 3 * pt
    arrayskip = array_group.get("arraystretch", 1) * baselineskip
    arstrut_height = 0.7 * arrayskip
    arstrut_depth = 0.3 * arrayskip

    total_height = 0

    def set_hline_pos(hlines_in_gap: List[bool]):
        nonlocal total_height
        for i, is_dashed in enumerate(hlines_in_gap):
            if i > 0:
                total_height += 0.25
            hlines.append({"pos": total_height, "isDashed": is_dashed})

    set_hline_pos(h_lines_before_row[0])

    for r in range(nr):
        inrow = array_group["body"][r]
        height = arstrut_height
        depth = arstrut_depth

        if nc < len(inrow):
            nc = len(inrow)

        outrow = [None] * len(inrow)
        for c, elt in enumerate(inrow):
            outrow[c] = html.build_group(elt, options)
            depth = max(depth, outrow[c].depth)
            height = max(height, outrow[c].height)

        row_gap = array_group.get("rowGaps", [None])[r]
        gap = 0
        if row_gap:
            gap = calculate_size(row_gap, options)
            if gap > 0:
                gap += arstrut_depth
                if depth < gap:
                    depth = gap
                gap = 0

        if array_group.get("addJot"):
            depth += jot

        outrow.extend([height, depth, total_height + height])
        total_height += height + depth + gap
        body[r] = outrow

        set_hline_pos(h_lines_before_row[r + 1])

    offset = total_height / 2 + options.font_metrics().get("axisHeight", 0)
    col_descriptions = array_group.get("cols", [])

    # Build columns with spacing and alignment
    cols = []
    col_sep = None

    for c, col_descr in enumerate(col_descriptions):
        if col_descr.get("type") == "separator":
            if col_descr.get("separator") in "|:":
                line_type = "solid" if col_descr["separator"] == "|" else "dashed"
                separator = make_span(["vertical-separator"], [], options)
                separator.style["height"] = make_em(total_height)
                separator.style["borderRightWidth"] = make_em(rule_thickness)
                separator.style["borderRightStyle"] = line_type
                separator.style["margin"] = f"0 {make_em(-rule_thickness / 2)}"
                shift = total_height - offset
                if shift:
                    separator.style["verticalAlign"] = make_em(-shift)
                cols.append(separator)
        else:
            # Regular column
            if c > 0 or array_group.get("hskipBeforeAndAfter"):
                sepwidth = deflt(col_descr.get("pregap"), arraycolsep)
                if sepwidth != 0:
                    col_sep = make_span(["arraycolsep"], [])
                    col_sep.style["width"] = make_em(sepwidth)
                    cols.append(col_sep)

            col = []
            for r in range(nr):
                row = body[r]
                elem = row[c]
                if elem:
                    shift = row[-1] - offset  # pos - offset
                    elem.depth = row[-2]  # depth
                    elem.height = row[-3]  # height
                    col.append({"type": "elem", "elem": elem, "shift": shift})

            col_vlist = make_v_list({
                "positionType": "individualShift",
                "children": col,
            }, options)
            col_vlist = make_span([f"col-align-{col_descr.get('align', 'c')}"], [col_vlist])
            cols.append(col_vlist)

            if c < nc - 1 or array_group.get("hskipBeforeAndAfter"):
                sepwidth = deflt(col_descr.get("postgap"), arraycolsep)
                if sepwidth != 0:
                    col_sep = make_span(["arraycolsep"], [])
                    col_sep.style["width"] = make_em(sepwidth)
                    cols.append(col_sep)

    table_body = make_span(["mtable"], cols)

    # Add \hline(s), if any.
    if hlines:
        line = make_line_span("hline", options, rule_thickness)
        dashes = make_line_span("hdashline", options, rule_thickness)
        v_list_elems = [{"type": "elem", "elem": table_body, "shift": 0}]

        for hline in reversed(hlines):
            line_shift = hline["pos"] - offset
            elem = dashes if hline["isDashed"] else line
            v_list_elems.append({"type": "elem", "elem": elem, "shift": line_shift})

        table_body = make_v_list({
            "positionType": "individualShift",
            "children": v_list_elems,
        }, options)

    if array_group.get("tags") and any(array_group["tags"]):
        # An environment with manual tags and/or automatic equation numbers.
        # Create node(s), the latter of which trigger CSS counter increment.
        tag_spans = []
        for r in range(nr):
            rw = body[r]
            shift = rw.pos - offset
            tag = array_group["tags"][r]
            tag_span = None
            if tag is True:  # automatic numbering
                tag_span = make_span(["eqn-num"], [], options)
            elif tag is False:
                # \nonumber/\notag or starred environment
                tag_span = make_span([], [], options)
            else:  # manual \tag
                tag_span = make_span([],
                    html.build_expression(tag, options, True), options)
            tag_span.depth = rw.depth
            tag_span.height = rw.height
            tag_spans.append({"type": "elem", "elem": tag_span, "shift": shift})

        eqn_num_col = make_v_list({
            "positionType": "individualShift",
            "children": tag_spans,
        }, options)
        eqn_num_col = make_span(["tag"], [eqn_num_col], options)
        return make_fragment([table_body, eqn_num_col])
    else:
        return make_span(["mord"], [table_body], options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for array environments."""
    from .. import build_mathml as mml
    from ..parse_node import ArrayParseNode
    from typing import cast

    array_group = cast(ArrayParseNode, group)

    tbl = []
    glue = MathNode("mtd", [], ["mtr-glue"])
    tag = MathNode("mtd", [], ["mml-eqn-num"])

    for i, rw in enumerate(array_group["body"]):
        row = []
        for j, cell in enumerate(rw):
            row.append(MathNode("mtd", [mml.build_group(cell, options)]))

        if array_group.get("tags") and array_group["tags"][i]:
            row.insert(0, glue)
            row.append(glue)
            if array_group.get("leqno"):
                row.insert(0, tag)
            else:
                row.append(tag)

        tbl.append(MathNode("mtr", row))

    table = MathNode("mtable", tbl)

    # Set row spacing
    arraystretch = array_group.get("arraystretch", 1)
    gap = (0.1 if arraystretch == 0.5  # smallmatrix, subarray
           else 0.16 + arraystretch - 1 + (0.09 if array_group.get("addJot") else 0))
    table.set_attribute("rowspacing", make_em(gap))

    # Set column alignment and lines
    if array_group.get("cols"):
        cols = array_group["cols"]
        align = ""
        column_lines = ""
        prev_type_was_align = False

        for col in cols:
            if col.get("type") == "align":
                align += {"c": "center ", "l": "left ", "r": "right "}.get(col.get("align", "c"), "center ")
                if prev_type_was_align:
                    column_lines += "none "
                prev_type_was_align = True
            elif col.get("type") == "separator":
                if prev_type_was_align:
                    column_lines += "solid " if col.get("separator") == "|" else "dashed "
                    prev_type_was_align = False

        table.set_attribute("columnalign", align.rstrip())
        if any(c in column_lines for c in "sd"):
            table.set_attribute("columnlines", column_lines.rstrip())

    # Set column spacing
    col_sep_type = array_group.get("colSeparationType")
    if col_sep_type == "align":
        spacing = ""
        cols = array_group.get("cols", [])
        for i in range(1, len(cols)):
            spacing += "0em " if i % 2 else "1em "
        table.set_attribute("columnspacing", spacing.rstrip())
    elif col_sep_type in ("alignat", "gather"):
        table.set_attribute("columnspacing", "0em")
    elif col_sep_type == "small":
        table.set_attribute("columnspacing", "0.2778em")
    elif col_sep_type == "CD":
        table.set_attribute("columnspacing", "0.5em")
    else:
        table.set_attribute("columnspacing", "1em")

    # Handle horizontal lines
    hlines = array_group.get("hLinesBeforeRow", [])
    row_lines = ""

    for i in range(1, len(hlines) - 1):
        if not hlines[i]:
            row_lines += "none "
        else:
            row_lines += "dashed " if hlines[i][0] else "solid "

    if any(c in row_lines for c in "sd"):
        table.set_attribute("rowlines", row_lines.rstrip())

    # Handler functions (defined before usage)


def _array_handler(context, args, is_darray) -> ParseNode:
    """Handler for array and darray environments."""
    from ..parse_node import assert_node_type

    sym_node = check_symbol_node_type(args[0])
    colalign = ([args[0]] if sym_node else
                cast("OrdgroupParseNode", assert_node_type(args[0], "ordgroup"))["body"])

    cols = []
    for nde in colalign:
        node = assert_symbol_node_type(nde)
        if node is None:
            raise ParseError("Expected symbol node", nde)
        ca = cast("AccentTokenParseNode", node)["text"]
        if ca in "lcr":
            cols.append({"type": "align", "align": ca})
        elif ca == "|":
            cols.append({"type": "separator", "separator": "|"})
        elif ca == ":":
            cols.append({"type": "separator", "separator": ":"})
        else:
            raise ParseError(f"Unknown column alignment: {ca}", nde)

    style = d_cell_style(context["envName"])
    return parse_array(context["parser"], {
        "cols": cols,
        "hskipBeforeAndAfter": True,
        "maxNumCols": len(cols),
    }, style)


def _matrix_handler(context) -> ParseNode:
    """Handler for matrix environments."""
    env_name = context["envName"]
    base_name = env_name.replace("*", "")

    delimiters = {
        "matrix": None,
        "pmatrix": ["(", ")"],
        "bmatrix": ["[", "]"],
        "Bmatrix": ["\\{", "\\}"],
        "vmatrix": ["|", "|"],
        "Vmatrix": ["\\Vert", "\\Vert"],
    }[base_name]

    col_align = "c"
    payload = {
        "hskipBeforeAndAfter": False,
        "cols": [{"type": "align", "align": col_align}],
    }

    if env_name.endswith("*"):
        # Parse optional alignment argument
        parser = context["parser"]
        parser.consume_spaces()
        if parser.fetch().text == "[":
            parser.consume()
            parser.consume_spaces()
            col_align = parser.fetch().text
            if col_align not in "lcr":
                raise ParseError("Expected l or c or r", parser.next_token)
            parser.consume()
            parser.consume_spaces()
            parser.expect("]")
            parser.consume()
            payload["cols"] = [{"type": "align", "align": col_align}]

    res = parse_array(context["parser"], payload, d_cell_style(env_name))

    # Populate cols with correct number
    num_cols = max((len(row) for row in res["body"]), default=0)
    res["cols"] = [{"type": "align", "align": col_align}] * num_cols

    if delimiters:
        return {
            "type": "leftright",
            "mode": context["mode"],
            "body": [res],
            "left": delimiters[0],
            "right": delimiters[1],
            "rightColor": None,
        }
    else:
        return res


def _aligned_handler(context) -> ParseNode:
    """Handler for AMS math environments (aligned, align, gathered, alignat, split)."""
    env_name = context["envName"]

    validate_ams_environment_context(context)

    cols: List[AlignSpec] = []
    separation_type = "alignat" if "at" in env_name else "align"
    is_split = env_name == "split"

    res = parse_array(context["parser"], {
        "cols": cols,
        "addJot": True,
        "autoTag": None if is_split else get_auto_tag(env_name),
        "emptySingleRow": True,
        "colSeparationType": separation_type,
        "maxNumCols": 2 if is_split else None,
        "leqno": context["parser"].settings.leqno,
    }, "display")

    # Determining number of columns
    num_maths = None
    num_cols = 0
    empty_group = {
        "type": "ordgroup",
        "mode": context["mode"],
        "body": [],
    }

    # Parse optional argument for alignat
    if "at" in env_name:
        # For alignat, first argument specifies number of alignment points
        # alignat{3} creates 6 columns (3 pairs of equation + relation)
        pass  # Simplified for now

    is_aligned = num_cols == 0

    # Process each row to add empty groups for binary operators
    for row in res["body"]:
        for i in range(1, len(row), 2):
            if i < len(row):
                styling = row[i]
                if styling.get("type") == "styling":
                    ordgroup = styling["body"][0]
                    if ordgroup.get("type") == "ordgroup":
                        ordgroup["body"].insert(0, empty_group)

        # Count columns
        if not is_aligned:
            if num_maths and len(row) // 2 > num_maths:
                raise ParseError(
                    f"Too many math in a row: expected {num_maths}, but got {len(row) // 2}",
                    row[0] if row else None
                )
        else:
            if num_cols < len(row):
                num_cols = len(row)

    # Adjust alignment
    if is_aligned:
        # In aligned mode, add \qquad between columns
        for i in range(num_cols):
            align = "r" if i % 2 == 1 else "l"
            pregap = 1 if i > 0 and i % 2 == 0 else 0  # \qquad between equations
            cols.append({
                "type": "align",
                "align": align,
                "pregap": pregap,
                "postgap": 0,
            })
        res["colSeparationType"] = "align"
    else:
        res["colSeparationType"] = "alignat"

    return res


def _subarray_handler(context, args) -> ParseNode:
    """Handler for subarray environment."""
    # Parse column alignment argument
    sym_node = check_symbol_node_type(args[0])
    colalign = [args[0]] if sym_node else cast("OrdgroupParseNode", assert_node_type(args[0], "ordgroup"))["body"]

    cols = []
    for nde in colalign:
        node = assert_symbol_node_type(nde)
        if node is None:
            raise ParseError("Expected symbol node", nde)
        ca = cast("AccentTokenParseNode", node)["text"]
        if ca in "lcr":
            cols.append({"type": "align", "align": ca})
        else:
            raise ParseError(f"Unknown column alignment: {ca}", nde)

    return parse_array(context["parser"], {
        "cols": cols,
        "hskipBeforeAndAfter": True,
        "maxNumCols": len(cols),
    }, d_cell_style(context["envName"]))


# Define array environment
define_environment({
    "type": "array",
    "names": ["array"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: _array_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Define darray environment (placeholder - same as array for now)
define_environment({
    "type": "array",
    "names": ["darray"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: _array_handler(context, args, True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Define matrix environments
define_environment({
    "type": "array",
    "names": [
        "matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix",
        "matrix*", "pmatrix*", "bmatrix*", "Bmatrix*", "vmatrix*", "Vmatrix*"
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": _matrix_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Define smallmatrix environment
define_environment({
    "type": "array",
    "names": ["smallmatrix"],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context: parse_array(context["parser"],
                                         {"arraystretch": 0.5}, "script"),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Define AMS math environments
define_environment({
    "type": "array",
    "names": ["aligned", "align", "gathered", "alignat", "split"],
    "props": {
        "numArgs": 0,
    },
    "handler": _aligned_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Define subarray environment
define_environment({
    "type": "array",
    "names": ["subarray"],
    "props": {
        "numArgs": 1,
    },
    "handler": _subarray_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


__all__ = ["parse_array", "html_builder", "mathml_builder"]
