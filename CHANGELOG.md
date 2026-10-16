# Changelog

## 0.2.0 — 2026-10-16

An admin panel and services for watching and using the bus; much less written to the database.

- **Admin panel** ("WOOW CAN" in the sidebar, admins): health cards per interface (state, TEC / REC, bus load with peak and 1 / 5 / 15-minute averages, frame rates, controller events, drops, the last error frame in plain words, hints); a **per-ID monitor** (highlights that fade, cyan rising / red falling / grey-violet for counters, Notch to mask always-changing bits, filter, pin, binary view, phone layout) that turns into a **time-ordered trace** when paused; **sending** with an optional reply ID and a list of **periodic sends**; **recordings** to candump log files, buffer download, upload and offline viewing; the **activity log**.
- The panel's monitor gets a batch every 250 ms and acknowledges each one, so a slow viewer gets fewer updates instead of being disconnected.
- **Services for AI agents** (also the tools of the LLM API "WOOW CAN"): describe, list_interfaces, get_monitor, get_trace, get_activity, list_periodic, list_captures, send (now also by interface name and with `frame`), save_periodic, control_periodic, capture, clear_monitor. Input is checked in the handler, so REST callers get the reason instead of a bare "400: Bad Request". Sending and settings changes need an admin.
- **Events are opt-in**: a new option "IDs that fire events" (`123, 7E0/7F0, 100-1FF`, `*` = all) decides which received frames fire `woow_can_frame` and the event entity; empty by default, and it applies without restarting the interface. Interfaces from 0.1 keep firing for every frame (`*`).
- **Less database load**: the last-frame sensors update at most once a second, no longer carry a `time` attribute, keep their frame attributes out of the recorder, and are disabled by default for new interfaces. Frames beyond the event rate are still monitored, traced and recorded.
- **Virtual interfaces**: add a vcan interface from the config flow to try everything without hardware; it is re-created after a reboot and deleted with its entry.
- Frames carry the kernel's receive time; frames WOOW CAN sent come back once they are on the bus and show as "tx"; socket drops, controller statistics (error warning / passive / bus-off / restarts, bus errors where the controller reports them) and a bus load estimate (worst-case bit stuffing) are read.
- New interfaces start in listen-only mode. A `bus_load` sensor (disabled by default).
- Tests: unit tests for the monitor, the trace buffer, the candump log format, the bus load estimate, the event filter and periodic sends; `tools/sim/can_sim.py` simulates a Pylontech battery, an inverter, a J1939 engine and an OBD-II ECU on a vcan; `tools/can_live_check.py` checks a running Home Assistant end to end.

## 0.1.1 — 2026-10-16

- WOOWTECH brand images (`brand/`): Home Assistant 2026.x shows a custom integration's own icon and logo.

## 0.1.0 — 2026-10-16

First public release (split out of the former woow_bus integration).

- SocketCAN interfaces with bitrate, CAN FD, listen-only, restart-after-bus-off, receive filters and an events-per-second limit, configured over netlink.
- Entities: send frame (text), last received / sent frame, bus state, counters, received-frame event.
- Service `woow_can.send` (optionally waiting for a reply ID), event `woow_can_frame`.
