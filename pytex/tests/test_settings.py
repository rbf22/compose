"""Targeted tests for the Settings module.

These tests exercise default computation, type coercion, strict mode
handling, and trust handling to raise coverage for ``pytex.settings``.
"""

from __future__ import annotations

from typing import Any, Dict

import warnings

import pytest  # type: ignore[import-not-found]

from pytex.parse_error import ParseError
from pytex.settings import (
    EnumSpec,
    OptionSpec,
    SETTINGS_SCHEMA,
    Settings,
    _coerce_value,
    _ensure_number,
    _matches_type,
)


class TestOptionSpecComputeDefault:
    def test_compute_default_uses_explicit_default(self) -> None:
        spec = OptionSpec(("string",), default="value")
        assert spec.compute_default() == "value"

    def test_compute_default_for_primitive_types(self) -> None:
        assert OptionSpec(("string",)).compute_default() == ""
        assert OptionSpec(("number",)).compute_default() == 0
        assert OptionSpec(("object",)).compute_default() == {}
        assert OptionSpec(("function",)).compute_default() is None

    def test_compute_default_for_enum_uses_first_value(self) -> None:
        enum = EnumSpec(("one", "two"))
        spec = OptionSpec((enum,))
        assert spec.compute_default() == "one"


class TestNumericAndTypeHelpers:
    def test_ensure_number_accepts_int_and_float(self) -> None:
        assert _ensure_number(2) == 2.0
        assert _ensure_number(2.5) == 2.5

    def test_ensure_number_rejects_bool_and_non_numeric(self) -> None:
        with pytest.raises(TypeError):
            _ensure_number(True)
        with pytest.raises(TypeError):
            _ensure_number("3")

    def test_matches_type_for_all_supported_kinds(self) -> None:
        enum = EnumSpec(("a", "b"))
        assert _matches_type(enum, "a")
        assert not _matches_type(enum, "c")

        assert _matches_type("string", "x")
        assert not _matches_type("string", 1)

        assert _matches_type("number", 5)
        assert not _matches_type("number", "not-num")

        assert _matches_type("object", {"a": 1})
        assert not _matches_type("object", [1, 2])

        assert _matches_type("function", lambda x: x)
        assert not _matches_type("function", 3)

    def test_coerce_value_number_with_processor_and_object_deepcopy(self) -> None:
        num_spec = OptionSpec(("number",), processor=lambda v: v * 2)
        assert _coerce_value(num_spec, 2) == 4.0

        original: Dict[str, Any] = {"a": 1}
        obj_spec = OptionSpec(("object",))
        result = _coerce_value(obj_spec, original)
        assert result == original
        assert result is not original

    def test_coerce_value_enum_and_invalid_type(self) -> None:
        enum = EnumSpec(("htmlAndMathml", "html"))
        enum_spec = OptionSpec((enum,), processor=lambda v: v.strip())
        assert _coerce_value(enum_spec, "html") == "html"

        str_spec = OptionSpec(("string",))
        with pytest.raises(TypeError):
            _coerce_value(str_spec, 123)


class TestSettingsDefaultsAndSchema:
    def test_settings_defaults_match_schema(self) -> None:
        s1 = Settings()
        s2 = Settings()

        # A few representative defaults from the schema.
        assert s1.displayMode is False
        assert s1.output == "htmlAndMathml"
        assert s1.throwOnError is True
        assert s1.errorColor == "#cc0000"

        # Objects should be deep-copied per instance (e.g. macros).
        assert isinstance(s1.macros, dict)
        assert isinstance(s2.macros, dict)
        assert s1.macros is not s2.macros

        # Numeric processors should clamp at zero for negative inputs.
        s3 = Settings({"minRuleThickness": -1.0, "maxSize": -10, "maxExpand": -5})
        assert s3.minRuleThickness == 0.0
        assert s3.maxSize == 0.0
        assert s3.maxExpand == 0.0

    def test_settings_schema_contains_expected_keys(self) -> None:
        # Sanity check to make sure schema remains in sync with the class.
        for key in (
            "displayMode",
            "output",
            "leqno",
            "fleqn",
            "throwOnError",
            "errorColor",
            "macros",
            "minRuleThickness",
            "strict",
            "trust",
            "maxSize",
            "maxExpand",
        ):
            assert key in SETTINGS_SCHEMA


class TestReportNonstrict:
    def test_report_nonstrict_ignored_for_false_and_ignore(self) -> None:
        s_false = Settings({"strict": False})
        s_ignore = Settings({"strict": "ignore"})

        # No warnings or errors should be produced.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("error", RuntimeWarning)
            s_false.report_nonstrict("code", "msg")
            s_ignore.report_nonstrict("code", "msg")
        assert not caught

    def test_report_nonstrict_raises_for_true_and_error(self) -> None:
        s_true = Settings({"strict": True})
        s_error = Settings({"strict": "error"})

        with pytest.raises(ParseError):
            s_true.report_nonstrict("C", "problem")
        with pytest.raises(ParseError):
            s_error.report_nonstrict("C", "problem")

    def test_report_nonstrict_warns_for_warn(self) -> None:
        s = Settings({"strict": "warn"})
        with pytest.warns(RuntimeWarning) as record:
            s.report_nonstrict("C", "something")
        assert "strict mode is 'warn'" in str(record[0].message)

    def test_report_nonstrict_uses_callable_and_unrecognized_value(self) -> None:
        calls: Dict[str, Any] = {}

        def strict_fn(code: str, msg: str, token: Any) -> str:
            calls["code"] = code
            calls["msg"] = msg
            return "warn"

        s_callable = Settings({"strict": strict_fn})
        with pytest.warns(RuntimeWarning) as record:
            s_callable.report_nonstrict("X", "cb warning")
        assert calls["code"] == "X"
        assert "strict mode is 'warn'" in str(record[0].message)

        # Unrecognized strict value should emit a different warning.
        s_weird = Settings({"strict": "warn"})
        s_weird.strict = "weird"
        with pytest.warns(RuntimeWarning) as record2:
            s_weird.report_nonstrict("Y", "msg")
        assert "unrecognized 'weird'" in str(record2[0].message)


class TestUseStrictBehavior:
    def test_use_strict_behavior_ignore_and_false(self) -> None:
        s_false = Settings({"strict": False})
        s_ignore = Settings({"strict": "ignore"})

        assert s_false.use_strict_behavior("C", "msg") is False
        assert s_ignore.use_strict_behavior("C", "msg") is False

    def test_use_strict_behavior_true_and_error(self) -> None:
        s_true = Settings({"strict": True})
        s_error = Settings({"strict": "error"})

        assert s_true.use_strict_behavior("C", "msg") is True
        assert s_error.use_strict_behavior("C", "msg") is True

    def test_use_strict_behavior_warn_and_unrecognized(self) -> None:
        s_warn = Settings({"strict": "warn"})
        with pytest.warns(RuntimeWarning) as record:
            result = s_warn.use_strict_behavior("C", "msg")
        assert result is False
        assert "strict mode is 'warn'" in str(record[0].message)

        s_weird = Settings({"strict": "warn"})
        s_weird.strict = "strange"
        with pytest.warns(RuntimeWarning) as record2:
            result2 = s_weird.use_strict_behavior("C", "msg")
        assert result2 is False
        assert "unrecognized 'strange'" in str(record2[0].message)

    def test_use_strict_behavior_callable_and_exception(self) -> None:
        state: Dict[str, int] = {"calls": 0}

        def strict_fn(code: str, msg: str, token: Any) -> bool:
            state["calls"] += 1
            if state["calls"] == 1:
                return True
            raise ValueError("boom")

        s = Settings({"strict": strict_fn})

        # First call: callback returns True, so strict behavior is used.
        assert s.use_strict_behavior("C1", "msg1") is True

        # Second call: callback raises, which should force strict="error".
        assert s.use_strict_behavior("C2", "msg2") is True
        assert state["calls"] == 2


class TestIsTrusted:
    def test_is_trusted_uses_protocol_from_url_and_bool_trust(self) -> None:
        s_true = Settings({"trust": True})

        # Safe http URL should be trusted.
        assert s_true.is_trusted({"url": "http://example.com"}) is True

        # Dangerous URL with invalid/encoded protocol should be rejected
        # before consulting the trust flag.
        assert s_true.is_trusted({"url": "javascript&#x3a;alert(1)"}) is False

    def test_is_trusted_with_callable_trust(self) -> None:
        def trust_fn(ctx: Dict[str, Any]) -> bool:
            # Ensure protocol has been injected into the context for URLs.
            proto = ctx.get("protocol", "")
            return proto == "http"

        s = Settings({"trust": trust_fn})

        assert s.is_trusted({"url": "http://example.com"}) is True
        assert s.is_trusted({"url": "mailto:user@example.com"}) is False

    def test_is_trusted_when_protocol_already_present(self) -> None:
        s = Settings({"trust": False})
        # If protocol is already given, is_trusted should just respect trust.
        assert s.is_trusted({"protocol": "http", "url": "ignored"}) is False
