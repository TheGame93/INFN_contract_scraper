"""End-to-end tests for the sync pipeline with mocked I/O boundaries."""

import sqlite3
import time
from pathlib import Path
from unittest.mock import Mock, patch

from infn_jobs.domain.call import CallRaw
from infn_jobs.domain.enums import TextQuality
from infn_jobs.domain.position import PositionRow
from infn_jobs.pipeline.export import run_export
from infn_jobs.pipeline.sync import run_sync
from infn_jobs.store.schema import init_db

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
            side_effect=lambda session, tipo: [c for c in make_calls() if c.source_tipo == tipo],
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
        side_effect=lambda session, tipo: [c for c in make_calls() if c.source_tipo == tipo],
    ), patch("infn_jobs.pipeline.sync.download", return_value=tmp_path / "mock.pdf"), patch(
        "infn_jobs.pipeline.sync.extract_text", return_value=(MULTI_TEXT, TextQuality.DIGITAL)
    ):
        run_sync(conn, dry_run=False, force_refetch=False)
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
        run_sync(conn, dry_run=False, force_refetch=False)

    assert events == [
        "fetch_all_calls:Borsa",
        "download:serial-1",
        "extract_text",
        "build_rows:serial-1",
        "upsert_call:serial-1",
        "upsert_position_rows:serial-1",
        "download:serial-2",
        "extract_text",
        "build_rows:serial-2",
        "upsert_call:serial-2",
        "upsert_position_rows:serial-2",
        "rebuild_curated",
    ]


def test_sync_db_has_calls_across_tipos(tmp_path: Path) -> None:
    """After sync, calls_raw must have 5 rows covering all 5 TIPOS."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn)

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
        run_sync(conn)
        first_calls = conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0]
        first_rows = conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0]
        run_sync(conn)

    assert conn.execute("SELECT COUNT(*) FROM calls_raw").fetchone()[0] == first_calls
    assert conn.execute("SELECT COUNT(*) FROM position_rows").fetchone()[0] == first_rows
    conn.close()


def test_first_seen_at_immutable(tmp_path: Path) -> None:
    """first_seen_at must not change on a second sync run."""
    conn = _make_conn(tmp_path)
    fac_p, dl_p, et_p = _patch_sync(tmp_path)
    with fac_p, dl_p, et_p:
        run_sync(conn)
        t1 = conn.execute(
            "SELECT first_seen_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]
        time.sleep(0.05)
        run_sync(conn)
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
        run_sync(conn)
        last1 = conn.execute(
            "SELECT last_synced_at FROM calls_raw WHERE detail_id='e2e-borsa-1'"
        ).fetchone()[0]
        time.sleep(0.05)
        run_sync(conn)
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
        run_sync(conn)
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
        run_sync(conn)

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
        run_sync(conn)

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
        run_sync(conn)

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
        run_sync(conn)

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
