# Contract diff

`diff_contracts` compares two contracts and classifies each difference as
breaking or non-breaking for data producers. The `dq diff` CLI command wraps it.
See [Diffing contracts](../guide/diff.md) for the classification table and the
JSON schema.

::: dqflow.diff.diff_contracts

::: dqflow.diff.ContractDiff
    options:
      members:
        - breaking_changes
        - non_breaking_changes
        - has_breaking
        - is_empty
        - to_dict
        - render_text

::: dqflow.diff.ContractChange
    options:
      members:
        - breaking
        - to_dict
