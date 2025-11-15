"""Python port of KaTeX's defineFunction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol

from .types import ArgType


class FunctionContext(Protocol):
    func_name: str


FunctionHandler = Callable[[FunctionContext, List[Any], List[Optional[Any]]], Any]
HtmlBuilder = Callable[[Any, Any], Any]
MathMLBuilder = Callable[[Any, Any], Any]


@dataclass
class FunctionPropSpec:
    num_args: int
    arg_types: Optional[List[ArgType]] = None
    allowed_in_argument: bool = False
    allowed_in_text: bool = False
    allowed_in_math: Optional[bool] = True
    num_optional_args: int = 0
    infix: bool = False
    primitive: bool = False


@dataclass
class FunctionDefSpec:
    type: str
    names: List[str]
    props: FunctionPropSpec
    handler: Optional[FunctionHandler]
    html_builder: Optional[HtmlBuilder] = None
    mathml_builder: Optional[MathMLBuilder] = None


@dataclass
class FunctionSpec:
    type: str
    num_args: int
    arg_types: Optional[List[ArgType]]
    allowed_in_argument: bool
    allowed_in_text: bool
    allowed_in_math: bool
    num_optional_args: int
    infix: bool
    primitive: bool
    handler: Optional[FunctionHandler]


FUNCTIONS: Dict[str, FunctionSpec] = {}
HTML_GROUP_BUILDERS: Dict[str, HtmlBuilder] = {}
MATHML_GROUP_BUILDERS: Dict[str, MathMLBuilder] = {}


def define_function(spec: FunctionDefSpec) -> None:
    data = FunctionSpec(
        type=spec.type,
        num_args=spec.props.num_args,
        arg_types=spec.props.arg_types,
        allowed_in_argument=bool(spec.props.allowed_in_argument),
        allowed_in_text=bool(spec.props.allowed_in_text),
        allowed_in_math=True if spec.props.allowed_in_math is None else spec.props.allowed_in_math,
        num_optional_args=spec.props.num_optional_args,
        infix=bool(spec.props.infix),
        primitive=bool(spec.props.primitive),
        handler=spec.handler,
    )

    for name in spec.names:
        FUNCTIONS[name] = data

    if spec.type:
        if spec.html_builder:
            HTML_GROUP_BUILDERS[spec.type] = spec.html_builder
        if spec.mathml_builder:
            MATHML_GROUP_BUILDERS[spec.type] = spec.mathml_builder


def define_function_builders(type_: str, html_builder: Optional[HtmlBuilder], mathml_builder: MathMLBuilder) -> None:
    define_function(
        FunctionDefSpec(
            type=type_,
            names=[],
            props=FunctionPropSpec(num_args=0),
            handler=lambda *_: (_ for _ in ()).throw(RuntimeError("Should never be called.")),
            html_builder=html_builder,
            mathml_builder=mathml_builder,
        )
    )


def normalize_argument(arg: Any) -> Any:
    if getattr(arg, "type", None) == "ordgroup" and len(getattr(arg, "body", [])) == 1:
        return arg.body[0]
    return arg


def ord_argument(arg: Any) -> List[Any]:
    if getattr(arg, "type", None) == "ordgroup":
        return list(getattr(arg, "body", []))
    return [arg]


__all__ = [
    "define_function",
    "define_function_builders",
    "FUNCTIONS",
    "HTML_GROUP_BUILDERS",
    "MATHML_GROUP_BUILDERS",
    "normalize_argument",
    "ord_argument",
]
