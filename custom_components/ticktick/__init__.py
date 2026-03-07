"""The TickTick Integration integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, SupportsResponse

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import TickTickCoordinator
from .pyticktick_client import AsyncPyTickTickClient
from .service_handlers import (
    handle_complete_task,
    handle_copy_task,
    handle_create_task,
    handle_delete_task,
    handle_get_projects,
    handle_get_task,
    handle_get_subtasks,
    handle_get_tasks_filtered,
    handle_update_task,
)

type TickTickConfigEntry = ConfigEntry[AsyncPyTickTickClient]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = datetime.timedelta(minutes=1)

PLATFORMS = [Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: TickTickConfigEntry) -> bool:
    """Set up TickTick Integration from a config entry.

    Uses username/password authentication with pyticktick library.
    Credentials are retrieved from the encrypted config entry storage.
    """
    # Get credentials from config entry (stored encrypted by HA)
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Create async client wrapper
    client = AsyncPyTickTickClient(
        hass=hass,
        username=username,
        password=password,
    )

    # Store client in runtime_data for access by services
    entry.runtime_data = client

    # Register coordinator for data updates
    await register_coordinator(hass, client, entry)

    # Register services
    await register_services(hass, client)

    # Set up platforms (todo entities)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TickTickConfigEntry) -> bool:
    """Unload a TickTick config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up client connection
        if entry.runtime_data:
            await entry.runtime_data.async_close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def register_coordinator(
    hass: HomeAssistant,
    client: AsyncPyTickTickClient,
    entry: TickTickConfigEntry,
) -> None:
    """Register Coordinator for TickTick Todo Entity."""
    coordinator = TickTickCoordinator(
        hass=hass,
        logger=_LOGGER,
        entry=entry,
        update_interval=SCAN_INTERVAL,
        client=client,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator


async def register_services(
    hass: HomeAssistant, client: AsyncPyTickTickClient
) -> None:
    """Register TickTick services."""
    hass.services.async_register(
        DOMAIN,
        "get_task",
        await handle_get_task(client),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "create_task",
        await handle_create_task(client),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "complete_task",
        await handle_complete_task(client),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "delete_task",
        await handle_delete_task(client),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "update_task",
        await handle_update_task(client),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "copy_task",
        await handle_copy_task(client),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "get_projects",
        await handle_get_projects(client),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "get_subtasks",
        await handle_get_subtasks(client),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "get_tasks_filtered",
        await handle_get_tasks_filtered(client),
        supports_response=SupportsResponse.ONLY,
    )
