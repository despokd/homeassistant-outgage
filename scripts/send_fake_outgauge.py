"""Send synthetic OutGauge packets, for testing without BeamNG.drive.

Usage: python scripts/send_fake_outgauge.py [host] [port] [rate_hz]
"""

import importlib.util
import math
from pathlib import Path
import socket
import sys
import time

# Load protocol.py directly so Home Assistant does not need to be installed.
_PROTOCOL = (
    Path(__file__).resolve().parents[1] / "custom_components/outgage/protocol.py"
)
_spec = importlib.util.spec_from_file_location("outgage_protocol", _PROTOCOL)
protocol = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = protocol
_spec.loader.exec_module(protocol)


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4444
    rate = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start = time.monotonic()
    print(f"Sending to {host}:{port} at {rate} Hz, Ctrl+C to stop")
    while True:
        t = time.monotonic() - start
        phase = (math.sin(t / 3) + 1) / 2
        packet = protocol.OutGaugePacket(
            time=0,
            car="beam",
            flags=protocol.OG_KM | protocol.OG_BAR | protocol.OG_TURBO,
            gear=2 + int(phase * 5),
            plid=0,
            speed=phase * 50,
            rpm=800 + phase * 6000,
            turbo=phase * 1.2,
            eng_temp=90,
            fuel=max(0.0, 1 - t / 600),
            oil_pressure=0,
            oil_temp=100,
            dash_lights=protocol.DL_FULLBEAM
            | protocol.DL_HANDBRAKE
            | protocol.DL_SIGNAL_L
            | protocol.DL_SIGNAL_R
            | protocol.DL_ABS,
            show_lights=protocol.DL_SIGNAL_L if int(t) % 2 else 0,
            throttle=phase,
            brake=1 - phase,
            clutch=0,
            display1="",
            display2="",
        )
        sock.sendto(packet.to_bytes(), (host, port))
        time.sleep(1 / rate)


if __name__ == "__main__":
    main()
