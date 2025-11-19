"""Python port of KaTeX's buildHTML.js - HTML output generation."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .build_common import make_span, try_combine_chars
from .dom_tree import Anchor, DomSpan, HtmlDomNode, Span
from .parse_error import ParseError
from .style import Style
from .tree import DocumentFragment
from .units import Measurement, make_em

# Placeholder imports
try:
    from .define_function import _htmlGroupBuilders as group_builders
except ImportError:  # pragma: no cover - fallback path
    from .define_function import HTML_GROUP_BUILDERS as group_builders

try:
    from .spacing_data import SPACINGS, TIGHT_SPACINGS
except ImportError:  # pragma: no cover - fallback path
    SPACINGS = {}
    TIGHT_SPACINGS = {}

if TYPE_CHECKING:
    from .options import Options
    from .parse_node import AnyParseNode

# Binary atoms (first class `mbin`) change into ordinary atoms (`mord`)
# depending on their surroundings. See TeXbook pg. 442-446, Rules 5 and 6,
# and the text before Rule 19.
BIN_LEFT_CANCELLER = ["leftmost", "mbin", "mopen", "mrel", "mop", "mpunct"]
BIN_RIGHT_CANCELLER = ["rightmost", "mrel", "mclose", "mpunct"]

STYLE_MAP = {
    "display": Style.DISPLAY,
    "text": Style.TEXT,
    "script": Style.SCRIPT,
    "scriptscript": Style.SCRIPTSCRIPT,
}

Side = str  # "left" | "right"

DOM_ENUM = {
    "mord": "mord",
    "mop": "mop",
    "mbin": "mbin",
    "mrel": "mrel",
    "mopen": "mopen",
    "mclose": "mclose",
    "mpunct": "mpunct",
    "minner": "minner",
}

DomType = str


def build_expression(
    expression: list[AnyParseNode],
    options: Options,
    is_real_group: bool | str,
    surrounding: list[DomType | None] | None = None,
) -> list[HtmlDomNode]:
    """Build HTML nodes from parse nodes."""
    if surrounding is None:
        surrounding = [None, None]

    # Parse expressions into groups
    groups: list[HtmlDomNode] = []
    for expr in expression:
        output = build_group(expr, options)
        if isinstance(output, DocumentFragment):
            groups.extend(cast(list[HtmlDomNode], list(output.children)))
        else:
            groups.append(output)

    # Combine consecutive symbolNodes into a single symbolNode
    try_combine_chars(groups)

    # If expression is a partial group, let parent handle spacings
    if not is_real_group:
        return groups

    glue_options: Options = options
    if len(expression) == 1:
        node = expression[0]
        if isinstance(node, dict):
            node_type = node.get("type")
            if node_type == "sizing":
                size_val = node.get("size")
                if isinstance(size_val, int):
                    glue_options = options.having_size(size_val)
            elif node_type == "styling":
                style_name = node.get("style")
                if isinstance(style_name, str):
                    style = STYLE_MAP.get(style_name)
                    if style is not None:
                        glue_options = options.having_style(style)

    # Dummy spans for determining spacings
    dummy_prev = make_span([surrounding[0] or "leftmost"], [], options)
    dummy_next = make_span([surrounding[1] or "rightmost"], [], options)

    # Perform bin cancellation
    is_root = (is_real_group == "root")
    traverse_non_space_nodes(
        groups,
        lambda node, prev: (
            setattr(prev, "classes", prev.classes[:1] + ["mord"])
            if (prev.classes and prev.classes[0] == "mbin" and BIN_RIGHT_CANCELLER.count(node.classes[0]) > 0)
            else setattr(node, "classes", node.classes[:1] + ["mord"])
            if (node.classes and node.classes[0] == "mbin" and BIN_LEFT_CANCELLER.count(prev.classes[0]) > 0)
            else None
        ),
        {"node": dummy_prev},
        dummy_next,
        is_root,
    )

    # Insert spacing
    def _spacing_cb(node: HtmlDomNode, prev_node: HtmlDomNode) -> HtmlDomNode | None:
        left_type = get_type_of_dom_tree(prev_node)
        right_type = get_type_of_dom_tree(node)
        if not left_type or not right_type:
            return None

        table = TIGHT_SPACINGS if node.has_class("mtight") else SPACINGS
        row = table.get(left_type)
        if not row:
            return None
        space = row.get(right_type)
        if space is None:
            return None

        return build_common_make_glue(space, glue_options)

    traverse_non_space_nodes(
        groups,
        _spacing_cb,
        {"node": dummy_prev},
        dummy_next,
        is_root,
    )

    return groups


def traverse_non_space_nodes(
    nodes: list[HtmlDomNode],
    callback: Callable[[HtmlDomNode, HtmlDomNode], HtmlDomNode | None],
    prev: dict[str, Any],
    next_node: HtmlDomNode | None,
    is_root: bool,
) -> None:
    """Depth-first traverse non-space nodes."""
    if next_node:
        nodes.append(next_node)

    i = 0
    while i < len(nodes):
        node = nodes[i]
        partial_group = check_partial_group(node)

        if partial_group:
            # Recursive DFS on a copy of children list for type safety
            child_nodes = cast(list[HtmlDomNode], list(partial_group.children))
            traverse_non_space_nodes(child_nodes, callback, prev, None, is_root)
        else:
            # Ignore spaces when determining spacing
            nonspace = not node.has_class("mspace")
            if nonspace:
                result = callback(node, prev["node"])
                if result:
                    if prev.get("insertAfter"):
                        prev["insertAfter"](result)
                    else:
                        nodes.insert(0, result)
                        i += 1

            if nonspace:
                prev["node"] = node
            elif is_root and node.has_class("newline"):
                prev["node"] = make_span(["leftmost"])

        def insert_after(index: int) -> Callable[[HtmlDomNode], None]:
            def _insert(n: HtmlDomNode) -> None:
                nodes.insert(index + 1, n)
                nonlocal i
                i += 1
            return _insert

        prev["insertAfter"] = insert_after(i)
        i += 1

    if next_node:
        nodes.pop()


def check_partial_group(node: HtmlDomNode) -> DocumentFragment | Anchor | DomSpan | None:
    """Check if node is a partial group."""
    if isinstance(node, DocumentFragment) or isinstance(node, Anchor) or (
        isinstance(node, Span) and node.has_class("enclosing")
    ):
        return node
    return None


def get_outermost_node(node: HtmlDomNode, side: Side) -> HtmlDomNode:
    """Get outermost node at given side."""
    partial_group = check_partial_group(node)
    if partial_group and partial_group.children:
        if side == "right":
            return get_outermost_node(cast(HtmlDomNode, partial_group.children[-1]), "right")
        elif side == "left":
            return get_outermost_node(cast(HtmlDomNode, partial_group.children[0]), "left")
    return node


def get_type_of_dom_tree(node: HtmlDomNode | None, side: Side | None = None) -> DomType | None:
    """Get math atom class of domTree."""
    if not node:
        return None

    if side:
        node = get_outermost_node(node, side)

    # Get the type from first class (assumes it's the math class)
    return DOM_ENUM.get(node.classes[0]) if node.classes else None


def make_null_delimiter(options: Options, classes: list[str]) -> DomSpan:
    """Create null delimiter span."""
    more_classes = ["nulldelimiter"] + options.base_sizing_classes()
    return make_span(classes + more_classes)


def build_group(
    group: AnyParseNode | None,
    options: Options,
    base_options: Options | None = None,
) -> HtmlDomNode:
    """Build HTML for a parse group."""
    if not group:
        return make_span()

    if group["type"] in group_builders:
        # Call the group builder function
        group_node = cast(HtmlDomNode, group_builders[group["type"]](group, options))

        # Handle size changes between parent and child
        if base_options and options.size != base_options.size:
            group_node = make_span(options.sizing_classes(base_options),
                                   [group_node], options)

            multiplier = options.size_multiplier / base_options.size_multiplier
            group_node.height *= multiplier
            group_node.depth *= multiplier

        return group_node
    else:
        raise ParseError(f"Got group of unknown type: '{group['type']}'")


def build_html_unbreakable(children: list[HtmlDomNode], options: Options) -> DomSpan:
    """Create unbreakable HTML unit."""
    body = make_span(["base"], children, options)

    # Add strut for proper vertical extent
    strut = make_span(["strut"])
    strut.style["height"] = make_em(body.height + body.depth)
    if body.depth:
        strut.style["verticalAlign"] = make_em(-body.depth)
    body.children.insert(0, strut)

    return body


def build_html(tree: list[AnyParseNode], options: Options) -> DomSpan:
    """Build complete HTML representation."""
    # Strip outer tag wrapper
    tag: list[AnyParseNode] | None = None
    if len(tree) == 1 and tree[0].get("type") == "tag":
        raw_tag = tree[0].get("tag")
        if isinstance(raw_tag, list):
            tag = cast(list["AnyParseNode"], raw_tag)
        tree = cast(list["AnyParseNode"], tree[0].get("body", []))

    # Build the expression
    expression = build_expression(tree, options, "root")

    eqn_num: HtmlDomNode | None = None
    if len(expression) == 2 and expression[1].has_class("tag"):
        # Environment with automatic equation numbers
        eqn_num = expression.pop()

    children: list[HtmlDomNode] = []

    # Create unbreakable units between line breaks
    parts: list[HtmlDomNode] = []
    i = 0
    while i < len(expression):
        parts.append(expression[i])

        if (expression[i].has_class("mbin") or
            expression[i].has_class("mrel") or
            expression[i].has_class("allowbreak")):

            # Include post-operator glue on same line
            nobreak = False
            while (i < len(expression) - 1 and
                   expression[i + 1].has_class("mspace") and
                   not expression[i + 1].has_class("newline")):
                i += 1
                parts.append(expression[i])
                if expression[i].has_class("nobreak"):
                    nobreak = True

            # Don't break if \nobreak present
            if not nobreak:
                children.append(build_html_unbreakable(parts, options))
                parts = []
        elif expression[i].has_class("newline"):
            # Write line except newline
            parts.pop()
            if parts:
                children.append(build_html_unbreakable(parts, options))
                parts = []
            # Put newline at top level
            children.append(expression[i])

        i += 1

    if parts:
        children.append(build_html_unbreakable(parts, options))

    # Add tag if present
    tag_child: DomSpan | None = None
    if tag:
        tag_child = build_html_unbreakable(
            build_expression(tag, options, True),
            options,
        )
        tag_child.classes = ["tag"]
        children.append(tag_child)
    elif eqn_num:
        children.append(eqn_num)

    html_node = make_span(["katex-html"], children)
    html_node.set_attribute("aria-hidden", "true")

    # Adjust tag strut for vertical alignment
    if tag_child and len(tag_child.children) > 0:
        strut = tag_child.children[0]
        strut.style["height"] = make_em(html_node.height + html_node.depth)
        if html_node.depth:
            strut.style["verticalAlign"] = make_em(-html_node.depth)

    return html_node


def build_common_make_glue(space: Measurement, options: Options) -> DomSpan:
    """Create glue (spacing) span from a numeric measurement mapping."""
    from .build_common import make_glue
    return make_glue(space, options)


__all__ = [
    "build_expression",
    "build_group",
    "build_html",
    "get_type_of_dom_tree",
    "make_null_delimiter",
]
