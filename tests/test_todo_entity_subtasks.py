#!/usr/bin/env python3
"""Tests for subtask-related entity attributes.

Verifies that task_to_todo_item_with_subtask_progress correctly handles
edge cases around checklist items (ItemV2) and their status values.
"""

import pytest
from unittest.mock import MagicMock

from homeassistant.components.todo import TodoItemStatus

from custom_components.ticktick.model_mapper import (
    task_to_todo_item,
    task_to_todo_item_with_subtask_progress,
)


def _make_mock_task(*, title="Task", desc=None, status=0, items=None):
    """Create a mock TaskV2."""
    task = MagicMock()
    task.id = "task123"
    task.title = title
    task.content = None
    task.desc = desc
    task.status = status
    task.due_date = None
    task.items = items or []
    return task


def _make_mock_item(*, item_id="item1", title="Sub", status=0, sort_order=0):
    """Create a mock ItemV2."""
    item = MagicMock()
    item.id = item_id
    item.title = title
    item.status = status
    item.sort_order = sort_order
    return item


# ---------------------------------------------------------------------------
# Subtask status interpretation in mapping
# ---------------------------------------------------------------------------

class TestSubtaskProgressMapping:
    """Test task_to_todo_item_with_subtask_progress edge cases."""

    def test_no_items_attribute(self):
        """Task with items=None returns base item."""
        task = _make_mock_task(items=None)
        # items is falsy, should fall back
        item = task_to_todo_item_with_subtask_progress(task)
        assert item.description is None

    def test_empty_list(self):
        """Task with items=[] returns base item."""
        task = _make_mock_task(items=[])
        item = task_to_todo_item_with_subtask_progress(task)
        assert item.description is None

    def test_single_completed_subtask(self):
        """One completed subtask shows [1/1]."""
        items = [_make_mock_item(status=1)]
        task = _make_mock_task(items=items)
        item = task_to_todo_item_with_subtask_progress(task)
        assert "[1/1 subtasks]" in item.description

    def test_mixed_subtask_statuses(self):
        """Mix of status 0 and 1 shows correct count."""
        items = [
            _make_mock_item(item_id="a", status=0),
            _make_mock_item(item_id="b", status=1),
            _make_mock_item(item_id="c", status=0),
            _make_mock_item(item_id="d", status=1),
            _make_mock_item(item_id="e", status=1),
        ]
        task = _make_mock_task(items=items)
        item = task_to_todo_item_with_subtask_progress(task)
        assert "[3/5 subtasks]" in item.description

    def test_preserves_uid_and_summary(self):
        """Subtask variant preserves uid and summary from base."""
        items = [_make_mock_item(status=0)]
        task = _make_mock_task(title="Keep this title", items=items)
        item = task_to_todo_item_with_subtask_progress(task)
        assert item.uid == "task123"
        assert item.summary == "Keep this title"

    def test_preserves_status(self):
        """Subtask variant preserves task status mapping."""
        items = [_make_mock_item(status=0)]
        task = _make_mock_task(status=2, items=items)  # completed task
        item = task_to_todo_item_with_subtask_progress(task)
        assert item.status == TodoItemStatus.COMPLETED


# ---------------------------------------------------------------------------
# Base task_to_todo_item with various ItemV2 states
# ---------------------------------------------------------------------------

class TestBaseMapperIgnoresItems:
    """Verify that task_to_todo_item does NOT look at items."""

    def test_items_not_in_description(self):
        """Base mapper does not put subtask info in description."""
        items = [
            _make_mock_item(status=1),
            _make_mock_item(status=0),
        ]
        task = _make_mock_task(items=items, desc=None)
        item = task_to_todo_item(task)
        # base mapper should not include subtask progress
        assert item.description is None

    def test_items_with_desc(self):
        """Base mapper passes desc through unmodified."""
        items = [_make_mock_item(status=1)]
        task = _make_mock_task(items=items, desc="My note")
        item = task_to_todo_item(task)
        assert item.description == "My note"
        assert "subtask" not in item.description.lower()
