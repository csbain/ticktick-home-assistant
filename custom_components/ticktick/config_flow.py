"""Config flow for TickTick Integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.http import async_import_module
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    CONF_COMPLETED_TASKS_DAYS,
    DEFAULT_COMPLETED_TASKS_DAYS,
    DOMAIN,
)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle TickTick Integration OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TickTickOptionsFlowHandler(config_entry)


class TickTickOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for TickTick."""

    async def async_step_init(self, user_input=None):
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
