# Infer and refine example

This example infers a draft from customer data, adjusts observed constraints to
business rules, writes a temporary YAML contract, and validates the source.

```bash
pip install dqflow
python examples/infer-refine/infer_and_validate.py
```

The checked-in `contract.yaml` shows the curated result that a team would review
and commit after inference.
