# Subtask Progress & Smart Filtering - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add subtask progress tracking to Todo entity attributes and implement advanced task filtering services for TickTick Home Assistant integration.

**Architecture:** Extend existing Todo entity's `extra_state_attributes` to expose subtask progress data, and add two new service handlers (`get_subtasks`, `get_tasks_filtered`) for querying subtask details and filtering tasks by multiple criteria.

**Tech Stack:** Python 3.12+, Home Assistant 2024.1+, pytest, aiohttp, custom_components/ticktick

---

## Prerequisites

- Read design document: `docs/plans/2026-02-21-subtask-progress-smart-filtering-design.md`
- Understand existing Task model: `custom_components/ticktick/ticktick_api_python/models/task.py`
- Understand CheckListItem model: `custom_components/ticktick/ticktick_api_python/models/check_list_item.py`
- Understand Todo entity: `custom_components/ticktick/todo.py`
- Understand service handlers: `custom_components/ticktick/service_handlers.py`

---

## Task 1: Add Subtask Progress Unit Tests

**Files:**
- Create: `tests/test_subtask_progress.py`

**Step 1: Write the failing test - Subtask progress calculation**

```python
# tests/test_subtask_progress.py
import pytest
from custom_components.ticktick.ticktick_api_python.models.task import Task
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem, TaskStatus

def test_subtask_progress_calculation_60_percent():
    """Test subtask progress calculation with 3/5 completed."""
    # Create task with 5 subtasks, 3 completed
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

    assert progress == 100

def test_subtask_progress_no_subtasks():
    """Test task with no subtasks."""
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[]
    )

    assert len(task.items) == 0
```

**Step 2: Run test to verify it passes**

```bash
pytest tests/test_subtask_progress.py -v
```

Expected: PASS (these are pure Python calculations, no integration yet)

**Step 3: Commit**

```bash
git add tests/test_subtask_progress.py
git commit -m "test: add subtask progress calculation tests"
```

---

## Task 2: Implement Subtask Progress in Todo Entity Attributes

**Files:**
- Modify: `custom_components/ticktick/todo.py:288-301`

**Step 1: Write test for Todo entity attributes**

```python
# tests/test_todo_entity_subtasks.py
import pytest
from custom_components.ticktick.todo import TickTickTodoListEntity
from custom_components.ticktick.coordinator import TickTickCoordinator
from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskPriority
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem, TaskStatus
from custom_components.ticktick.ticktick_api_python.models.project import Project
from custom_components.ticktick.ticktick_api_python.models.project_with_tasks import ProjectWithTasks
from unittest.mock import Mock

def test_todo_entity_has_subtask_attributes():
    """Test that Todo entity exposes subtask progress in attributes."""
    # Create mock coordinator with subtask data
    coordinator = Mock(spec=TickTickCoordinator)

    # Create project with tasks that have subtasks
    task1 = Task(
        projectId="proj1",
        id="task1",
        title="Parent Task",
        items=[
            CheckListItem(id="sub1", title="Step 1", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="sub2", title="Step 2", status=TaskStatus.NORMAL),
        ]
    )

    project = Project(id="proj1", name="Test Project")
    project_data = ProjectWithTasks(project=project, tasks=[task1])
    coordinator.data = [project_data]

    # Create entity
    entity = TickTickTodoListEntity(
        coordinator=coordinator,
        config_entry_id="entry1",
        project_id="proj1",
        project_name="Test Project",
        task_type="active"
    )

    # Get attributes
    attrs = entity.extra_state_attributes

    # Verify subtask progress is present
    assert "subtask_progress" in attrs
    assert len(attrs["subtask_progress"]) == 1

    task_progress = attrs["subtask_progress"][0]
    assert task_progress["task_id"] == "task1"
    assert task_progress["subtask_total"] == 2
    assert task_progress["subtask_completed"] == 1
    assert task_progress["subtask_progress_percent"] == 50

def test_todo_entity_project_subtask_aggregates():
    """Test that Todo entity calculates project-level subtask aggregates."""
    coordinator = Mock(spec=TickTickCoordinator)

    # Multiple tasks with subtasks
    task1 = Task(
        projectId="proj1",
        id="task1",
        title="Task 1",
        items=[
            CheckListItem(id="sub1", title="A", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="sub2", title="B", status=TaskStatus.COMPLETED_1),
        ]
    )

    task2 = Task(
        projectId="proj1",
        id="task2",
        title="Task 2",
        items=[
            CheckListItem(id="sub3", title="C", status=TaskStatus.NORMAL),
        ]
    )

    project = Project(id="proj1", name="Test Project")
    project_data = ProjectWithTasks(project=project, tasks=[task1, task2])
    coordinator.data = [project_data]

    entity = TickTickTodoListEntity(
        coordinator=coordinator,
        config_entry_id="entry1",
        project_id="proj1",
        project_name="Test Project",
        task_type="active"
    )

    attrs = entity.extra_state_attributes

    # Verify project-level aggregates
    assert attrs["project_subtask_total"] == 3
    assert attrs["project_subtask_completed"] == 2
    assert attrs["project_subtask_progress_percent"] == 66
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_todo_entity_subtasks.py::test_todo_entity_has_subtask_attributes -v
```

Expected: FAIL with "AssertionError: assert 'subtask_progress' in attrs"

**Step 3: Implement subtask progress in Todo entity**

```python
# custom_components/ticktick/todo.py - Modify extra_state_attributes property (around line 288)

@property
def extra_state_attributes(self):
    """Return entity specific state attributes."""
    from custom_components.ticktick.ticktick_api_python.models.check_list_item import TaskStatus

    attrs = {}

    # Existing: completed tasks count
    if self._task_type == "completed" and self.coordinator.data:
        for project_with_tasks in self.coordinator.data:
            if project_with_tasks.project.id == self._project_id:
                attrs["completed_tasks_count"] = (
                    project_with_tasks.completed_tasks_count or 0
                )
                break

    # NEW: Subtask progress for each task in this entity
    if self.coordinator.data:
        for project_with_tasks in self.coordinator.data:
            if project_with_tasks.project.id == self._project_id:
                tasks = (
                    project_with_tasks.tasks
                    if self._task_type == "active"
                    else project_with_tasks.completed_tasks or []
                )

                # Build subtask summary for all tasks
                subtask_summary = []
                for task in tasks:
                    if task.items:  # Has subtasks
                        total_subtasks = len(task.items)
                        completed_subtasks = sum(
                            1 for item in task.items
                            if item.status != TaskStatus.NORMAL
                        )
                        progress_percent = int(
                            (completed_subtasks / total_subtasks) * 100
                        ) if total_subtasks > 0 else 0

                        subtask_summary.append({
                            "task_id": task.id,
                            "task_title": task.title,
                            "subtask_total": total_subtasks,
                            "subtask_completed": completed_subtasks,
                            "subtask_progress_percent": progress_percent,
                            "subtasks": [
                                {
                                    "id": item.id,
                                    "title": item.title,
                                    "status": "completed" if item.status != TaskStatus.NORMAL else "active"
                                }
                                for item in task.items
                            ]
                        })

                if subtask_summary:
                    attrs["subtask_progress"] = subtask_summary

                # Aggregate stats for the entire project
                all_subtasks = []
                for task in tasks:
                    if task.items:
                        all_subtasks.extend(task.items)

                if all_subtasks:
                    attrs["project_subtask_total"] = len(all_subtasks)
                    attrs["project_subtask_completed"] = sum(
                        1 for item in all_subtasks
                        if item.status != TaskStatus.NORMAL
                    )
                    attrs["project_subtask_progress_percent"] = int(
                        (attrs["project_subtask_completed"] / attrs["project_subtask_total"]) * 100
                    )

                break

    return attrs
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_todo_entity_subtasks.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add custom_components/ticktick/todo.py tests/test_todo_entity_subtasks.py
git commit -m "feat: add subtask progress to Todo entity attributes"
```

---

## Task 3: Implement Get Subtasks Service

**Files:**
- Modify: `custom_components/ticktick/service_handlers.py`

**Step 1: Write test for get_subtasks service**

```python
# tests/test_service_get_subtasks.py
import pytest
from custom_components.ticktick.service_handlers import handle_get_subtasks
from custom_components.ticktick.ticktick_api_python.ticktick_api import TickTickAPIClient
from unittest.mock import Mock, AsyncMock
from homeassistant.core import ServiceCall

@pytest.mark.asyncio
async def test_get_subtasks_service_returns_progress():
    """Test that get_subtasks service returns subtask progress."""
    # Mock API client
    client = Mock(spec=TickTickAPIClient)

    # Mock API response
    client.get_task = AsyncMock(return_value={
        "id": "task123",
        "title": "Grocery Shopping",
        "items": [
            {"id": "sub1", "title": "Milk", "status": 1},
            {"id": "sub2", "title": "Eggs", "status": 1},
            {"id": "sub3", "title": "Bread", "status": 0},
        ]
    })

    # Get handler
    handler = await handle_get_subtasks(client)

    # Call service
    call = Mock(spec=ServiceCall)
    call.data = {"project_id": "proj1", "task_id": "task123"}

    result = await handler(call)

    # Verify response
    assert "data" in result
    assert result["data"]["task_id"] == "task123"
    assert result["data"]["subtask_total"] == 3
    assert result["data"]["subtask_completed"] == 2
    assert result["data"]["subtask_progress_percent"] == 66
    assert len(result["data"]["subtasks"]) == 3

@pytest.mark.asyncio
async def test_get_subtasks_service_no_subtasks():
    """Test get_subtasks service with task that has no subtasks."""
    client = Mock(spec=TickTickAPIClient)

    client.get_task = AsyncMock(return_value={
        "id": "task123",
        "title": "Simple Task",
        "items": []
    })

    handler = await handle_get_subtasks(client)

    call = Mock(spec=ServiceCall)
    call.data = {"project_id": "proj1", "task_id": "task123"}

    result = await handler(call)

    assert result["data"]["subtask_total"] == 0
    assert result["data"]["subtasks"] == []

@pytest.mark.asyncio
async def test_get_subtasks_service_missing_params():
    """Test get_subtasks service with missing parameters."""
    client = Mock(spec=TickTickAPIClient)
    handler = await handle_get_subtasks(client)

    call = Mock(spec=ServiceCall)
    call.data = {"project_id": "proj1"}  # Missing task_id

    result = await handler(call)

    assert "error" in result
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_service_get_subtasks.py -v
```

Expected: FAIL with "AttributeError: module 'custom_components.ticktick.service_handlers' has no attribute 'handle_get_subtasks'"

**Step 3: Implement handle_get_subtasks**

```python
# custom_components/ticktick/service_handlers.py - Add after line 134 (after copy_task handler)

async def handle_get_subtasks(client: TickTickAPIClient) -> Callable:
    """Return a handler function for the 'get_subtasks' service."""

    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the get_subtasks service call."""
        project_id = call.data.get(PROJECT_ID)
        task_id = call.data.get(TASK_ID)

        if not project_id or not task_id:
            return {"error": f"Both {PROJECT_ID} and {TASK_ID} are required"}

        try:
            # Get the task
            task_response = await client.get_task(
                project_id, task_id, returnAsJson=True
            )

            # Extract subtasks (items)
            items = task_response.get("items", [])

            if not items:
                return {
                    "data": {
                        "task_id": task_id,
                        "task_title": task_response.get("title"),
                        "subtask_total": 0,
                        "subtask_completed": 0,
                        "subtask_progress_percent": 0,
                        "subtasks": []
                    }
                }

            # Calculate progress
            completed_count = sum(
                1 for item in items
                if item.get("status") not in (0, "0", None)
            )
            total_count = len(items)
            progress_percent = int((completed_count / total_count) * 100)

            return {
                "data": {
                    "task_id": task_id,
                    "task_title": task_response.get("title"),
                    "subtask_total": total_count,
                    "subtask_completed": completed_count,
                    "subtask_progress_percent": progress_percent,
                    "subtasks": [
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "status": "completed" if item.get("status") not in (0, "0", None) else "active",
                            "sort_order": item.get("sortOrder")
                        }
                        for item in items
                    ]
                }
            }

        except Exception as e:
            _LOGGER.error("Error getting subtasks: %s", str(e))
            return {"error": str(e)}

    return handler
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_service_get_subtasks.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add custom_components/ticktick/service_handlers.py tests/test_service_get_subtasks.py
git commit -m "feat: add get_subtasks service handler"
```

---

## Task 4: Implement Filtered Queries Service - Basic Structure

**Files:**
- Modify: `custom_components/ticktick/service_handlers.py`

**Step 1: Write test for basic filter functionality**

```python
# tests/test_service_get_tasks_filtered.py
import pytest
from datetime import datetime, timedelta
from custom_components.ticktick.service_handlers import handle_get_tasks_filtered
from custom_components.ticktick.ticktick_api_python.ticktick_api import TickTickAPIClient
from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskPriority, TaskStatus
from custom_components.ticktick.ticktick_api_python.models.project import Project
from custom_components.ticktick.ticktick_api_python.models.project_with_tasks import ProjectWithTasks
from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem
from unittest.mock import Mock, AsyncMock
from homeassistant.core import ServiceCall

@pytest.mark.asyncio
async def test_filter_by_priority_high():
    """Test filtering tasks by high priority."""
    # Mock client
    client = Mock(spec=TickTickAPIClient)

    # Create tasks with different priorities
    high_task = Task(
        projectId="proj1",
        id="task1",
        title="Urgent",
        priority=TaskPriority.HIGH
    )

    low_task = Task(
        projectId="proj1",
        id="task2",
        title="Low",
        priority=TaskPriority.LOW
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(project=project, tasks=[high_task, low_task])

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    # Get handler
    handler = await handle_get_tasks_filtered(client)

    # Call service with high priority filter
    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {"priority": "high"}
    }

    result = await handler(call)

    # Verify only high priority task returned
    assert result["data"]["count"] == 1
    assert result["data"]["filtered_tasks"][0]["title"] == "Urgent"
    assert result["data"]["filtered_tasks"][0]["priority"] == "HIGH"

@pytest.mark.asyncio
async def test_filter_by_multiple_priorities():
    """Test filtering tasks by multiple priorities (OR logic)."""
    client = Mock(spec=TickTickAPIClient)

    high_task = Task(
        projectId="proj1",
        id="task1",
        title="Urgent",
        priority=TaskPriority.HIGH
    )

    medium_task = Task(
        projectId="proj1",
        id="task2",
        title="Medium",
        priority=TaskPriority.MEDIUM
    )

    low_task = Task(
        projectId="proj1",
        id="task3",
        title="Low",
        priority=TaskPriority.LOW
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(
        project=project,
        tasks=[high_task, medium_task, low_task]
    )

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    handler = await handle_get_tasks_filtered(client)

    # Filter for high OR medium
    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {"priority": ["high", "medium"]}
    }

    result = await handler(call)

    # Should return 2 tasks (high + medium)
    assert result["data"]["count"] == 2
    priorities = [t["priority"] for t in result["data"]["filtered_tasks"]]
    assert "HIGH" in priorities
    assert "MEDIUM" in priorities
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_by_priority_high -v
```

Expected: FAIL with "AttributeError: module ... has no attribute 'handle_get_tasks_filtered'"

**Step 3: Implement handle_get_tasks_filtered - Priority filters**

```python
# custom_components/ticktick/service_handlers.py - Add after handle_get_subtasks

async def handle_get_tasks_filtered(client: TickTickAPIClient) -> Callable:
    """Return a handler function for the 'get_tasks_filtered' service."""
    from datetime import datetime, timedelta

    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the get_tasks_filtered service call."""
        project_id = call.data.get(PROJECT_ID)

        if not project_id:
            return {"error": f"{PROJECT_ID} is required"}

        try:
            # Get all tasks for project
            project_data = await client.get_project_with_tasks(project_id)
            all_tasks = project_data[0].tasks if project_data else []

            if not all_tasks:
                return {"data": {"filtered_tasks": [], "count": 0}}

            # Apply filters
            filters = call.data.get("filters", {})
            filtered_tasks = []

            for task in all_tasks:
                # Priority filter
                if "priority" in filters:
                    filter_priority = filters["priority"]
                    if isinstance(filter_priority, str):
                        filter_priority = TaskPriority[filter_priority.upper()]

                    if isinstance(filter_priority, list):
                        # Multiple priorities allowed
                        filter_priorities = [
                            TaskPriority[p.upper()] if isinstance(p, str) else p
                            for p in filter_priority
                        ]
                        if task.priority not in filter_priorities:
                            continue
                    else:
                        if task.priority != filter_priority:
                            continue

                # Task matches all filters so far
                filtered_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.name,
                    "due_date": task.dueDate.isoformat() if task.dueDate else None,
                    "status": task.status.name,
                    "has_subtasks": len(task.items) > 0,
                    "subtask_total": len(task.items),
                    "subtask_completed": sum(
                        1 for item in task.items
                        if item.status != TaskStatus.NORMAL
                    ) if task.items else 0
                })

            return {
                "data": {
                    "filtered_tasks": filtered_tasks,
                    "count": len(filtered_tasks)
                }
            }

        except Exception as e:
            _LOGGER.error("Error filtering tasks: %s", str(e))
            return {"error": str(e)}

    return handler
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_by_priority_high -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add custom_components/ticktick/service_handlers.py tests/test_service_get_tasks_filtered.py
git commit -m "feat: add basic get_tasks_filtered service with priority filter"
```

---

## Task 5: Add Date Filters to Filtered Queries Service

**Files:**
- Modify: `custom_components/ticktick/service_handlers.py`

**Step 1: Write tests for date filters**

```python
# tests/test_service_get_tasks_filtered.py - Add tests

@pytest.mark.asyncio
async def test_filter_due_within_days():
    """Test filtering tasks due within N days."""
    client = Mock(spec=TickTickAPIClient)

    # Task due tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    due_task = Task(
        projectId="proj1",
        id="task1",
        title="Due Tomorrow",
        dueDate=tomorrow
    )

    # Task due next month
    next_month = datetime.now() + timedelta(days=30)
    future_task = Task(
        projectId="proj1",
        id="task2",
        title="Due Next Month",
        dueDate=next_month
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(project=project, tasks=[due_task, future_task])

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    handler = await handle_get_tasks_filtered(client)

    # Filter for tasks due within 7 days
    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {"due_within_days": 7}
    }

    result = await handler(call)

    # Should only return task due tomorrow
    assert result["data"]["count"] == 1
    assert result["data"]["filtered_tasks"][0]["title"] == "Due Tomorrow"

@pytest.mark.asyncio
async def test_filter_overdue():
    """Test filtering overdue tasks."""
    client = Mock(spec=TickTickAPIClient)

    # Overdue task
    yesterday = datetime.now() - timedelta(days=1)
    overdue_task = Task(
        projectId="proj1",
        id="task1",
        title="Overdue",
        dueDate=yesterday
    )

    # Future task
    next_week = datetime.now() + timedelta(days=7)
    future_task = Task(
        projectId="proj1",
        id="task2",
        title="Future",
        dueDate=next_week
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(project=project, tasks=[overdue_task, future_task])

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    handler = await handle_get_tasks_filtered(client)

    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {"overdue": True}
    }

    result = await handler(call)

    assert result["data"]["count"] == 1
    assert result["data"]["filtered_tasks"][0]["title"] == "Overdue"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_due_within_days -v
```

Expected: FAIL - date filters not yet implemented

**Step 3: Implement date filters**

```python
# In handle_get_tasks_filtered - Add to filter logic (before building response)

# Due date filters
if "due_before" in filters:
    due_date = filters["due_before"]
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date)
    if not task.dueDate or task.dueDate > due_date:
        continue

if "due_within_days" in filters:
    days = filters["due_within_days"]
    cutoff = datetime.now() + timedelta(days=days)
    if not task.dueDate or task.dueDate > cutoff:
        continue

if "overdue" in filters:
    if filters["overdue"]:
        if not task.dueDate or task.dueDate >= datetime.now():
            continue
    else:
        if task.dueDate and task.dueDate < datetime.now():
            continue
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_due_within_days -v
pytest tests/test_service_get_tasks_filtered.py::test_filter_overdue -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add custom_components/ticktick/service_handlers.py tests/test_service_get_tasks_filtered.py
git commit -m "feat: add date filters to get_tasks_filtered service"
```

---

## Task 6: Add Subtask Progress Filters

**Files:**
- Modify: `custom_components/ticktick/service_handlers.py`

**Step 1: Write tests for subtask progress filters**

```python
# tests/test_service_get_tasks_filtered.py - Add tests

@pytest.mark.asyncio
async def test_filter_has_subtasks():
    """Test filtering tasks that have subtasks."""
    client = Mock(spec=TickTickAPIClient)

    # Task with subtasks
    task_with_subs = Task(
        projectId="proj1",
        id="task1",
        title="With Subtasks",
        items=[
            CheckListItem(id="sub1", title="A", status=TaskStatus.NORMAL),
            CheckListItem(id="sub2", title="B", status=TaskStatus.NORMAL),
        ]
    )

    # Task without subtasks
    task_no_subs = Task(
        projectId="proj1",
        id="task2",
        title="No Subtasks",
        items=[]
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(
        project=project,
        tasks=[task_with_subs, task_no_subs]
    )

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    handler = await handle_get_tasks_filtered(client)

    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {"has_subtasks": True}
    }

    result = await handler(call)

    assert result["data"]["count"] == 1
    assert result["data"]["filtered_tasks"][0]["title"] == "With Subtasks"

@pytest.mark.asyncio
async def test_filter_subtask_progress_lt():
    """Test filtering tasks with subtask progress less than X%."""
    client = Mock(spec=TickTickAPIClient)

    # 50% complete task
    half_done = Task(
        projectId="proj1",
        id="task1",
        title="Half Done",
        items=[
            CheckListItem(id="sub1", title="A", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="sub2", title="B", status=TaskStatus.NORMAL),
        ]
    )

    # 100% complete task
    fully_done = Task(
        projectId="proj1",
        id="task2",
        title="Fully Done",
        items=[
            CheckListItem(id="sub3", title="C", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="sub4", title="D", status=TaskStatus.COMPLETED_1),
        ]
    )

    project = Project(id="proj1", name="Test")
    project_data = ProjectWithTasks(project=project, tasks=[half_done, fully_done])

    client.get_project_with_tasks = AsyncMock(return_value=[project_data])

    handler = await handle_get_tasks_filtered(client)

    # Filter for tasks with progress < 100%
    call = Mock(spec=ServiceCall)
    call.data = {
        "project_id": "proj1",
        "filters": {
            "has_subtasks": True,
            "subtask_progress_lt": 100
        }
    }

    result = await handler(call)

    # Should only return half_done task
    assert result["data"]["count"] == 1
    assert result["data"]["filtered_tasks"][0]["title"] == "Half Done"
    assert result["data"]["filtered_tasks"][0]["subtask_progress_percent"] == 50
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_has_subtasks -v
```

Expected: FAIL - subtask filters not yet implemented

**Step 3: Implement subtask filters**

```python
# In handle_get_tasks_filtered - Add to filter logic

# Has subtasks filter
if "has_subtasks" in filters:
    if filters["has_subtasks"] and not task.items:
        continue
    if not filters["has_subtasks"] and task.items:
        continue

# Subtask progress filter
if "subtask_progress_lt" in filters:
    if not task.items:
        continue
    completed = sum(1 for item in task.items if item.status != TaskStatus.NORMAL)
    progress = int((completed / len(task.items)) * 100)
    if progress >= filters["subtask_progress_lt"]:
        continue

if "subtask_progress_gte" in filters:
    if not task.items:
        continue
    completed = sum(1 for item in task.items if item.status != TaskStatus.NORMAL)
    progress = int((completed / len(task.items)) * 100)
    if progress < filters["subtask_progress_gte"]:
        continue
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_service_get_tasks_filtered.py::test_filter_has_subtasks -v
pytest tests/test_service_get_tasks_filtered.py::test_filter_subtask_progress_lt -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add custom_components/ticktick/service_handlers.py tests/test_service_get_tasks_filtered.py
git commit -m "feat: add subtask progress filters to get_tasks_filtered"
```

---

## Task 7: Register Services in __init__.py

**Files:**
- Modify: `custom_components/ticktick/__init__.py`

**Step 1: Locate service registration**

```bash
grep -n "async_setup_services" custom_components/ticktick/__init__.py
```

Find the async_setup_services function (typically around line 50-100).

**Step 2: Add service registrations**

```python
# In async_setup_services function, add:

# Existing service registrations...
hservice = async_register_admin_service(
    hass,
    DOMAIN,
    "get_subtasks",
    handle_get_subtasks(client),
)

hservice = async_register_admin_service(
    hass,
    DOMAIN,
    "get_tasks_filtered",
    handle_get_tasks_filtered(client),
)
```

**Step 3: Verify services appear in Home Assistant**

Restart Home Assistant and check Developer Tools → Services → `ticktick.get_subtasks` and `ticktick.get_tasks_filtered` appear.

**Step 4: Commit**

```bash
git add custom_components/ticktick/__init__.py
git commit -m "feat: register get_subtasks and get_tasks_filtered services"
```

---

## Task 8: Update README Documentation

**Files:**
- Modify: `README.md`

**Step 1: Add feature documentation**

```markdown
# Add after "Recently Completed Tasks" section

## Subtask Progress Tracking

The integration exposes subtask progress in Todo entity attributes, enabling powerful automations and template sensors.

### Entity Attributes

For each Todo entity, the following attributes are available:

- `subtask_progress` - Array of tasks with subtasks, showing individual progress
- `project_subtask_total` - Total subtasks across all tasks in project
- `project_subtask_completed` - Number of completed subtasks
- `project_subtask_progress_percent` - Overall project subtask progress percentage

### Example Automation

```yaml
automation:
  - alias: "Track subtask progress"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('todo.my_project', 'project_subtask_progress_percent') == 100 }}
    action:
      - service: notify.notify
        data:
          message: "🎉 All project subtasks completed!"
```

## Smart Task Filtering

Use the `ticktick.get_tasks_filtered` service to query tasks with advanced filters.

### Service Usage

```yaml
service: ticktick.get_tasks_filtered
data:
  project_id: "your_project_id"
  filters:
    priority: "high"
    overdue: true
    has_subtasks: true
```

### Supported Filters

- `priority` - Task priority ("none", "low", "medium", "high") or list
- `due_before` - Due date cutoff (ISO format)
- `due_within_days` - Due within N days
- `overdue` - Only overdue tasks (true/false)
- `has_subtasks` - Only tasks with subtasks (true/false)
- `subtask_progress_lt` - Subtask progress less than X%
- `subtask_progress_gte` - Subtask progress greater than or equal to X%
- `has_reminders` - Only tasks with reminders (true/false)
- `is_recurring` - Only recurring tasks (true/false)

### Example: Find Overdue High-Priority Tasks

```yaml
automation:
  - alias: "Alert on urgent tasks"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: ticktick.get_tasks_filtered
        data:
          project_id: !secret ticktick_project_id
          filters:
            priority: "high"
            overdue: true
        response_variable: urgent_tasks
      - service: notify.notify
        data:
          message: "You have {{ urgent_tasks.data.count }} urgent overdue tasks!"
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document subtask progress and smart filtering features"
```

---

## Task 9: Manual Testing Checklist

**Step 1: Test subtask progress attributes**

1. Open Home Assistant Developer Tools → States
2. Search for your TickTick Todo entity
3. Click entity to view attributes
4. Verify `subtask_progress` array appears (if project has tasks with subtasks)
5. Verify `project_subtask_*` aggregate attributes appear

**Step 2: Test get_subtasks service**

1. Open Developer Tools → Services
2. Select service: `ticktick.get_subtasks`
3. Enter `project_id` and `task_id` (get from entity attributes)
4. Call service
5. Verify response contains subtask details and progress

**Step 3: Test get_tasks_filtered service**

1. Open Developer Tools → Services
2. Select service: `ticktick.get_tasks_filtered`
3. Enter `project_id`
4. Add filter: `filters: {"priority": "high"}`
5. Call service
6. Verify only high-priority tasks returned
7. Try multiple filters: `{"priority": ["high", "medium"], "overdue": true}`

**Step 4: Test automations**

1. Create template sensor for subtask progress
2. Create automation that triggers on subtask completion
3. Verify automations fire correctly

**Step 5: Document test results**

Create `docs/SUBTASK_FEATURE_TESTING.md` with test results.

---

## Task 10: Final Verification and Cleanup

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass

**Step 2: Check for TODO comments**

```bash
grep -r "TODO" custom_components/ticktick/
```

Remove or address any TODOs

**Step 3: Verify no breaking changes**

- Existing Todo entities still work
- Existing services still function
- No errors in Home Assistant logs

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete subtask progress and smart filtering implementation

- Add subtask progress attributes to Todo entities
- Implement get_subtasks service for detailed subtask queries
- Implement get_tasks_filtered service with multi-criteria filtering
- Add comprehensive unit tests
- Update documentation"
```

---

## Summary

This implementation plan adds two powerful features to the TickTick integration:

1. **Subtask Progress Tracking** - Exposes subtask data in Todo entity attributes
2. **Smart Filtering** - Advanced service-based task filtering

**Total Tasks:** 10
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Breaking Changes:** None (backward compatible)

**Next Steps:**
1. Review plan and adjust if needed
2. Choose execution approach (subagent-driven vs parallel session)
3. Implement following TDD principles
4. Manual testing with real TickTick data
5. Deploy and monitor
