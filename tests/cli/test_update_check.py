"""Tests for CLI startup update checks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from infn_jobs.cli.update_check import (
    UpdateInfo,
    _prompt_user,
    check_for_github_update,
    maybe_handle_startup_update_check,
)


def test_check_for_github_update_returns_none_when_commits_match():
    with patch(
        "infn_jobs.cli.update_check._run_git",
        side_effect=["true", "main", "abc123", "abc123\trefs/heads/main"],
    ):
        assert check_for_github_update(Path("/tmp/repo")) is None


def test_check_for_github_update_returns_info_when_remote_differs():
    with patch(
        "infn_jobs.cli.update_check._run_git",
        side_effect=["true", "main", "abc123", "def456\trefs/heads/main"],
    ):
        result = check_for_github_update(Path("/tmp/repo"))

    assert result == UpdateInfo(branch="main", local_sha="abc123", remote_sha="def456")


def test_maybe_handle_startup_update_check_skips_when_env_set(monkeypatch):
    monkeypatch.setenv("INFN_JOBS_SKIP_UPDATE_CHECK", "1")
    with patch("infn_jobs.cli.update_check.check_for_github_update") as check_mock:
        assert maybe_handle_startup_update_check(Path("/tmp/repo")) is True
    check_mock.assert_not_called()


def test_maybe_handle_startup_update_check_skips_when_not_tty():
    with (
        patch("infn_jobs.cli.update_check.sys.stdin.isatty", return_value=False),
        patch("infn_jobs.cli.update_check.check_for_github_update") as check_mock,
    ):
        assert maybe_handle_startup_update_check(Path("/tmp/repo")) is True
    check_mock.assert_not_called()


def test_prompt_user_continue_current_version():
    update = UpdateInfo(branch="main", local_sha="abc123", remote_sha="def456")
    with (
        patch("builtins.input", return_value="y"),
        patch("infn_jobs.cli.update_check.subprocess.run") as run_mock,
    ):
        assert _prompt_user(update, Path("/tmp/repo")) is True
    run_mock.assert_not_called()


def test_prompt_user_download_update_success():
    update = UpdateInfo(branch="main", local_sha="abc123", remote_sha="def456")
    with (
        patch("builtins.input", side_effect=["n", ""]),
        patch(
            "infn_jobs.cli.update_check.subprocess.run",
            return_value=Mock(returncode=0),
        ) as run_mock,
    ):
        assert _prompt_user(update, Path("/tmp/repo")) is False

    run_mock.assert_called_once_with(
        ["git", "-C", "/tmp/repo", "pull", "--ff-only"],
        check=False,
    )


def test_prompt_user_download_update_failure_then_continue():
    update = UpdateInfo(branch="main", local_sha="abc123", remote_sha="def456")
    with (
        patch("builtins.input", side_effect=["n", "y", "y"]),
        patch("infn_jobs.cli.update_check.subprocess.run", return_value=Mock(returncode=1)),
    ):
        assert _prompt_user(update, Path("/tmp/repo")) is True
