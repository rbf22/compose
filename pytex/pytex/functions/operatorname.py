"""Python port of KaTeX's functions/operatorname.js - operator name handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, cast

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..define_macro import define_macro
from ..dom_tree import DomSpan, Span, SymbolNode
from ..mathml_tree import MathNode, TextNode
from ..parse_node import AnyParseNode, ParseNode
from ..types import Mode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import OperatornameParseNode


def _coerce_body_to_textords(nodes: List[AnyParseNode]) -> List[AnyParseNode]:
    coerced: List[AnyParseNode] = []
    for child in nodes:
        child_map = cast(Dict[str, Any], child)
        text_value = child_map.get("text")
        if isinstance(text_value, str):
            coerced.append(cast(AnyParseNode, {
                "type": "textord",
                "mode": child_map.get("mode", "math"),
                "text": text_value,
            }))
        else:
            coerced.append(child)
    return coerced


def _normalize_operator_body(group: Mapping[str, Any]) -> List[AnyParseNode]:
    raw_body = group.get("body")
    if not isinstance(raw_body, list):
        return []
    typed_nodes = cast(List[AnyParseNode], [node for node in raw_body if isinstance(node, dict)])
    return _coerce_body_to_textords(typed_nodes)


def _apply_text_replacements(span: DomSpan) -> None:
    for child in span.children:
        if hasattr(child, "text") and isinstance(child.text, str):
            child.text = child.text.replace("\u2212", "-").replace("\u2217", "*")


def _operatorname_handler(context: Dict[str, Any], args: List[ParseNode]) -> Dict[str, Any]:
    parser = context["parser"]
    return {
        "type": "operatorname",
        "mode": parser.mode,
        "body": ordargument(args[0]),
        "alwaysHandleSupSub": context["funcName"] == "\\operatornamewithlimits",
        "limits": False,
        "parentIsSupSub": False,
    }


def html_builder(group: ParseNode, options: "Options") -> DomSpan:
    """Build HTML for operatorname command."""
    from .. import build_html as html

    operatorname_group = cast("OperatornameParseNode", group)
    sup_group: Optional[ParseNode] = None
    sub_group: Optional[ParseNode] = None
    base_group: Mapping[str, Any] = operatorname_group
    has_limits = False

    if operatorname_group.get("type") == "supsub":
        sup_val = operatorname_group.get("sup")
        sub_val = operatorname_group.get("sub")
        base_val = operatorname_group.get("base", operatorname_group)
        sup_group = cast(Optional[ParseNode], sup_val)
        sub_group = cast(Optional[ParseNode], sub_val)
        base_group = cast(Mapping[str, Any], base_val)
        has_limits = True

    body_nodes = _normalize_operator_body(base_group)
    expression = html.build_expression(body_nodes, options.with_font("mathrm"), True)
    base = make_span(["mop"], expression, options)
    _apply_text_replacements(base)

    if has_limits:
        return assemble_sup_sub(base, sup_group, sub_group, options, options.style, 0.0, 0.0)
    return base


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for operatorname command."""
    from .. import build_mathml as mml
    from ..mathml_tree import SpaceNode

    operatorname_group = cast("OperatornameParseNode", group)
    body_nodes = _normalize_operator_body(operatorname_group)
    expression: List[Any] = mml.build_expression(body_nodes, options.with_font("mathrm"))

    is_all_string = True
    for node in expression:
        if isinstance(node, SpaceNode):
            continue
        if isinstance(node, MathNode):
            if node.type in ("mi", "mn", "ms", "mspace", "mtext"):
                continue
            if node.type == "mo" and len(node.children) == 1 and isinstance(node.children[0], TextNode):
                child = node.children[0]
                child.text = child.text.replace("\u2212", "-").replace("\u2217", "*")
                continue
        is_all_string = False
        break

    if is_all_string:
        word = "".join(node.to_text() for node in expression)
        expression_nodes: List[Any] = [TextNode(word)]
    else:
        expression_nodes = expression

    identifier = MathNode("mi", expression_nodes)
    identifier.set_attribute("mathvariant", "normal")
    operator = MathNode("mo", [mml.make_text("\u2061", Mode.TEXT)])
    return MathNode("mrow", [identifier, operator])


define_function({
    "type": "operatorname",
    "names": ["\\operatorname@", "\\operatornamewithlimits"],
    "props": {"numArgs": 1},
    "handler": _operatorname_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_macro("\\operatorname", "\\@ifstar\\operatornamewithlimits\\operatorname@")


try:
    from .utils.assembleSupSub import assembleSupSub as assemble_sup_sub
except ImportError:
    def assemble_sup_sub(
        base: Span | SymbolNode,
        sup_group: Optional[AnyParseNode],
        sub_group: Optional[AnyParseNode],
        options: "Options",
        style: Any,
        slant: float,
        base_shift: float,
    ) -> Span:
        return base if isinstance(base, Span) else cast(Span, base)
