#!/usr/bin/env python3
"""Generate docs/info_functions.md from source docstrings.

Walks src/infn_jobs/, extracts public functions and classes via the `ast`
module (no runtime import of the package), and writes a compact markdown
index to docs/info_functions.md.

Usage (run from project root):
    python3 scripts/gen_info_functions.py
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path("src/infn_jobs")
OUTPUT = Path("docs/info_functions.md")


def _module_name(path: Path) -> str:
    """Convert a source file path to a dotted module name."""
    parts = path.with_suffix("").parts
    try:
        idx = list(parts).index("src")
        return ".".join(parts[idx + 1 :])
    except ValueError:
        return ".".join(parts)


def _render_args(args: ast.arguments) -> str:
    """Render function arguments as 'name: type, ...' skipping self/cls."""
    parts = []
    for arg in args.posonlyargs + args.args + args.kwonlyargs:
        if arg.arg in ("self", "cls"):
            continue
        if arg.annotation:
            parts.append(f"`{arg.arg}: {ast.unparse(arg.annotation)}`")
        else:
            parts.append(f"`{arg.arg}`")
    if args.vararg:
        a = args.vararg
        ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
        parts.append(f"`*{a.arg}{ann}`")
    if args.kwarg:
        a = args.kwarg
        ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
        parts.append(f"`**{a.arg}{ann}`")
    return ", ".join(parts) if parts else "—"


def _render_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render the return annotation, or '—' if absent."""
    return f"`{ast.unparse(node.returns)}`" if node.returns else "—"


def _entry(
    name: str,
    parent: str,
    inputs: str,
    output: str,
    description: str,
) -> str:
    """Format one compact markdown entry line."""
    return f"- `{name}` | `{parent}` | {inputs} | {output} | {description}"


def _extract_entries(path: Path) -> list[tuple[int, str]]:
    """Return (lineno, markdown_entry) tuples for public symbols in path."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    file_rel = str(path).replace("\\", "/")
    mod_name = _module_name(path)
    entries: list[tuple[int, str]] = []

    for node in tree.body:
        # ── Top-level class ──────────────────────────────────────────────
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            doc = ast.get_docstring(node) or "(no docstring)"
            e = _entry(node.name, mod_name, "—", "—", doc.splitlines()[0])
            entries.append((node.lineno, e))

            # Public methods (excluding dunder methods except __init__)
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name.startswith("_"):
                    continue
                mdoc = ast.get_docstring(item) or "(no docstring)"
                e = _entry(
                    item.name,
                    node.name,
                    _render_args(item.args),
                    _render_return(item),
                    mdoc.splitlines()[0],
                )
                entries.append((item.lineno, e))

        # ── Top-level function ────────────────────────────────────────────
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            doc = ast.get_docstring(node) or "(no docstring)"
            e = _entry(
                node.name,
                mod_name,
                _render_args(node.args),
                _render_return(node),
                doc.splitlines()[0],
            )
            entries.append((node.lineno, e))

    return entries


def main() -> None:
    """Walk src/infn_jobs/, extract docstrings, write docs/info_functions.md."""
    if not SRC_ROOT.exists():
        raise SystemExit(
            f"Source root not found: {SRC_ROOT}\n"
            "Run this script from the project root directory."
        )

    all_entries: list[tuple[str, int, str]] = []  # (file_rel, lineno, markdown)
    for path in sorted(SRC_ROOT.rglob("*.py")):
        file_rel = str(path).replace("\\", "/")
        for lineno, text in _extract_entries(path):
            all_entries.append((file_rel, lineno, text))

    # Sort by file path (alphabetical), then by line number within each file
    all_entries.sort(key=lambda x: (x[0], x[1]))

    header = (
        "# Function and Class Index\n\n"
        "> **Location:** `docs/info_functions.md`  \n"
        "> **Auto-generated** by `scripts/gen_info_functions.py` — do not edit by hand.  \n"
        "> Re-run whenever public functions are added, renamed, or removed:\n"
        "> `python3 scripts/gen_info_functions.py`\n\n"
        "Fields per entry: `name | parent | inputs | output | description`\n\n"
    )

    lines: list[str] = []
    current_file: str | None = None
    for file_rel, _, text in all_entries:
        if file_rel != current_file:
            if current_file is not None:
                lines.append("")
            lines.append(f"## `{file_rel}`")
            current_file = file_rel
        lines.append(text)

    body = "\n".join(lines)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(header + body + "\n", encoding="utf-8")
    print(f"Written {len(all_entries)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()
