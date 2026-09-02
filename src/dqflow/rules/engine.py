"""A safe evaluator for table-rule expressions.

Table rules are short boolean expressions over three names:

* ``row_count`` — the number of rows (an ``int``)
* ``null_rate('col')`` — the fraction of nulls in ``col`` (``0.0`` when the
  column is absent)
* ``unique_count('col')`` — the number of distinct values in ``col``

Expressions are parsed with :mod:`ast` and evaluated by walking a strict
whitelist of node types — no :func:`eval`, no attribute access, no builtins.
This is a smaller surface than ``eval`` but, as the docs say, still not a
security boundary: only run rules from contracts you trust.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from typing import Any

_BIN_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_CMP_OPS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

_STAT_FUNCTIONS = frozenset({"null_rate", "unique_count"})


class RuleError(Exception):
    """Raised when a table-rule expression cannot be parsed or is not allowed."""


def evaluate_rule(
    expression: str,
    *,
    row_count: int,
    null_rate: Callable[[str], float],
    unique_count: Callable[[str], float],
) -> bool:
    """Evaluate ``expression`` and return its truthiness as a ``bool``.

    Args:
        expression: The rule text, e.g. ``"row_count > 0 and null_rate('x') < 0.1"``.
        row_count: Value bound to the ``row_count`` name.
        null_rate: Called with a column name for ``null_rate('col')``.
        unique_count: Called with a column name for ``unique_count('col')``.

    Raises:
        RuleError: If the expression is syntactically invalid or uses a
            construct outside the supported whitelist.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise RuleError(f"could not parse rule {expression!r}: {exc.msg}") from exc

    evaluator = _Evaluator(
        names={"row_count": row_count},
        functions={"null_rate": null_rate, "unique_count": unique_count},
    )
    return bool(evaluator.run(tree.body))


class _Evaluator:
    def __init__(
        self,
        *,
        names: dict[str, Any],
        functions: dict[str, Callable[[str], float]],
    ) -> None:
        self._names = names
        self._functions = functions

    def run(self, node: ast.AST) -> Any:
        handler = getattr(self, f"_eval_{type(node).__name__}", None)
        if handler is None:
            raise RuleError(f"{type(node).__name__} is not allowed in a rule expression")
        return handler(node)

    def _eval_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (str, int, float, bool)) or node.value is None:
            return node.value
        raise RuleError(f"constant {node.value!r} is not allowed in a rule expression")

    def _eval_Name(self, node: ast.Name) -> Any:
        try:
            return self._names[node.id]
        except KeyError:
            raise RuleError(f"unknown name {node.id!r} in rule expression") from None

    def _eval_BoolOp(self, node: ast.BoolOp) -> Any:
        values = node.values
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in values:
                result = self.run(value)
                if not result:
                    return result
            return result
        result = False
        for value in values:
            result = self.run(value)
            if result:
                return result
        return result

    def _eval_UnaryOp(self, node: ast.UnaryOp) -> Any:
        fn = _UNARY_OPS.get(type(node.op))
        if fn is None:
            raise RuleError(f"unary operator {type(node.op).__name__} is not allowed")
        return fn(self.run(node.operand))

    def _eval_BinOp(self, node: ast.BinOp) -> Any:
        fn = _BIN_OPS.get(type(node.op))
        if fn is None:
            raise RuleError(f"operator {type(node.op).__name__} is not allowed")
        return fn(self.run(node.left), self.run(node.right))

    def _eval_Compare(self, node: ast.Compare) -> bool:
        left = self.run(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            fn = _CMP_OPS.get(type(op_node))
            if fn is None:
                raise RuleError(f"comparison {type(op_node).__name__} is not allowed")
            right = self.run(comparator)
            if not fn(left, right):
                return False
            left = right
        return True

    def _eval_Call(self, node: ast.Call) -> float:
        if not isinstance(node.func, ast.Name) or node.func.id not in _STAT_FUNCTIONS:
            raise RuleError("only null_rate() and unique_count() may be called in a rule")
        if node.keywords or len(node.args) != 1:
            raise RuleError(f"{node.func.id}() takes exactly one column-name argument")
        arg = node.args[0]
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            raise RuleError(f"{node.func.id}() argument must be a string literal")
        return self._functions[node.func.id](arg.value)
