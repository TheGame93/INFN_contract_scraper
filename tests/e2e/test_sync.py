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
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir(exist_ok=True)

    return (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch(
            "infn_jobs.pipeline.sync.fetch_all_calls",
            side_effect=lambda session, tipo, *_args: [
                c for c in make_calls() if c.source_tipo == tipo
            ],
        ),
        patch("infn_jobs.pipeline.sync.download", return_value=tmp_path / "mock.pdf"),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=(MULTI_TEXT, TextQuality.DIGITAL)),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)
    conn.close()


def test_sync_uses_build_rows_tuple_contract_and_persists_title(tmp_path: Path) -> None:
    """run_sync must honor `(rows, pdf_call_title)` from build_rows."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / "mock-contract-shape.pdf"
    mock_pdf_path.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
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
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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


def test_sync_reconciles_rows_when_numero_posti_html_is_one(tmp_path: Path, caplog) -> None:
    """run_sync must reconcile multi-row parse output when numero_posti_html equals 1."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / "mock-reconcile-1.pdf"
    mock_pdf_path.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    remote_call = CallRaw(
        detail_id="reconcile-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/reconcile-1.pdf",
        anno="2026",
        numero_posti_html=1,
    )
    built_rows = [
        PositionRow(
            detail_id="reconcile-1",
            position_row_index=0,
            text_quality="digital",
            parse_confidence="low",
        ),
        PositionRow(
            detail_id="reconcile-1",
            position_row_index=1,
            text_quality="digital",
            contract_type="Borsa di studio",
            duration_months=12,
            gross_income_yearly_eur=1234.0,
            parse_confidence="high",
        ),
    ]

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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
            return_value=(built_rows, "Reconcile title"),
        ),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    stored_rows = conn.execute(
        "SELECT position_row_index, contract_type FROM position_rows "
        "WHERE detail_id = 'reconcile-1'"
    ).fetchall()
    assert stored_rows == [(1, "Borsa di studio")]
    assert (
        "row_reconciliation reason=applied_numero_posti_singleton_guard "
        "raw_rows=2 kept_rows=1"
    ) in (
        caplog.text
    )
    conn.close()


def test_sync_reconciliation_is_noop_when_numero_posti_html_is_missing(
    tmp_path: Path, caplog
) -> None:
    """run_sync must keep all parsed rows when numero_posti_html is NULL/missing."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / "mock-reconcile-missing.pdf"
    mock_pdf_path.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    remote_call = CallRaw(
        detail_id="reconcile-missing-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/reconcile-missing-1.pdf",
        anno="2026",
        numero_posti_html=None,
    )
    built_rows = [
        PositionRow(
            detail_id="reconcile-missing-1",
            position_row_index=0,
            text_quality="digital",
            contract_type="Borsa di studio",
            parse_confidence="high",
        ),
        PositionRow(
            detail_id="reconcile-missing-1",
            position_row_index=1,
            text_quality="digital",
            contract_type="Borsa di studio",
            parse_confidence="high",
        ),
    ]

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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
            return_value=(built_rows, "Reconcile title"),
        ),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    stored_rows = conn.execute(
        "SELECT position_row_index FROM position_rows WHERE detail_id = 'reconcile-missing-1' "
        "ORDER BY position_row_index"
    ).fetchall()
    assert stored_rows == [(0,), (1,)]
    assert (
        "row_reconciliation reason=not_applicable_numero_posti_missing "
        "raw_rows=2 kept_rows=2"
    ) in (
        caplog.text
    )
    conn.close()


@pytest.mark.parametrize(
    ("detail_id", "winner_index"),
    [
        ("4441", 1),
        ("4458", 2),
    ],
)
def test_sync_reconciles_4441_4458_style_oversplitting(
    tmp_path: Path,
    caplog,
    detail_id: str,
    winner_index: int,
) -> None:
    """run_sync must trim oversplit rows to one strongest row for 4441/4458-style cases."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / f"{detail_id}.pdf"
    mock_pdf_path.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    remote_call = CallRaw(
        detail_id=detail_id,
        source_tipo="Contratto di ricerca",
        listing_status="active",
        pdf_url=f"https://jobs.dsi.infn.it/{detail_id}.pdf",
        anno="2025",
        numero_posti_html=1,
    )
    built_rows = [
        PositionRow(detail_id=detail_id, position_row_index=0, text_quality="ocr_clean"),
        PositionRow(detail_id=detail_id, position_row_index=1, text_quality="ocr_clean"),
        PositionRow(detail_id=detail_id, position_row_index=2, text_quality="ocr_clean"),
    ]
    built_rows[winner_index] = PositionRow(
        detail_id=detail_id,
        position_row_index=winner_index,
        text_quality="ocr_clean",
        contract_type="Contratto di ricerca",
        duration_months=24,
        gross_income_yearly_eur=28761.73,
        parse_confidence="high",
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Contratto di ricerca"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf_path),
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=("fixture text", TextQuality.OCR_CLEAN),
        ),
        patch(
            "infn_jobs.pipeline.sync.build_rows",
            return_value=(built_rows, "Reconcile canary title"),
        ),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    persisted = conn.execute(
        "SELECT position_row_index FROM position_rows WHERE detail_id = ?",
        (detail_id,),
    ).fetchall()
    assert persisted == [(winner_index,)]
    assert (
        "row_reconciliation reason=applied_numero_posti_singleton_guard "
        "raw_rows=3 kept_rows=1"
    ) in caplog.text
    conn.close()


def test_sync_accepts_posti_gt_one_with_single_parsed_row(tmp_path: Path, caplog) -> None:
    """run_sync must keep single parsed row when numero_posti_html reports multiple posti."""
    conn = _make_conn(tmp_path)
    mock_pdf_path = tmp_path / "posti-gt-one.pdf"
    mock_pdf_path.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    remote_call = CallRaw(
        detail_id="posti-gt-one-1",
        source_tipo="Contratto di ricerca",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/posti-gt-one-1.pdf",
        anno="2025",
        numero_posti_html=3,
    )
    built_rows = [
        PositionRow(
            detail_id="posti-gt-one-1",
            position_row_index=0,
            text_quality="digital",
            contract_type="Contratto di ricerca",
            parse_confidence="high",
        )
    ]

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Contratto di ricerca"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf_path),
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=("fixture text", TextQuality.DIGITAL),
        ),
        patch(
            "infn_jobs.pipeline.sync.build_rows",
            return_value=(built_rows, "Counterexample title"),
        ),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    persisted = conn.execute(
        "SELECT position_row_index FROM position_rows WHERE detail_id = 'posti-gt-one-1'"
    ).fetchall()
    assert persisted == [(0,)]
    assert "row_reconciliation reason=" not in caplog.text
    conn.close()


def test_sync_request_processing_is_serial(tmp_path: Path) -> None:
    """run_sync must process request-bearing operations strictly in serial order."""
    conn = Mock()
    session = Mock()
    mock_pdf = tmp_path / "serial.pdf"
    mock_pdf.touch()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
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
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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


def test_sync_remote_source_passes_limit_to_fetch_orchestrator(tmp_path: Path) -> None:
    """run_sync must pass limit_per_tipo to fetch_all_calls for source=remote."""
    conn = Mock()
    session = Mock()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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



def test_sync_download_only_skips_parse_and_db_writes(tmp_path: Path) -> None:
    """download_only=True must stop after cache materialization and skip persistence."""
    conn = Mock()
    session = Mock()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    cached_pdf = tmp_path / "download-only.pdf"
    cached_pdf.write_bytes(b"%PDF-download-only")
    remote_call = CallRaw(
        detail_id="download-only-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/download-only-1.pdf",
    )
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
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
    conn = _make_conn(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zero_pdf = cache_dir / "zero-remote-1.pdf"
    zero_pdf.write_bytes(b"")
    upsert_call(
        conn,
        CallRaw(
            detail_id="zero-remote-1",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url="https://jobs.dsi.infn.it/zero-remote-1.pdf",
            pdf_cache_path=str(zero_pdf),
        ),
    )

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", cache_dir),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]),
        patch("infn_jobs.pipeline.sync.download", return_value=zero_pdf) as download_mock,
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
    ):
        run_sync(conn, source="remote", dry_run=True)

    download_mock.assert_called_once()
    assert download_mock.call_args.kwargs["force"] is True
    conn.close()


def test_sync_db_has_calls_across_tipos(tmp_path: Path) -> None:
    """After sync, calls_raw must have 5 rows covering all 5 TIPOS."""
    conn = _make_conn(tmp_path)
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
        run_sync(conn, source="remote")

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 5

    stored_tipos = {r[0] for r in conn.execute("SELECT DISTINCT source_tipo FROM calls_raw")}
    assert stored_tipos == set(_TIPOS)
    conn.close()


def test_sync_is_idempotent(tmp_path: Path) -> None:
    """Running sync twice must not change row counts."""
    conn = _make_conn(tmp_path)
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
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
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
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
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
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
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
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
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
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
    cache_p, fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with cache_p, fac_p, dl_p, et_p:
        run_sync(conn, source="remote")

    nc = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    nr = conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
    assert nr > nc, f"position_rows ({nr}) must exceed calls_raw ({nc})"
    conn.close()


def test_no_text_produces_zero_position_rows(tmp_path: Path) -> None:
    """no_text PDF quality must produce 0 position_rows but pdf_fetch_status='ok'."""
    conn = _make_conn(tmp_path)
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    single_call = CallRaw(
        detail_id="e2e-notext-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/notext.pdf",
        anno="2022",
    )
    mock_pdf = tmp_path / "notext.pdf"
    mock_pdf.touch()

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch(
            "infn_jobs.pipeline.sync.fetch_all_calls",
            side_effect=lambda session, tipo: [single_call] if tipo == "Borsa" else [],
        ),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
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
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    single_call = CallRaw(
        detail_id="e2e-ocr-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/ocr.pdf",
        anno="2022",
    )
    mock_pdf = tmp_path / "ocr.pdf"
    mock_pdf.touch()

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch(
            "infn_jobs.pipeline.sync.fetch_all_calls",
            side_effect=lambda session, tipo: [single_call] if tipo == "Borsa" else [],
        ),
        patch("infn_jobs.pipeline.sync.download", return_value=mock_pdf),
        patch(
            "infn_jobs.pipeline.sync.extract_text",
            return_value=(OCR_DEGRADED_TEXT, TextQuality.OCR_DEGRADED),
        ),
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


def test_sync_logs_throttle_reminder_on_success(tmp_path: Path, caplog):
    """run_sync must log throttle reminder on normal completion."""
    conn = Mock()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[]),
        caplog.at_level("INFO", logger="infn_jobs.pipeline.sync"),
    ):
        run_sync(conn, source="remote", dry_run=True, force_refetch=False)

    assert "Throttle reminder" in caplog.text
    assert "5-10s" in caplog.text


def test_sync_runtime_logs_phase_timings_and_summary_for_dry_run(tmp_path: Path, caplog) -> None:
    """run_sync dry-run must emit runtime phase timings and deterministic summary counters."""
    conn = Mock()
    runtime_call = CallRaw(
        detail_id="runtime-1",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/runtime-1.pdf",
        anno="2024",
    )
    runtime_pdf = tmp_path / "runtime-1.pdf"
    runtime_pdf.write_bytes(b"%PDF-runtime")
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[runtime_call]),
        patch("infn_jobs.pipeline.sync.download", return_value=runtime_pdf),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        patch("infn_jobs.pipeline.sync.build_rows", return_value=([], None)),
        patch(
            "infn_jobs.pipeline.sync._resolve_runtime_logfile_path",
            return_value="/tmp/sync.log",
        ),
        caplog.at_level("INFO", logger="infn_jobs.runtime.sync"),
    ):
        run_sync(conn, source="remote", dry_run=True, force_refetch=False)

    assert "Sync start: source=remote logfile=/tmp/sync.log heartbeat_interval=250" in caplog.text
    assert "Phase A complete: discovered_contracts=1 elapsed_s=" in caplog.text
    assert "Phase B complete: materialized_contracts=1 elapsed_s=" in caplog.text
    assert "Phase C complete: parsed_contracts=1 elapsed_s=" in caplog.text
    assert "Phase D complete: skipped=True reason=dry_run elapsed_s=0.00" in caplog.text
    assert (
        "Sync summary: status=completed partial_run=false processed_contracts=1 "
        "ok=1 skipped=0 download_error=0 parse_error=0 other=0"
    ) in caplog.text


def test_sync_runtime_logs_heartbeat_every_250_processed_contracts(
    tmp_path: Path, caplog
) -> None:
    """run_sync must emit heartbeat every 250 processed contracts during Phase B."""
    conn = Mock()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    calls = [
        CallRaw(
            detail_id=f"heartbeat-{i}",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url=None,
        )
        for i in range(251)
    ]
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=calls),
        caplog.at_level("INFO", logger="infn_jobs.runtime.sync"),
    ):
        run_sync(conn, source="remote", download_only=True, dry_run=False, force_refetch=False)

    heartbeat_lines = [
        rec.getMessage()
        for rec in caplog.records
        if rec.name == "infn_jobs.runtime.sync" and rec.getMessage().startswith("Sync heartbeat:")
    ]
    assert heartbeat_lines == ["Sync heartbeat: processed_contracts=250/251"]
    assert "Phase C complete: skipped=True reason=download_only elapsed_s=0.00" in caplog.text
    assert "Phase D complete: skipped=True reason=download_only elapsed_s=0.00" in caplog.text
    assert (
        "Sync summary: status=completed partial_run=false processed_contracts=251 "
        "ok=0 skipped=251 download_error=0 parse_error=0 other=0"
    ) in caplog.text


def test_sync_runtime_logs_heartbeat_for_phase_c_and_d(tmp_path: Path, caplog) -> None:
    """run_sync must emit heartbeat lines for Phase C and Phase D on discovered items."""
    conn = _make_conn(tmp_path)
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    calls = [
        CallRaw(
            detail_id=f"phase-cd-{i}",
            source_tipo="Borsa",
            listing_status="active",
            pdf_url=None,
        )
        for i in range(251)
    ]
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=calls),
        caplog.at_level("INFO", logger="infn_jobs.runtime.sync"),
    ):
        run_sync(conn, source="remote", dry_run=False, force_refetch=False)

    runtime_messages = [
        rec.getMessage() for rec in caplog.records if rec.name == "infn_jobs.runtime.sync"
    ]
    assert "Sync heartbeat: processed_contracts=250/251" in runtime_messages
    assert "Phase C heartbeat: processed_contracts=250/251" in runtime_messages
    assert "Phase D heartbeat: processed_contracts=250/251" in runtime_messages
    conn.close()


def test_sync_logs_throttle_reminder_on_keyboard_interrupt(tmp_path: Path, caplog):
    """run_sync must log throttle reminder when interrupted."""
    conn = Mock()
    empty_cache = tmp_path / "pdf_cache"
    empty_cache.mkdir()
    caplog.set_level("INFO", logger="infn_jobs.pipeline.sync")
    caplog.set_level("INFO", logger="infn_jobs.runtime.sync")
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", empty_cache),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", side_effect=KeyboardInterrupt),
    ):
        with pytest.raises(KeyboardInterrupt):
            run_sync(conn, source="remote", dry_run=True, force_refetch=False)

    assert "Throttle reminder" in caplog.text
    assert "5-10s" in caplog.text
    assert "Sync summary: status=interrupted partial_run=true processed_contracts=0" in caplog.text


# ---------------------------------------------------------------------------
# Filesystem-driven local source tests (section 4.2)
# ---------------------------------------------------------------------------


def test_sync_local_source_uses_filesystem_to_discover_calls(tmp_path: Path) -> None:
    """run_sync source=local must discover calls from pdf_cache/*.pdf, not DB."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    (pdf_cache / "detail-a.pdf").write_bytes(b"%PDF-fake-a")
    (pdf_cache / "detail-b.pdf").write_bytes(b"%PDF-fake-b")
    upsert_call(conn, CallRaw(detail_id="detail-a", source_tipo="Borsa", listing_status="active"))

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.fetch_all_calls") as fac_mock,
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        patch("infn_jobs.pipeline.sync.build_rows", return_value=([], None)),
    ):
        run_sync(conn, source="local", dry_run=False)

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 2, f"expected 2 entries in calls_raw, got {count}"
    fac_mock.assert_not_called()
    conn.close()


def test_sync_local_source_empty_cache_produces_empty_db_noop(tmp_path: Path) -> None:
    """run_sync source=local on empty pdf_cache must not prune existing DB entries."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    upsert_call(conn, CallRaw(detail_id="existing-1", listing_status="active"))
    upsert_call(conn, CallRaw(detail_id="existing-2", listing_status="active"))

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
    ):
        run_sync(conn, source="local", dry_run=False)

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 2, "prune safety guard must leave pre-existing rows untouched on empty cache"
    conn.close()


# ---------------------------------------------------------------------------
# Prune behavior tests (section 4.3)
# ---------------------------------------------------------------------------


def test_sync_local_source_prunes_stale_db_entries(tmp_path: Path, caplog) -> None:
    """run_sync source=local must prune DB entries absent from the current pdf_cache."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    (pdf_cache / "detail-keep.pdf").write_bytes(b"%PDF-keep")
    upsert_call(conn, CallRaw(detail_id="detail-keep", listing_status="active"))
    upsert_call(conn, CallRaw(detail_id="detail-stale", listing_status="active"))

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        patch("infn_jobs.pipeline.sync.build_rows", return_value=([], None)),
        caplog.at_level("INFO", logger="infn_jobs.runtime.sync"),
    ):
        run_sync(conn, source="local", dry_run=False)

    ids = {r[0] for r in conn.execute("SELECT detail_id FROM calls_raw")}
    assert "detail-keep" in ids
    assert "detail-stale" not in ids, "stale entry must be pruned after sync"
    assert "Prune: removed 1 stale DB entries" in caplog.text
    conn.close()


def test_sync_dry_run_does_not_prune(tmp_path: Path) -> None:
    """run_sync dry_run=True must skip Phase D entirely; no prune must occur."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    (pdf_cache / "detail-keep.pdf").write_bytes(b"%PDF-keep")
    upsert_call(conn, CallRaw(detail_id="detail-keep", listing_status="active"))
    upsert_call(conn, CallRaw(detail_id="detail-stale", listing_status="active"))

    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        patch("infn_jobs.pipeline.sync.build_rows", return_value=([], None)),
    ):
        run_sync(conn, source="local", dry_run=True)

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 2, "dry_run must skip prune; both entries must remain"
    conn.close()


# ---------------------------------------------------------------------------
# Remote source merge tests (section 4.4)
# ---------------------------------------------------------------------------


def test_sync_remote_source_includes_cached_pdfs_not_in_remote_discovery(
    tmp_path: Path,
) -> None:
    """run_sync source=remote must include local-cache PDFs absent from remote results."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    (pdf_cache / "remote-one.pdf").write_bytes(b"%PDF-remote-one")
    (pdf_cache / "local-only.pdf").write_bytes(b"%PDF-local-only")

    remote_call = CallRaw(
        detail_id="remote-one",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/remote-one.pdf",
    )
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.extract_text", return_value=("", TextQuality.NO_TEXT)),
        patch("infn_jobs.pipeline.sync.build_rows", return_value=([], None)),
    ):
        run_sync(conn, source="remote", dry_run=False)

    count = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
    assert count == 2, f"both local-only and remote-one must be in DB, got {count}"
    ids = {r[0] for r in conn.execute("SELECT detail_id FROM calls_raw")}
    assert ids == {"remote-one", "local-only"}
    conn.close()


def test_sync_remote_source_does_not_download_already_cached_pdf(tmp_path: Path) -> None:
    """run_sync source=remote must skip download for PDFs already in pdf_cache."""
    conn = _make_conn(tmp_path)
    pdf_cache = tmp_path / "pdf_cache"
    pdf_cache.mkdir()
    cached_pdf = pdf_cache / "cached-contract.pdf"
    cached_pdf.write_bytes(b"%PDF-already-here")

    remote_call = CallRaw(
        detail_id="cached-contract",
        source_tipo="Borsa",
        listing_status="active",
        pdf_url="https://jobs.dsi.infn.it/cached-contract.pdf",
    )
    with (
        patch("infn_jobs.pipeline.sync.PDF_CACHE_DIR", pdf_cache),
        patch("infn_jobs.pipeline.sync.init_data_dirs"),
        patch("infn_jobs.pipeline.sync.get_session", return_value=Mock()),
        patch("infn_jobs.pipeline.sync.TIPOS", ["Borsa"]),
        patch("infn_jobs.pipeline.sync.fetch_all_calls", return_value=[remote_call]),
        patch("infn_jobs.pipeline.sync.download") as download_mock,
    ):
        run_sync(conn, source="remote", dry_run=True)

    download_mock.assert_not_called()
    conn.close()
