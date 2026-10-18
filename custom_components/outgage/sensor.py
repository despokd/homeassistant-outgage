"""Sensors for the OutGage integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import OutGageConfigEntry
from .entity import OutGageEntity
from .protocol import OutGaugePacket

GEARS = ["R", "N", *(str(gear) for gear in range(1, 11))]


@dataclass(frozen=True, kw_only=True)
class OutGageSensorEntityDescription(SensorEntityDescription):
    """Describes an OutGage sensor."""

    value_fn: Callable[[OutGaugePacket], float | str | None]
    available_fn: Callable[[OutGaugePacket], bool] = lambda _packet: True


SENSORS: tuple[OutGageSensorEntityDescription, ...] = (
    OutGageSensorEntityDescription(
        key="speed",
        translation_key="speed",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        value_fn=lambda p: p.speed,
    ),
    OutGageSensorEntityDescription(
        key="rpm",
        translation_key="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        suggested_display_precision=0,
        value_fn=lambda p: p.rpm,
    ),
    OutGageSensorEntityDescription(
        key="gear",
        translation_key="gear",
        device_class=SensorDeviceClass.ENUM,
        options=GEARS,
        value_fn=lambda p: p.gear_label if p.gear_label in GEARS else None,
    ),
    OutGageSensorEntityDescription(
        key="turbo",
        translation_key="turbo",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda p: p.turbo,
        available_fn=lambda p: p.has_turbo,
    ),
    OutGageSensorEntityDescription(
        key="engine_temperature",
        translation_key="engine_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        value_fn=lambda p: p.eng_temp,
    ),
    OutGageSensorEntityDescription(
        key="oil_temperature",
        translation_key="oil_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        value_fn=lambda p: p.oil_temp,
    ),
    OutGageSensorEntityDescription(
        key="fuel",
        translation_key="fuel",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda p: p.fuel * 100,
    ),
    OutGageSensorEntityDescription(
        key="throttle",
        translation_key="throttle",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda p: p.throttle * 100,
    ),
    OutGageSensorEntityDescription(
        key="brake",
        translation_key="brake",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda p: p.brake * 100,
    ),
    OutGageSensorEntityDescription(
        key="clutch",
        translation_key="clutch",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda p: p.clutch * 100,
    ),
    OutGageSensorEntityDescription(
        key="car",
        translation_key="car",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda p: p.car,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OutGageConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up OutGage sensors."""
    async_add_entities(OutGageSensor(entry, description) for description in SENSORS)


class OutGageSensor(OutGageEntity, SensorEntity):
    """An OutGauge value."""

    entity_description: OutGageSensorEntityDescription

    @property
    def available(self) -> bool:
        """Hide values the current vehicle does not report."""
        return super().available and self.entity_description.available_fn(
            self.coordinator.data
        )

    @property
    def native_value(self) -> float | str | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
