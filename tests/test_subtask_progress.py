#!/usr/bin/env python3
"""Test subtask progress calculation logic."""

import pytest
from custom_components.ticktick.ticktick_api_python.models.task import Task
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem, TaskStatus


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

    total = len(task.items)
    completed = sum(1 for item in task.items if item.status != TaskStatus.NORMAL)
    progress = int((completed / total) * 100)

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

    total = len(task.items)
    completed = sum(1 for item in task.items if item.status != TaskStatus.NORMAL)
    progress = int((completed / total) * 100)

    assert total == 3
    assert completed == 3
    assert progress == 100


def test_subtask_progress_no_subtasks():
    """Test subtask progress calculation with no subtasks."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=None
    )

    if task.items is None:
        total = 0
        completed = 0
        progress = 0
    else:
        total = len(task.items)
        completed = sum(1 for item in task.items if item.status != TaskStatus.NORMAL)
        progress = int((completed / total) * 100) if total > 0 else 0

    assert total == 0
    assert completed == 0
    assert progress == 0
