"""Tests for shared adjacent-line text-window helpers."""

from __future__ import annotations

import pytest

from infn_jobs.extract.parse.rules.text_windows import iter_adjacent_line_windows


def test_iter_adjacent_line_windows_returns_deterministic_order() -> None:
    """Windows should be ordered by start line, then by increasing window size."""
    windows = iter_adjacent_line_windows("A\nB\nC", max_lines=2)
    texts = tuple(window.text for window in windows)
    assert texts == ("A", "A B", "B", "B C", "C")


def test_iter_adjacent_line_windows_strips_blank_lines() -> None:
    """Blank lines should not produce empty windows."""
    windows = iter_adjacent_line_windows("A\n\nB\n", max_lines=2)
    texts = tuple(window.text for window in windows)
    assert texts == ("A", "A B", "B")


def test_iter_adjacent_line_windows_joins_with_space() -> None:
    """Joined windows should preserve punctuation context across adjacent lines."""
    windows = iter_adjacent_line_windows("Compenso lordo annuo:\n€ 22.500,00", max_lines=2)
    texts = tuple(window.text for window in windows)
    assert "Compenso lordo annuo: € 22.500,00" in texts


def test_iter_adjacent_line_windows_rejects_invalid_window_size() -> None:
    """Window size must be positive."""
    with pytest.raises(ValueError, match="max_lines must be >= 1"):
        iter_adjacent_line_windows("A", max_lines=0)
