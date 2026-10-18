"""Fixtures for OutGage tests."""

import socket

import pytest

from custom_components.outgage.protocol import (
    DL_ABS,
    DL_HANDBRAKE,
    OG_TURBO,
    OutGaugePacket,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading the custom integration in all tests."""
    return


@pytest.fixture(autouse=True)
def auto_enable_sockets(socket_enabled):
    """The integration and tests use real UDP sockets on localhost."""
    return


@pytest.fixture
def free_port() -> int:
    """Return a UDP port that is currently free."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def make_packet(**overrides) -> OutGaugePacket:
    """Build a packet with sensible defaults."""
    values = dict(
        time=0,
        car="beam",
        flags=OG_TURBO,
        gear=3,
        plid=0,
        speed=10.0,
        rpm=3000.0,
        turbo=0.5,
        eng_temp=90.0,
        fuel=0.75,
        oil_pressure=0.0,
        oil_temp=100.0,
        dash_lights=DL_HANDBRAKE | DL_ABS,
        show_lights=DL_HANDBRAKE,
        throttle=0.5,
        brake=0.0,
        clutch=0.0,
        display1="",
        display2="",
    )
    values.update(overrides)
    return OutGaugePacket(**values)
