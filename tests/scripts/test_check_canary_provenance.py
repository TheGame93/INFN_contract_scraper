"""Tests for scripts/check_canary_provenance.py."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def _load_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_manifest(path: Path, rows: list[tuple[str, str, str, str, str, str]]) -> None:
    header = (
        "| detail_id | Fixture path | source_tipo | listing_status | "
        "PDF SHA256 | Fixture TXT SHA256 |\n"
    )
    separator = "|---|---|---|---|---|---|\n"
    body = "".join(
        (
            f"| `{detail_id}` | `{fixture_path}` | `{source_tipo}` | `{listing_status}` | "
            f"`{pdf_sha}` | `{fixture_sha}` |\n"
        )
        for detail_id, fixture_path, source_tipo, listing_status, pdf_sha, fixture_sha in rows
    )
    path.write_text(header + separator + body, encoding="utf-8")


def test_check_canary_provenance_passes_with_valid_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should pass when fixture hashes in the manifest match file contents."""
    fixture = tmp_path / "detail_1000.txt"
    fixture.write_text("fixture-content", encoding="utf-8")
    manifest = tmp_path / "canary_provenance.md"
    _write_manifest(
        manifest,
        [
            (
                "1000",
                str(fixture),
                "Borsa",
                "active",
                "a" * 64,
                _sha256(fixture),
            )
        ],
    )

    module = _load_module(Path("scripts/check_canary_provenance.py"))
    exit_code = module.main(["--manifest", str(manifest)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SUMMARY entries=1" in output
    assert "errors=0" in output


def test_check_canary_provenance_fails_on_duplicate_detail_id(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should fail when manifest contains duplicate detail_id rows."""
    fixture = tmp_path / "detail_1000.txt"
    fixture.write_text("fixture-content", encoding="utf-8")
    fixture_hash = _sha256(fixture)
    manifest = tmp_path / "canary_provenance.md"
    _write_manifest(
        manifest,
        [
            ("1000", str(fixture), "Borsa", "active", "a" * 64, fixture_hash),
            ("1000", str(fixture), "Borsa", "expired", "b" * 64, fixture_hash),
        ],
    )

    module = _load_module(Path("scripts/check_canary_provenance.py"))
    exit_code = module.main(["--manifest", str(manifest)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Duplicate detail_id" in output


def test_check_canary_provenance_fails_on_fixture_hash_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should fail when fixture SHA256 in manifest is stale or incorrect."""
    fixture = tmp_path / "detail_1000.txt"
    fixture.write_text("fixture-content", encoding="utf-8")
    manifest = tmp_path / "canary_provenance.md"
    _write_manifest(
        manifest,
        [
            (
                "1000",
                str(fixture),
                "Borsa",
                "active",
                "a" * 64,
                "f" * 64,
            )
        ],
    )

    module = _load_module(Path("scripts/check_canary_provenance.py"))
    exit_code = module.main(["--manifest", str(manifest)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "fixture SHA256 mismatch" in output


def test_check_canary_provenance_verify_pdf_hashes_skips_missing_pdf(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should warn, not fail, when --verify-pdf-hashes is enabled and PDF is missing."""
    fixture = tmp_path / "detail_1000.txt"
    fixture.write_text("fixture-content", encoding="utf-8")
    manifest = tmp_path / "canary_provenance.md"
    _write_manifest(
        manifest,
        [
            (
                "1000",
                str(fixture),
                "Borsa",
                "active",
                "a" * 64,
                _sha256(fixture),
            )
        ],
    )

    module = _load_module(Path("scripts/check_canary_provenance.py"))
    exit_code = module.main(
        [
            "--manifest",
            str(manifest),
            "--verify-pdf-hashes",
            "--pdf-cache-dir",
            str(tmp_path / "pdf_cache"),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "WARN detail_id=1000: PDF missing in cache" in output
    assert "verify_pdf_hashes=yes" in output


def test_check_canary_provenance_verify_pdf_hashes_fails_on_pdf_mismatch(
    tmp_path: Path,
    capsys,
) -> None:
    """Checker should fail when a present PDF hash differs from the manifest value."""
    fixture = tmp_path / "detail_1000.txt"
    fixture.write_text("fixture-content", encoding="utf-8")
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    (pdf_cache / "1000.pdf").write_bytes(b"pdf-content")

    manifest = tmp_path / "canary_provenance.md"
    _write_manifest(
        manifest,
        [
            (
                "1000",
                str(fixture),
                "Borsa",
                "active",
                "a" * 64,
                _sha256(fixture),
            )
        ],
    )

    module = _load_module(Path("scripts/check_canary_provenance.py"))
    exit_code = module.main(
        [
            "--manifest",
            str(manifest),
            "--verify-pdf-hashes",
            "--pdf-cache-dir",
            str(pdf_cache),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "PDF SHA256 mismatch" in output
