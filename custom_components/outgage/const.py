"""Constants for the OutGage integration."""

from datetime import timedelta

DOMAIN = "outgage"

CONF_OUTGAUGE_ID = "outgauge_id"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_TIMEOUT = "timeout"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 4444
DEFAULT_UPDATE_INTERVAL = 1.0
DEFAULT_TIMEOUT = 5

MIN_UPDATE_INTERVAL = 0.1
MAX_UPDATE_INTERVAL = 60.0

WATCHDOG_INTERVAL = timedelta(seconds=1)
