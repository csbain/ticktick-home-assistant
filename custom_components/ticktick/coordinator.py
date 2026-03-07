"""DataUpdateCoordinator for the TickTick component."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from pyticktick.models.v2 import ProjectV2, TaskV2

from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_COMPLETED_TASKS_DAYS, DEFAULT_COMPLETED_TASKS_DAYS
from .exceptions import TickTickAPIError, TickTickAuthError
from .pyticktick_client import AsyncPyTickTickClient

if TYPE_CHECKING:
    from . import TickTickConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class ProjectWithTasks:
    """Container for a project with its tasks."""

    project: ProjectV2
    tasks: list[TaskV2] = field(default_factory=list)
    completed_tasks: list[TaskV2] = field(default_factory=list)
    completed_tasks_count: int = 0


class TickTickCoordinator(DataUpdateCoordinator[dict[str, ProjectWithTasks]]):
    """Coordinator for updating task data from TickTick.

    Uses pyticktick V2 API to fetch all active data via batch endpoint
    and completed tasks via dedicated closed tasks endpoint.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        entry: TickTickConfigEntry,
        update_interval: timedelta,
        client: AsyncPyTickTickClient,
    ) -> None:
        """Initialize the TickTick coordinator.

        Args:
            hass: Home Assistant instance.
            logger: Logger instance.
            entry: Config entry.
            update_interval: How often to poll for updates.
            client: Async pyticktick client wrapper.
        """
        super().__init__(
            hass,
            logger,
            config_entry=entry,
            name="TickTick",
            update_interval=update_interval,
        )
        self._client = client
        self._inbox_id: str | None = None

    async def _async_update_data(self) -> dict[str, ProjectWithTasks]:
        """Fetch project data including both active and completed tasks.

        Returns:
            Dictionary mapping project ID to ProjectWithTasks.

        Raises:
            UpdateFailed: If data fetch fails.
            ConfigEntryAuthFailed: If authentication fails (triggers reauth).
        """
        try:
            # Fetch all active data in single batch call
            batch = await self._client.async_get_batch()

            # Build project lookup
            projects_by_id: dict[str, ProjectWithTasks] = {}
            for project in batch.project_profiles:
                projects_by_id[project.id] = ProjectWithTasks(project=project)
                # Track inbox ID for default project
                if project.name == "Inbox" and self._inbox_id is None:
                    self._inbox_id = project.id

            # Distribute tasks to their projects
            for task in batch.sync_task_bean.update:
                if task.project_id in projects_by_id:
                    projects_by_id[task.project_id].tasks.append(task)

            # Get configured days for completed tasks
            completed_days = self.config_entry.options.get(
                CONF_COMPLETED_TASKS_DAYS, DEFAULT_COMPLETED_TASKS_DAYS
            )

            # Fetch completed tasks for each project
            await self._fetch_completed_tasks(projects_by_id, completed_days)

            return projects_by_id

        except TickTickAuthError as err:
            # Triggers HA reauth flow automatically
            raise ConfigEntryAuthFailed(
                f"Authentication expired: {err}"
            ) from err
        except TickTickAPIError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Request timed out") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _fetch_completed_tasks(
        self,
        projects_by_id: dict[str, ProjectWithTasks],
        days: int,
    ) -> None:
        """Fetch completed tasks for all projects.

        Args:
            projects_by_id: Project lookup to populate with completed tasks.
            days: Number of days of history to fetch.
        """
        try:
            # Fetch all completed tasks
            closed_tasks = await self._client.async_get_closed_tasks(status="Completed")

            # Distribute completed tasks to their projects
            for task in closed_tasks:
                if task.project_id in projects_by_id:
                    projects_by_id[task.project_id].completed_tasks.append(task)
                    projects_by_id[task.project_id].completed_tasks_count += 1

        except (TickTickAPIError, asyncio.TimeoutError) as err:
            # Log warning but don't fail - completed tasks are optional
            _LOGGER.warning("Failed to fetch completed tasks: %s", err)

    @property
    def inbox_id(self) -> str | None:
        """Return the Inbox project ID if found."""
        return self._inbox_id

    async def async_get_projects(self) -> list[ProjectV2]:
        """Return all TickTick projects from current data."""
        if self.data is None:
            return []
        return [pwt.project for pwt in self.data.values()]

    async def async_get_project_with_tasks(
        self, project_id: str
    ) -> ProjectWithTasks | None:
        """Return a specific project with its tasks."""
        if self.data is None:
            return None
        return self.data.get(project_id)
