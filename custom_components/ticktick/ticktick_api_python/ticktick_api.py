"""TickTick API Client."""

from aiohttp import ClientResponse, ClientSession
from custom_components.ticktick.const import (
    COMPLETE_TASK,
    CREATE_TASK,
    DELETE_TASK,
    GET_PROJECTS,
    GET_PROJECTS_WITH_TASKS,
    GET_TASK,
    UPDATE_TASK,
)

from .models.check_list_item import TaskStatus
from .models.project import Kind, Project
from .models.project_with_tasks import ProjectWithTasks
from .models.task import Task


class TickTickAPIClient:
    """TickTick API Client."""

    def __init__(self, access_token: str, session: ClientSession) -> None:
        """Initialize the TickTick API client."""
        self._headers = {"Authorization": f"Bearer {access_token}"}
        self._session = session

    # === Task Scope ===
    async def get_task(
        self, projectId: str, taskId: str, returnAsJson: bool = False
    ) -> Task:
        """Return a task."""
        response = await self._get(GET_TASK.format(projectId=projectId, taskId=taskId))
        if returnAsJson:
            return response

        return Task.from_dict(response)

    async def create_task(self, task: Task, returnAsJson: bool = False) -> Task:
        """Create a task."""
        json = task.toJSON()
        response = await self._post(CREATE_TASK, json)
        if returnAsJson:
            return response

        return Task.from_dict(response)

    async def update_task(self, task: Task, returnAsJson: bool = False) -> Task:
        """Update a task."""
        json = task.toJSON()
        response = await self._post(UPDATE_TASK.format(taskId=task.id), json)
        if returnAsJson:
            return response

        return Task.from_dict(response)

    async def complete_task(self, projectId: str, taskId: str) -> str:
        """Complete a task."""
        return await self._post(
            COMPLETE_TASK.format(projectId=projectId, taskId=taskId)
        )

    async def delete_task(self, projectId: str, taskId: str) -> str:
        """Delete a task."""
        return await self._delete(
            DELETE_TASK.format(projectId=projectId, taskId=taskId)
        )

    # === Project Scope ===
    async def get_projects(self, returnAsJson: bool = False) -> list[Project]:
        """Return a dict of all projects basic informations."""
        response = await self._get(GET_PROJECTS)
        if returnAsJson:
            return response

        mappedResponse = [Project.from_dict(project) for project in response]
        filtered_projects = list(
            filter(
                lambda project: project.kind == Kind.TASK and not project.closed,
                mappedResponse,
            )  # Filtering out for now Notes
        )
        return filtered_projects

    async def get_project_with_tasks(self, projectId: str) -> list[ProjectWithTasks]:
        """Return a dict of tasks for project."""
        response = await self._get(GET_PROJECTS_WITH_TASKS.format(projectId=projectId))
        return ProjectWithTasks.from_dict(response)

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

        from .models.task import TaskPriority
        from .models.check_list_item import CheckListItem

        # Get all tasks for the project (includes completed ones)
        response = await self._get(
            GET_PROJECTS_WITH_TASKS.format(projectId=projectId)
        )

        if returnAsJson:
            return response

        # Parse response manually to include completed tasks
        # Note: We can't use ProjectWithTasks.from_dict() because it filters out completed tasks
        project = Project.from_dict(response["project"])

        # Parse all tasks including completed ones (status 1, 2, or COMPLETED)
        tasks_data = response.get("tasks", [])
        if not tasks_data:
            return []

        # Parse all tasks (including completed ones)
        all_tasks = []
        for task_data in tasks_data:
            # Parse task with its items (subtasks)
            items = [
                CheckListItem.from_dict(item)
                for item in task_data.get("items", [])
            ] if task_data.get("items") else []

            task = Task(
                projectId=task_data["projectId"],
                title=task_data.get("title") if task_data.get("title") else "Unnamed Task",
                id=task_data.get("id"),
                parentId=task_data.get("parentId"),
                desc=task_data.get("desc"),
                content=task_data.get("content"),
                priority=TaskPriority(task_data.get("priority", TaskPriority.NONE.value)),
                sortOrder=task_data.get("sortOrder"),
                isAllDay=task_data.get("isAllDay"),
                startDate=task_data.get("startDate"),
                dueDate=task_data.get("dueDate"),
                completedTime=task_data.get("completedTime"),
                timeZone=task_data.get("timeZone"),
                reminders=task_data.get("reminders", []),
                repeatFlag=task_data.get("repeatFlag"),
                status=TaskStatus(task_data.get("status", TaskStatus.NORMAL.value)),
                items=items,
            )
            all_tasks.append(task)

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter for completed tasks within date range
        completed_tasks = []
        for task in all_tasks:
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

    async def _get(self, url: str) -> ClientResponse:
        response = await self._session.get(f"https://{url}", headers=self._headers)
        return await self._get_response(response)

    async def _post(self, url: str, json_body: str | None = None) -> ClientResponse:
        self._headers["Content-Type"] = "application/json"
        response = await self._session.post(
            f"https://{url}",
            headers=self._headers,
            data=json_body if json_body else None,
        )
        return await self._get_response(response)

    async def _delete(self, url: str) -> ClientResponse:
        response = await self._session.delete(f"https://{url}", headers=self._headers)
        return await self._get_response(response)

    async def _get_response(
        self, response: ClientResponse
    ) -> tuple[ClientResponse, bool]:
        if response.ok:
            try:
                json_data = await response.json()
            except Exception:  # noqa: BLE001
                return {"status": "Success"}

            if json_data is None:  # Handle case when the response body is null
                return {"status": "Success"}
            return json_data
        raise Exception(  # noqa: TRY002
            f"Unsucessful response from TickTick, status code: {response.status}, content: {await response.json()}"
        )
