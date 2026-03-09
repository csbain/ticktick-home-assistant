"""Async wrapper for the vendored pyticktick v2 library."""

from __future__ import annotations

import asyncio
import warnings
from typing import TYPE_CHECKING

from pydantic import SecretStr

from .pyticktick_v2 import Client
from .pyticktick_v2.models.v2 import (
    BatchRespV2,
    GetBatchV2,
    GetClosedV2,
    PostBatchTaskV2,
)

from .exceptions import TickTickAPIError, TickTickAuthError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Suppress pyticktick v1 warnings since we only use v2 API
warnings.filterwarnings(
    "ignore",
    message="Cannot signon to v1*",
    category=UserWarning,
)


class AsyncPyTickTickClient:
    """Async wrapper for sync pyticktick library.

    This class wraps the synchronous pyticktick Client to work with
    Home Assistant's async event loop using async_add_executor_job.

    Thread safety is provided via asyncio.Lock for client initialization.
    All API calls include explicit timeouts to prevent thread pool exhaustion.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
    ) -> None:
        """Initialize the async client wrapper.

        Args:
            hass: Home Assistant instance.
            username: TickTick username/email.
            password: TickTick password.

        Note:
            Credentials are stored for on-demand client creation.
            The password is NOT stored in the pyticktick Client instance.
        """
        self._hass = hass
        self._username = username
        self._password = password
        self._client: Client | None = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> Client:
        """Ensure client is initialized and authenticated.

        Thread-safe initialization using asyncio.Lock.
        Client is created on first use and reused for subsequent calls.

        Returns:
            Authenticated pyticktick Client instance.

        Raises:
            TickTickAuthError: If authentication fails.
        """
        async with self._lock:
            if self._client is None:
                self._client = await self._hass.async_add_executor_job(
                    self._create_client
                )
        return self._client

    def _create_client(self) -> Client:
        """Create and authenticate the sync client.

        Called via executor to avoid blocking the event loop.

        Returns:
            Authenticated pyticktick Client instance.

        Note:
            pyticktick handles token caching internally.
            If 2FA is required, authentication will fail here
            and user will need to reconfigure with TOTP code.
        """
        return Client(
            v2_username=self._username,
            v2_password=SecretStr(self._password),
            override_forbid_extra=True,
        )

    async def async_get_batch(self) -> GetBatchV2:
        """Fetch all data (projects, tasks, tags) in single call.

        This is the primary method for coordinator refresh.

        Returns:
            GetBatchV2 containing all active projects and tasks.

        Raises:
            TickTickAuthError: If authentication fails.
            TickTickAPIError: If the API returns an error.
        """
        try:
            client = await self._ensure_client()
            return await asyncio.wait_for(
                self._hass.async_add_executor_job(client.get_batch_v2),
                timeout=30,
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "login" in error_msg or "username" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e
        except asyncio.TimeoutError as e:
            raise TickTickAPIError(0, "Request timed out") from e
        except Exception as e:
            # Catch any other exceptions (pydantic errors, network errors, etc.)
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "username" in error_msg or "signon" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e

    async def async_get_closed_tasks(
        self,
        status: str = "Completed",
    ) -> list:
        """Get completed or abandoned tasks.

        Args:
            status: "Completed" or "Abandoned"

        Returns:
            List of closed TaskV2 objects.

        Raises:
            TickTickAuthError: If authentication fails.
            TickTickAPIError: If the API returns an error.
        """
        try:
            client = await self._ensure_client()
            return await asyncio.wait_for(
                self._hass.async_add_executor_job(
                    lambda: client.get_project_all_closed_v2(
                        GetClosedV2(status=status)
                    )
                ),
                timeout=30,
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "login" in error_msg or "username" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e
        except asyncio.TimeoutError as e:
            raise TickTickAPIError(0, "Request timed out") from e

    async def async_create_task(self, task_data: dict) -> BatchRespV2:
        """Create a new task using batch API.

        Args:
            task_data: Task creation data matching CreateTaskV2 schema.

        Returns:
            BatchRespV2 with created task details.

        Raises:
            TickTickAuthError: If authentication fails.
            TickTickAPIError: If the API returns an error.
        """
        try:
            client = await self._ensure_client()
            return await asyncio.wait_for(
                self._hass.async_add_executor_job(
                    lambda: client.post_task_v2(
                        PostBatchTaskV2(add=[task_data])
                    )
                ),
                timeout=30,
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "login" in error_msg or "username" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e
        except asyncio.TimeoutError as e:
            raise TickTickAPIError(0, "Request timed out") from e

    async def async_update_task(self, task_data: dict) -> BatchRespV2:
        """Update an existing task using batch API.

        Args:
            task_data: Task update data matching UpdateTaskV2 schema.
                Must include task 'id' field.

        Returns:
            BatchRespV2 with updated task details.

        Raises:
            TickTickAuthError: If authentication fails.
            TickTickAPIError: If the API returns an error.
        """
        try:
            client = await self._ensure_client()
            return await asyncio.wait_for(
                self._hass.async_add_executor_job(
                    lambda: client.post_task_v2(
                        PostBatchTaskV2(update=[task_data])
                    )
                ),
                timeout=30,
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "login" in error_msg or "username" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e
        except asyncio.TimeoutError as e:
            raise TickTickAPIError(0, "Request timed out") from e

    async def async_delete_task(self, task_id: str, project_id: str) -> BatchRespV2:
        """Delete a task using batch API.

        Args:
            task_id: ID of the task to delete.
            project_id: ID of the project containing the task (required by TickTick API).

        Returns:
            BatchRespV2 confirming deletion.

        Raises:
            TickTickAuthError: If authentication fails.
            TickTickAPIError: If the API returns an error.
        """
        try:
            client = await self._ensure_client()
            return await asyncio.wait_for(
                self._hass.async_add_executor_job(
                    lambda: client.post_task_v2(
                        PostBatchTaskV2(delete=[{"task_id": task_id, "project_id": project_id}])
                    )
                ),
                timeout=30,
            )
        except ValueError as e:
            error_msg = str(e).lower()
            if "auth" in error_msg or "password" in error_msg or "login" in error_msg or "username" in error_msg:
                raise TickTickAuthError(str(e)) from e
            raise TickTickAPIError(0, str(e)) from e
        except asyncio.TimeoutError as e:
            raise TickTickAPIError(0, "Request timed out") from e

    async def async_close(self) -> None:
        """Close the underlying client connection.

        Called during integration unload to clean up resources.
        """
        if self._client:
            # pyticktick uses httpx which handles cleanup automatically
            # but we clear the reference to allow garbage collection
            self._client = None
