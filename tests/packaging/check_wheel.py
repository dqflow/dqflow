"""Validate packaging metadata and contents without installing the wheel."""

from __future__ import annotations

import email
import re
import sys
import zipfile
from pathlib import Path


def main(wheel_name: str) -> None:
    wheel = Path(wheel_name)
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_name))

    assert metadata["Name"] == "dqflow"
    version_source = Path("src/dqflow/_version.py").read_text(encoding="utf-8")
    expected_version = re.search(r'^__version__ = "([^"]+)"$', version_source, re.MULTILINE)
    assert expected_version is not None
    assert metadata["Version"] == expected_version.group(1)
    assert set(metadata["Requires-Python"].split(",")) == {">=3.11", "<3.15"}
    assert set(metadata.get_all("Provides-Extra", [])) == {
        "all",
        "dev",
        "docs",
        "pandas",
        "pandas-parquet",
        "parquet",
        "polars",
    }
    requirements = set(metadata.get_all("Requires-Dist", []))
    assert {"click<9,>=8.1.7", "pyyaml<7,>=6.0.2"} <= requirements
    assert "pandas<4,>=2.3.3; extra == 'pandas'" in requirements
    assert "polars<2,>=1.0; extra == 'polars'" in requirements
    assert "pyarrow<26,>=22; extra == 'pandas-parquet'" in requirements
    assert "dqflow/schema/contract-1.0.json" in names
    assert "dqflow/_version.py" in names
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
    assert not any(name.startswith(("tests/", "docs/", "examples/")) for name in names)


if __name__ == "__main__":
    main(sys.argv[1])
