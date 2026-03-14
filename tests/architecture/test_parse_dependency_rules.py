"""Architecture checks for parse-layer dependency direction."""

from __future__ import annotations

import ast
from pathlib import Path

_PARSE_ROOT = Path("src/infn_jobs/extract/parse")
_BANNED_PREFIXES = ("infn_jobs.fetch", "infn_jobs.store", "infn_jobs.pipeline")


def _collect_parse_py_files() -> list[Path]:
    """Return all parse-layer Python files excluding bytecode artifacts."""
    return sorted(
        path
        for path in _PARSE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def test_parse_layer_does_not_import_fetch_store_or_pipeline() -> None:
    """Parse modules must not import fetch/store/pipeline modules."""
    violations: list[str] = []
    for py_file in _collect_parse_py_files():
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.module else []
            else:
                continue

            for imported_name in names:
                if imported_name and imported_name.startswith(_BANNED_PREFIXES):
                    violations.append(f"{py_file}: {imported_name}")

    assert violations == []

