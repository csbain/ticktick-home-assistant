#!/usr/bin/env python3
"""Tests for the get_subtasks service handler.

Verifies the handler returned by handle_get_subtasks(), which:
  - Looks up a task by ID from batch data
  - Returns subtask info with completion counts
  - Returns error when task_id missing or task not found
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helper to build mock batch / tasks / items
# ---------------------------------------------------------------------------

def _make_mock_item(*, item_id="item1", title="Sub", status=0, sort_order=0):
    """Create a mock ItemV2."""
    item = MagicMock()
    item.id = item_id
    item.title = title
    item.status = status
    item.sort_order = sort_order
    return item


def _make_mock_task(*, task_id="task1", title="Task", items=None):
    """Create a mock TaskV2."""
    task = MagicMock()
    task.id = task_id
    task.title = title
    task.items = items or []
    return task


def _make_mock_batch(tasks):
    """Create a mock batch response."""
    batch = MagicMock()
    batch.sync_task_bean.update = tasks
    return batch


def _make_mock_service_call(data):
    """Create a mock ServiceCall."""
    call = MagicMock()
    call.data = data
    return call


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_subtasks_task_not_found():
    """Returns error when task_id doesn't match any task."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    client = AsyncMock()
    client.async_get_batch = AsyncMock(return_value=_make_mock_batch([]))

    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({"task_id": "nonexistent"})
    result = await handler(call)

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_get_subtasks_missing_task_id():
    """Returns error when task_id not provided."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    client = AsyncMock()
    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({})
    result = await handler(call)

    assert "error" in result
    assert "required" in result["error"].lower()


@pytest.mark.asyncio
async def test_get_subtasks_with_items():
    """Returns correct subtask data when task has items."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    items = [
        _make_mock_item(item_id="i1", title="Buy eggs", status=1, sort_order=1),
        _make_mock_item(item_id="i2", title="Buy milk", status=0, sort_order=2),
        _make_mock_item(item_id="i3", title="Buy bread", status=1, sort_order=3),
    ]
    task = _make_mock_task(task_id="t1", title="Shopping", items=items)
    batch = _make_mock_batch([task])

    client = AsyncMock()
    client.async_get_batch = AsyncMock(return_value=batch)

    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({"task_id": "t1"})
    result = await handler(call)

    assert "data" in result
    data = result["data"]
    assert data["task_id"] == "t1"
    assert data["task_title"] == "Shopping"
    assert data["subtask_total"] == 3
    assert data["subtask_completed"] == 2
    assert data["subtask_progress_percent"] == 66  # int(2/3 * 100) = 66

    # Verify subtask details
    subtasks = data["subtasks"]
    assert len(subtasks) == 3
    assert subtasks[0]["title"] == "Buy eggs"
    assert subtasks[0]["status"] == "completed"
    assert subtasks[1]["title"] == "Buy milk"
    assert subtasks[1]["status"] == "active"


@pytest.mark.asyncio
async def test_get_subtasks_no_items():
    """Task with empty items list returns zeros."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    task = _make_mock_task(task_id="t1", title="Simple", items=[])
    batch = _make_mock_batch([task])

    client = AsyncMock()
    client.async_get_batch = AsyncMock(return_value=batch)

    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({"task_id": "t1"})
    result = await handler(call)

    assert "data" in result
    data = result["data"]
    assert data["subtask_total"] == 0
    assert data["subtask_completed"] == 0
    assert data["subtask_progress_percent"] == 0
    assert data["subtasks"] == []


@pytest.mark.asyncio
async def test_get_subtasks_all_completed():
    """All items completed gives 100%."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    items = [
        _make_mock_item(item_id="i1", status=1),
        _make_mock_item(item_id="i2", status=1),
    ]
    task = _make_mock_task(task_id="t1", title="Done", items=items)
    batch = _make_mock_batch([task])

    client = AsyncMock()
    client.async_get_batch = AsyncMock(return_value=batch)

    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({"task_id": "t1"})
    result = await handler(call)

    assert result["data"]["subtask_progress_percent"] == 100


@pytest.mark.asyncio
async def test_get_subtasks_selects_correct_task():
    """Handler selects the correct task from multiple tasks."""
    from custom_components.ticktick.service_handlers import handle_get_subtasks

    task1 = _make_mock_task(task_id="t1", title="Task 1", items=[])
    task2 = _make_mock_task(
        task_id="t2",
        title="Task 2",
        items=[_make_mock_item(item_id="i1", status=1)],
    )
    task3 = _make_mock_task(task_id="t3", title="Task 3", items=[])
    batch = _make_mock_batch([task1, task2, task3])

    client = AsyncMock()
    client.async_get_batch = AsyncMock(return_value=batch)

    handler = await handle_get_subtasks(client)
    call = _make_mock_service_call({"task_id": "t2"})
    result = await handler(call)

    assert result["data"]["task_title"] == "Task 2"
    assert result["data"]["subtask_total"] == 1
