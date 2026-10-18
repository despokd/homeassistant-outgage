"""Base entity for the OutGage integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN
from .coordinator import OutGageConfigEntry, OutGageCoordinator


class OutGageEntity(Entity):
    """An entity fed by the OutGage coordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, entry: OutGageConfigEntry, description: EntityDescription
    ) -> None:
        self.coordinator: OutGageCoordinator = entry.runtime_data
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="BeamNG",
            model="OutGauge",
        )

    @property
    def available(self) -> bool:
        """Entities are available while packets keep arriving."""
        return self.coordinator.connected and self.coordinator.data is not None

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator pushes."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
