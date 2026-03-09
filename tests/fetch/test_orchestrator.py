"""Tests for the fetch orchestrator."""

from __future__ import annotations

from unittest.mock import Mock, call, patch

import pytest
import requests

from infn_jobs.config.settings import RATE_LIMIT_JITTER_MAX, RATE_LIMIT_JITTER_MIN
from infn_jobs.domain.call import CallRaw
from infn_jobs.fetch.orchestrator import fetch_all_calls


def _response(content: bytes = b"", error: Exception | None = None) -> Mock:
    """Build a mock HTTP response with optional raise_for_status error."""
    response = Mock()
    response.content = content
    if error is None:
        response.raise_for_status.return_value = None
    else:
        response.raise_for_status.side_effect = error
    return response


def _call(detail_id: str) -> CallRaw:
    """Build a minimal CallRaw object for orchestrator tests."""
    call_raw = CallRaw()
    call_raw.detail_id = detail_id
    return call_raw


def _http_error(status_code: int) -> requests.HTTPError:
    """Build an HTTPError carrying a response with the provided status code."""
    err = requests.HTTPError(f"http {status_code}")
    response = Mock()
    response.status_code = status_code
    err.response = response
    return err


def test_fetch_all_calls_happy_path_sets_status_source_and_jittered_rate_limit():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        _response(b"detail-1"),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [{"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}],
            ],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_detail",
            side_effect=[_call("1"), _call("2")],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.random.uniform",
            side_effect=[2.11, 2.22, 2.33, 2.44],
        ) as jitter_mock,
        patch("infn_jobs.fetch.orchestrator.time.sleep") as sleep_mock,
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert [c.detail_id for c in calls] == ["1", "2"]
    assert [c.listing_status for c in calls] == ["active", "expired"]
    assert [c.source_tipo for c in calls] == ["Borsa", "Borsa"]
    assert sleep_mock.call_count == 4
    sleep_mock.assert_has_calls([call(2.11), call(2.22), call(2.33), call(2.44)])
    assert jitter_mock.call_count == 4
    jitter_mock.assert_has_calls([call(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX)] * 4)


def test_fetch_all_calls_limit_inside_active_list():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        _response(b"detail-1"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [
                    {"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"},
                    {"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"},
                    {"detail_id": "3", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=3"},
                ],
                [{"detail_id": "4", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=4"}],
            ],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_detail",
            side_effect=[_call("1"), _call("2")],
        ),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep") as sleep_mock,
    ):
        calls = fetch_all_calls(session, "Borsa", limit_per_tipo=2)

    assert [c.detail_id for c in calls] == ["1", "2"]
    assert [c.listing_status for c in calls] == ["active", "active"]
    assert session.get.call_args_list == [
        call("active-url"),
        call("https://jobs.dsi.infn.it/dettagli_job.php?id=1"),
        call("https://jobs.dsi.infn.it/dettagli_job.php?id=2"),
    ]
    assert sleep_mock.call_count == 2


def test_fetch_all_calls_limit_crosses_active_expired_boundary():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        _response(b"detail-1"),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [
                    {"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"},
                    {"detail_id": "3", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=3"},
                ],
            ],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_detail",
            side_effect=[_call("1"), _call("2")],
        ),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep") as sleep_mock,
    ):
        calls = fetch_all_calls(session, "Borsa", limit_per_tipo=2)

    assert [c.detail_id for c in calls] == ["1", "2"]
    assert [c.listing_status for c in calls] == ["active", "expired"]
    assert session.get.call_args_list == [
        call("active-url"),
        call("https://jobs.dsi.infn.it/dettagli_job.php?id=1"),
        call("expired-url"),
        call("https://jobs.dsi.infn.it/dettagli_job.php?id=2"),
    ]
    assert sleep_mock.call_count == 3


def test_fetch_all_calls_limit_greater_than_available_returns_all():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        _response(b"detail-1"),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [{"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}],
            ],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_detail",
            side_effect=[_call("1"), _call("2")],
        ),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
    ):
        calls = fetch_all_calls(session, "Borsa", limit_per_tipo=10)

    assert [c.detail_id for c in calls] == ["1", "2"]
    assert [c.listing_status for c in calls] == ["active", "expired"]


def test_fetch_all_calls_http_error_on_detail_skips_call():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        _response(b"detail-1", error=requests.HTTPError("404")),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [{"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}],
            ],
        ),
        patch("infn_jobs.fetch.orchestrator.parse_detail", return_value=_call("2")),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert len(calls) == 1
    assert calls[0].detail_id == "2"
    assert calls[0].listing_status == "expired"


def test_fetch_all_calls_connection_error_on_detail_skips_call():
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        requests.ConnectionError("network down"),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [{"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}],
            ],
        ),
        patch("infn_jobs.fetch.orchestrator.parse_detail", return_value=_call("2")),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert len(calls) == 1
    assert calls[0].detail_id == "2"
    assert calls[0].listing_status == "expired"


def test_fetch_all_calls_zero_rows_logs_warning(caplog):
    session = Mock()
    session.get.side_effect = [_response(b"listing-active"), _response(b"listing-expired")]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch("infn_jobs.fetch.orchestrator.parse_rows", side_effect=[[], []]),
        patch("infn_jobs.fetch.orchestrator.random.uniform", side_effect=[2.15, 2.65]) as jitter_mock,
        patch("infn_jobs.fetch.orchestrator.time.sleep") as sleep_mock,
        caplog.at_level("WARNING", logger="infn_jobs.fetch.orchestrator"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert calls == []
    assert caplog.text.count("0 rows at") == 2
    assert sleep_mock.call_count == 2
    sleep_mock.assert_has_calls([call(2.15), call(2.65)])
    jitter_mock.assert_has_calls([call(RATE_LIMIT_JITTER_MIN, RATE_LIMIT_JITTER_MAX)] * 2)


@pytest.mark.parametrize("status_code", [429, 503])
def test_fetch_all_calls_listing_pressure_signal_logs_guidance_and_continues(caplog, status_code):
    session = Mock()
    session.get.side_effect = [
        _response(b"", error=_http_error(status_code)),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            return_value=[
                {"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}
            ],
        ),
        patch("infn_jobs.fetch.orchestrator.parse_detail", return_value=_call("2")),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
        caplog.at_level("WARNING", logger="infn_jobs.fetch.orchestrator"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert [c.detail_id for c in calls] == ["2"]
    assert f"status={status_code}" in caplog.text
    assert "5-10s" in caplog.text


def test_fetch_all_calls_listing_retry_error_503_logs_guidance_and_continues(caplog):
    session = Mock()
    session.get.side_effect = [
        requests.exceptions.RetryError("too many 503 error responses"),
        _response(b"listing-expired"),
        _response(b"detail-2"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            return_value=[
                {"detail_id": "2", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=2"}
            ],
        ),
        patch("infn_jobs.fetch.orchestrator.parse_detail", return_value=_call("2")),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
        caplog.at_level("WARNING", logger="infn_jobs.fetch.orchestrator"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert [c.detail_id for c in calls] == ["2"]
    assert "status=503" in caplog.text
    assert "5-10s" in caplog.text


def test_fetch_all_calls_detail_timeout_logs_guidance(caplog):
    session = Mock()
    session.get.side_effect = [
        _response(b"listing-active"),
        requests.Timeout("slow response"),
        _response(b"listing-expired"),
    ]

    with (
        patch(
            "infn_jobs.fetch.orchestrator.build_urls",
            return_value=["active-url", "expired-url"],
        ),
        patch(
            "infn_jobs.fetch.orchestrator.parse_rows",
            side_effect=[
                [{"detail_id": "1", "detail_url": "https://jobs.dsi.infn.it/dettagli_job.php?id=1"}],
                [],
            ],
        ),
        patch("infn_jobs.fetch.orchestrator.random.uniform", return_value=2.5),
        patch("infn_jobs.fetch.orchestrator.time.sleep"),
        caplog.at_level("WARNING", logger="infn_jobs.fetch.orchestrator"),
    ):
        calls = fetch_all_calls(session, "Borsa")

    assert calls == []
    assert "pressure signal (timeout)" in caplog.text
    assert "5-10s" in caplog.text
