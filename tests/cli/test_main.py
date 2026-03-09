"""Tests for CLI parser, dispatcher, and command DB lifecycle."""

from __future__ import annotations

import argparse
from unittest.mock import Mock, patch

import pytest

from infn_jobs.cli import cmd_export, cmd_sync
from infn_jobs.cli.main import build_parser, run
from infn_jobs.config.settings import DB_PATH, EXPORT_DIR


def test_build_parser_sync_subcommand():
    parser = build_parser()
    args = parser.parse_args(["sync"])
    assert args.command == "sync"
    assert args.dry_run is False
    assert args.force_refetch is False


def test_build_parser_sync_flags():
    parser = build_parser()
    args = parser.parse_args(["sync", "--dry-run", "--force-refetch"])
    assert args.dry_run is True
    assert args.force_refetch is True


def test_build_parser_export_csv_subcommand():
    parser = build_parser()
    args = parser.parse_args(["export-csv"])
    assert args.command == "export-csv"


def test_run_dispatches_to_selected_command():
    parser = Mock()
    args = argparse.Namespace(func=Mock())
    parser.parse_args.return_value = args

    with (
        patch("infn_jobs.cli.main.logging.basicConfig"),
        patch("infn_jobs.cli.main.init_data_dirs"),
        patch("infn_jobs.cli.main.build_parser", return_value=parser),
    ):
        run()

    args.func.assert_called_once_with(args)


def test_run_fatal_error_exits_with_code_1(capsys):
    def _boom(_: argparse.Namespace) -> None:
        raise RuntimeError("boom")

    parser = Mock()
    parser.parse_args.return_value = argparse.Namespace(func=_boom)

    with (
        patch("infn_jobs.cli.main.logging.basicConfig"),
        patch("infn_jobs.cli.main.init_data_dirs"),
        patch("infn_jobs.cli.main.build_parser", return_value=parser),
        pytest.raises(SystemExit) as exc_info,
    ):
        run()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: boom" in captured.err


def test_cmd_sync_execute_db_lifecycle_success():
    conn = Mock()
    args = argparse.Namespace(dry_run=True, force_refetch=False)

    with (
        patch("infn_jobs.cli.cmd_sync.sqlite3.connect", return_value=conn) as connect_mock,
        patch("infn_jobs.cli.cmd_sync.init_db") as init_db_mock,
        patch("infn_jobs.cli.cmd_sync.run_sync") as run_sync_mock,
    ):
        cmd_sync.execute(args)

    connect_mock.assert_called_once_with(str(DB_PATH))
    init_db_mock.assert_called_once_with(conn)
    run_sync_mock.assert_called_once_with(conn, dry_run=True, force_refetch=False)
    conn.close.assert_called_once()


def test_cmd_sync_execute_closes_db_on_error():
    conn = Mock()
    args = argparse.Namespace(dry_run=False, force_refetch=True)

    with (
        patch("infn_jobs.cli.cmd_sync.sqlite3.connect", return_value=conn),
        patch("infn_jobs.cli.cmd_sync.init_db"),
        patch("infn_jobs.cli.cmd_sync.run_sync", side_effect=RuntimeError("sync failed")),
    ):
        with pytest.raises(RuntimeError, match="sync failed"):
            cmd_sync.execute(args)

    conn.close.assert_called_once()


def test_cmd_export_execute_db_lifecycle_success():
    conn = Mock()
    args = argparse.Namespace()

    with (
        patch("infn_jobs.cli.cmd_export.sqlite3.connect", return_value=conn) as connect_mock,
        patch("infn_jobs.cli.cmd_export.init_db") as init_db_mock,
        patch("infn_jobs.cli.cmd_export.run_export") as run_export_mock,
    ):
        cmd_export.execute(args)

    connect_mock.assert_called_once_with(str(DB_PATH))
    init_db_mock.assert_called_once_with(conn)
    run_export_mock.assert_called_once_with(conn, EXPORT_DIR)
    conn.close.assert_called_once()


def test_cmd_export_execute_closes_db_on_error():
    conn = Mock()
    args = argparse.Namespace()

    with (
        patch("infn_jobs.cli.cmd_export.sqlite3.connect", return_value=conn),
        patch("infn_jobs.cli.cmd_export.init_db"),
        patch("infn_jobs.cli.cmd_export.run_export", side_effect=RuntimeError("export failed")),
    ):
        with pytest.raises(RuntimeError, match="export failed"):
            cmd_export.execute(args)

    conn.close.assert_called_once()
