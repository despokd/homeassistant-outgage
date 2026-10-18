"""OutGauge UDP packet parsing.

See https://documentation.beamng.com/modding/protocols/#outgauge-udp-protocol
"""

from __future__ import annotations

from dataclasses import dataclass
import struct

# time, car, flags, gear, plid, speed, rpm, turbo, engTemp, fuel, oilPressure,
# oilTemp, dashLights, showLights, throttle, brake, clutch, display1, display2
PACKET = struct.Struct("<I4sHBBfffffffIIfff16s16s")
PACKET_WITH_ID = struct.Struct("<I4sHBBfffffffIIfff16s16si")

# flags
OG_SHIFT = 1
OG_CTRL = 2
OG_TURBO = 8192
OG_KM = 16384
OG_BAR = 32768

# dashLights / showLights bits
DL_SHIFT = 1 << 0
DL_FULLBEAM = 1 << 1
DL_HANDBRAKE = 1 << 2
DL_PITSPEED = 1 << 3
DL_TC = 1 << 4
DL_SIGNAL_L = 1 << 5
DL_SIGNAL_R = 1 << 6
DL_SIGNAL_ANY = 1 << 7
DL_OILWARN = 1 << 8
DL_BATTERY = 1 << 9
DL_ABS = 1 << 10


class OutGaugeParseError(ValueError):
    """Raised when a datagram is not a valid OutGauge packet."""


def _decode(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("ascii", errors="replace")


@dataclass(frozen=True, slots=True)
class OutGaugePacket:
    """A decoded OutGauge packet."""

    time: int
    car: str
    flags: int
    gear: int
    plid: int
    speed: float
    rpm: float
    turbo: float
    eng_temp: float
    fuel: float
    oil_pressure: float
    oil_temp: float
    dash_lights: int
    show_lights: int
    throttle: float
    brake: float
    clutch: float
    display1: str
    display2: str
    id: int | None = None

    @classmethod
    def from_bytes(cls, data: bytes) -> OutGaugePacket:
        """Parse a raw datagram (92 bytes, or 96 with the optional ID)."""
        if len(data) == PACKET.size:
            values = PACKET.unpack(data)
            packet_id = None
        elif len(data) == PACKET_WITH_ID.size:
            *values, packet_id = PACKET_WITH_ID.unpack(data)
        else:
            raise OutGaugeParseError(f"Unexpected packet size {len(data)}")

        (
            time,
            car,
            flags,
            gear,
            plid,
            speed,
            rpm,
            turbo,
            eng_temp,
            fuel,
            oil_pressure,
            oil_temp,
            dash_lights,
            show_lights,
            throttle,
            brake,
            clutch,
            display1,
            display2,
        ) = values
        return cls(
            time=time,
            car=_decode(car),
            flags=flags,
            gear=gear,
            plid=plid,
            speed=speed,
            rpm=rpm,
            turbo=turbo,
            eng_temp=eng_temp,
            fuel=fuel,
            oil_pressure=oil_pressure,
            oil_temp=oil_temp,
            dash_lights=dash_lights,
            show_lights=show_lights,
            throttle=throttle,
            brake=brake,
            clutch=clutch,
            display1=_decode(display1),
            display2=_decode(display2),
            id=packet_id,
        )

    def to_bytes(self) -> bytes:
        """Serialize the packet, mainly for tests and the fake sender."""
        values = (
            self.time,
            self.car.encode("ascii")[:4],
            self.flags,
            self.gear,
            self.plid,
            self.speed,
            self.rpm,
            self.turbo,
            self.eng_temp,
            self.fuel,
            self.oil_pressure,
            self.oil_temp,
            self.dash_lights,
            self.show_lights,
            self.throttle,
            self.brake,
            self.clutch,
            self.display1.encode("ascii")[:15],
            self.display2.encode("ascii")[:15],
        )
        if self.id is None:
            return PACKET.pack(*values)
        return PACKET_WITH_ID.pack(*values, self.id)

    @property
    def gear_label(self) -> str:
        """Gear as shown on a dashboard: R, N, 1, 2, ..."""
        if self.gear == 0:
            return "R"
        if self.gear == 1:
            return "N"
        return str(self.gear - 1)

    @property
    def has_turbo(self) -> bool:
        """Whether the vehicle reports a turbo."""
        return bool(self.flags & OG_TURBO)

    def light_available(self, bit: int) -> bool:
        """Whether the vehicle has the given dash light."""
        return bool(self.dash_lights & bit)

    def light_on(self, bit: int) -> bool:
        """Whether the given dash light is currently lit."""
        return bool(self.show_lights & bit)
