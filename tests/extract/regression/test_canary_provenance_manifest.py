"""Regression gate for canary provenance manifest integrity."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canary_provenance_manifest_hashes_are_current(capsys) -> None:
    """Current canary provenance manifest should validate fixture hash integrity."""
    module = _load_module(Path("scripts/check_canary_provenance.py"))

    exit_code = module.main(["--manifest", "docs/regressions/canary_provenance.md"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SUMMARY" in output
    assert "errors=0" in output
