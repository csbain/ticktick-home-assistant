"""Client for the vendored pyticktick v2 API.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).

This is a simplified version that only supports v2 API with username/password.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from .settings import Settings
from .pydantic import update_model_config
from ..models.v2 import (
    GetBatchV2,
    BatchRespV2,
    ClosedRespV2,
    GetClosedV2,
    PostBatchTaskV2,
    UserProfileV2,
    UserStatusV2,
    UserStatisticsV2,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

_logger = logging.getLogger(__name__)


class Client(Settings):
    """Client class for TickTick V2 API.

    This client provides methods to interact with the TickTick V2 API endpoints.
    It inherits from Settings which handles authentication.

    Example:
        ```python
        from pyticktick_v2 import Client

        client = Client(
            v2_username="user@example.com",
            v2_password="password",
        )

        # Get all active data
        batch = client.get_batch_v2()

        # Get completed tasks
        completed = client.get_project_all_closed_v2(
            GetClosedV2(status="Completed")
        )
        ```
    """

    @staticmethod
    def _model_dump(model: BaseModel) -> dict[str, Any]:
        """Dump model to dict with aliases for API serialization."""
        return model.model_dump(by_alias=True, mode="json")

    def _get_api_v2(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a GET request to the V2 API."""
        try:
            resp = httpx.get(
                url=self.v2_base_url + endpoint,
                headers=self.v2_headers,
                cookies=self.v2_cookies,
                params=data,
            )
            resp.raise_for_status()
            if resp.content is None or len(resp.content) == 0:
                msg = "Response content is empty"
                raise ValueError(msg)
        except httpx.HTTPStatusError as e:
            try:
                content = e.response.json()
            except json.decoder.JSONDecodeError:
                content = e.response.content.decode()
            msg = f"Response [{e.response.status_code}]: {content}"
            _logger.error(msg)
            raise ValueError(msg) from e

        return resp.json()

    def _post_api_v2(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a POST request to the V2 API."""
        if data is None:
            data = {}
        try:
            resp = httpx.post(
                url=self.v2_base_url + endpoint,
                headers=self.v2_headers,
                cookies=self.v2_cookies,
                json=data,
            )
            resp.raise_for_status()
            if resp.content is None or len(resp.content) == 0:
                msg = "Response content is empty"
                raise ValueError(msg)
        except httpx.HTTPStatusError as e:
            try:
                content = e.response.json()
            except json.decoder.JSONDecodeError:
                content = e.response.content.decode()
            msg = f"Response [{e.response.status_code}]: {content}"
            _logger.error(msg)
            raise ValueError(msg) from e

        return resp.json()

    def _delete_api_v2(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Make a DELETE request to the V2 API."""
        try:
            resp = httpx.delete(
                url=self.v2_base_url + endpoint,
                headers=self.v2_headers,
                cookies=self.v2_cookies,
                params=data,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                content = e.response.json()
            except json.decoder.JSONDecodeError:
                content = e.response.content.decode()
            msg = f"Response [{e.response.status_code}]: {content}"
            _logger.error(msg)
            raise ValueError(msg) from e

    def get_profile_v2(self) -> UserProfileV2:
        """Get the user profile from the V2 API.

        This method gets the user profile from the GET /user/profile V2 endpoint.

        Returns:
            UserProfileV2: The user profile object.
        """
        resp = self._get_api_v2("/user/profile")
        if self.override_forbid_extra:
            update_model_config(UserProfileV2, extra="allow")
        return UserProfileV2.model_validate(resp)

    def get_status_v2(self) -> UserStatusV2:
        """Get the user status from the V2 API.

        This method gets the user status from the GET /user/status V2 endpoint.
        The user "status" is mainly about the user's subscription status.

        Returns:
            UserStatusV2: The user status object.
        """
        resp = self._get_api_v2("/user/status")
        if self.override_forbid_extra:
            update_model_config(UserStatusV2, extra="allow")
        return UserStatusV2.model_validate(resp)

    def get_statistics_v2(self) -> UserStatisticsV2:
        """Get user statistics from the V2 API.

        This method gets the user statistics from the GET /statistics/general V2 endpoint.

        Returns:
            UserStatisticsV2: The user statistics object.
        """
        resp = self._get_api_v2("/statistics/general")
        if self.override_forbid_extra:
            update_model_config(UserStatisticsV2, extra="allow")
        return UserStatisticsV2.model_validate(resp)

    def get_project_all_closed_v2(
        self,
        data: GetClosedV2 | dict[str, Any],
    ) -> ClosedRespV2:
        """Get all completed or abandoned tasks from the V2 API.

        This method gets all completed or abandoned tasks from the
        GET /project/all/closed V2 endpoint.

        Args:
            data: GetClosedV2 model or dict with status ("Completed" or "Abandoned")
                and optional date range (from_, to).

        Returns:
            ClosedRespV2: List of closed tasks.
        """
        if isinstance(data, dict):
            validated_data = GetClosedV2.model_validate(data)
        else:
            validated_data = data
        resp = self._get_api_v2("/project/all/closed", data=self._model_dump(validated_data))
        if self.override_forbid_extra:
            update_model_config(ClosedRespV2, extra="allow")
        return ClosedRespV2.model_validate(resp)

    def get_batch_v2(self) -> GetBatchV2:
        """Get all active objects for the current user from the V2 API.

        This method gets the status of all objects for the current user from the
        GET /batch/check/0 V2 endpoint. This includes projects, tasks, tags, etc.

        Returns:
            GetBatchV2: The batch object with all active data.
        """
        resp = self._get_api_v2("/batch/check/0")
        if self.override_forbid_extra:
            update_model_config(GetBatchV2, extra="allow")
        return GetBatchV2.model_validate(resp)

    def post_task_v2(self, data: PostBatchTaskV2 | dict[str, Any]) -> BatchRespV2:
        """Create, update, or delete tasks in bulk against the V2 API.

        This method creates, updates, and deletes tasks in bulk using the
        POST /batch/task V2 endpoint.

        Args:
            data: PostBatchTaskV2 model or dict with add/update/delete lists.

        Returns:
            BatchRespV2: Response with id2error and id2etag maps.
        """
        if isinstance(data, dict):
            validated_data = PostBatchTaskV2.model_validate(data)
        else:
            validated_data = data
        resp = self._post_api_v2("/batch/task", data=self._model_dump(validated_data))
        if self.override_forbid_extra:
            update_model_config(BatchRespV2, extra="allow")
        return BatchRespV2.model_validate(resp)
