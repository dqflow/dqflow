# ValidationSpec

`ValidationSpec` is the engine-agnostic intermediate representation of a
contract. `Contract.validate()` compiles the contract with
`ValidationSpec.from_contract()` and hands the spec to an engine; engines execute
the flat list of `CheckSpec` entries and never read `Column` fields directly.

Most users never construct these types — they are the contract between
`Contract` and the engines, and the extension point for new engines.

::: dqflow.spec.ValidationSpec

::: dqflow.spec.CheckSpec

::: dqflow.spec.CHECK_KINDS
