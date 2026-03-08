"""Settings for the vendored pyticktick v2 API client.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).

This is a simplified version that only supports v2 API with username/password.
"""

from __future__ import annotations

import logging
import warnings
from time import time
from typing import Any
from urllib.parse import parse_qsl, urlparse

import httpx
from bson import ObjectId as BsonObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from pyticktick_v2.models.v2 import UserSignOnV2, UserSignOnWithTOTPV2
from pyticktick_v2.api.pydantic import update_model_config

_logger = logging.getLogger(__name__)

TICKTICK_INCORRECT_HEADER_CODE = 429


class TokenV1(BaseModel):
    """Model for the V1 API token (unused but kept for compatibility)."""

    model_config = ConfigDict(extra="forbid")

    value: str = Field(description="The token string")
    expiration: int = Field(description="Unix timestamp when token expires")


class V2XDevice(BaseModel):
    """Model for the V2 API X-Device header."""

    model_config = ConfigDict(extra="allow")

    platform: str = Field(default="web", description="Platform")
    version: int = Field(default=6430, description="Version")
    id: str = Field(
        default_factory=lambda: str(BsonObjectId()),
        description="Random MongoDB ObjectId string",
    )


class Settings(BaseSettings):
    """Settings for the pyticktick v2 client.

    This is a simplified version that only supports v2 API.
    """

    model_config = SettingsConfigDict(
        env_prefix="pyticktick_",
        env_nested_delimiter="_",
        extra="forbid",
    )

    # V1 settings (unused but kept for compatibility)
    v1_client_id: str | None = Field(default=None, description="V1 client ID")
    v1_client_secret: SecretStr | None = Field(default=None, description="V1 client secret")
    v1_token: TokenV1 | None = Field(default=None, description="V1 token")
    v1_base_url: str = Field(
        default="https://api.ticktick.com/open/v1/",
        description="V1 API base URL",
    )
    v1_oauth_redirect_url: str = Field(
        default="http://127.0.0.1:8080/",
        description="OAuth redirect URL",
    )

    # V2 settings
    v2_username: EmailStr | None = Field(default=None, description="Username")
    v2_password: SecretStr | None = Field(default=None, description="Password")
    v2_totp_secret: SecretStr | None = Field(
        default=None,
        description="TOTP secret for 2FA",
    )
    v2_token: str | None = Field(default=None, description="Cookie token")
    v2_base_url: str = Field(
        default="https://api.ticktick.com/api/v2/",
        description="V2 API base URL",
    )
    v2_user_agent: str = Field(
        default="Mozilla/5.0 (rv:145.0) Firefox/145.0",
        description="User-Agent header",
    )
    v2_x_device: V2XDevice = Field(
        default=V2XDevice(),
        description="X-Device header",
    )

    override_forbid_extra: bool = Field(
        default=False,
        description="Override extra='forbid' in models",
    )

    @staticmethod
    def _v2_signon(
        username: str,
        password: str,
        base_url: str,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        try:
            resp = httpx.post(
                url=base_url + "/user/signon?wc=true&remember=true",
                headers=headers,
                json={"username": username, "password": password},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            content = (
                e.response.content.decode()
                if isinstance(e.response.content, bytes)
                else e.response.content
            )
            if e.response.status_code == TICKTICK_INCORRECT_HEADER_CODE:
                _logger.warning(
                    "Request failed with 429 - may be related to request headers"
                )
            msg = f"Response [{e.response.status_code}]: {content}"
            _logger.error(msg)
            raise ValueError(msg) from e

        result = resp.json()
        if not isinstance(result, dict):
            msg = f"Invalid response, expected dict, got {type(result)}"
            raise TypeError(msg)
        return result

    @classmethod
    def v2_signon(
        cls,
        username: str,
        password: str,
        base_url: str,
        headers: dict[str, str],
        override_forbid_extra: bool = False,
    ) -> UserSignOnV2:
        """Generate a cookie token for the V2 API."""
        resp = cls._v2_signon(
            username=username,
            password=password,
            base_url=base_url,
            headers=headers,
        )

        # Check if TOTP is required (not supported in this vendored version)
        try:
            UserSignOnWithTOTPV2.model_validate(resp)
            msg = "Sign on requires TOTP verification, but TOTP is not supported in this vendored version"
            raise ValueError(msg)
        except ValidationError:
            pass

        if override_forbid_extra:
            update_model_config(UserSignOnV2, extra="allow")
        return UserSignOnV2.model_validate(resp)

    def _check_no_settings(self) -> "Settings":
        if self.v2_username is None and self.v2_password is None:
            msg = "No settings provided, cannot signon to V2 API"
            _logger.error(msg)
            raise ValueError(msg)
        return self

    def _get_v2_token(self) -> "Settings":
        if self.v2_token is None:
            if self.v2_username is None or self.v2_password is None:
                msg = "Cannot signon to v2 without v2_username and v2_password"
                _logger.warning(msg)
                warnings.warn(msg, UserWarning, stacklevel=1)
            else:
                self.v2_token = self.v2_signon(
                    username=self.v2_username,
                    password=self.v2_password.get_secret_value(),
                    base_url=self.v2_base_url,
                    headers=self.v2_headers,
                    override_forbid_extra=self.override_forbid_extra,
                ).token
        return self

    @model_validator(mode="after")
    def _validate_model(self) -> "Settings":
        self._check_no_settings()
        self._get_v2_token()
        return self

    @property
    def v2_headers(self) -> dict[str, str]:
        """Get headers for V2 API requests."""
        return {
            "User-Agent": self.v2_user_agent,
            "X-Device": self.v2_x_device.model_dump_json(),
        }

    @property
    def v2_cookies(self) -> dict[str, str]:
        """Get cookies for V2 API requests."""
        if self.v2_token is None:
            msg = "Cannot get v2 cookies without v2_token"
            _logger.error(msg)
            raise ValueError(msg)
        return {"t": self.v2_token}
