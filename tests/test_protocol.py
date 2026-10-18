"""Tests for OutGauge packet parsing."""

import pytest

from custom_components.outgage.protocol import (
    DL_ABS,
    DL_FULLBEAM,
    DL_HANDBRAKE,
    PACKET,
    PACKET_WITH_ID,
    OutGaugePacket,
    OutGaugeParseError,
)

from .conftest import make_packet


def test_sizes() -> None:
    """BeamNG sends 92 bytes, or 96 with an ID."""
    assert PACKET.size == 92
    assert PACKET_WITH_ID.size == 96


@pytest.mark.parametrize("packet_id", [None, 7])
def test_roundtrip(packet_id: int | None) -> None:
    """Packets survive serialization."""
    packet = make_packet(id=packet_id, display1="hello")
    assert OutGaugePacket.from_bytes(packet.to_bytes()) == packet


@pytest.mark.parametrize("size", [0, 91, 93, 256])
def test_bad_size(size: int) -> None:
    """Datagrams of the wrong size are rejected."""
    with pytest.raises(OutGaugeParseError):
        OutGaugePacket.from_bytes(bytes(size))


@pytest.mark.parametrize(("gear", "label"), [(0, "R"), (1, "N"), (2, "1"), (7, "6")])
def test_gear_label(gear: int, label: str) -> None:
    """Gear numbers map to dashboard labels."""
    assert make_packet(gear=gear).gear_label == label


def test_lights() -> None:
    """Dash light bitmasks are decoded."""
    packet = make_packet(dash_lights=DL_HANDBRAKE | DL_ABS, show_lights=DL_HANDBRAKE)
    assert packet.light_available(DL_ABS)
    assert not packet.light_available(DL_FULLBEAM)
    assert packet.light_on(DL_HANDBRAKE)
    assert not packet.light_on(DL_ABS)
