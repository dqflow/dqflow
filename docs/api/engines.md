# Engines

Engines execute the same contract against a DataFrame implementation and return
the shared `ValidationResult` format.

## Engine interface

::: dqflow.engines.base.Engine

## PandasEngine

::: dqflow.engines.pandas.PandasEngine

## PolarsEngine

::: dqflow.engines.polars.PolarsEngine

The Polars engine is experimental and requires `pip install "dqflow[polars]"`.
It accepts both `polars.DataFrame` and `polars.LazyFrame`; a lazy frame is
currently collected before validation.

See [Choosing an engine](../guide/engines.md) for usage and trade-offs.
