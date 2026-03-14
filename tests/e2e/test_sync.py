"""End-to-end tests for the sync pipeline with mocked I/O boundaries."""

import sqlite3
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import TextQuality
from infn_jobs.domain.position import PositionRow
from infn_jobs.pipeline.export import run_export
from infn_jobs.pipeline.sync import run_sync
from infn_jobs.store.schema import init_db
from infn_jobs.store.upsert import upsert_call

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pdf_text"
MULTI_TEXT: str = (_FIXTURES_DIR / "multi_same_type.txt").read_text(encoding="utf-8")
OCR_DEGRADED_TEXT: str = (_FIXTURES_DIR / "ocr_degraded.txt").read_text(encoding="utf-8")

_TIPOS = [
    "Borsa",
    "Incarico di ricerca",
    "Incarico Post-Doc",
    "Contratto di ricerca",
    "Assegno di ricerca",
]


def make_calls() -> list[CallRaw]:
    """Return one CallRaw per TIPO for e2e testing."""
    calls = [
        CallRaw(
            detail_id="e2e-borsa-1",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url="https://jobs.dsi.infn.it/bando.pdf",
            anno="2022",
        ),
        CallRaw(
            detail_id="e2e-assegno-1",
            source_tipo="Assegno di ricerca",
            listing_status="active",
            pdf_url=None,
            anno="2005",
        ),
    ]
    remaining = [t for t in _TIPOS if t not in ("Borsa", "Assegno di ricerca")]
    for i, tipo in enumerate(remaining):
        calls.append(
            CallRaw(
                detail_id=f"e2e-{i}",
                source_tipo=tipo,
                listing_status="expired",
                pdf_url="https://jobs.dsi.infn.it/bando2.pdf",
                anno="2015",
            )
        )
    return calls


def _make_conn(tmp_path: Path) -> sqlite3.Connection:
    """Create and initialise a fresh SQLite connection."""
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    init_db(conn)
    return conn


def _patch_sync(tmp_path: Path, text: str = MULTI_TEXT, quality: TextQuality = TextQuality.DIGITAL):
    """Return a context-manager stack that patches all I/O in run_sync."""
    mock_pdf_path = tmp_path / "mock.pdf"
    mock_pdf_path.touch()

    return (
        patch(
            "infn_jobs.pipeline.sync.fetch_all_calls",
            side_effect=lambda session, tipo, *_args: [
                c for c in make_calls() if c.source_tipo == tipo
            ],
        ),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf_path),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=(text, quality)),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sync_runs_without_error(tmp_path: Path) -> None:
    """run_sync must complete without raising."""
    conn = _make_conn(tmp_path)
    with patch(
        "infn_jobs.pipeline.sync.fetch_all_calls",
        side_effect=lambda session, tipo, *_args: [
            c for c in make_calls() if c.source_tipo == tipo
        ],
    ), patch("infn_jobs.pipeline.sync.download", return_value=tmp_path / "mock.pdf"), patch(
        "infn_jobs.pipeline.sync.extract_text", return_value=(MULTI_TEXT, TextQuality.DIGITAL)
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)
    conn.close()


def test_sync_uses_build_rows_tuple_contract_and_persists_title(tmp_path: Path) -> None:
    """run_sync must honor `(rows, pdf_call_title)` from build_rows."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / "mock-contract-shape.pdf"
    mock_pdf_path.touch()
    remote_call = CallRaw(
        detail_id="contract-shape-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/contract-shape-1.pdf",
        anno="2026",
    )
    built_rows = [
        PositionRow(
            detail_id="contract-shape-1",
            position_row_index=0,
            text_quality="digital",
            contract_type="Borsa di studio",
        )
    ]

    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf_path),
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=("fixture text", TextQuality.DIGITAL),
        ),
        patch(
            "infn_jobs.pipeline.sync.build_rows",
            return_value=(built_rows, "Tuple contract title"),
        ) as build_rows_mock,
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    build_rows_mock.assert_called_once_with("fixture text", "contract-shape-1", "digital", 2026)
    stored_title = conn.execute(
        "SELECT pdf_call_title FROM calls_raw WHERE detail_id = 'contract-shape-1'"
    ).fetchone()[0]
    stored_rows = conn.execute(
        "SELECT COUNT(*) FROM position_rows WHERE detail_id = 'contract-shape-1'"
    ).fetchone()[0]
    assert stored_title == "Tuple contract title"
    assert stored_rows == 1
    conn.close()


def test_sync_request_processing_is_serial(tmp_path: Path) -> None:
    """run_sync must process request-bearing operations strictly in serial order."""
    conn = Mock()
    session = Mock()
    mock_pdf = tmp_path / "serial.pdf"
    mock_pdf.touch()
    events: list[str] = []

    calls = [
        CallRaw(
            detail_id="serial-1",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url="https://jobs.dsi.infn.it/serial-1.pdf",
            anno="2022",
        ),
        CallRaw(
            detail_id="serial-2",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url="https://jobs.dsi.infn.it/serial-2.pdf",
            anno="2022",
        ),
    ]

    def _fetch_all_calls(_session, tipo):
        events.append(f"fetch_all_calls:{tipo}")
        return calls

    def _download(_url, dest, session=None, force=False):
        events.append(f"download:{dest.stem}")
        return mock_pdf

    def _extract_text(_pdf_path):
        events.append("extract_text")
        return MULTI_TEXT, TextQuality.DIGITAL

    def _build_rows(_text, detail_id, _text_quality, _anno):
        events.append(f"build_rows:{detail_id}")
        return [PositionRow(detail_id=detail_id, position_row_index=0)], None

    def _upsert_call(_conn, call):
        events.append(f"upsert_call:{call.detail_id}")

    def _upsert_position_rows(_conn, rows):
        events.append(f"upsert_position_rows:{rows[0].detail_id}")

    def _rebuild_curated(_conn):
        events.append("rebuild_curated")

    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", side_effect=_fetch_all_calls),
        patch("infn_jobs.pipeline.sync.download", side_effect=_download),
        patch("infn_jobs.pipeline.sync.extract_text", side_effect=_extract_text),
        patch("infn_jobs.pipeline.sync.build_rows", side_effect=_build_rows),
        patch("infn_jobs.pipeline.sync.upsert_call", side_effect=_upsert_call),
        patch("infn_jobs.pipeline.sync.upsert_position_rows", side_effect=_upsert_position_rows),
        patch("infn_jobs.pipeline.sync.rebuild_curated", side_effect=_rebuild_curated),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    assert events == [
        "fetch_all_calls:Borsa",
        "download:serial-1",
        "download:serial-2",
        "extract_text",
        "build_rows:serial-1",
        "extract_text",
        "build_rows:serial-2",
        "upsert_call:serial-1",
        "upsert_position_rows:serial-1",
        "upsert_call:serial-2",
        "upsert_position_rows:serial-2",
        "rebuild_curated",
    ]


def test_sync_remote_source_passes_limit_to_fetch_orchestrator() -> None:
    """run_sync must pass limit_per_tipo to fetch_all_calls for source=remote."""
    conn = Mock()
    session = Mock()
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]) as fetch_mock,
    ):
        run_sync(
            conn,
            source="remote",
            limit_per_tipo=3,
            download_only=False,
            dry_run=True,
            force_refetch=False,
        )

    fetch_mock.assert_called_once_with(session, "Borsa", 3)


def test_sync_auto_source_passes_limit_to_fetch_orchestrator() -> None:
    """run_sync must pass limit_per_tipo to fetch_all_calls for source=auto."""
    conn = Mock()
    session = Mock()
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=[]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]) as fetch_mock,
    ):
        run_sync(
            conn,
            source="auto",
            limit_per_tipo=2,
            download_only=False,
            dry_run=True,
            force_refetch=False,
        )

    fetch_mock.assert_called_once_with(session, "Borsa", 2)


def test_sync_local_source_does_not_pass_limit_to_fetch_orchestrator() -> None:
    """run_sync local discovery must not call fetch_all_calls."""
    conn = Mock()
    session = Mock()
    local_call = CallRaw(detail_id="local-1", pdf_url=None)
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=[local_call]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]) as fetch_mock,
    ):
        run_sync(
            conn,
            source="local",
            limit_per_tipo=4,
            download_only=False,
            dry_run=True,
            force_refetch=False,
        )

    fetch_mock.assert_not_called()


def test_sync_local_source_bootstrap_empty_db_raises_actionable_error(tmp_path: Path) -> None:
    """source=local with empty calls_raw must fail fast with actionable guidance."""
    conn = _make_conn(tmp_path)

    with pytest.raises(ValueError, match="--source remote"):
        run_sync(conn, source="local", dry_run=True)

    conn.close()


def test_sync_local_source_uses_db_calls_and_local_cache_only(tmp_path: Path) -> None:
    """source=local must parse existing cache without listing/detail fetch or downloads."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    local_pdf = cache_dir / "local-1.pdf"
    local_pdf.write_bytes(b"%PDF-local")
    upsert_call(
        conn,
        CallRaw(
            detail_id="local-1",
            source_tipo="Borsa",
            pdf_url="https://jobs.dsi.infn.it/local-1.pdf",
            pdf_cache_path=str(local_pdf),
            listing_status="active",
            anno="2022",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.fetch_all_calls") as fetch_mock,
        patch("infn_jobs.pipeline.sync.download") as download_mock,
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=("", TextQuality.NO_TEXT),
        ) as extract_mock,
    ):
        run_sync(conn, source="local", dry_run=True)

    fetch_mock.assert_not_called()
    download_mock.assert_not_called()
    extract_mock.assert_called_once_with(local_pdf)
    conn.close()


def test_sync_auto_source_uses_local_db_and_downloads_missing_cache(tmp_path: Path) -> None:
    """source=auto with non-empty DB must avoid listing fetch and download only missing caches."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    expected_dest = cache_dir / "auto-1.pdf"
    upsert_call(
        conn,
        CallRaw(
            detail_id="auto-1",
            source_tipo="Borsa",
            pdf_url="https://jobs.dsi.infn.it/auto-1.pdf",
            pdf_cache_path=None,
            listing_status="active",
            anno="2021",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.fetch_all_calls") as fetch_mock,
        patch("infn_jobs.pipeline.sync.download", return_value=expected_dest) as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
    ):
        run_sync(conn, source="auto", dry_run=True)

    fetch_mock.assert_not_called()
    download_mock.assert_called_once()
    assert download_mock.call_args.args[0] == "https://jobs.dsi.infn.it/auto-1.pdf"
    assert download_mock.call_args.args[1] == cache_dir / "auto-1.pdf"
    assert download_mock.call_args.kwargs["force"] is False
    conn.close()


def test_sync_auto_source_falls_back_to_remote_when_db_empty() -> None:
    """source=auto must fetch remotely when local DB has zero calls."""
    conn = Mock()
    session = Mock()
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.list_calls_for_pdf_processing", return_value=[]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]) as fetch_mock,
    ):
        run_sync(conn, source="auto", dry_run=True)

    fetch_mock.assert_called_once_with(session, "Borsa")


def test_sync_download_only_skips_parse_and_db_writes(tmp_path: Path) -> None:
    """download_only=True must stop after cache materialization and skip persistence."""
    conn = Mock()
    session = Mock()
    cached_pdf = tmp_path / "download-only.pdf"
    cached_pdf.write_bytes(b"%PDF-download-only")
    remote_call = CallRaw(
        detail_id="download-only-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/download-only-1.pdf",
    )
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=cached_pdf) as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text") as extract_mock,
        patch("infn_jobs.pipeline.sync.build_rows") as build_rows_mock,
        patch("infn_jobs.pipeline.sync.upsert_call") as upsert_call_mock,
        patch("infn_jobs.pipeline.sync.upsert_position_rows") as upsert_rows_mock,
        patch("infn_jobs.pipeline.sync.rebuild_curated") as rebuild_mock,
    ):
        run_sync(conn, source="remote", download_only=True, dry_run=False)

    download_mock.assert_called_once()
    extract_mock.assert_not_called()
    build_rows_mock.assert_not_called()
    upsert_call_mock.assert_not_called()
    upsert_rows_mock.assert_not_called()
    rebuild_mock.assert_not_called()


def test_sync_local_source_falls_back_to_canonical_cache_when_stored_path_is_stale(
    tmp_path: Path,
) -> None:
    """source=local must use canonical cache path when stored path is stale."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    canonical_pdf = cache_dir / "fallback-1.pdf"
    canonical_pdf.write_bytes(b"%PDF-fallback")
    stale_path = tmp_path / "missing.pdf"
    upsert_call(
        conn,
        CallRaw(
            detail_id="fallback-1",
            source_tipo="Borsa",
            pdf_url=None,
            pdf_cache_path=str(stale_path),
            listing_status="active",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.download") as download_mock,
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=("", TextQuality.NO_TEXT),
        ) as extract_mock,
    ):
        run_sync(conn, source="local", dry_run=True)

    download_mock.assert_not_called()
    extract_mock.assert_called_once_with(canonical_pdf)
    conn.close()


def test_sync_local_source_logs_orphan_cache_files(tmp_path: Path, caplog) -> None:
    """source=local must warn about orphan cache files without matching calls_raw detail_id."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "known-1.pdf").write_bytes(b"%PDF-known")
    (cache_dir / "orphan-999.pdf").write_bytes(b"%PDF-orphan")
    upsert_call(
        conn,
        CallRaw(
            detail_id="known-1",
            source_tipo="Borsa",
            pdf_url=None,
            pdf_cache_path=str(cache_dir / "known-1.pdf"),
            listing_status="active",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        caplog.at_level("WARNING", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="local", dry_run=True)

    assert "Orphan cache file orphan-999.pdf" in caplog.text
    conn.close()


def test_sync_remote_source_orphan_scan_respects_discovered_and_db_ids(
    tmp_path: Path, caplog
) -> None:
    """source=remote orphan scan must ignore cache files tied to DB or discovered calls."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "known-db-1.pdf").write_bytes(b"%PDF-known-db")
    (cache_dir / "known-remote-1.pdf").write_bytes(b"%PDF-known-remote")
    (cache_dir / "orphan-remote-1.pdf").write_bytes(b"%PDF-orphan-remote")
    upsert_call(
        conn,
        CallRaw(
            detail_id="known-db-1",
            source_tipo="Borsa",
            pdf_url=None,
            pdf_cache_path=str(cache_dir / "known-db-1.pdf"),
            listing_status="active",
        ),
    )
    remote_call = CallRaw(
        detail_id="known-remote-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url=None,
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        caplog.at_level("WARNING", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=True)

    assert "Orphan cache file orphan-remote-1.pdf" in caplog.text
    assert "Orphan cache file known-db-1.pdf" not in caplog.text
    assert "Orphan cache file known-remote-1.pdf" not in caplog.text
    conn.close()


def test_sync_auto_fallback_remote_runs_orphan_scan(tmp_path: Path, caplog) -> None:
    """source=auto fallback-to-remote must run orphan scan with discovered ids."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "auto-fallback-1.pdf").write_bytes(b"%PDF-known-auto-fallback")
    (cache_dir / "orphan-auto-fallback-1.pdf").write_bytes(b"%PDF-orphan-auto-fallback")
    remote_call = CallRaw(
        detail_id="auto-fallback-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url=None,
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]) as fetch_mock,
        caplog.at_level("WARNING", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="auto", dry_run=True)

    fetch_mock.assert_called_once()
    assert "Orphan cache file orphan-auto-fallback-1.pdf" in caplog.text
    assert "Orphan cache file auto-fallback-1.pdf" not in caplog.text
    conn.close()


def test_sync_local_source_missing_cache_warns_and_skips(tmp_path: Path, caplog) -> None:
    """source=local must warn and skip when no valid cache is available."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    upsert_call(
        conn,
        CallRaw(
            detail_id="missing-local-1",
            source_tipo="Borsa",
            pdf_url="https://jobs.dsi.infn.it/missing-local-1.pdf",
            pdf_cache_path=None,
            listing_status="active",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.download") as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text") as extract_mock,
        caplog.at_level("WARNING", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="local", dry_run=True)

    download_mock.assert_not_called()
    extract_mock.assert_not_called()
    assert "missing valid local cache" in caplog.text
    conn.close()


def test_sync_local_source_zero_byte_cache_warns_and_skips(tmp_path: Path, caplog) -> None:
    """source=local must treat zero-byte cache as invalid and skip without download."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zero_pdf = cache_dir / "zero-local-1.pdf"
    zero_pdf.write_bytes(b"")
    upsert_call(
        conn,
        CallRaw(
            detail_id="zero-local-1",
            source_tipo="Borsa",
            pdf_url="https://jobs.dsi.infn.it/zero-local-1.pdf",
            pdf_cache_path=str(zero_pdf),
            listing_status="active",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.download") as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text") as extract_mock,
        caplog.at_level("WARNING", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="local", dry_run=True)

    download_mock.assert_not_called()
    extract_mock.assert_not_called()
    assert "zero-byte local cache detected" in caplog.text
    conn.close()


def test_sync_remote_source_zero_byte_cache_forces_redownload(tmp_path: Path) -> None:
    """source=remote must force re-download when canonical cache is zero-byte."""
    conn = Mock()
    session = Mock()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zero_pdf = cache_dir / "zero-remote-1.pdf"
    zero_pdf.write_bytes(b"")
    remote_call = CallRaw(
        detail_id="zero-remote-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/zero-remote-1.pdf",
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.get_session", return_value=session),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=zero_pdf) as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
    ):
        run_sync(conn, source="remote", dry_run=True)

    assert download_mock.call_args.kwargs["force"] is True


def test_sync_auto_source_zero_byte_cache_forces_redownload(tmp_path: Path) -> None:
    """source=auto (local discovery) must re-download zero-byte cached PDFs when URL exists."""
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zero_pdf = cache_dir / "zero-auto-1.pdf"
    zero_pdf.write_bytes(b"")
    upsert_call(
        conn,
        CallRaw(
            detail_id="zero-auto-1",
            source_tipo="Borsa",
            pdf_url="https://jobs.dsi.infn.it/zero-auto-1.pdf",
            pdf_cache_path=str(zero_pdf),
            listing_status="active",
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.fetch_all_calls") as fetch_mock,
        patch(
            "infn_jobs.pipeline.sync.download",
            return_value=cache_dir / "zero-auto-1.pdf",
        ) as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
    ):
        run_sync(conn, source="auto", dry_run=True)

    fetch_mock.assert_not_called()
    assert download_mock.call_args.kwargs["force"] is True
    conn.close()


def test_sync_db_has_calls_across_tipos(tmp_path: Path) -> None:
    """After sync, calls_raw must have 5 rows covering all 5 TIPOS."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 5

    stored_tipos = {r[0] for r in conn.execute("SELECT DISTINCT source_tipo FROM calls_raw")}
    assert stored_tipos == set(_TIPOS)
    conn.close()


def test_sync_is_idempotent(tmp_path: Path) -> None:
    """Running sync twice must not change row counts."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")
        first_calls = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
        first_rows = conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
        run_sync(conn, source="remote")

    assert conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0] == first_calls
    assert conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0] == first_rows
    conn.close()


def test_first_seen_at_immutable(tmp_path: Path) -> None:
    """first_seen_at must not change on a second sync run."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")
        t1 = conn.execute(
            "SELECT first_seen_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]
        time.sleep(0.05)
        run_sync(conn, source="remote")
        t2 = conn.execute(
            "SELECT first_seen_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]

    assert t1 == t2
    conn.close()


def test_last_synced_at_updated(tmp_path: Path) -> None:
    """last_synced_at must be >= its previous value after a second sync."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")
        last1 = conn.execute(
            "SELECT last_synced_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]
        time.sleep(0.05)
        run_sync(conn, source="remote")
        last2 = conn.execute(
            "SELECT last_synced_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]

    assert last2 >= last1
    conn.close()


def test_export_csv_creates_four_files(tmp_path: Path) -> None:
    """After sync + export, all 4 CSV files must exist with at least 2 lines each."""
    conn = _make_conn(tmp_path)
    export_dir = tmp_path / "exports"
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")
    run_export(conn, export_dir)

    expected = {
        "calls_raw.csv",
        "calls_curated.csv",
        "position_rows_raw.csv",
        "position_rows_curated.csv",
    }
    created = {p.name for p in export_dir.glob("*.csv")}
    assert expected == created

    for name in expected:
        lines = (export_dir / name).read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 2, f"{name} must have header + at least 1 data row"
    conn.close()


def test_sync_rebuilds_curated_tables(tmp_path: Path) -> None:
    """run_sync must keep calls_curated in sync with calls_raw when not dry-run."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")

    raw_count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    curated_count = conn.execute("SELECT COUNT(*) FROM calls_curated").fetchone()[0]
    curated_rows = conn.execute("SELECT COUNT(*) FROM position_rows_curated").fetchone()[0]

    assert raw_count == 5
    assert curated_count == raw_count
    assert curated_rows > 0
    conn.close()


def test_position_row_count_exceeds_call_count(tmp_path: Path) -> None:
    """position_rows count must exceed calls_raw count (multi-entry PDFs)."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn, source="remote")

    nc = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    nr = conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
    assert nr > nc, f"position_rows ({nr}) must exceed calls_raw ({nc})"
    conn.close()


def test_no_text_produces_zero_position_rows(tmp_path: Path) -> None:
    """no_text PDF quality must produce 0 position_rows but pdf_fetch_status='ok'."""
    conn = _make_conn(tmp_path)
    single_call = CallRaw(
        detail_id="e2e-notext-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/notext.pdf",
        anno="2022",
    )
    mock_pdf = tmp_path / "notext.pdf"
    mock_pdf.touch()

    with patch(
        "infn_jobs.pipeline.sync.fetch_all_calls",
        side_effect=lambda session, tipo: [single_call] if tipo == "Borsa" else [],
    ), patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf), patch(
        "infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)
    ):
        run_sync(conn, source="remote")

    assert conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0] == 0
    status = conn.execute(
        "SELECT pdf_fetch_status FROM calls_raw WHERE detail_id='e2e-notext-1'"
    ).fetchone()[0]
    assert status == "ok"
    conn.close()


def test_ocr_degraded_produces_low_confidence_rows(tmp_path: Path) -> None:
    """ocr_degraded quality must produce rows with parse_confidence='low'."""
    conn = _make_conn(tmp_path)
    single_call = CallRaw(
        detail_id="e2e-ocr-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/ocr.pdf",
        anno="2022",
    )
    mock_pdf = tmp_path / "ocr.pdf"
    mock_pdf.touch()

    with patch(
        "infn_jobs.pipeline.sync.fetch_all_calls",
        side_effect=lambda session, tipo: [single_call] if tipo == "Borsa" else [],
    ), patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf), patch(
        "infn_jobs.pipeline.sync.extract_text",
        return_value=(OCR_DEGRADED_TEXT, TextQuality.OCR_DEGRADED),
    ):
        run_sync(conn, source="remote")

    row_count = conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
    assert row_count >= 1, "ocr_degraded must attempt extraction and produce ≥1 row"

    confidences = {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT parse_confidence FROM position_rows WHERE detail_id='e2e-ocr-1'"
        )
    }
    assert confidences == {"low"}, f"all rows must have confidence=low, got {confidences}"
    conn.close()


def test_sync_logs_throttle_reminder_on_success(caplog):
    """run_sync must log throttle reminder on normal completion."""
    conn = Mock()
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=True, force_refetch=False)

    assert "Throttle reminder" in caplog.text
    assert "5-10s" in caplog.text


def test_sync_logs_throttle_reminder_on_keyboard_interrupt(caplog):
    """run_sync must log throttle reminder when interrupted."""
    conn = Mock()
    with (
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", side_effect=KeyboardInterrupt),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        with pytest.raises(KeyboardInterrupt):
            run_sync(conn, source="remote", dry_run=True, force_refetch=False)

    assert "Throttle reminder" in caplog.text
    assert "5-10s" in caplog.text
