"""Binary sensors for the OutGage integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .coordinator import OutGageConfigEntry
from .entity import OutGageEntity


@dataclass(frozen=True, kw_only=True)
class OutGageLightEntityDescription(BinarySensorEntityDescription):
    """Describes a dash light."""

    bit: int


LIGHTS: tuple[OutGageLightEntityDescription, ...] = (
    OutGageLightEntityDescription(
        key="shift_light", translation_key="shift_light", bit=protocol.DL_SHIFT
    ),
    OutGageLightEntityDescription(
        key="high_beam", translation_key="high_beam", bit=protocol.DL_FULLBEAM
    ),
    OutGageLightEntityDescription(
        key="handbrake", translation_key="handbrake", bit=protocol.DL_HANDBRAKE
    ),
    OutGageLightEntityDescription(
        key="traction_control", translation_key="traction_control", bit=protocol.DL_TC
    ),
    OutGageLightEntityDescription(
        key="signal_left", translation_key="signal_left", bit=protocol.DL_SIGNAL_L
    ),
    OutGageLightEntityDescription(
        key="signal_right", translation_key="signal_right", bit=protocol.DL_SIGNAL_R
    ),
    OutGageLightEntityDescription(
        key="oil_warning",
        translation_key="oil_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        bit=protocol.DL_OILWARN,
    ),
    OutGageLightEntityDescription(
        key="battery_warning",
        translation_key="battery_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        bit=protocol.DL_BATTERY,
    ),
    OutGageLightEntityDescription(
        key="abs", translation_key="abs", bit=protocol.DL_ABS
    ),
)

CONNECTED = BinarySensorEntityDescription(
    key="connected",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OutGageConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OutGage binary sensors."""
    async_add_entities(
        [
            OutGageConnectedSensor(entry, CONNECTED),
            *(OutGageLightSensor(entry, description) for description in LIGHTS),
        ]
    )


class OutGageConnectedSensor(OutGageEntity, BinarySensorEntity):
    """Whether BeamNG is currently sending data."""

    @property
    def available(self) -> bool:
        """Always available, so it can report the game being offline."""
        return True

    @property
    def is_on(self) -> bool:
        """Return True while packets arrive."""
        return self.coordinator.connected


class OutGageLightSensor(OutGageEntity, BinarySensorEntity):
    """A dash light."""

    entity_description: OutGageLightEntityDescription

    @property
    def available(self) -> bool:
        """Only available if the current vehicle has this light."""
        return super().available and self.coordinator.data.light_available(
            self.entity_description.bit
        )

    @property
    def is_on(self) -> bool | None:
        """Return whether the light is lit."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.light_on(self.entity_description.bit)
