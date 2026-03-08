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
    DEFAULT_COMPLETED_TASKS_DAYS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TickTickConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TickTick Integration.

    This uses v2 username/password authentication which is fully automatable
    without requiring browser-based OAuth interaction.

    Note: Credentials are saved without validation during setup.
    Validation happens when the integration attempts to connect.
    """

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Handle the initial step (username/password form).

        Credentials are saved without validation.
        Validation occurs when the integration connects to TickTick.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            # Save credentials without validation
            # Validation will happen when the integration connects
            title = f"TickTick ({user_input[CONF_USERNAME]})"
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle re-authentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Handle re-authentication confirmation."""
        errors: dict[str, str] = {}

        existing_entry = await self.async_set_unique_id(self._get_reauth_unique_id())
        if existing_entry is None:
            return self.async_abort(reason="unique_id_mismatch")

        if user_input is not None:
            # Update credentials without validation
            self.hass.config_entries.async_update_entry(
                existing_entry, data=user_input
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=existing_entry.data.get(CONF_USERNAME, "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={"username": existing_entry.data.get(CONF_USERNAME, "")},
            errors=errors,
        )

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
        # Store in private attribute - base class property reads from this
        self._config_entry = config_entry

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
