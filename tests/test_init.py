"""End-to-end tests: UDP packets to entity states."""

import asyncio
from datetime import timedelta
import socket

from freezegun.api import FrozenDateTimeFactory

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.outgage.const import CONF_OUTGAUGE_ID, DOMAIN

from .conftest import make_packet


async def _setup(
    hass: HomeAssistant, port: int, outgauge_id: int = 0
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="BeamNG.drive",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: port, CONF_OUTGAUGE_ID: outgauge_id},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _send(port: int, data: bytes) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data, ("127.0.0.1", port))
    # Let the event loop deliver the datagram.
    for _ in range(50):
        await asyncio.sleep(0)


async def _tick(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float
) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_packets_update_entities(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, free_port: int
) -> None:
    """Packets are pushed to entities on the update interval."""
    entry = await _setup(hass, free_port)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("binary_sensor.beamng_drive_connectivity").state == STATE_OFF
    assert hass.states.get("sensor.beamng_drive_rpm").state == STATE_UNAVAILABLE

    await _send(free_port, make_packet().to_bytes())
    await _tick(hass, freezer, 1)

    assert hass.states.get("binary_sensor.beamng_drive_connectivity").state == STATE_ON
    assert float(hass.states.get("sensor.beamng_drive_rpm").state) == 3000
    assert hass.states.get("sensor.beamng_drive_gear").state == "2"
    assert float(hass.states.get("sensor.beamng_drive_speed").state) == 36
    assert float(hass.states.get("sensor.beamng_drive_fuel").state) == 75
    assert hass.states.get("binary_sensor.beamng_drive_handbrake").state == STATE_ON
    assert hass.states.get("binary_sensor.beamng_drive_abs").state == STATE_OFF
    # The vehicle has no high beam light.
    assert (
        hass.states.get("binary_sensor.beamng_drive_high_beam").state
        == STATE_UNAVAILABLE
    )

    await hass.config_entries.async_unload(entry.entry_id)


async def test_timeout_marks_unavailable(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, free_port: int
) -> None:
    """Entities become unavailable when the game stops sending."""
    entry = await _setup(hass, free_port)
    await _send(free_port, make_packet().to_bytes())
    await _tick(hass, freezer, 1)
    assert float(hass.states.get("sensor.beamng_drive_rpm").state) == 3000

    await _tick(hass, freezer, 10)
    assert hass.states.get("binary_sensor.beamng_drive_connectivity").state == STATE_OFF
    assert hass.states.get("sensor.beamng_drive_rpm").state == STATE_UNAVAILABLE

    await hass.config_entries.async_unload(entry.entry_id)


async def test_id_filter(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, free_port: int
) -> None:
    """Packets with another ID are ignored."""
    entry = await _setup(hass, free_port, outgauge_id=5)
    await _send(free_port, make_packet(id=4).to_bytes())
    await _send(free_port, b"garbage")
    await _tick(hass, freezer, 1)
    assert hass.states.get("binary_sensor.beamng_drive_connectivity").state == STATE_OFF

    await _send(free_port, make_packet(id=5).to_bytes())
    await _tick(hass, freezer, 1)
    assert hass.states.get("binary_sensor.beamng_drive_connectivity").state == STATE_ON

    await hass.config_entries.async_unload(entry.entry_id)


async def test_port_in_use(hass: HomeAssistant) -> None:
    """Setup is retried while the port is busy."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as busy:
        busy.bind(("127.0.0.1", 0))
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "127.0.0.1",
                CONF_PORT: busy.getsockname()[1],
                CONF_OUTGAUGE_ID: 0,
            },
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY
