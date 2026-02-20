# Recently Completed Tasks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add support for viewing and reopening recently completed TickTick tasks through separate companion Todo entities in Home Assistant.

**Architecture:** Create companion Todo entities (e.g., `todo.shopping_list` and `todo.shopping_list_completed`) that share the same underlying TickTick project data. Active entity shows incomplete tasks (status=0), completed entity shows tasks completed within configurable N days (status=1 or 2). Users can complete tasks in active entity (moves to completed) or reopen tasks in completed entity (moves to active).

**Tech Stack:** Python 3.12+, Home Assistant 2024.x, aiohttp, TickTick Open API

---

## Overview

This feature enables TickTick integration users to:
1. View recently completed tasks in a separate Todo entity
2. Reopen completed tasks by unchecking them in the UI
3. Configure how many days of completed history to display
4. Use native Home Assistant Todo platform features (cards, automations, etc.)

**Key Design Decisions:**
- Separate entities rather than attributes (HA Todo platform constraint)
- Bidirectional status flow (complete ↔ reopen)
- Configurable lookback period (default 7 days)
- Uses existing API methods (no new endpoints needed)

---

## Task 1: Add Configuration Option for Completed Tasks Days

**Files:**
- Modify: `custom_components/ticktick/const.py`
- Modify: `custom_components/ticktick/config_flow.py`
- Modify: `custom_components/ticktick/strings.json` (or `translations/en.json`)

**Why First:** Add configuration before implementation so it's available when entities need it.

### Step 1: Add configuration constant to const.py

Add at end of constants section:

```python
# === Configuration === #
CONF_COMPLETED_TASKS_DAYS = "completed_tasks_days"
DEFAULT_COMPLETED_TASKS_DAYS = 7
```

Commit: `git add custom_components/ticktick/const.py && git commit -m "feat: add completed tasks days config constant"`

### Step 2: Update config flow step schema

Modify `config_flow.py` to add completed days option to config step:

```python
from homeassistant.helpers import config_entry_flow
from .const import CONF_COMPLETED_TASKS_DAYS, DEFAULT_COMPLETED_TASKS_DAYS

# In the appropriate step method (likely async_step_user or similar)
# Add to the schema:
DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COMPLETED_TASKS_DAYS, default=DEFAULT_COMPLETED_TASKS_DAYS): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=365)
        )
    }
)
```

Commit: `git add custom_components/ticktick/config_flow.py && git commit -m "feat: add completed days input to config flow"`

### Step 3: Add translation strings

Add to `translations/en.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "completed_tasks_days": "Completed tasks history (days)",
          "completed_tasks_days_description": "How many days of completed tasks to show in companion entity"
        }
      }
    }
  }
}
```

Commit: `git add custom_components/ticktick/translations/en.json && git commit -m "feat: add completed days translation strings"`

### Step 4: Verify config flow loads

Run: `python -m homeassistant -c custom_components/ticktick/config_flow.py`
Expected: No import errors, schema includes `completed_tasks_days` field

---

## Task 2: Add get_completed_tasks Method to API Client

**Files:**
- Modify: `custom_components/ticktick/ticktick_api_python/ticktick_api.py`
- Test: `tests/test_ticktick_api.py` (if exists, create if not)

**Why Second:** Core API method needed before entity and coordinator can use it.

### Step 1: Write failing test

Create or add to `tests/test_ticktick_api.py`:

```python
import pytest
from datetime import datetime, timedelta
from custom_components.ticktick.ticktick_api_python.ticktick_api import TickTickAPIClient
from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskStatus

@pytest.mark.asyncio
async def test_get_completed_tasks_filters_by_date():
    """Test that get_completed_tasks only returns tasks completed within specified days."""
    # Setup
    client = TickTickAPIClient("test_token", mock_session)
    project_id = "test_project"

    # Create mock tasks - some completed recently, some older
    recent_task = Task(
        projectId=project_id,
        title="Recent completed",
        id="1",
        status=TaskStatus.COMPLETED,
        completedTime=datetime.now() - timedelta(days=2)
    )
    old_task = Task(
        projectId=project_id,
        title="Old completed",
        id="2",
        status=TaskStatus.COMPLETED,
        completedTime=datetime.now() - timedelta(days=10)
    )
    active_task = Task(
        projectId=project_id,
        title="Active task",
        id="3",
        status=TaskStatus.NORMAL
    )

    # Mock get_project_with_tasks to return these tasks
    # (implementation depends on test setup)

    # Act
    result = await client.get_completed_tasks(project_id, days=7)

    # Assert
    assert len(result) == 1
    assert result[0].id == "1"
    assert result[0].title == "Recent completed"
```

Commit: `git add tests/test_ticktick_api.py && git commit -m "test: add failing test for get_completed_tasks"`

### Step 2: Run test to verify it fails

Run: `pytest tests/test_ticktick_api.py::test_get_completed_tasks_filters_by_date -v`
Expected: FAIL with "method 'get_completed_tasks' not found"

### Step 3: Implement get_completed_tasks method

Add to `ticktick_api.py` after `get_project_with_tasks` method:

```python
async def get_completed_tasks(
    self,
    projectId: str,
    days: int = 7,
    returnAsJson: bool = False
) -> list[Task]:
    """Return tasks completed within the last N days.

    Args:
        projectId: The project ID to fetch tasks from
        days: Number of days to look back for completed tasks
        returnAsJson: If True, return raw JSON instead of Task objects

    Returns:
        List of Task objects completed within the specified time range,
        sorted by completedTime (newest first).
    """
    from datetime import datetime, timedelta

    # Get all tasks for the project (includes completed ones)
    response = await self._get(
        GET_PROJECTS_WITH_TASKS.format(projectId=projectId)
    )

    if returnAsJson:
        return response

    # Parse response
    project_with_tasks = ProjectWithTasks.from_dict(response)

    if not project_with_tasks.tasks:
        return []

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)

    # Filter for completed tasks within date range
    completed_tasks = []
    for task in project_with_tasks.tasks:
        # Check if task is completed (status 1 or 2) and has completedTime
        if task.status in (TaskStatus.COMPLETED_1, TaskStatus.COMPLETED_2, TaskStatus.COMPLETED):
            if task.completedTime and task.completedTime >= cutoff_date:
                completed_tasks.append(task)

    # Sort by completion time (newest first)
    completed_tasks.sort(
        key=lambda t: t.completedTime or datetime.min,
        reverse=True
    )

    return completed_tasks
```

Commit: `git add custom_components/ticktick/ticktick_api_python/ticktick_api.py && git commit -m "feat: add get_completed_tasks API method"`

### Step 4: Run test to verify it passes

Run: `pytest tests/test_ticktick_api.py::test_get_completed_tasks_filters_by_date -v`
Expected: PASS

---

## Task 3: Add reopen_task API Method

**Files:**
- Modify: `custom_components/ticktick/ticktick_api_python/ticktick_api.py`
- Test: `tests/test_ticktick_api.py`

**Why Third:** Helper method for reopening tasks (update status to 0).

### Step 1: Write failing test

Add to `tests/test_ticktick_api.py`:

```python
@pytest.mark.asyncio
async def test_reopen_task_sets_status_to_normal():
    """Test that reopen_task updates task status to NORMAL."""
    client = TickTickAPIClient("test_token", mock_session)

    # Mock update_task to capture the call
    # ...

    await client.reopen_task("test_project", "task_123")

    # Assert update_task was called with status=0
    # ...
```

Commit: `git add tests/test_ticktick_api.py && git commit -m "test: add failing test for reopen_task"`

### Step 2: Run test to verify it fails

Run: `pytest tests/test_ticktick_api.py::test_reopen_task_sets_status_to_normal -v`
Expected: FAIL with "method 'reopen_task' not found"

### Step 3: Implement reopen_task method

Add to `ticktick_api.py` after `complete_task` method:

```python
async def reopen_task(self, projectId: str, taskId: str) -> Task:
    """Reopen a completed task by setting status to NORMAL.

    Args:
        projectId: The project ID containing the task
        taskId: The task ID to reopen

    Returns:
        The updated Task object with status=NORMAL
    """
    # Get the current task state
    response = await self._get(
        GET_TASK.format(projectId=projectId, taskId=taskId)
    )

    # Parse and update status
    task = Task.from_dict(response)
    task.status = TaskStatus.NORMAL

    # Send update to API
    update_response = await self._post(
        UPDATE_TASK.format(taskId=taskId),
        task.toJSON()
    )

    return Task.from_dict(update_response)
```

Commit: `git add custom_components/ticktick/ticktick_api_python/ticktick_api.py && git commit -m "feat: add reopen_task API method"`

### Step 4: Run test to verify it passes

Run: `pytest tests/test_ticktick_api.py::test_reopen_task_sets_status_to_normal -v`
Expected: PASS

---

## Task 4: Update Coordinator to Fetch Completed Tasks

**Files:**
- Modify: `custom_components/ticktick/coordinator.py`

**Why Fourth:** Coordinator needs to fetch both active and completed tasks for entities.

### Step 1: Read coordinator implementation

Read: `custom_components/ticktick/coordinator.py`
Understand: How `_async_update_data` works, how data is stored

### Step 2: Modify coordinator to include completed tasks

Update the coordinator's `_async_update_data` method:

```python
async def _async_update_data(self) -> list[ProjectWithTasks]:
    """Fetch project data including both active and completed tasks."""
    from homeassistant.util import dt as dt_util

    # Get configured days for completed tasks
    completed_days = self.config_entry.options.get(
        CONF_COMPLETED_TASKS_DAYS,
        DEFAULT_COMPLETED_TASKS_DAYS
    )

    # Fetch all projects
    projects = await self.api.get_projects()

    result = []
    for project in projects:
        # Get active tasks (existing behavior)
        project_data = await self.api.get_project_with_tasks(project.id)

        # Get completed tasks (new behavior)
        completed_tasks = await self.api.get_completed_tasks(
            project.id,
            days=completed_days
        )

        # Store completed tasks count for entity attributes
        project_with_tasks = project_data
        project_with_tasks.completed_tasks = completed_tasks
        project_with_tasks.completed_tasks_count = len(completed_tasks)

        result.append(project_with_tasks)

    return result
```

Commit: `git add custom_components/ticktick/coordinator.py && git commit -m "feat: fetch completed tasks in coordinator"`

### Step 3: Verify coordinator update

Check: `python -c "from custom_components.ticktick.coordinator import TickTickCoordinator; print('OK')"`
Expected: No import errors

---

## Task 5: Modify Todo Platform to Create Dual Entities

**Files:**
- Modify: `custom_components/ticktick/todo.py`

**Why Fifth:** Core entity changes - create two entities per project (active + completed).

### Step 1: Update entity setup to create dual entities

Modify `async_setup_entry` function:

```python
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the TickTick todo platform config entry."""
    coordinator: TickTickCoordinator = hass.data[DOMAIN][entry.entry_id]
    projects = await coordinator.async_get_projects()

    entities = []
    for project in projects:
        # Active tasks entity (existing behavior)
        entities.append(
            TickTickTodoListEntity(
                coordinator,
                entry.entry_id,
                project.id,
                project.name,
                task_type="active"
            )
        )

        # Completed tasks entity (new behavior)
        entities.append(
            TickTickTodoListEntity(
                coordinator,
                entry.entry_id,
                project.id,
                project.name,
                task_type="completed"
            )
        )

    async_add_entities(entities)
```

Commit: `git add custom_components/ticktick/todo.py && git commit -m "feat: create dual entities (active and completed)"`

### Step 2: Add task_type parameter to entity class

Update `TickTickTodoListEntity.__init__`:

```python
def __init__(
    self,
    coordinator: TickTickCoordinator,
    config_entry_id: str,
    project_id: str,
    project_name: str,
    task_type: str = "active"  # "active" or "completed"
) -> None:
    """Initialize TickTickTodoListEntity."""
    super().__init__(coordinator=coordinator)
    self._project_id = project_id
    self._task_type = task_type

    # Set unique_id and name based on task type
    if task_type == "completed":
        self._attr_unique_id = f"{config_entry_id}-{project_id}-completed"
        self._attr_name = f"{project_name} Completed"
    else:
        self._attr_unique_id = f"{config_entry_id}-{project_id}"
        self._attr_name = project_name

    self._attr_todo_items = []
```

Commit: `git add custom_components/ticktick/todo.py && git commit -m "feat: add task_type parameter to entity initialization"`

### Step 3: Update _handle_coordinator_update to filter by task type

Modify the data handler to show appropriate tasks:

```python
@callback
def _handle_coordinator_update(self) -> None:
    """Handle updated data from the coordinator."""
    projects_with_tasks = self.coordinator.data

    if projects_with_tasks is None:
        self._attr_todo_items = None
    else:
        tasks_to_add = []
        for project_with_tasks in projects_with_tasks:
            if project_with_tasks.project.id != self._project_id:
                continue

            # Get tasks based on entity type
            if self._task_type == "completed":
                # Use completed tasks from coordinator
                tasks = project_with_tasks.completed_tasks or []
            else:
                # Use active tasks (existing behavior)
                tasks = project_with_tasks.tasks or []

            for task in tasks:
                # For completed entity, add checkmark to title
                summary = task.title
                if self._task_type == "completed":
                    summary = f"{task.title} ✓"

                tasks_to_add.insert(0,
                    TodoItem(
                        uid=task.id,
                        summary=summary,
                        status=TodoItemStatus.COMPLETED
                        if task.status in (
                            TaskStatus.COMPLETED,
                            TaskStatus.COMPLETED_1,
                            TaskStatus.COMPLETED_2
                        )
                        else TodoItemStatus.NEEDS_ACTION,
                        due=task.dueDate,
                        description=task.content or None,
                    )
                )

        if tasks_to_add:
            self._attr_todo_items = tasks_to_add

    super()._handle_coordinator_update()
```

Commit: `git add custom_components/ticktick/todo.py && git commit -m "feat: filter tasks by entity type in update handler"`

### Step 4: Update async_update_todo_item to handle reopening

Modify the status change handler to support reopening:

```python
async def async_update_todo_item(self, item: TodoItem) -> None:
    """Update a To-do item."""

    async def process_status_change() -> bool:
        if item.status is not None:
            # Only update status if changed
            for existing_item in self._attr_todo_items or ():
                if existing_item.uid != item.uid:
                    continue

                if item.status != existing_item.status:
                    # COMPLETING: Active entity, marking as complete
                    if item.status == TodoItemStatus.COMPLETED:
                        await self.coordinator.api.complete_task(
                            projectId=self._project_id,
                            taskId=item.uid
                        )
                        return True

                    # REOPENING: Completed entity, marking as needs action
                    elif item.status == TodoItemStatus.NEEDS_ACTION:
                        if self._task_type == "completed":
                            # Reopen the task
                            await self.coordinator.api.reopen_task(
                                projectId=self._project_id,
                                taskId=item.uid
                            )
                            return True
        return False

    projects_with_tasks = self.coordinator.data

    # Find the task from appropriate list based on entity type
    api_task = None
    for project_with_tasks in projects_with_tasks:
        if project_with_tasks.project.id != self._project_id:
            continue

        # Search in active or completed tasks based on entity type
        tasks = (
            project_with_tasks.tasks
            if self._task_type == "active"
            else project_with_tasks.completed_tasks or []
        )

        if tasks:
            api_task = next((t for t in tasks if t.id == item.uid), None)
            if api_task:
                break

    if await process_status_change():
        await self.coordinator.async_refresh()
        return

    # Handle non-status updates (title, description, due date)
    mapped_task, is_modified = _map_task(item, self._project_id, api_task)

    if is_modified:
        await self.coordinator.api.update_task(mapped_task)

    await self.coordinator.async_refresh()
```

Commit: `git add custom_components/ticktick/todo.py && git commit -m "feat: support reopening tasks from completed entity"`

### Step 5: Update entity attributes

Add extra state attributes for completed count:

```python
@property
def extra_state_attributes(self):
    """Return entity specific state attributes."""
    attrs = {}

    if self._task_type == "completed" and self.coordinator.data:
        for project_with_tasks in self.coordinator.data:
            if project_with_tasks.project.id == self._project_id:
                attrs["completed_tasks_count"] = (
                    project_with_tasks.completed_tasks_count or 0
                )
                break

    return attrs
```

Commit: `git add custom_components/ticktick/todo.py && git commit -m "feat: add completed count attribute to entity"`

---

## Task 6: Add Integration Tests

**Files:**
- Create: `tests/test_todo_entity.py`

**Why Sixth:** Verify dual entity creation and task movement works correctly.

### Step 1: Write test for dual entity creation

```python
import pytest
from custom_components.ticktick.todo import TickTickTodoListEntity

@pytest.mark.asyncio
async def test_dual_entities_created_per_project():
    """Test that both active and completed entities are created for each project."""
    # Setup mock coordinator with project data
    # ...

    # Call async_setup_entry
    await todo.async_setup_entry(hass, config_entry, async_add_entities)

    # Assert two entities were created
    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2

    # Assert entity types
    active_entity = next(e for e in entities if e._task_type == "active")
    completed_entity = next(e for e in entities if e._task_type == "completed")

    assert "Completed" in completed_entity.name
    assert "Completed" not in active_entity.name
```

Commit: `git add tests/test_todo_entity.py && git commit -m "test: add dual entity creation test"`

### Step 2: Write test for task status changes

```python
@pytest.mark.asyncio
async def test_task_moves_between_entities():
    """Test that completing a task moves it to completed entity."""
    # Setup entities
    # ...

    # Complete task in active entity
    active_entity.async_update_todo_item(TodoItem(
        uid="task_1",
        summary="Test task",
        status=TodoItemStatus.COMPLETED
    ))

    # Assert task appears in completed entity
    completed_items = completed_entity.todo_items
    assert any(t.uid == "task_1" for t in completed_items)

    # Reopen task from completed entity
    completed_entity.async_update_todo_item(TodoItem(
        uid="task_1",
        summary="Test task ✓",
        status=TodoItemStatus.NEEDS_ACTION
    ))

    # Assert task appears back in active entity
    active_items = active_entity.todo_items
    assert any(t.uid == "task_1" for t in active_items)
```

Commit: `git add tests/test_todo_entity.py && git commit -m "test: add task movement test between entities"`

### Step 3: Run all tests

Run: `pytest tests/ -v`
Expected: All tests PASS

---

## Task 7: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/completed-tasks.md`

**Why Seventh:** Document new feature for users.

### Step 1: Update README with completed tasks feature

Add section to `README.md`:

```markdown
## Recently Completed Tasks

This integration creates companion Todo entities for viewing and managing recently completed tasks.

### Entities

For each TickTick project, two Todo entities are created:
- `todo.{project_name}` - Active/incomplete tasks
- `todo.{project_name}_completed` - Tasks completed in the last 7 days (configurable)

### Usage

**Complete a task:**
Check the checkbox in the active entity. The task will move to the completed entity.

**Reopen a task:**
Uncheck the checkbox in the completed entity. The task will move back to the active entity.

**Configure history period:**
Navigate to **Settings → Devices & Services → TickTick → Configure** and adjust "Completed tasks history (days)".

### Example Automation

```yaml
automation:
  - alias: "Daily completed tasks summary"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.notify
        data:
          message: "You completed {{ states('todo.my_tasks_completed') }} tasks today!"
```
```

Commit: `git add README.md && git commit -m "docs: add completed tasks feature documentation"`

### Step 2: Create detailed documentation

Create `docs/completed-tasks.md` with detailed usage examples and troubleshooting.

Commit: `git add docs/completed-tasks.md && git commit -m "docs: add detailed completed tasks guide"`

---

## Task 8: Manual Testing Checklist

**Files:** None (manual verification)

**Why Eighth:** Validate integration works end-to-end in real Home Assistant instance.

### Step 1: Install integration

- Install HACS or copy integration to HA
- Restart Home Assistant
- Configure TickTick integration with completed_days=7

### Step 2: Verify entity creation

Check Developer Tools → States:
- ✅ `todo.my_project` exists
- ✅ `todo.my_project_completed` exists
- ✅ Both entities show task counts

### Step 3: Test task completion

- Go to Lovelace, add Todo card for active entity
- Check a task checkbox
- ✅ Task disappears from active entity
- ✅ Task appears in completed entity with ✓ symbol

### Step 4: Test task reopening

- Go to completed entity Todo card
- Uncheck a task checkbox
- ✅ Task disappears from completed entity
- ✅ Task appears in active entity without ✓

### Step 5: Test configuration

- Change completed_days from 7 to 30
- Reload integration
- ✅ Completed entity shows older completed tasks

### Step 6: Test attributes

- Check entity state attributes
- ✅ `completed_tasks_count` attribute present
- ✅ Count matches actual completed tasks

---

## Task 9: Update AGENTS.md

**Files:**
- Modify: `custom_components/ticktick/AGENTS.md`
- Modify: `custom_components/ticktick/AGENTS.md`

**Why Ninth:** Update AI documentation with new feature context.

### Step 1: Update main AGENTS.md

Add to architecture section:

```markdown
### Completed Tasks Feature

The integration creates companion Todo entities for completed tasks:
- Active entity: Shows tasks with status=0 (NEEDS_ACTION)
- Completed entity: Shows tasks with status=1/2 (COMPLETED) within configured days

Users can:
- Complete tasks in active entity (moves to completed)
- Reopen tasks in completed entity (moves to active)
- Configure lookback period via integration options

Key methods:
- `get_completed_tasks(projectId, days)` - Fetch completed tasks by date
- `reopen_task(projectId, taskId)` - Set task status to NORMAL (0)
```

Commit: `git add custom_components/ticktick/AGENTS.md && git commit -m "docs: update AGENTS.md with completed tasks feature"`

---

## Testing Strategy

### Unit Tests
- Test date filtering in `get_completed_tasks`
- Test status changes (complete/reopen)
- Test entity creation and filtering

### Integration Tests
- Test task movement between entities
- Test coordinator data fetching
- Test configuration options

### Manual Tests
- Real Home Assistant instance
- Actual TickTick API calls
- UI interaction (Lovelace cards)

### Rollback Plan
If issues arise:
1. Revert to single-entity behavior (remove `task_type` parameter)
2. Comment out completed entity creation in `async_setup_entry`
3. Keep API methods (harmless if unused)

---

## Success Criteria

✅ Companion Todo entities created for each project
✅ Tasks move between entities on status change
✅ Completed entity shows tasks within configured days
✅ Reopening tasks works via checkbox uncheck
✅ Configuration option for days works
✅ All tests pass
✅ No regression in existing functionality
✅ Documentation updated

---

**Implementation estimated time:** 2-3 hours
**Lines of code:** ~400 (including tests)
**Files modified:** 6
**Files created:** 3
