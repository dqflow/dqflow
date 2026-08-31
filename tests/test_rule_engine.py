"""The central table-rule evaluator (issue #18)."""

from __future__ import annotations

import pytest

from dqflow.rules import RuleError, evaluate_rule


def _eval(
    expression: str,
    *,
    row_count: int = 10,
    nulls: dict[str, float] | None = None,
    uniques: dict[str, float] | None = None,
) -> bool:
    nulls = nulls or {}
    uniques = uniques or {}
    return evaluate_rule(
        expression,
        row_count=row_count,
        null_rate=lambda c: nulls.get(c, 0.0),
        unique_count=lambda c: uniques.get(c, 0),
    )


class TestEvaluation:
    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("row_count > 0", True),
            ("row_count >= 10", True),
            ("row_count == 10", True),
            ("row_count != 10", False),
            ("row_count < 5", False),
            ("2 < row_count <= 10", True),
            ("row_count > 0 and row_count < 100", True),
            ("row_count > 100 or row_count == 10", True),
            ("not row_count > 100", True),
            ("row_count / 2 == 5", True),
            ("row_count * 2 - 1 >= 19", True),
        ],
    )
    def test_row_count_expressions(self, expression: str, expected: bool) -> None:
        assert _eval(expression) is expected

    def test_stat_functions(self) -> None:
        assert _eval("null_rate('email') < 0.05", nulls={"email": 0.01}) is True
        assert _eval("null_rate('email') == 0", nulls={"email": 0.0}) is True
        assert _eval("unique_count('status') <= 3", uniques={"status": 3}) is True
        assert (
            _eval(
                "row_count > 0 and null_rate('a') < 0.1 and unique_count('b') == 2",
                nulls={"a": 0.05},
                uniques={"b": 2},
            )
            is True
        )

    def test_missing_column_stats_default_to_zero(self) -> None:
        assert _eval("null_rate('nope') == 0") is True
        assert _eval("unique_count('nope') == 0") is True

    def test_result_is_always_a_plain_bool(self) -> None:
        result = _eval("row_count and 1")
        assert result is True and isinstance(result, bool)


class TestRejected:
    @pytest.mark.parametrize(
        "expression",
        [
            "__import__('os').system('echo hi')",
            "row_count.__class__",
            "().__class__.__bases__",
            "[x for x in range(3)]",
            "(lambda: 1)()",
            "{'a': 1}",
            "[1, 2, 3]",
            "f'{row_count}'",
            "open('/etc/passwd')",
            "len('abc')",
            "row_count if row_count else 0",
            "unknown_name > 1",
            "null_rate('a', 'b') < 1",
            "null_rate(col_name) < 1",
            "unique_count() == 0",
            "row_count = 5",
        ],
    )
    def test_disallowed_constructs_raise_rule_error(self, expression: str) -> None:
        with pytest.raises(RuleError):
            _eval(expression)

    def test_syntax_error_raises_rule_error(self) -> None:
        with pytest.raises(RuleError, match="could not parse"):
            _eval("row_count >")

    def test_type_error_from_comparison_propagates(self) -> None:
        # Not a RuleError: mirrors today's behaviour where evaluation errors
        # bubble up for the engine to convert into a failed check.
        with pytest.raises(TypeError):
            _eval("row_count < 'x'")
