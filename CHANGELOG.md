# Changelog

## 0.5.0 — 2026-10-17

Devices that ask their equipment and devices with outputs — both off until a person turns them on.

- **Polling**: a device can carry requests (a frame, a period, the message that answers it), sent only while polling is on for that device. One request per device waits for its reply at a time, a device sends at most `max_rate` a second and an interface at most 50; a request unanswered three times in a row slows down step by step to once a minute and recovers with the first reply; polling pauses while the interface is listen-only, down or bus-off. The panel shows each request's period, counts and state.
- **Writable signals**: switch, number, select and button entities, created only while writing is allowed for the device; command frames are built over the last frame sent (outputs sharing a byte keep their state, restored after a restart), numbers are range-checked, writes of one frame are at least 50 ms apart, and every write is in the activity log. Command messages (`send`) can carry fixed bytes (`data`), also built from template parameters.
- **Four new templates**: OBD-II live data (Service 01, 11 PIDs, 11- or 29-bit), Daly BMS (native CAN), CANopen I/O module (CiA 401: inputs, output switches, NMT start, analogue inputs by SDO) and CANopen drive monitor (CiA 402: state from the statusword, actual values by SDO; it never controls a drive). Each decodes the research's verified frames in the tests.
- Message filters accept a list of values (`{byte, values}`, e.g. SDO response codes); a `masked_lookup` derived value names states from bit masks (CiA 402).
- New services `control_device` and `write_signal`; the Devices tab has polling / writing switches with a confirmation, the request table and controls for writable signals; a device's status (receiving, silent, never seen) now updates live.
- The simulator plays an OBD-II car, a CiA 402 drive with an SDO server, a CiA 401 I/O node and a Daly BMS; tools/active_check.py checks them end to end. tools/esp holds an ESP32 (ESPHome) test node that plays the same equipment on a real bus.

## 0.4.0 — 2026-10-17

Finding unknown signals, and log files in the formats other tools use.

- **Analyze tab** (and services for agents): a **guided capture** that ranks what an action changes over alternating idle / action phases (bits that follow the action every time, bytes that change level, IDs only sent during the action; rolling counters recognised by their carry pattern and left out; robust to pressing Next a moment early or late); **find a signal by its value** like a memory scanner (bytes, words, nibbles and bits, both byte orders, signed and unsigned, common scalings and offsets; narrow by a new value or by increased / decreased / changed / unchanged); a **bit heat map** of one ID where two taps set a field and its decoded values show at once; **add to a device** turns a found field into an entity. The Monitor tab's ID details link to it.
- New services: `guided_capture`, `find_signal`, `bit_activity`, `add_signal`, `convert_capture`; `test_signal` takes a direction.
- **Log formats**: recordings and the buffer download as candump log, Vector ASC (CANalyzer, CANoe, python-can), SavvyCAN GVRET CSV or pcap (Wireshark); uploads of candump, ASC, CSV, PEAK TRC (1.0-2.1), OVMS CRTD and pcap open in the monitor. Conversions stream, so large files fit. Checked against python-can's ASC, TRC and candump readers and writers in CI.
- The simulator gains a body controller (door and light, "pressed" with 6F0#01 / 6F0#02); tools/analysis_check.py checks the formats and the analysis tools end to end.

## 0.3.1 — 2026-10-16

- The factor and offset fields of `test_signal` take any step (Home Assistant refuses number steps under 0.001, which failed hassfest). A test now checks every selector in services.yaml with Home Assistant's own schema. No change to how the integration works.

## 0.3.0 — 2026-10-16

Signals and devices: frames decoded into Home Assistant entities, from templates or DBC files.

- **Signal engine** without external packages: Intel and Motorola fields, signed, float, ASCII, factor / offset, value tables, simple and extended multiplexing, derived values (power from voltage x current, any-alarm summaries), "no data" rules of J1939, NMEA 2000 and SMA, J1939 BAM and NMEA 2000 fast-packet reassembly, J1939 DM1 decoding. Checked against cantools in CI.
- **DBC files**: import (panel or `import_dbc`), attach to interfaces to name and decode the monitor's rows, make devices from their messages; the report lists what was skipped. DBC export for devices.
- **Devices**: JSON definitions with an entity block on adopted signals; sensor and binary_sensor entities, each throttled (1 s for numbers, tolerance, timeout from the cycle time); J1939 / NMEA 2000 matching by PGN and source address; NMEA 2000 instance filters.
- **Five built-in templates** that only listen, each with sources, license, verification and confidence: low-voltage battery BMS (Pylontech / SMA / Victron 0x35x, groups detected from traffic), J1939 engine and vehicle, J1939 active faults (DM1), NMEA 2000 battery / DC status, CANopen node monitor. Local templates in the configuration directory's woow_can/templates.
- **Panel**: a Devices tab (template picker, DBC files, live values, entity toggles and settings, live charts); the monitor names rows after their message and decodes the opened row.
- **Services**: list_templates, create_from_template, list_devices, get_device, save_device, delete_device, set_signal, decode_frame, test_signal, import_dbc, list_databases, attach_dbc, create_from_dbc.
- tools/template_check.py checks every template on a live Home Assistant against the simulator, which now also plays a J1939 engine with DM1 (single frame and BAM), an NMEA 2000 battery (fast-packet) and a CANopen node that goes silent.

## 0.2.1 — 2026-10-16

- Service and message texts no longer contain angle brackets, which hassfest reads as HTML (the capture folder is named in words). No change to how the integration works.

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
