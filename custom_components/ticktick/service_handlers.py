"""Service Handlers for TickTick Integration."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from .pyticktick_v2.models.v2 import (
    CreateTaskV2,
    DeleteTaskV2,
    PostBatchTaskV2,
    UpdateTaskV2,
)

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util

from .pyticktick_client import AsyncPyTickTickClient

_LOGGER = logging.getLogger(__name__)


async def handle_get_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'get_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the get_task service call."""
        project_id = call.data.get("project_id")
        task_id = call.data.get("task_id")

        if not project_id or not task_id:
            return {"error": "Both project_id and task_id are required"}

        try:
            # Get batch data and find the task
            batch = await client.async_get_batch()
            for task in batch.sync_task_bean.update:
                if task.id == task_id and task.project_id == project_id:
                    return {
                        "data": {
                            "id": str(task.id),
                            "title": task.title,
                            "content": task.content,
                            "description": task.desc,
                            "project_id": task.project_id,
                            "status": task.status,
                            "priority": task.priority,
                            "due_date": task.due_date,
                            "items": [
                                {
                                    "id": str(item.id),
                                    "title": item.title,
                                    "status": item.status,
                                }
                                for item in (task.items or [])
                            ],
                        }
                    }
            return {"error": f"Task {task_id} not found in project {project_id}"}
        except Exception as e:
            _LOGGER.error("Error getting task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_create_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'create_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the create_task service call."""
        title = call.data.get("title")
        project_id = call.data.get("project_id")
        content = call.data.get("content")
        due_date = call.data.get("due_date")
        priority = call.data.get("priority", 0)

        if not title:
            return {"error": "title is required"}

        try:
            # Build task creation data
            task_data: dict[str, Any] = {
                "title": title,
            }

            if project_id:
                task_data["project_id"] = project_id

            if content:
                task_data["content"] = content

            if due_date:
                task_data["due_date"] = _sanitize_date(due_date, call.data.get("time_zone"))

            if priority is not None:
                task_data["priority"] = priority

            # Create task using batch API
            result = await client.async_create_task(task_data)

            if result.add and len(result.add) > 0:
                created = result.add[0]
                return {
                    "data": {
                        "id": str(created.id),
                        "title": created.title,
                        "project_id": created.project_id,
                    }
                }
            return {"error": "Task creation returned no result"}

        except Exception as e:
            _LOGGER.error("Error creating task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_complete_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'complete_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the complete_task service call."""
        task_id = call.data.get("task_id")

        if not task_id:
            return {"error": "task_id is required"}

        try:
            # Update task status to completed (2)
            update_data = {
                "id": task_id,
                "status": 2,  # COMPLETED status for Task
            }

            result = await client.async_update_task(update_data)

            if result.update and len(result.update) > 0:
                return {"data": {"id": str(result.update[0].id), "status": "completed"}}
            return {"error": "Task update returned no result"}

        except Exception as e:
            _LOGGER.error("Error completing task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_delete_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'delete_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the delete_task service call."""
        task_id = call.data.get("task_id")

        if not task_id:
            return {"error": "task_id is required"}

        try:
            result = await client.async_delete_task(task_id)
            return {"data": {"id": task_id, "status": "deleted"}}
        except Exception as e:
            _LOGGER.error("Error deleting task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_update_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'update_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the update_task service call."""
        task_id = call.data.get("task_id")

        if not task_id:
            return {"error": "task_id is required"}

        try:
            update_data: dict[str, Any] = {"id": task_id}

            if "title" in call.data:
                update_data["title"] = call.data["title"]

            if "content" in call.data:
                update_data["content"] = call.data["content"]

            if "desc" in call.data:
                update_data["desc"] = call.data["desc"]

            if "due_date" in call.data:
                update_data["due_date"] = _sanitize_date(
                    call.data["due_date"], call.data.get("time_zone")
                )

            if "priority" in call.data:
                priority = call.data["priority"]
                if isinstance(priority, str):
                    priority_map = {"none": 0, "low": 1, "medium": 2, "high": 3}
                    priority = priority_map.get(priority.lower(), 0)
                update_data["priority"] = priority

            result = await client.async_update_task(update_data)

            if result.update and len(result.update) > 0:
                updated = result.update[0]
                return {
                    "data": {
                        "id": str(updated.id),
                        "title": updated.title,
                        "status": updated.status,
                    }
                }
            return {"error": "Task update returned no result"}

        except Exception as e:
            _LOGGER.error("Error updating task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_copy_task(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'copy_task' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the copy_task service call."""
        task_id = call.data.get("task_id")
        target_project_id = call.data.get("target_project_id")

        if not task_id or not target_project_id:
            return {"error": "Both task_id and target_project_id are required"}

        try:
            # Get batch data and find the source task
            batch = await client.async_get_batch()
            source_task = None
            for task in batch.sync_task_bean.update:
                if task.id == task_id:
                    source_task = task
                    break

            if not source_task:
                return {"error": f"Task {task_id} not found"}

            # Create new task in target project
            task_data: dict[str, Any] = {
                "title": source_task.title,
                "project_id": target_project_id,
            }

            if source_task.content:
                task_data["content"] = source_task.content

            if source_task.desc:
                task_data["desc"] = source_task.desc

            if source_task.priority is not None:
                task_data["priority"] = source_task.priority

            if source_task.due_date:
                task_data["due_date"] = source_task.due_date

            result = await client.async_create_task(task_data)

            if result.add and len(result.add) > 0:
                return {
                    "data": {
                        "new_task_id": str(result.add[0].id),
                        "title": result.add[0].title,
                    }
                }
            return {"error": "Task copy returned no result"}

        except Exception as e:
            _LOGGER.error("Error copying task: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_get_projects(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler function for the 'get_projects' service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle the get_projects service call."""
        try:
            batch = await client.async_get_batch()
            projects = [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "color": p.color,
                    "group_id": p.group_id,
                    "view_mode": p.view_mode,
                }
                for p in batch.project_profiles
            ]
            return {"data": projects}
        except Exception as e:
            _LOGGER.error("Error getting projects: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_get_subtasks(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler for get_subtasks service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle get_subtasks service call."""
        task_id = call.data.get("task_id")

        if not task_id:
            return {"error": "task_id is required"}

        try:
            # Get batch data and find the task
            batch = await client.async_get_batch()
            for task in batch.sync_task_bean.update:
                if task.id == task_id:
                    items = task.items or []
                    total = len(items)
                    completed = sum(1 for item in items if item.status == 1)
                    progress = int((completed / total) * 100) if total > 0 else 0

                    return {
                        "data": {
                            "task_id": str(task.id),
                            "task_title": task.title,
                            "subtask_total": total,
                            "subtask_completed": completed,
                            "subtask_progress_percent": progress,
                            "subtasks": [
                                {
                                    "id": str(item.id),
                                    "title": item.title,
                                    "status": "completed" if item.status == 1 else "active",
                                    "sort_order": item.sort_order,
                                }
                                for item in items
                            ],
                        }
                    }
            return {"error": f"Task {task_id} not found"}
        except Exception as e:
            _LOGGER.error("Error in get_subtasks service: %s", str(e))
            return {"error": str(e)}

    return handler


async def handle_get_tasks_filtered(client: AsyncPyTickTickClient) -> Callable[[ServiceCall], dict[str, Any]]:
    """Return a handler for get_tasks_filtered service."""
    async def handler(call: ServiceCall) -> dict[str, Any]:
        """Handle get_tasks_filtered service call."""
        project_id = call.data.get("project_id")
        status = call.data.get("status", "active")
        include_subtask_progress = call.data.get("include_subtask_progress", False)

        try:
            batch = await client.async_get_batch()
            tasks = []

            for task in batch.sync_task_bean.update:
                # Filter by project if specified
                if project_id and task.project_id != project_id:
                    continue

                # Filter by status
                status_map = {"active": 0, "completed": 2, "abandoned": -1}
                target_status = status_map.get(status.lower(), 0)
                if task.status != target_status:
                    continue

                task_data = {
                    "id": str(task.id),
                    "title": task.title,
                    "project_id": task.project_id,
                    "priority": task.priority or 0,
                    "status": task.status,
                    "due_date": task.due_date,
                }

                # Include subtask progress if requested
                if include_subtask_progress and task.items:
                    total = len(task.items)
                    completed = sum(1 for item in task.items if item.status == 1)
                    task_data["subtask_total"] = total
                    task_data["subtask_completed"] = completed
                    task_data["subtask_progress_percent"] = int((completed / total) * 100) if total > 0 else 0

                tasks.append(task_data)

            return {
                "data": {
                    "filtered_tasks": tasks,
                    "count": len(tasks),
                }
            }
        except Exception as e:
            _LOGGER.error("Error in get_tasks_filtered service: %s", str(e))
            return {"error": str(e)}

    return handler


def _sanitize_date(date: str, time_zone: str | None) -> str:
    """Sanitize a date string to the format expected by TickTick API.

    TickTick expects format: YYYY-MM-DDThh:mm:ss+ZZZZ (no colon in timezone)
    """
    # Parse the input date
    if isinstance(date, str):
        # Handle various input formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                naive_dt = datetime.strptime(date, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse date: {date}")
    else:
        naive_dt = date

    # Apply timezone
    if time_zone:
        from zoneinfo import ZoneInfo
        zone_info = ZoneInfo(time_zone)
    else:
        zone_info = dt_util.get_default_time_zone()

    aware_dt = naive_dt.replace(tzinfo=zone_info)

    # Format without colon in timezone offset (TickTick requirement)
    return aware_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
