"""Constants for WOOW CAN."""

DOMAIN = "woow_can"

CONF_KIND = "kind"
KIND_CAN = "can"  # one SocketCAN interface (can0, can1, vcan0 ...)
KIND_HUB = "hub"  # the admin layer: panel, monitor feed, periodic sends, captures (one per Home Assistant)

CONF_PORT = "port"  # the interface name (can0, can1, ...)
CONF_VIRTUAL = "virtual"  # a vcan interface this integration created (re-created after a reboot)

CONF_BITRATE = "bitrate"
CONF_FD = "fd"
CONF_DBITRATE = "dbitrate"
CONF_LISTEN_ONLY = "listen_only"
CONF_RESTART_MS = "restart_ms"
CONF_FILTERS = "filters"
CONF_EVENT_FILTER = "event_filter"
CONF_MAX_RATE = "max_events_per_sec"

BITRATES = [10000, 20000, 50000, 100000, 125000, 250000, 500000, 800000, 1000000]
DBITRATES = [1000000, 2000000, 4000000, 5000000, 8000000]

CAN_DEFAULTS = {
    CONF_BITRATE: 500000,
    CONF_FD: False,
    CONF_DBITRATE: 2000000,
    CONF_LISTEN_ONLY: True,  # new interfaces only watch the bus; sending is a deliberate choice
    CONF_RESTART_MS: 100,
    CONF_FILTERS: "",
    CONF_EVENT_FILTER: "",  # no woow_can_frame events unless IDs are chosen ("*" = every frame)
    CONF_MAX_RATE: 20,
}
# Options that apply without restarting the interface.
LIVE_OPTIONS = {CONF_EVENT_FILTER, CONF_MAX_RATE}

# Fired on the HA event bus for frames whose ID matches the interface's event filter (up to max_events_per_sec).
EVENT_FRAME = f"{DOMAIN}_frame"

SERVICE_SEND = "send"
ATTR_ENTRY = "config_entry_id"

# Admin panel
PANEL_URL = "woow-can"
PANEL_ICON = "mdi:transit-connection-horizontal"
PANEL_ELEMENT = "woow-can-panel"
PANEL_FILE = "woow-can-panel.js"
PANEL_STATIC = "/woow_can_static"

# Monitor, trace and pushes to the panel
MONITOR_PUSH = 0.25  # s between monitor batches
MONITOR_UNACKED = 2  # batches a viewer may have unacknowledged before the next one waits
MONITOR_MAX_IDS = 4096  # distinct (ID, direction) rows per interface; beyond that frames are only counted
TRACE_CAPACITY = 200_000  # frames kept per interface for the time-ordered view and exports
TRACE_PAGE = 200  # frames per trace page
STATUS_SLOW = 10.0  # s between interface status reads
STATUS_FAST = 1.0  # ... while the panel shows the health cards
ENTITY_MIN_INTERVAL = 1.0  # s between updates of the last-frame sensors
LIVE_PUSH = 0.3  # s between activity / list pushes to the panel

# Periodic sends
PERIODIC_MIN_MS = 10
PERIODIC_MAX_ITEMS = 64

# Captures (recordings to files under <config>/woow_can/captures)
CAPTURE_DIR = "woow_can/captures"
CAPTURE_MAX_BYTES = 200 * 1024 * 1024
CAPTURE_FLUSH = 1.0  # s between writes
