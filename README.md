# OutGauge Integration for Homeassistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/despokd/homeassistant-outgage)](https://github.com/despokd/homeassistant-outgage/releases)

The `OutGage` integration listens to the OutGauge UDP protocol to show running vehicle data from BeamNG.drive. 

[BeamNG documentation](https://documentation.beamng.com/modding/protocols/#outgauge-udp-protocol)

## Installation

### 1. Using HACS (recommended way)

This integration is a not yet an official HACS Integration.

1. Open HACS
2. Open options with the three dots at the upper right
3. Add this repo `https://github.com/despokd/homeassistant-outgage` as a custom repository with type `Integration`
4. Then install the "OutGage" integration or use the link below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=despokd&repository=homeassistant-outgage&category=integration)

If you use this method, your component will always update to the latest version.

### 2. Manual

- Download the latest zip release from [Github Releases](https://github.com/despokd/homeassistant-outgage/releases/latest)
- Extract the zip file
- Copy the folder "outgage" from within custom_components with all of its components to `<config>/custom_components/`

where `<config>` is your Home Assistant configuration directory.

>__NOTE__: Do not download the file by using the link above directly, the status in the "main" branch can be in development and therefore is maybe not working.

## Configuration

Go to Configuration -> Integrations and click on "add integration". Then search for "OutGage".

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=outgage)

Only one instance can be configured.

### Configuration Variables

- __host__ : Local address Home Assistant listens on. Keep `0.0.0.0` to listen on all interfaces.
- __port__ : UDP port Home Assistant listens on (default `4444`).
- __OutGauge ID__ : Optional. If not `0`, only packets with this ID are accepted.

### Options

- __Update interval__ : How often entity states are updated (default 1 s). BeamNG sends far more packets than Home Assistant should record.
- __Offline timeout__ : Seconds without packets before the game is shown as disconnected (default 5 s).

## BeamNG.drive setup

BeamNG.drive sends the data to Home Assistant, not the other way round.

1. In BeamNG.drive open Options → Other and enable __OutGauge support__.
2. Set the __IP__ to the address of your Home Assistant instance.
3. Set the __port__ to the one configured above.

If Home Assistant runs in Docker, publish the UDP port (e.g. `4444:4444/udp`) or use host networking.

## Entities

Sensors: speed, RPM, gear, turbo pressure, engine temperature, oil temperature, fuel, throttle, brake, clutch and car. Throttle, brake, clutch and car are disabled by default.

Binary sensors: connectivity, shift light, high beam, handbrake, traction control, left/right turn signal, oil warning, battery warning and ABS. Lights the current vehicle does not have are unavailable.

Units follow your Home Assistant unit system.

>__TIP__: Even at a 1 s interval, driving produces a lot of history. Consider excluding the fast-changing sensors from the [recorder](https://www.home-assistant.io/integrations/recorder/).

## Development

- `docker compose up -d` starts Home Assistant with the integration mounted.
- `python scripts/send_fake_outgauge.py [host] [port] [rate_hz]` sends synthetic packets without BeamNG.drive.
- `pip install -r requirements_test.txt && pytest` runs the tests.
