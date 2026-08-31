"""Tests for the text renderer, exercised without any engine."""

from __future__ import annotations

import pytest

from dqflow.report import Verbosity, render_result, resolve_color
from dqflow.result import CheckResult, ValidationResult


def _result(*checks: CheckResult, name: str = "orders") -> ValidationResult:
    return ValidationResult(contract_name=name, checks=list(checks))


def _sample_failure() -> ValidationResult:
    return _result(
        CheckResult("column_exists:order_id", True),
        CheckResult("column_exists:region", False, "Column 'region' is missing from the data"),
        CheckResult(
            "not_null:order_id",
            False,
            "Column 'order_id' has 3 null values",
            {"null_count": 3, "null_rate": 0.25},
        ),
        CheckResult(
            "allowed:currency",
            False,
            "Column 'currency' has 2 values outside the allowed set",
            {
                "sample_invalid_values": ["GBP", "JPY"],
                "violating_rows": 2,
                "violating_rate": 0.5,
            },
        ),
        CheckResult("min:amount", True, "", {"actual_min": 0.0}),
        CheckResult("rule:row_count > 100", False, "Rule 'row_count > 100' failed"),
        CheckResult(
            "cross_column:amount_positive",
            False,
            "amount must be positive",
            {"failing_rows": 1, "failing_rate": 0.083},
        ),
    )


class TestGrouping:
    def test_sections_are_grouped_by_kind(self) -> None:
        text = render_result(_sample_failure())
        assert "Schema" in text
        assert "Columns" in text
        assert "Table rules" in text
        assert "Cross-column rules" in text
        # Section order is stable.
        assert (
            text.index("Schema")
            < text.index("Columns")
            < text.index("Table rules")
            < text.index("Cross-column rules")
        )

    def test_header_reports_failed_count_and_footer_reports_both(self) -> None:
        text = render_result(_sample_failure())
        assert "orders" in text.splitlines()[0]
        assert "5 of 7 checks failed" in text
        assert "2 passed" in text
        assert "5 failed" in text

    def test_each_group_header_carries_a_pass_fail_count(self) -> None:
        text = render_result(_sample_failure())
        assert "Schema  1/2 failed" in text
        assert "Columns  2/3 failed" in text
        assert "Table rules  1/1 failed" in text
        assert "Cross-column rules  1/1 failed" in text

    def test_all_passing_header_keeps_ratio(self) -> None:
        text = render_result(
            _result(
                CheckResult("column_exists:a", True),
                CheckResult("not_null:a", True),
            )
        )
        assert "2/2 checks passed" in text

    def test_row_count_rendered_in_header(self) -> None:
        text = render_result(_sample_failure(), row_count=12043)
        assert "on 12,043 rows" in text


class TestDetail:
    def test_failure_shows_bounded_sample(self) -> None:
        text = render_result(_sample_failure())
        assert "e.g. 'GBP', 'JPY'" in text

    def test_failure_shows_rate_as_percentage(self) -> None:
        text = render_result(_sample_failure())
        assert "(25.0%)" in text  # not_null null_rate
        assert "(8.3%)" in text  # cross-column failing_rate

    def test_tiny_rate_is_clamped(self) -> None:
        text = render_result(
            _result(
                CheckResult(
                    "not_null:x",
                    False,
                    "Column 'x' has 1 null values",
                    {"null_rate": 0.0004},
                )
            )
        )
        assert "(<0.1%)" in text

    def test_column_prefix_is_stripped_from_message(self) -> None:
        text = render_result(_sample_failure())
        assert "Column 'order_id' has 3 null values" not in text
        assert "has 3 null values" in text

    def test_rule_boilerplate_message_is_hidden(self) -> None:
        text = render_result(_sample_failure())
        assert "row_count > 100" in text
        assert "Rule 'row_count > 100' failed" not in text

    def test_missing_column_message_is_shown(self) -> None:
        text = render_result(_sample_failure())
        assert "is missing from the data" in text


class TestVerbosity:
    def test_quiet_hides_passing_checks_and_summary_lines(self) -> None:
        text = render_result(_sample_failure(), verbosity=Verbosity.QUIET)
        assert "more columns passed" not in text
        assert "checks passed" not in text
        # "amount" only has a passing min check, so it is not listed at all.
        assert "amount positive" in text.replace("_", " ")  # the cross-column rule
        columns_block = text.split("Columns")[1].split("Table rules")[0]
        assert "amount" not in columns_block

    def test_quiet_still_shows_failures_and_footer(self) -> None:
        text = render_result(_sample_failure(), verbosity=Verbosity.QUIET)
        assert "has 3 null values" in text
        assert "5 failed" in text

    def test_quiet_all_passing_is_compact(self) -> None:
        text = render_result(_result(CheckResult("not_null:a", True)), verbosity=Verbosity.QUIET)
        assert "1/1 checks passed" in text
        assert "Columns" not in text

    def test_verbose_lists_every_check(self) -> None:
        text = render_result(_sample_failure(), verbosity=Verbosity.VERBOSE)
        assert text.count("✔") >= 2  # passing column_exists + passing min
        assert "min" in text

    def test_normal_notes_cleanly_passing_columns(self) -> None:
        text = render_result(
            _result(
                CheckResult("not_null:a", False, "Column 'a' has 1 null value", {"null_rate": 0.5}),
                CheckResult("not_null:b", True),
                CheckResult("min:c", True, "", {}),
            )
        )
        assert "2 more columns passed" in text


class TestColor:
    def test_no_color_by_default(self) -> None:
        assert "\x1b[" not in render_result(_sample_failure())

    def test_color_emits_ansi(self) -> None:
        assert "\x1b[" in render_result(_sample_failure(), color=True)


class TestResolveColor:
    def test_explicit_flag_wins(self) -> None:
        assert resolve_color(True, isatty=False) is True
        assert resolve_color(False, isatty=True) is False

    def test_defaults_to_tty(self) -> None:
        assert resolve_color(None, isatty=True) is True
        assert resolve_color(None, isatty=False) is False

    def test_no_color_env_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        assert resolve_color(None, isatty=True) is False
        # An explicit --color still wins over NO_COLOR.
        assert resolve_color(True, isatty=False) is True
