#!/usr/bin/env python3
"""Tests for subtask progress calculation.

Verifies the subtask progress helper in todo.py and the
model_mapper variant. Uses MagicMock to simulate TaskV2.
"""

import pytest
from unittest.mock import MagicMock

from custom_components.ticktick.todo import _calculate_subtask_progress as calculate_subtask_progress


def _make_mock_item(status=0):
    """Create a mock ItemV2."""
    item = MagicMock()
    item.status = status
    return item


def test_progress_empty_items():
    """No items gives 0, 0, 0."""
    total, completed, progress = calculate_subtask_progress([])
    assert total == 0
    assert completed == 0
    assert progress == 0


def test_progress_all_active():
    """All status=0 gives 0% complete."""
    items = [_make_mock_item(0), _make_mock_item(0), _make_mock_item(0)]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 3
    assert completed == 0
    assert progress == 0


def test_progress_all_completed():
    """All status=1 gives 100%."""
    items = [_make_mock_item(1), _make_mock_item(1)]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 2
    assert completed == 2
    assert progress == 100


def test_progress_mixed():
    """2 of 4 completed gives 50%."""
    items = [
        _make_mock_item(1),
        _make_mock_item(0),
        _make_mock_item(1),
        _make_mock_item(0),
    ]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 4
    assert completed == 2
    assert progress == 50


def test_progress_one_of_three():
    """1 of 3 completed gives 33%."""
    items = [_make_mock_item(1), _make_mock_item(0), _make_mock_item(0)]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 3
    assert completed == 1
    assert progress == 33  # int(1/3 * 100) = 33


def test_progress_single_completed():
    """Single completed item gives 100%."""
    items = [_make_mock_item(1)]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 1
    assert completed == 1
    assert progress == 100


def test_progress_single_active():
    """Single active item gives 0%."""
    items = [_make_mock_item(0)]
    total, completed, progress = calculate_subtask_progress(items)
    assert total == 1
    assert completed == 0
    assert progress == 0
