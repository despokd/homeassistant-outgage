"""Check that UDP packets reach a port on this machine.

Binds the port, sends one OutGauge test packet to itself, then prints every
datagram that arrives (e.g. from BeamNG.drive). Stop the Home Assistant
integration first, only one process can listen on the port.

Usage: python scripts/test_udp_port.py [port] [host] [-v]

Non-OutGauge datagrams are only shown with -v/--verbose.
"""

import argparse
import importlib.util
from pathlib import Path
import socket
import sys

# Load protocol.py directly so Home Assistant does not need to be installed.
_PROTOCOL = (
    Path(__file__).resolve().parents[1] / "custom_components/outgage/protocol.py"
)
_spec = importlib.util.spec_from_file_location("outgage_protocol", _PROTOCOL)
protocol = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = protocol
_spec.loader.exec_module(protocol)


def describe(data: bytes, verbose: bool) -> str | None:
    try:
        packet = protocol.OutGaugePacket.from_bytes(data)
    except protocol.OutGaugeParseError as err:
        return f"not OutGauge ({err})" if verbose else None
    return (
        f"OutGauge car={packet.car!r} gear={packet.gear_label} "
        f"speed={packet.speed * 3.6:.0f} km/h rpm={packet.rpm:.0f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check that UDP packets arrive.")
    parser.add_argument("port", nargs="?", type=int, default=4444)
    parser.add_argument("host", nargs="?", default="0.0.0.0")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="also show non-OutGauge data"
    )
    args = parser.parse_args()
    port, host = args.port, args.host

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((host, port))
    except OSError as err:
        sys.exit(f"Cannot bind {host}:{port}: {err}")

    test_packet = protocol.OutGaugePacket(
        time=0, car="test", flags=0, gear=2, plid=0, speed=0, rpm=0, turbo=0,
        eng_temp=0, fuel=0, oil_pressure=0, oil_temp=0, dash_lights=0,
        show_lights=0, throttle=0, brake=0, clutch=0, display1="", display2="",
    )  # fmt: skip
    sock.sendto(test_packet.to_bytes(), ("127.0.0.1", port))

    print(f"Listening on {host}:{port}, Ctrl+C to stop")
    print("Local IPs for BeamNG:", ", ".join(local_ips()) or "unknown")
    try:
        while True:
            data, (src_host, src_port) = sock.recvfrom(1024)
            if (description := describe(data, args.verbose)) is not None:
                print(f"{src_host}:{src_port} {len(data)} bytes, {description}")
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()


def local_ips() -> list[str]:
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    # The address used for the default route, without sending anything.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.0.2.1", 1))
            ips.add(probe.getsockname()[0])
        except OSError:
            pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


if __name__ == "__main__":
    main()
