"""Constants for WOOW CAN."""

DOMAIN = "woow_can"

CONF_PORT = "port"  # the interface name (can0, can1, ...)

CONF_BITRATE = "bitrate"
CONF_FD = "fd"
CONF_DBITRATE = "dbitrate"
CONF_LISTEN_ONLY = "listen_only"
CONF_RESTART_MS = "restart_ms"
CONF_FILTERS = "filters"
CONF_MAX_RATE = "max_events_per_sec"

BITRATES = [10000, 20000, 50000, 100000, 125000, 250000, 500000, 800000, 1000000]
DBITRATES = [1000000, 2000000, 4000000, 5000000, 8000000]

CAN_DEFAULTS = {
    CONF_BITRATE: 500000,
    CONF_FD: False,
    CONF_DBITRATE: 2000000,
    CONF_LISTEN_ONLY: False,
    CONF_RESTART_MS: 100,
    CONF_FILTERS: "",
    CONF_MAX_RATE: 20,
}

# Fired on the HA event bus for every received frame (up to max_events_per_sec).
EVENT_FRAME = f"{DOMAIN}_frame"

SERVICE_SEND = "send"
ATTR_ENTRY = "config_entry_id"
