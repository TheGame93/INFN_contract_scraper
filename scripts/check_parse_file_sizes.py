#!/usr/bin/env python3
"""Warn/fail when parse module files exceed configured line-count thresholds."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for parse file-size policy checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory to scan recursively for *.py.",
    )
    parser.add_argument("--warn", type=int, default=150, help="Warn threshold in lines.")
    parser.add_argument("--fail", type=int, default=250, help="Fail threshold in lines.")
    return parser


def _line_count(path: Path) -> int:
    """Return number of text lines in path."""
    return len(path.read_text(encoding="utf-8").splitlines())


def main(argv: list[str] | None = None) -> int:
    """Run parse file-size checks and return process exit code."""
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    paths = sorted(path for path in root.rglob("*.py") if path.is_file())

    warn_hits: list[tuple[Path, int]] = []
    fail_hits: list[tuple[Path, int]] = []

    for path in paths:
        lines = _line_count(path)
        if lines > args.fail:
            fail_hits.append((path, lines))
        elif lines > args.warn:
            warn_hits.append((path, lines))

    for path, lines in warn_hits:
        print(f"WARN {lines:4d} {path}")
    for path, lines in fail_hits:
        print(f"FAIL {lines:4d} {path}")

    print(
        f"SUMMARY warn>{args.warn} fail>{args.fail} scanned={len(paths)} "
        f"warnings={len(warn_hits)} failures={len(fail_hits)}"
    )
    return 1 if fail_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
