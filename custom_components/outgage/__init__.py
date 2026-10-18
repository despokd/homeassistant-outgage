"""The OutGage integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import OutGageConfigEntry, OutGageCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: OutGageConfigEntry) -> bool:
    """Set up OutGage from a config entry."""
    coordinator = OutGageCoordinator(hass, entry)
    try:
        await coordinator.async_start()
    except OSError as err:
        raise ConfigEntryNotReady(
            f"Cannot listen on {coordinator.host}:{coordinator.port}: {err}"
        ) from err

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OutGageConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_stop()
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: OutGageConfigEntry
) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
