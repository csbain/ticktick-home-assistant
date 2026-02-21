#!/usr/bin/env python3
"""Test subtask progress in Todo entity attributes."""

import sys
sys.path.insert(0, '/home/csbain/p/ticktick-home-assistant')

from unittest.mock import Mock
from custom_components.ticktick.todo import TickTickTodoListEntity
from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskStatus
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem
from custom_components.ticktick.coordinator import ProjectWithTasks
from custom_components.ticktick.ticktick_api_python.models.project import Project


def test_active_entity_has_subtask_progress():
    """Test that active entity includes subtask progress attributes."""
    print("\n🧪 Testing active entity subtask progress...")

    coordinator = Mock()
    coordinator.data = [
        ProjectWithTasks(
            project=Project(
                id="proj1",
                name="Test Project",
                viewMode="LIST",
            ),
            tasks=[
                # Task with 3/5 subtasks completed (60%)
                Task(
                    projectId="proj1",
                    id="task1",
                    title="Task with subtasks",
                    items=[
                        CheckListItem(id="sub1", title="Sub 1", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub2", title="Sub 2", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub3", title="Sub 3", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub4", title="Sub 4", status=TaskStatus.NORMAL),
                        CheckListItem(id="sub5", title="Sub 5", status=TaskStatus.NORMAL),
                    ]
                ),
                # Task with no subtasks
                Task(
                    projectId="proj1",
                    id="task2",
                    title="Task without subtasks",
                    items=None
                ),
                # Task with all subtasks completed (100%)
                Task(
                    projectId="proj1",
                    id="task3",
                    title="Completed task",
                    items=[
                        CheckListItem(id="sub6", title="Sub 6", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub7", title="Sub 7", status=TaskStatus.COMPLETED_1),
                    ]
                ),
            ],
            completed_tasks=[]
        )
    ]

    entity = TickTickTodoListEntity(
        coordinator=coordinator,
        config_entry_id="entry1",
        project_id="proj1",
        project_name="Test Project",
        task_type="active"
    )

    attrs = entity.extra_state_attributes

    # Verify task-level subtask progress array
    assert "subtask_progress" in attrs, "subtask_progress should be in attributes"
    assert len(attrs["subtask_progress"]) == 2, f"Expected 2 tasks with subtasks, got {len(attrs['subtask_progress'])}"

    # Check first task (60% progress)
    task1_progress = next(t for t in attrs["subtask_progress"] if t["task_id"] == "task1")
    assert task1_progress["task_title"] == "Task with subtasks", f"Expected 'Task with subtasks', got {task1_progress['task_title']}"
    assert task1_progress["subtask_total"] == 5, f"Expected 5 total subtasks, got {task1_progress['subtask_total']}"
    assert task1_progress["subtask_completed"] == 3, f"Expected 3 completed subtasks, got {task1_progress['subtask_completed']}"
    assert task1_progress["subtask_progress_percent"] == 60, f"Expected 60% progress, got {task1_progress['subtask_progress_percent']}"
    assert len(task1_progress["subtasks"]) == 5, f"Expected 5 subtasks in list, got {len(task1_progress['subtasks'])}"

    # Check third task (100% progress)
    task3_progress = next(t for t in attrs["subtask_progress"] if t["task_id"] == "task3")
    assert task3_progress["task_title"] == "Completed task", f"Expected 'Completed task', got {task3_progress['task_title']}"
    assert task3_progress["subtask_total"] == 2, f"Expected 2 total subtasks, got {task3_progress['subtask_total']}"
    assert task3_progress["subtask_completed"] == 2, f"Expected 2 completed subtasks, got {task3_progress['subtask_completed']}"
    assert task3_progress["subtask_progress_percent"] == 100, f"Expected 100% progress, got {task3_progress['subtask_progress_percent']}"

    # Verify project-level aggregates
    assert attrs["project_subtask_total"] == 7, f"Expected 7 total subtasks across project, got {attrs['project_subtask_total']}"
    assert attrs["project_subtask_completed"] == 5, f"Expected 5 completed subtasks across project, got {attrs['project_subtask_completed']}"
    assert attrs["project_subtask_progress_percent"] == 71, f"Expected 71% project progress, got {attrs['project_subtask_progress_percent']}"

    print("✅ Active entity subtask progress test PASSED")


def test_completed_entity_has_subtask_progress():
    """Test that completed entity also includes subtask progress."""
    print("\n🧪 Testing completed entity subtask progress...")

    coordinator = Mock()
    coordinator.data = [
        ProjectWithTasks(
            project=Project(
                id="proj1",
                name="Test Project",
                viewMode="LIST",
            ),
            tasks=[
                Task(
                    projectId="proj1",
                    id="task1",
                    title="Task with subtasks",
                    items=[
                        CheckListItem(id="sub1", title="Sub 1", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub2", title="Sub 2", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub3", title="Sub 3", status=TaskStatus.COMPLETED_1),
                        CheckListItem(id="sub4", title="Sub 4", status=TaskStatus.NORMAL),
                        CheckListItem(id="sub5", title="Sub 5", status=TaskStatus.NORMAL),
                    ]
                ),
            ],
            completed_tasks=[],
            completed_tasks_count=5
        )
    ]

    entity = TickTickTodoListEntity(
        coordinator=coordinator,
        config_entry_id="entry1",
        project_id="proj1",
        project_name="Test Project",
        task_type="completed"
    )

    attrs = entity.extra_state_attributes

    # Completed entity should have both completed_tasks_count AND subtask progress
    assert "completed_tasks_count" in attrs, "completed_tasks_count should be in attributes"
    assert "subtask_progress" in attrs, "subtask_progress should be in attributes"
    assert "project_subtask_total" in attrs, "project_subtask_total should be in attributes"

    print("✅ Completed entity subtask progress test PASSED")


def test_entity_with_no_subtasks():
    """Test entity when project has no tasks with subtasks."""
    print("\n🧪 Testing entity with no subtasks...")

    coordinator = Mock()
    coordinator.data = [
        ProjectWithTasks(
            project=Project(id="proj2", name="No Subtasks", viewMode="LIST"),
            tasks=[
                Task(projectId="proj2", id="task1", title="Simple task", items=None),
            ],
            completed_tasks=[]
        )
    ]

    entity = TickTickTodoListEntity(
        coordinator=coordinator,
        config_entry_id="entry1",
        project_id="proj2",
        project_name="No Subtasks",
        task_type="active"
    )

    attrs = entity.extra_state_attributes

    # Should not have subtask attributes when no subtasks exist
    assert "subtask_progress" not in attrs, "subtask_progress should NOT be in attributes when no subtasks exist"
    assert "project_subtask_total" not in attrs, "project_subtask_total should NOT be in attributes when no subtasks exist"

    print("✅ No subtasks test PASSED")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Todo Entity Subtask Progress Implementation")
    print("="*60)

    try:
        test_active_entity_has_subtask_progress()
        test_completed_entity_has_subtask_progress()
        test_entity_with_no_subtasks()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED (3/3)")
        print("="*60 + "\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
