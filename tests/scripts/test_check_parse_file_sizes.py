"""Tests for scripts/check_parse_file_sizes.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_parse_file_sizes_warns_and_passes_without_failures(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should emit WARN lines and succeed when nothing exceeds fail threshold."""
    root = tmp_path / "parse"
    root.mkdir()
    (root / "a.py").write_text("\n".join("x=1" for _ in range(4)), encoding="utf-8")
    (root / "b.py").write_text("\n".join("x=1" for _ in range(2)), encoding="utf-8")
    module = _load_module(Path("scripts/check_parse_file_sizes.py"))

    exit_code = module.main(["--root", str(root), "--warn", "3", "--fail", "10"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "WARN" in output
    assert "SUMMARY" in output
    assert "failures=0" in output


def test_check_parse_file_sizes_fails_when_file_exceeds_limit(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should emit FAIL lines and non-zero exit code when threshold exceeded."""
    root = tmp_path / "parse"
    root.mkdir()
    (root / "a.py").write_text("\n".join("x=1" for _ in range(11)), encoding="utf-8")
    module = _load_module(Path("scripts/check_parse_file_sizes.py"))

    exit_code = module.main(["--root", str(root), "--warn", "3", "--fail", "10"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "FAIL" in output
    assert "failures=1" in output


def test_check_parse_file_sizes_real_parse_tree_has_no_warnings(capsys) -> None:
    """Project parse tree should currently fit within warn/fail size thresholds."""
    module = _load_module(Path("scripts/check_parse_file_sizes.py"))

    exit_code = module.main(
        [
            "--root",
            "src/infn_jobs/extract/parse",
            "--warn",
            "150",
            "--fail",
            "250",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "warnings=0" in output
    assert "failures=0" in output
