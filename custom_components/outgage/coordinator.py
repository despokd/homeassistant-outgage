"""UDP listener that pushes throttled OutGauge data to entities."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_OUTGAUGE_ID,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    WATCHDOG_INTERVAL,
)
from .protocol import OutGaugePacket, OutGaugeParseError

_LOGGER = logging.getLogger(__name__)

type OutGageConfigEntry = ConfigEntry[OutGageCoordinator]


class _OutGaugeProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_datagram: Callable[[bytes], None]) -> None:
        self._on_datagram = on_datagram

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self._on_datagram(data)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("OutGauge socket error: %s", exc)


async def async_open_listener(
    hass: HomeAssistant, host: str, port: int, on_datagram: Callable[[bytes], None]
) -> asyncio.DatagramTransport:
    """Bind the UDP socket. Raises OSError if the port is unavailable."""
    transport, _ = await hass.loop.create_datagram_endpoint(
        lambda: _OutGaugeProtocol(on_datagram), local_addr=(host, port)
    )
    return transport


class OutGageCoordinator:
    """Receives packets at game rate and notifies listeners at a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: OutGageConfigEntry) -> None:
        self.hass = hass
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self._expected_id: int | None = entry.data.get(CONF_OUTGAUGE_ID) or None
        self._update_interval = timedelta(
            seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        self._timeout: float = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        self.data: OutGaugePacket | None = None
        self.connected = False
        self._latest: OutGaugePacket | None = None
        self._last_received = 0.0
        self._transport: asyncio.DatagramTransport | None = None
        self._listeners: list[CALLBACK_TYPE] = []
        self._unsubs: list[CALLBACK_TYPE] = []

    async def async_start(self) -> None:
        """Open the socket and start the push timers."""
        self._transport = await async_open_listener(
            self.hass, self.host, self.port, self._handle_datagram
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass, self._async_push, self._update_interval
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass, self._async_watchdog, WATCHDOG_INTERVAL
            )
        )

    async def async_stop(self) -> None:
        """Close the socket and cancel timers."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._transport is not None:
            self._transport.close()
            self._transport = None

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Register an entity update callback."""
        self._listeners.append(update_callback)

        @callback
        def remove_listener() -> None:
            self._listeners.remove(update_callback)

        return remove_listener

    @callback
    def _handle_datagram(self, data: bytes) -> None:
        try:
            packet = OutGaugePacket.from_bytes(data)
        except OutGaugeParseError as err:
            _LOGGER.debug("Ignoring datagram: %s", err)
            return
        if self._expected_id is not None and packet.id != self._expected_id:
            return
        self._latest = packet
        self._last_received = time.monotonic()

    @callback
    def _async_push(self, _now: datetime | None = None) -> None:
        latest = self._latest
        if latest is None or latest == self.data:
            return
        self.data = latest
        self.connected = True
        self._notify()

    @callback
    def _async_watchdog(self, _now: datetime | None = None) -> None:
        online = (
            self._latest is not None
            and time.monotonic() - self._last_received < self._timeout
        )
        if online == self.connected:
            return
        self.connected = online
        if online:
            self.data = self._latest
        self._notify()

    @callback
    def _notify(self) -> None:
        for update_callback in list(self._listeners):
            update_callback()
