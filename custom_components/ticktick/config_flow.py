"""Config flow for TickTick Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_COMPLETED_TASKS_DAYS,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_V1_CLIENT_ID,
    CONF_V1_CLIENT_SECRET,
    DEFAULT_COMPLETED_TASKS_DAYS,
    DOMAIN,
)
from .exceptions import TickTickAPIError, TickTickAuthError
from .pyticktick_client import AsyncPyTickTickClient

_LOGGER = logging.getLogger(__name__)


class TickTickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TickTick Integration.

    This implements a two-step authentication flow:
    1. Step 1 (user): OAuth2 v1 credentials (client_id, client_secret)
    2. Step 2 (v2_credentials): Username and password for v2 API

    The v1 OAuth must complete before v2 credentials are validated.
    """

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._v1_credentials: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Handle step 1: OAuth2 v1 credentials.

        This step collects the Client ID and Client Secret from
        the TickTick Developer Portal. The redirect URL is displayed
        to help users configure their OAuth app correctly.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store v1 credentials for use in step 2
            self._v1_credentials = {
                CONF_V1_CLIENT_ID: user_input[CONF_V1_CLIENT_ID],
                CONF_V1_CLIENT_SECRET: user_input[CONF_V1_CLIENT_SECRET],
            }

            # Move to step 2 for v2 credentials
            return await self.async_step_v2_credentials(None)

        # Step 1: Show OAuth2 v1 credential form with redirect URL
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_V1_CLIENT_ID): str,
                    vol.Required(CONF_V1_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )

    async def async_step_v2_credentials(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Handle step 2: v2 API credentials (username/password).

        This step is only shown after v1 OAuth credentials have been collected.
        The full authentication is validated here with both v1 and v2 credentials.
        """
        errors: dict[str, str] = {}
        existing_entry = None

        if user_input is not None:
            # Combine v1 credentials from step 1 with v2 credentials from step 2
            full_data = {
                **self._v1_credentials,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            try:
                info = await validate_input(self.hass, full_data)
            except CannotConnect:
                errors["base"] = "connection_error"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except OAuthError:
                errors["base"] = "oauth_error"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(full_data[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=full_data)

        # Check for reauth flow
        if self._get_reauth_unique_id():
            existing_entry = await self.async_set_unique_id(self._get_reauth_unique_id())
            if existing_entry is None:
                return self.async_abort(reason="unique_id_mismatch")

        # Step 2: Show v2 credential form
        return self.async_show_form(
            step_id="v2_credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(existing_entry.data.get(CONF_USERNAME, "") if existing_entry else "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={
                "redirect_url": "https://my.home-assistant.io/redirect/oauth",
            },
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle re-authentication flow."""
        # Restore v1 credentials from existing entry for reauth
        self._v1_credentials = {
            CONF_V1_CLIENT_ID: entry_data.get(CONF_V1_CLIENT_ID, ""),
            CONF_V1_CLIENT_SECRET: entry_data.get(CONF_V1_CLIENT_SECRET, ""),
        }
        return await self.async_step_v2_credentials(None)

    def _get_reauth_unique_id(self) -> str:
        """Get the unique_id from the reauth context."""
        if self.context and "source" in self.context:
            if "unique_id" in self.context:
                return str(self.context["unique_id"])
        return ""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TickTickOptionsFlowHandler(config_entry)


class TickTickOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for TickTick."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        completed_days = options.get(
            CONF_COMPLETED_TASKS_DAYS, DEFAULT_COMPLETED_TASKS_DAYS
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_COMPLETED_TASKS_DAYS, default=completed_days
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365))
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance.
        data: User input data with all credentials (v1 and v2).

    Returns:
        Dict with info to be stored in config entry.

    Raises:
        InvalidAuth: If credentials are invalid.
        CannotConnect: If connection to TickTick fails.
        OAuthError: If v1 OAuth credentials are invalid.
    """
    client = AsyncPyTickTickClient(
        hass=hass,
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        v1_client_id=data[CONF_V1_CLIENT_ID],
        v1_client_secret=data[CONF_V1_CLIENT_SECRET],
    )

    try:
        # Attempt to fetch data to validate credentials
        await client.async_get_batch()
    except TickTickAuthError as err:
        raise InvalidAuth from err
    except TickTickAPIError as err:
        # Check if error is related to v1 OAuth
        error_msg = str(err).lower()
        if "v1" in error_msg or "client" in error_msg or "oauth" in error_msg:
            raise OAuthError from err
        raise CannotConnect from err
    except ValueError as err:
        # Handle pydantic validation errors for v1 credentials
        error_msg = str(err).lower()
        if "v1" in error_msg or "client_id" in error_msg or "client_secret" in error_msg:
            raise OAuthError from err
        raise InvalidAuth from err
    finally:
        await client.async_close()

    # Return info to store in config entry
    return {"title": f"TickTick ({data[CONF_USERNAME]})"}


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OAuthError(HomeAssistantError):
    """Error to indicate OAuth2 v1 credentials are invalid."""
