"""Python port of KaTeX's defineFunction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

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

# Compatibility aliases matching the original KaTeX module layout
_functions = FUNCTIONS
_htmlGroupBuilders = HTML_GROUP_BUILDERS
_mathmlGroupBuilders = MATHML_GROUP_BUILDERS


def _coerce_props(props: Dict[str, Any]) -> FunctionPropSpec:
    return FunctionPropSpec(
        num_args=props.get("numArgs", 0),
        arg_types=props.get("argTypes"),
        allowed_in_argument=bool(props.get("allowedInArgument", False)),
        allowed_in_text=bool(props.get("allowedInText", False)),
        allowed_in_math=props.get("allowedInMath", True),
        num_optional_args=props.get("numOptionalArgs", 0),
        infix=bool(props.get("infix", False)),
        primitive=bool(props.get("primitive", False)),
    )


def _coerce_function_def(spec: Union[FunctionDefSpec, Dict[str, Any]]) -> FunctionDefSpec:
    if isinstance(spec, FunctionDefSpec):
        return spec
    if not isinstance(spec, dict):
        raise TypeError("Function definition must be FunctionDefSpec or dict")

    props = _coerce_props(spec.get("props", {}))
    return FunctionDefSpec(
        type=spec.get("type", ""),
        names=list(spec.get("names", [])),
        props=props,
        handler=spec.get("handler"),
        html_builder=spec.get("html_builder"),
        mathml_builder=spec.get("mathml_builder"),
    )


def define_function(spec: Union[FunctionDefSpec, Dict[str, Any]]) -> None:
    spec = _coerce_function_def(spec)
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
        # Normalise legacy KaTeX-style function names that may be written
        # with a double leading backslash in Python (e.g. r"\\custom").
        # The parser always sees TeX control sequences with a single
        # leading backslash ("\\custom"), so register both forms.
        canonical = name
        if canonical.startswith("\\\\") and not canonical.startswith("\\\\\\"):
            canonical = canonical[1:]
        FUNCTIONS[name] = data
        FUNCTIONS[canonical] = data

    if spec.type:
        if spec.html_builder:
            HTML_GROUP_BUILDERS[spec.type] = spec.html_builder
        if spec.mathml_builder:
            MATHML_GROUP_BUILDERS[spec.type] = spec.mathml_builder


def defineFunction(spec: Union[FunctionDefSpec, Dict[str, Any]]) -> None:
    """Compatibility wrapper mirroring KaTeX's camelCase API."""
    define_function(spec)


def define_function_builders(
    type_or_spec: Union[str, Dict[str, Any]],
    html_builder: Optional[HtmlBuilder] = None,
    mathml_builder: Optional[MathMLBuilder] = None,
) -> None:
    if isinstance(type_or_spec, dict) and html_builder is None and mathml_builder is None:
        # Legacy KaTeX usage passing a dict
        spec = type_or_spec
        type_name = spec.get("type", "")
        html_builder = spec.get("html_builder")
        mathml_builder = spec.get("mathml_builder")
    else:
        type_name = str(type_or_spec)
        if mathml_builder is None:
            raise TypeError("mathml_builder is required")

    define_function(
        FunctionDefSpec(
            type=type_name,
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


def ordargument(arg: Any) -> List[Any]:
    """Compatibility wrapper for the camelCase KaTeX helper name."""

    return ord_argument(arg)


__all__ = [
    "define_function",
    "defineFunction",
    "_coerce_function_def",
    "define_function_builders",
    "FUNCTIONS",
    "HTML_GROUP_BUILDERS",
    "MATHML_GROUP_BUILDERS",
    "_functions",
    "_htmlGroupBuilders",
    "_mathmlGroupBuilders",
    "normalize_argument",
    "ord_argument",
    "ordargument",
]
