#!/usr/bin/env python3
"""Validate canary provenance manifest structure and fixture hash integrity."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import NamedTuple

REQUIRED_COLUMNS = (
    "detail_id",
    "Fixture path",
    "source_tipo",
    "listing_status",
    "PDF SHA256",
    "Fixture TXT SHA256",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceEntry(NamedTuple):
    """One parsed row from the canary provenance manifest table."""

    detail_id: str
    fixture_path: str
    source_tipo: str
    listing_status: str
    pdf_sha256: str
    fixture_txt_sha256: str


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for canary provenance validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="docs/regressions/canary_provenance.md",
        help="Path to canary provenance markdown manifest.",
    )
    parser.add_argument(
        "--verify-pdf-hashes",
        action="store_true",
        help="Also verify PDF hashes for local cache files when present.",
    )
    parser.add_argument(
        "--pdf-cache-dir",
        default="data/pdf_cache",
        help="PDF cache directory used when --verify-pdf-hashes is enabled.",
    )
    return parser


def _strip_code(value: str) -> str:
    """Return value without optional markdown inline-code backticks."""
    stripped = value.strip()
    if stripped.startswith("`") and stripped.endswith("`") and len(stripped) >= 2:
        return stripped[1:-1].strip()
    return stripped


def _sha256(path: Path) -> str:
    """Return lowercase SHA256 hex digest for one file path."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: str) -> bool:
    """Return True when value is a lowercase 64-char SHA256 hex string."""
    return bool(_SHA256_RE.fullmatch(value))


def parse_manifest(manifest_path: Path) -> tuple[list[ProvenanceEntry], list[str]]:
    """Parse provenance markdown table rows and return entries + parse errors."""
    errors: list[str] = []
    lines = manifest_path.read_text(encoding="utf-8").splitlines()

    header_index: int | None = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and "detail_id" in line:
            header_index = idx
            break
    if header_index is None or header_index + 1 >= len(lines):
        return [], ["Manifest table header not found."]

    header_cells = [cell.strip() for cell in lines[header_index].strip().strip("|").split("|")]
    if tuple(header_cells) != REQUIRED_COLUMNS:
        errors.append(
            "Manifest columns mismatch. "
            f"Expected {REQUIRED_COLUMNS}, found {tuple(header_cells)}."
        )
        return [], errors

    separator_line = lines[header_index + 1].strip().strip("|")
    separator_cells = [cell.strip() for cell in separator_line.split("|")]
    if len(separator_cells) != len(REQUIRED_COLUMNS) or not all(
        set(cell) <= {"-", ":"} and cell for cell in separator_cells
    ):
        errors.append("Manifest table separator row is invalid.")
        return [], errors

    entries: list[ProvenanceEntry] = []
    for line in lines[header_index + 2 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != len(REQUIRED_COLUMNS):
            errors.append(f"Invalid table row cell count: {line}")
            continue

        detail_id, fixture_path, source_tipo, listing_status, pdf_sha, fixture_sha = (
            _strip_code(cell) for cell in cells
        )
        entries.append(
            ProvenanceEntry(
                detail_id=detail_id,
                fixture_path=fixture_path,
                source_tipo=source_tipo,
                listing_status=listing_status,
                pdf_sha256=pdf_sha.lower(),
                fixture_txt_sha256=fixture_sha.lower(),
            )
        )

    if not entries:
        errors.append("Manifest table contains no data rows.")

    return entries, errors


def validate_manifest(
    entries: list[ProvenanceEntry],
    *,
    verify_pdf_hashes: bool,
    pdf_cache_dir: Path,
) -> tuple[list[str], list[str]]:
    """Validate parsed manifest entries and return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    seen_detail_ids: set[str] = set()
    for entry in entries:
        if not entry.detail_id:
            errors.append("Entry has empty detail_id.")
        if entry.detail_id in seen_detail_ids:
            errors.append(f"Duplicate detail_id in manifest: {entry.detail_id}")
        seen_detail_ids.add(entry.detail_id)

        if not entry.fixture_path:
            errors.append(f"detail_id={entry.detail_id}: empty fixture path.")
            continue

        fixture_path = Path(entry.fixture_path)
        if not fixture_path.exists():
            errors.append(
                f"detail_id={entry.detail_id}: fixture file missing: {entry.fixture_path}"
            )
            continue

        if not _is_sha256(entry.fixture_txt_sha256):
            errors.append(
                f"detail_id={entry.detail_id}: invalid fixture SHA256 format: "
                f"{entry.fixture_txt_sha256}"
            )
        else:
            fixture_hash = _sha256(fixture_path)
            if fixture_hash != entry.fixture_txt_sha256:
                errors.append(
                    f"detail_id={entry.detail_id}: fixture SHA256 mismatch "
                    f"(manifest={entry.fixture_txt_sha256}, actual={fixture_hash})"
                )

        if not _is_sha256(entry.pdf_sha256):
            errors.append(
                f"detail_id={entry.detail_id}: invalid PDF SHA256 format: {entry.pdf_sha256}"
            )
        if verify_pdf_hashes:
            pdf_path = pdf_cache_dir / f"{entry.detail_id}.pdf"
            if not pdf_path.exists():
                warnings.append(
                    f"detail_id={entry.detail_id}: PDF missing in cache, skipped PDF hash check"
                )
                continue
            pdf_hash = _sha256(pdf_path)
            if pdf_hash != entry.pdf_sha256:
                errors.append(
                    f"detail_id={entry.detail_id}: PDF SHA256 mismatch "
                    f"(manifest={entry.pdf_sha256}, actual={pdf_hash})"
                )

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Validate canary provenance manifest and return process exit code."""
    args = build_parser().parse_args(argv)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR manifest not found: {manifest_path}")
        return 1

    entries, parse_errors = parse_manifest(manifest_path)
    for error in parse_errors:
        print(f"ERROR {error}")
    if parse_errors:
        print(f"SUMMARY entries=0 warnings=0 errors={len(parse_errors)}")
        return 1

    errors, warnings = validate_manifest(
        entries,
        verify_pdf_hashes=args.verify_pdf_hashes,
        pdf_cache_dir=Path(args.pdf_cache_dir),
    )
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}")

    print(
        f"SUMMARY entries={len(entries)} warnings={len(warnings)} errors={len(errors)} "
        f"verify_pdf_hashes={'yes' if args.verify_pdf_hashes else 'no'}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
