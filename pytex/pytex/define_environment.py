"""Python port of KaTeX's defineEnvironment helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union, cast

from .define_function import HTML_GROUP_BUILDERS, MATHML_GROUP_BUILDERS, HtmlBuilder, MathMLBuilder


@dataclass
class EnvProps:
    num_args: int = 0
    allowed_in_text: bool = False
    num_optional_args: int = 0


@dataclass
class EnvDefSpec:
    type: str
    names: List[str]
    props: EnvProps
    handler: Callable[..., Any]
    html_builder: Optional[HtmlBuilder]
    mathml_builder: Optional[MathMLBuilder]


@dataclass
class EnvSpec:
    type: str
    num_args: int
    allowed_in_text: bool
    num_optional_args: int
    handler: Callable[..., Any]


ENVIRONMENTS: Dict[str, EnvSpec] = {}


def _coerce_props(props: Dict[str, Any]) -> EnvProps:
    return EnvProps(
        num_args=props.get("numArgs", 0),
        allowed_in_text=bool(props.get("allowedInText", False)),
        num_optional_args=props.get("numOptionalArgs", 0),
    )


def _coerce_env_spec(spec: Union[EnvDefSpec, Dict[str, Any]]) -> EnvDefSpec:
    if isinstance(spec, EnvDefSpec):
        return spec
    if not isinstance(spec, dict):
        raise TypeError("Environment definition must be EnvDefSpec or dict")

    props = _coerce_props(spec.get("props", {}))
    raw_handler = spec.get("handler")
    if raw_handler is None:
        raise TypeError("Environment definition requires a 'handler'")
    handler = cast(Callable[..., Any], raw_handler)
    return EnvDefSpec(
        type=spec.get("type", ""),
        names=list(spec.get("names", [])),
        props=props,
        handler=handler,
        html_builder=spec.get("html_builder"),
        mathml_builder=spec.get("mathml_builder"),
    )


def define_environment(spec: Union[EnvDefSpec, Dict[str, Any]]) -> None:
    spec = _coerce_env_spec(spec)
    data = EnvSpec(
        type=spec.type,
        num_args=spec.props.num_args,
        allowed_in_text=spec.props.allowed_in_text,
        num_optional_args=spec.props.num_optional_args,
        handler=spec.handler,
    )

    for name in spec.names:
        ENVIRONMENTS[name] = data

    if spec.html_builder:
        HTML_GROUP_BUILDERS[spec.type] = spec.html_builder
    if spec.mathml_builder:
        MATHML_GROUP_BUILDERS[spec.type] = spec.mathml_builder


__all__ = [
    "define_environment",
    "_coerce_env_spec",
    "ENVIRONMENTS",
]
