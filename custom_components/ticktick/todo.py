import asyncio
from typing import Any
from datetime import datetime

from custom_components.ticktick.coordinator import TickTickCoordinator
from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskStatus

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the TickTick todo platform config entry."""
    from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

    coordinator: TickTickCoordinator = hass.data[DOMAIN][entry.entry_id]
    projects = await coordinator.async_get_projects()
    entity_registry = async_get_entity_registry(hass)

    entities = []
    for project in projects:
        # Check if active entity already exists with a numeric suffix
        active_unique_id = f"{entry.entry_id}-{project.id}"
        active_entity_id = entity_registry.async_get_entity_id(
            "todo", DOMAIN, active_unique_id
        )

        # Extract suffix from existing entity ID if present
        suffix = ""
        if active_entity_id:
            # Entity ID format: todo.project_name or todo.project_name_2
            base_name = active_entity_id.replace("todo.", "")
            if "_" in base_name:
                parts = base_name.rsplit("_", 1)
                if parts[1].isdigit():
                    suffix = f"_{parts[1]}"

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

        # Completed tasks entity with matching suffix
        entities.append(
            TickTickTodoListEntity(
                coordinator,
                entry.entry_id,
                project.id,
                project.name,
                task_type="completed",
                suffix=suffix
            )
        )

    async_add_entities(entities)


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


def _format_date_for_comparison(date_value) -> str:
    """Format a date value for comparison, handling different types."""
    if date_value is None:
        return ""
    if isinstance(date_value, datetime):
        # Convert datetime to string in a consistent format
        return date_value.isoformat()
    if isinstance(date_value, str):
        return date_value.strip()
    # For any other type, convert to string
    return str(date_value).strip()


def _map_task(
    item: TodoItem, projectId: str, api_task: Task | None = None
) -> tuple[Task, bool]:
    """Convert a TodoItem to Task."""
    modified = False
    if api_task:
        if (item.summary or "").strip() != (api_task.title or "").strip():
            api_task.title = item.summary
            modified = True
        if (item.description or "").strip() != (api_task.content or "").strip():
            api_task.content = item.description
            modified = True
        
        # Handle due date comparison with proper type checking
        item_due_str = _format_date_for_comparison(item.due)
        api_due_str = _format_date_for_comparison(api_task.dueDate)
        
        if item_due_str != api_due_str:
            api_task.dueDate = item.due
            modified = True
            
        return api_task, modified
    return Task(
        projectId=projectId,
        title=item.summary,
        content=item.description,
        dueDate=item.due,
    ), modified


class TickTickTodoListEntity(CoordinatorEntity[TickTickCoordinator], TodoListEntity):
    """A TickTick TodoListEntity."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(
        self,
        coordinator: TickTickCoordinator,
        config_entry_id: str,
        project_id: str,
        project_name: str,
        task_type: str = "active",  # "active" or "completed"
        suffix: str = ""  # Numeric suffix from existing entity (e.g., "_2")
    ) -> None:
        """Initialize TickTickTodoListEntity."""
        super().__init__(coordinator=coordinator)
        self._project_id = project_id
        self._task_type = task_type

        # Set unique_id and name based on task type
        if task_type == "completed":
            self._attr_unique_id = f"{config_entry_id}-{project_id}-completed"
            self._attr_name = f"{project_name}{suffix} Completed"
        else:
            self._attr_unique_id = f"{config_entry_id}-{project_id}"
            self._attr_name = project_name

        self._attr_todo_items = []

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

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a To-do item."""
        if item.status != TodoItemStatus.NEEDS_ACTION:
            raise ValueError("Only active tasks may be created.")
        mapped_task, _ = _map_task(item, self._project_id)
        await self.coordinator.api.create_task(mapped_task)
        await self.coordinator.async_refresh()

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

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete a To-do item."""
        await asyncio.gather(
            *[
                self.coordinator.api.delete_task(projectId=self._project_id, taskId=uid)
                for uid in uids
            ]
        )
        await self.coordinator.async_refresh()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass update state from existing coordinator data."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        from custom_components.ticktick.ticktick_api_python.models.check_list_item import CheckListItem

        attrs = {}

        if self._task_type == "completed" and self.coordinator.data:
            for project_with_tasks in self.coordinator.data:
                if project_with_tasks.project.id == self._project_id:
                    attrs["completed_tasks_count"] = (
                        project_with_tasks.completed_tasks_count or 0
                    )
                    break

        # Add subtask progress for both active and completed entities
        if self.coordinator.data:
            for project_with_tasks in self.coordinator.data:
                if project_with_tasks.project.id != self._project_id:
                    continue

                # Build subtask_progress array (task-level data)
                subtask_progress = []
                project_subtask_total = 0
                project_subtask_completed = 0

                for task in project_with_tasks.tasks:
                    if task.items and len(task.items) > 0:
                        total, completed, progress = _calculate_subtask_progress(task.items)

                        subtask_progress.append({
                            "task_id": task.id,
                            "task_title": task.title,
                            "subtask_total": total,
                            "subtask_completed": completed,
                            "subtask_progress_percent": progress,
                            "subtasks": [
                                {
                                    "id": item.id,
                                    "title": item.title,
                                    "status": "completed" if item.status != TaskStatus.NORMAL else "active"
                                }
                                for item in task.items
                            ]
                        })

                        # Accumulate project-level stats
                        project_subtask_total += total
                        project_subtask_completed += completed

                # Add task-level subtask progress array if any tasks have subtasks
                if subtask_progress:
                    attrs["subtask_progress"] = subtask_progress

                # Add project-level aggregate stats if any subtasks exist
                if project_subtask_total > 0:
                    attrs["project_subtask_total"] = project_subtask_total
                    attrs["project_subtask_completed"] = project_subtask_completed
                    attrs["project_subtask_progress_percent"] = int(
                        (project_subtask_completed / project_subtask_total) * 100
                    )

                break

        return attrs
