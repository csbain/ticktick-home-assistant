#!/usr/bin/env python3
"""Test subtask progress calculation logic."""

from custom_components.ticktick.ticktick_api_python.models.task import Task
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem, TaskStatus


def _calculate_subtask_progress(items):
    """Calculate subtask progress metrics.

    Args:
        items: List of CheckListItem objects or None

    Returns:
        Tuple of (total, completed, progress_percent)
    """
    if items is None or len(items) == 0:
        return 0, 0, 0

    total = len(items)
    completed = sum(1 for item in items if item.status != TaskStatus.NORMAL)
    progress = int((completed / total) * 100) if total > 0 else 0

    return total, completed, progress


def test_subtask_progress_calculation_60_percent():
    """Test subtask progress calculation with 3/5 completed."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="4", title="Sub4", status=TaskStatus.NORMAL),
            CheckListItem(id="5", title="Sub5", status=TaskStatus.NORMAL),
        ]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 5
    assert completed == 3
    assert progress == 60


def test_subtask_progress_calculation_100_percent():
    """Test subtask progress calculation with all completed."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.COMPLETED_1),
        ]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 3
    assert completed == 3
    assert progress == 100


def test_subtask_progress_0_percent():
    """Test subtask progress calculation with 0% completed (all NORMAL)."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.NORMAL),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.NORMAL),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.NORMAL),
        ]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 3
    assert completed == 0
    assert progress == 0


def test_subtask_progress_no_subtasks_none():
    """Test subtask progress calculation with None items."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=None
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 0
    assert completed == 0
    assert progress == 0


def test_subtask_progress_no_subtasks_empty_list():
    """Test subtask progress calculation with empty items list."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 0
    assert completed == 0
    assert progress == 0


def test_subtask_progress_completed_2_status():
    """Test subtask progress calculation with COMPLETED_2 status."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.COMPLETED_2),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.NORMAL),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.NORMAL),
        ]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 3
    assert completed == 1
    assert progress == 33  # Round down from 33.33


def test_subtask_progress_mixed_completed_statuses():
    """Test subtask progress with mixed COMPLETED_1 and COMPLETED_2."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.COMPLETED_2),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.NORMAL),
            CheckListItem(id="4", title="Sub4", status=TaskStatus.NORMAL),
        ]
    )

    total, completed, progress = _calculate_subtask_progress(task.items)

    assert total == 4
    assert completed == 2
    assert progress == 50
