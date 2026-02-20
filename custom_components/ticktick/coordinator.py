"""DataUpdateCoordinator for the TickTick component."""

import asyncio
from datetime import timedelta
import logging

from custom_components.ticktick.const import (
    CONF_COMPLETED_TASKS_DAYS,
    DEFAULT_COMPLETED_TASKS_DAYS,
)
from custom_components.ticktick.ticktick_api_python.models.project import Project
from custom_components.ticktick.ticktick_api_python.models.project_with_tasks import (
    ProjectWithTasks,
)
from custom_components.ticktick.ticktick_api_python.ticktick_api import (
    TickTickAPIClient,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


class TickTickCoordinator(DataUpdateCoordinator[list[ProjectWithTasks]]):
    """Coordinator for updating task data from TickTick."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        entry: ConfigEntry | None,
        update_interval: timedelta,
        api: TickTickAPIClient,
        access_token: str,
    ) -> None:
        """Initialize the TickTick coordinator."""
        super().__init__(
            hass,
            logger,
            config_entry=entry,
            name="TickTick",
            update_interval=update_interval,
        )
        self.api = api
        self._projects: list[Project] | None = None
        self.access_token = access_token

    async def _async_update_data(self) -> list[ProjectWithTasks]:
        """Fetch project data including both active and completed tasks."""
        try:
            if self._projects is None:
                await self.async_get_projects()

            # Get configured days for completed tasks
            completed_days = self.config_entry.options.get(
                CONF_COMPLETED_TASKS_DAYS,
                DEFAULT_COMPLETED_TASKS_DAYS
            )

            # Fetch all projects with active tasks
            fetch_projects_with_tasks = [
                self.api.get_project_with_tasks(project.id)
                for project in self._projects
            ]

            projects_with_tasks = await asyncio.gather(*fetch_projects_with_tasks)

            # Fetch completed tasks for each project
            result = []
            for project_data in projects_with_tasks:
                # Get completed tasks for the project
                completed_tasks = await self.api.get_completed_tasks(
                    project_data.project.id,
                    days=completed_days
                )

                # Store completed tasks count for entity attributes
                project_data.completed_tasks = completed_tasks
                project_data.completed_tasks_count = len(completed_tasks)

                result.append(project_data)

            return result
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_get_projects(self) -> list[Project]:
        """Return TickTick projects fetched at most once."""
        if self._projects is None:
            self._projects = await self.api.get_projects()
        return self._projects
