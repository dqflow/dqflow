# Table-rule evaluator

`dqflow.rules.evaluate_rule` is the single evaluator for table-rule expressions,
shared by every engine. It parses the expression with `ast` and walks a strict
whitelist — `row_count`, `null_rate('col')`, `unique_count('col')`, literals,
`and` / `or` / `not`, arithmetic, and comparisons. No `eval`, no attribute
access, no builtins.

See [Table rules](../guide/rules.md) for the expression language and the safety
model.

::: dqflow.rules.evaluate_rule

::: dqflow.rules.RuleError
