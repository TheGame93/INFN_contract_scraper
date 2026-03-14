#!/usr/bin/env python3
"""Print deterministic parse-review artifacts for one local PDF case."""

from __future__ import annotations

import argparse
from pathlib import Path

from infn_jobs.extract.parse.diagnostics.review_mode import (
    build_review_report,
    render_review_report,
)
from infn_jobs.extract.pdf.mutool import extract_text


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for parse-case review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--detail-id",
        required=True,
        help="Detail id for diagnostics traceability.",
    )
    parser.add_argument("--pdf-path", required=True, help="Local PDF path to review.")
    parser.add_argument(
        "--text-quality",
        default=None,
        help="Optional override for text quality (default: mutool-classified value).",
    )
    parser.add_argument("--anno", type=int, default=None, help="Optional year context.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run parse review for one PDF and print deterministic artifacts."""
    parser = build_parser()
    args = parser.parse_args(argv)
    pdf_path = Path(args.pdf_path)
    text, detected_quality = extract_text(pdf_path)
    review = build_review_report(
        text=text,
        detail_id=args.detail_id,
        text_quality=args.text_quality or detected_quality.value,
        anno=args.anno,
    )
    print(render_review_report(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
