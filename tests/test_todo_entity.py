#!/usr/bin/env python3
"""Tests for todo entity mapping, status conversion, and date formatting.

Uses MagicMock objects to simulate TaskV2 since constructing real Pydantic
models requires many fields. These tests verify:
  - _STATUS_MAP covers all TaskV2 status values
  - task_to_todo_item maps fields correctly
  - task_to_todo_item_with_subtask_progress builds description
  - _format_date_for_comparison handles datetime, str, None
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from homeassistant.components.todo import TodoItemStatus

from custom_components.ticktick.model_mapper import (
    _STATUS_MAP,
    task_to_todo_item,
    task_to_todo_item_with_subtask_progress,
)
from custom_components.ticktick.todo import _format_date_for_comparison


# ---------------------------------------------------------------------------
# _STATUS_MAP tests
# ---------------------------------------------------------------------------

def test_status_map_normal():
    """Status 0 (NORMAL) -> NEEDS_ACTION."""
    assert _STATUS_MAP[0] == TodoItemStatus.NEEDS_ACTION


def test_status_map_completed_checklist():
    """Status 1 (COMPLETED for CheckListItem) -> COMPLETED."""
    assert _STATUS_MAP[1] == TodoItemStatus.COMPLETED


def test_status_map_completed_task():
    """Status 2 (COMPLETED for Task) -> COMPLETED."""
    assert _STATUS_MAP[2] == TodoItemStatus.COMPLETED


def test_status_map_abandoned():
    """Status -1 (ABANDONED) -> NEEDS_ACTION."""
    assert _STATUS_MAP[-1] == TodoItemStatus.NEEDS_ACTION


def test_status_map_unknown_defaults_to_needs_action():
    """Unknown status values should default to NEEDS_ACTION via .get()."""
    assert _STATUS_MAP.get(99, TodoItemStatus.NEEDS_ACTION) == TodoItemStatus.NEEDS_ACTION


# ---------------------------------------------------------------------------
# task_to_todo_item tests
# ---------------------------------------------------------------------------

def _make_mock_task(
    *,
    task_id="abc123",
    title="Test Task",
    content=None,
    desc=None,
    status=0,
    due_date=None,
    items=None,
):
    """Create a mock TaskV2 with the fields used by model_mapper."""
    task = MagicMock()
    task.id = task_id
    task.title = title
    task.content = content
    task.desc = desc
    task.status = status
    task.due_date = due_date
    task.items = items or []
    return task


def test_task_to_todo_item_basic():
    """Basic field mapping with title, status, no due date."""
    task = _make_mock_task(title="Buy milk", status=0)
    item = task_to_todo_item(task)

    assert item.uid == "abc123"
    assert item.summary == "Buy milk"
    assert item.status == TodoItemStatus.NEEDS_ACTION
    assert item.due is None
    assert item.description is None


def test_task_to_todo_item_completed():
    """Task with status 2 (completed) maps correctly."""
    task = _make_mock_task(title="Done task", status=2)
    item = task_to_todo_item(task)

    assert item.status == TodoItemStatus.COMPLETED


def test_task_to_todo_item_with_due_date():
    """Due date is passed through."""
    due = datetime(2025, 6, 15, 14, 30)
    task = _make_mock_task(title="Deadline task", due_date=due)
    item = task_to_todo_item(task)

    assert item.due == due


def test_task_to_todo_item_with_description():
    """desc field becomes TodoItem.description."""
    task = _make_mock_task(title="Task with notes", desc="Some notes")
    item = task_to_todo_item(task)

    assert item.description == "Some notes"


def test_task_to_todo_item_title_none_falls_back_to_content():
    """When title is None, content is used as summary."""
    task = _make_mock_task(title=None, content="Content text")
    item = task_to_todo_item(task)

    assert item.summary == "Content text"


def test_task_to_todo_item_title_and_content_none():
    """When both title and content are None, 'Untitled' is used."""
    task = _make_mock_task(title=None, content=None)
    item = task_to_todo_item(task)

    assert item.summary == "Untitled"


# ---------------------------------------------------------------------------
# task_to_todo_item_with_subtask_progress tests
# ---------------------------------------------------------------------------

def _make_mock_item(*, item_id="item1", title="Subtask", status=0):
    """Create a mock ItemV2 (checklist item)."""
    item = MagicMock()
    item.id = item_id
    item.title = title
    item.status = status
    return item


def test_subtask_progress_no_items():
    """Task with no items returns base todo item unchanged."""
    task = _make_mock_task(title="Simple task", items=[])
    item = task_to_todo_item_with_subtask_progress(task)

    assert item.summary == "Simple task"
    assert item.description is None


def test_subtask_progress_with_items():
    """Task with checklist items includes progress in description."""
    items = [
        _make_mock_item(item_id="i1", title="A", status=1),
        _make_mock_item(item_id="i2", title="B", status=0),
        _make_mock_item(item_id="i3", title="C", status=1),
    ]
    task = _make_mock_task(title="Shopping", items=items)
    item = task_to_todo_item_with_subtask_progress(task)

    assert "[2/3 subtasks]" in item.description


def test_subtask_progress_with_existing_description():
    """Progress is prepended to existing desc."""
    items = [
        _make_mock_item(item_id="i1", status=1),
    ]
    task = _make_mock_task(title="Task", desc="Original notes", items=items)
    item = task_to_todo_item_with_subtask_progress(task)

    assert item.description.startswith("[1/1 subtasks]")
    assert "Original notes" in item.description


def test_subtask_progress_all_completed():
    """All items completed shows correct count."""
    items = [
        _make_mock_item(item_id="i1", status=1),
        _make_mock_item(item_id="i2", status=1),
    ]
    task = _make_mock_task(title="All done", items=items)
    item = task_to_todo_item_with_subtask_progress(task)

    assert "[2/2 subtasks]" in item.description


def test_subtask_progress_none_completed():
    """No items completed shows 0/N."""
    items = [
        _make_mock_item(item_id="i1", status=0),
        _make_mock_item(item_id="i2", status=0),
        _make_mock_item(item_id="i3", status=0),
    ]
    task = _make_mock_task(title="Not started", items=items)
    item = task_to_todo_item_with_subtask_progress(task)

    assert "[0/3 subtasks]" in item.description


# ---------------------------------------------------------------------------
# _format_date_for_comparison tests
# ---------------------------------------------------------------------------

def test_format_date_none():
    """None returns empty string."""
    assert _format_date_for_comparison(None) == ""


def test_format_date_datetime():
    """datetime returns ISO format string."""
    dt = datetime(2025, 6, 15, 10, 30, 0)
    result = _format_date_for_comparison(dt)
    assert result == dt.isoformat()


def test_format_date_string():
    """String is stripped and returned."""
    assert _format_date_for_comparison("  2025-06-15  ") == "2025-06-15"


def test_format_date_other_type():
    """Other types are converted to string."""
    assert _format_date_for_comparison(42) == "42"
