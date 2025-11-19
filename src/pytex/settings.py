"""Python port of KaTeX's Settings module."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .parse_error import ParseError
from .utils import protocol_from_url

StrictFunction = Callable[[str, str, Any | None], bool | str | None]
TrustFunction = Callable[[dict[str, Any]], bool | None]


@dataclass(frozen=True)
class EnumSpec:
    values: tuple[str, ...]


@dataclass(frozen=True)
class OptionSpec:
    allowed_types: tuple[str | EnumSpec, ...]
    default: Any = None
    processor: Callable[[Any], Any] | None = None

    def compute_default(self) -> Any:
        if self.default is not None:
            return deepcopy(self.default)

        first = self.allowed_types[0]
        if isinstance(first, EnumSpec):
            return first.values[0]
        if first == "boolean":
            return False
        if first == "string":
            return ""
        if first == "number":
            return 0
        if first == "object":
            return {}
        if first == "function":
            return None
        return None


def _ensure_number(value: Any) -> float:
    if isinstance(value, bool):
        raise TypeError("Booleans are not valid numeric values for Settings options")
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"Expected numeric value, received {value!r}")


def _matches_type(spec_type: str | EnumSpec, value: Any) -> bool:
    if isinstance(spec_type, EnumSpec):
        return isinstance(value, str) and value in spec_type.values

    if spec_type == "boolean":
        return isinstance(value, bool)
    if spec_type == "string":
        return isinstance(value, str)
    if spec_type == "number":
        try:
            _ensure_number(value)
            return True
        except TypeError:
            return False
    if spec_type == "object":
        return isinstance(value, dict)
    if spec_type == "function":
        return callable(value)
    return False


def _coerce_value(spec: OptionSpec, value: Any) -> Any:
    for spec_type in spec.allowed_types:
        if _matches_type(spec_type, value):
            result = value
            if spec.processor:
                result = spec.processor(result)
            if isinstance(spec_type, EnumSpec):
                return result
            if spec_type == "number":
                return _ensure_number(result)
            if spec_type == "object":
                return deepcopy(result)
            return result
    raise TypeError(
        "Invalid value for Settings option; allowed types are "
        f"{spec.allowed_types}, received {value!r}"
    )


SETTINGS_SCHEMA: dict[str, OptionSpec] = {
    "display_mode": OptionSpec(("boolean",)),
    "output": OptionSpec((EnumSpec(("htmlAndMathml", "html", "mathml")),)),
    "leqno": OptionSpec(("boolean",)),
    "fleqn": OptionSpec(("boolean",)),
    "throw_on_error": OptionSpec(("boolean",), default=True),
    "error_color": OptionSpec(("string",), default="#cc0000"),
    "macros": OptionSpec(("object",), default={}),
    "min_rule_thickness": OptionSpec(("number",), processor=lambda t: max(0.0, _ensure_number(t))),
    "color_is_text_color": OptionSpec(("boolean",)),
    "strict": OptionSpec((EnumSpec(("warn", "ignore", "error")), "boolean", "function"), default=False),
    "trust": OptionSpec(("boolean", "function")),
    "max_size": OptionSpec(("number",), default=float("inf"), processor=lambda s: max(0.0, _ensure_number(s))),
    "max_expand": OptionSpec(("number",), default=1000, processor=lambda n: max(0.0, _ensure_number(n))),
    "global_group": OptionSpec(("boolean",)),
}


class Settings:
    """Container for renderer configuration options."""

    display_mode: bool
    output: str
    leqno: bool
    fleqn: bool
    throw_on_error: bool
    error_color: str
    macros: dict[str, Any]
    min_rule_thickness: float
    color_is_text_color: bool
    strict: bool | str | StrictFunction
    trust: bool | TrustFunction | None
    max_size: float
    max_expand: float
    global_group: bool

    def __init__(self, options: dict[str, Any] | None = None):
        opts = dict(options or {})
        for key, spec in SETTINGS_SCHEMA.items():
            value = opts.get(key)
            if value is None:
                computed = spec.compute_default()
            else:
                computed = _coerce_value(spec, value)
            setattr(self, key, computed)

    def report_nonstrict(self, error_code: str, error_msg: str, token: Any | None = None) -> None:
        strict = self.strict
        if callable(strict):
            callback_result = strict(error_code, error_msg, token)
            if callback_result is not None:
                strict = callback_result

        if not strict or strict == "ignore":
            return
        if strict is True or strict == "error":
            raise ParseError(
                "LaTeX-incompatible input and strict mode is 'error': "
                f"{error_msg} [{error_code}]",
                token,
            )
        if strict == "warn":
            warnings.warn(
                "LaTeX-incompatible input and strict mode is 'warn': "
                f"{error_msg} [{error_code}]",
                RuntimeWarning,
                stacklevel=2,
            )
            return
        warnings.warn(
            "LaTeX-incompatible input and strict mode is set to "
            f"unrecognized '{strict}': {error_msg} [{error_code}]",
            RuntimeWarning,
            stacklevel=2,
        )

    def use_strict_behavior(self, error_code: str, error_msg: str, token: Any | None = None) -> bool:
        strict = self.strict
        if callable(strict):
            try:
                callback_result = strict(error_code, error_msg, token)
                if callback_result is not None:
                    strict = callback_result
            except Exception:
                strict = "error"

        if not strict or strict == "ignore":
            return False
        if strict is True or strict == "error":
            return True
        if strict == "warn":
            warnings.warn(
                "LaTeX-incompatible input and strict mode is 'warn': "
                f"{error_msg} [{error_code}]",
                RuntimeWarning,
                stacklevel=2,
            )
            return False
        warnings.warn(
            "LaTeX-incompatible input and strict mode is set to "
            f"unrecognized '{strict}': {error_msg} [{error_code}]",
            RuntimeWarning,
            stacklevel=2,
        )
        return False

    def is_trusted(self, context: dict[str, Any]) -> bool:
        if "url" in context and "protocol" not in context:
            protocol = protocol_from_url(context["url"])
            if protocol is None:
                return False
            context = dict(context)
            context["protocol"] = protocol

        trust = self.trust
        if callable(trust):
            result = trust(context)
            return bool(result)
        return bool(trust)


__all__ = ["Settings", "SETTINGS_SCHEMA", "StrictFunction", "TrustFunction"]
