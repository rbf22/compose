"""Python port of KaTeX's defineEnvironment helper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

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
    handler: callable
    html_builder: Optional[HtmlBuilder]
    mathml_builder: Optional[MathMLBuilder]


@dataclass
class EnvSpec:
    type: str
    num_args: int
    allowed_in_text: bool
    num_optional_args: int
    handler: callable


ENVIRONMENTS: Dict[str, EnvSpec] = {}


def define_environment(spec: EnvDefSpec) -> None:
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


__all__ = ["define_environment", "ENVIRONMENTS"]
