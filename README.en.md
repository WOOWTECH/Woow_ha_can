# WOOW CAN

[中文](README.md)

Brings Linux SocketCAN interfaces (CAN / CAN FD) into Home Assistant: one device per interface, plus an admin panel to watch the whole bus per ID, check bus health, send and repeat frames, and record log files. Whatever the panel does, an AI agent can do through services, and it is written to the activity log. No extra packages to install.

For RS485 / RS232 use [WOOW Serial](https://github.com/WOOWTECH/Woow_ha_serial).

## Admin panel

"WOOW CAN" in the sidebar (admins), with seven tabs:

| Tab | What it shows |
|---|---|
| Overview | A health card per interface: state (normal / error warning / error passive / bus off), TEC / REC, bus load (now, peak, 1 / 5 / 15 min, with a sparkline of the last minutes), frame rates, controller events, drops, the last error frame in plain words, and hints such as "nothing acknowledges" |
| Monitor | One row per ID, like cansniffer or SavvyCAN: a changed byte lights up and fades, cyan rising, red falling, grey-violet for bytes that keep jumping (counters, checksums); Notch masks the bits that always change, so only what you operate lights up; filter, pin, binary view. Paused, it shows the frames in time order and pages back through them. On a phone each ID is a card |
| Analyze | Find unknown signals: a guided capture (which bits an action changes), finding a signal by its value, a bit heat map of one ID; a found field becomes an entity in one step (see "Finding unknown signals") |
| Devices | Templates, DBC files, live values, entity settings and charts (see "Devices, templates and DBC files") |
| Send | One frame in cansend notation (optionally waiting for a reply ID); a list of periodic sends (period, count, start / stop). The first send on an interface asks for confirmation |
| Recordings | Record an interface to a candump log; download the buffer (the last 200,000 frames) as candump, Vector ASC, SavvyCAN CSV or pcap (Wireshark); upload a log (candump, ASC, CSV, PEAK TRC, OVMS CRTD, pcap) and open it in the same monitor views; convert recordings to the other formats |
| Activity | Sends and changes by AI agents (services) and people (panel), with the user and the note |

The panel gets a batch every 250 ms and must acknowledge each one before the next is sent, so on a busy bus a phone just updates less often instead of being disconnected by Home Assistant.

## Devices, templates and DBC files

The Devices tab decodes frames into values; chosen signals become Home Assistant entities (sensors and binary sensors; switches, numbers, selects and buttons on devices that allow writing):

- **Built-in templates** (each names its sources, license, what it was checked against and its confidence; the first five only listen, the last four ask their equipment or have outputs, see "Polling and writing"):

| Template | For | Main entities |
|---|---|---|
| Low-voltage battery BMS (0x35x) | Pylontech, BYD LVS, Seplos, REC, JK in Pylon mode and most 48 V batteries, with SMA, Victron, Deye, Sofar or GoodWe inverters | State of charge and health, voltage, current, power, temperature, charge / discharge limits, protections and alarms, charge / discharge allowed; SMA alarms and Victron cell extremes / energy are added when their frames are seen |
| J1939 engine and vehicle | Trucks, buses, generator sets, farm and marine diesel engines | Engine speed, torque, vehicle speed, coolant / oil / fuel temperatures, oil pressure and level, fuel rate and economy, throttle, battery voltage, engine hours |
| J1939 active faults (DM1) | The same, including multi-frame BAM | Four lamps, number of faults, fault codes (SPN / FMI) |
| NMEA 2000 battery / DC status | Victron VE.Can (Lynx Shunt, MPPT), boats, campers | Voltage, current, power, temperature, state of charge and health, time remaining |
| CANopen node monitor | Any CiA 301 device | Online / offline (off when the heartbeat stops), NMT state, emergency error code |
| OBD-II live data (Service 01, polling) | Cars and light vans (OBD-II socket) | Engine speed, vehicle speed, coolant / intake / oil temperature, fuel level, module voltage, load, throttle, fuel rate |
| Daly BMS (native CAN, polling) | Daly smart BMS | Pack voltage, current, power, state of charge, highest / lowest cell and their difference, temperatures, charge / discharge MOS, remaining capacity, faults |
| CANopen I/O module (CiA 401) | ICP DAS CAN-2053C / 2057C / 2017C and similar | 16 digital inputs, 16 output switches (once writing is allowed), an NMT start button, 4 analogue inputs (SDO polling) |
| CANopen drive monitor (CiA 402) | Servo, stepper and frequency drives (maxon EPOS4 ...) | Drive state, fault, warning; polled actual position, velocity, torque, operating mode, error code. Read only: it never enables a drive |

- **DBC files**: attached to an interface they name and decode the monitor's rows; make a device from some of their messages. The reader covers what matters (messages, signals, Intel / Motorola, signed, float, value tables, comments, cycle times, multiplexing, J1939 PGNs) and lists what it skipped.
- **Each entity is throttled on its own**: numbers at most once a second, changes under half a resolution step are not written; silent for longer than max(3 cycles, 5 s) the entity turns unavailable. Tune it in the panel or with `set_signal`.
- Every numeric signal can be charted live.
- Decoding needs no external package; it is tested against the verified real and example frames from the research, and compared with cantools in CI.

## Polling and writing

Some equipment answers only when asked (OBD-II cars, Daly BMS, CANopen SDO), some has outputs (relays, set points). Both are **off by default** and turned on per device in the Devices tab (after a confirmation), or by an agent with `control_device`:

- **Polling** asks with the template's requests, politely: one request of a device waits for its reply at a time, a device sends at most `max_rate` a second (OBD-II about 6.7 in all), an interface at most 50; a request unanswered three times in a row slows down step by step to once a minute (an engine switched off, a PID the car does not have) and recovers with the first reply. Polling pauses while the interface is listen-only, down or bus-off. The panel lists each request's period, counts and state.
- **Allow writing** creates the switch, number, select and button entities and accepts `write_signal`. Outputs that share a frame (eight relays in one byte) are written over the last frame sent, so only the one changed moves; after Home Assistant restarts, the outputs' last states are restored first. Numbers are checked against their range; two writes of one frame are at least 50 ms apart.
- Every write goes to the activity log (who, what). Only one master per piece of equipment: leave both off where a PLC already polls or controls it.

## Finding unknown signals

For equipment without a DBC file or a template, the Analyze tab finds where the signals are (on the source picked on the Monitor tab):

- **Guided capture**: press Start and leave the equipment idle, press Next and do the action (open the door, press the button, switch the light on) and hold it, press Next and undo it; repeat two or three times, then Finish. The IDs are ranked by what differs: bits that follow the action every time (switches, lamps), bytes that change level, IDs only sent during the action. Rolling counters are recognised and left out, and pressing Next a moment before or after acting does not matter.
- **Find a signal by its value**: start with a value read off the equipment's display (say 52.3 V), let it change, enter the new value and narrow; repeat until one or two fields are left. It tries bytes, words, nibbles and bits in both byte orders, signed and unsigned, with the usual scalings and offsets (0.1, 0.01, −40, −273 ...). Without a known value, narrow by "increased / decreased / changed / unchanged".
- **Bits of one ID**: a heat map of how often each bit changes; tap two bits to set a field and see its decoded values at once.
- **Add to a device** turns a found field into an entity (1-bit fields are binary sensors, others sensors), in an existing device or a new one.
- Every ID's details on the Monitor tab link here ("Bits & analysis").

## Interface settings

- Finds the host's CAN interfaces (MCP2515, MCP2518FD, …).
- Bitrate, CAN FD and data bitrate (on capable controllers), listen-only (on by default for new interfaces), restart after bus-off, receive filter (`123, 7E0/7F0, 18FF50E5`).
  - HAOS's `ip` cannot set CAN bit timing; the integration does it over netlink.
- **IDs that fire events**: only these IDs fire `woow_can_frame` events and the event entity, e.g. `123, 7E0/7F0, 100-1FF`; `*` = all; empty = none (the default). Changing it applies at once, without restarting the interface.
- **Virtual interface (vcan)**: choose "Virtual interface" when adding the integration to try the panel, automations and agents without hardware; it is re-created after the host restarts.

## Entities

| Entity | Purpose |
|---|---|
| `text.<interface>_send_frame` | Type a frame to send it, cansend notation: `123#11223344`, `18FF50E5#0102`, `123#R`, `456##1AABB` (CAN FD) |
| `sensor.<interface>_bus_state` | Error active, error warning, error passive, bus off, stopped, virtual |
| `event.<interface>_rx_frame` | Fires for the IDs that fire events |
| `sensor.<interface>_last_frame` / `_last_sent_frame` | Last received / sent frame, at most one update a second. Disabled by default for new interfaces |
| `sensor.<interface>_bus_load` | Bus load (one-minute average). Disabled by default |
| Frame counters, bus errors | Diagnostics |

## Services (for AI agents too)

| Service | Purpose |
|---|---|
| `describe`, `list_interfaces` | What the integration does; each interface's state, load and error counters |
| `get_monitor` | Per-ID summary: count, rate, period, latest data, number of data changes |
| `get_trace` | Frames in time order, newest first; filter by IDs, direction or the last seconds |
| `get_activity`, `list_periodic`, `list_captures` | Activity log, periodic sends, recordings |
| `send` | Send a frame, optionally waiting for a reply (`wait_id`, `wait_ms`); `frame: 7DF#02010C` or `can_id` with `data` |
| `save_periodic`, `control_periodic` | Add or change a periodic send; start, stop, delete |
| `capture`, `convert_capture` | Start or stop a recording; write a recording as ASC, CSV or pcap |
| `clear_monitor` | Start an interface's monitor statistics over |
| `list_templates`, `create_from_template` | Templates; make a device from one (groups detected from traffic unless given) |
| `list_devices`, `get_device`, `save_device`, `delete_device` | Devices with current values and full definitions; create or change one from JSON; delete |
| `set_signal` | Make a signal an entity or drop it; minimum interval, tolerance, timeout |
| `control_device`, `write_signal` | Turn a device's polling and writing on / off; write one signal (an output, a set point, a command) |
| `decode_frame`, `test_signal` | Decode one frame with the interface's definitions; try a bit field on recent frames (where is the value?) |
| `guided_capture`, `find_signal`, `bit_activity`, `add_signal` | Find unknown signals: guided capture, find by value, bit activity; put a found field into a device |
| `import_dbc`, `list_databases`, `attach_dbc`, `create_from_dbc` | Import a DBC file, attach it, make a device from it |

- Interfaces can be named by config entry id, name (CAN0) or interface (can0).
- Sending and changing settings need an admin user; reading does not. Every send and change goes to the activity log; `note` says why.
- Home Assistant's own MCP server: the same services are the tools of the LLM API "WOOW CAN". Guidance for agents: [llms.txt](llms.txt).

## Requirements

- Home Assistant 2026.10 or newer, and a host with SocketCAN interfaces (e.g. a Raspberry Pi 5 with a CAN HAT enabled in HAOS's `config.txt`). Without hardware, use a virtual interface.

## Installation

**HACS**: add `https://github.com/WOOWTECH/Woow_ha_can` as a custom repository (category Integration), download, restart.

**Manual**: copy `custom_components/woow_can` into `custom_components/` and restart.

Then Settings → Devices & services → Add integration → WOOW CAN → "CAN interface on this host", and set the bitrate. The "Admin panel" entry is added automatically the first time.

## Examples

Run an automation when ID 18FF50E5 arrives (first put `18FF50E5` in the interface's "IDs that fire events"):

```yaml
triggers:
  - trigger: event
    event_type: woow_can_frame
    event_data:
      name: CAN0
      id_hex: "18FF50E5"
```

Send an OBD-II request and wait for the answer:

```yaml
action: woow_can.send
data:
  interface: CAN0
  frame: "7DF#02010C"
  wait_id: "7E8"
  wait_ms: 500
response_variable: r   # r.reply.data
```

A heartbeat every second, stopping after 60 sends:

```yaml
action: woow_can.save_periodic
data:
  interface: CAN0
  name: Heartbeat
  frame: "305#0000000000000000"
  period_ms: 1000
  count: 60
  start: true
```

## Database and performance

- The monitor, the trace and the load estimate live in memory; nothing goes to the database or through Home Assistant's event bus.
- Only the IDs that fire events produce events, and every event is written to the history database. To just watch in the panel, leave the list empty.
- To fire events for a busy ID, keep them out of the recorder:

```yaml
recorder:
  exclude:
    event_types:
      - woow_can_frame
```

- A full 500 kbit/s bus carries about 3,100–4,500 frames/s per interface; each frame costs a fixed, small amount of work.

## Notes

- With no other node on the bus, nobody acknowledges a sent frame: the state goes error passive and the controller keeps retrying. Reload the interface to clear it.
- Terminate both ends of the bus with 120 Ω; every node must use the same bitrate.
- Listen-only never acknowledges. If the only other node on the bus needs this host's acknowledgement, turn listen-only off.
- The MCP2515 has two receive buffers and loses frames on a busy bus (the overview shows controller overflows); it does not report bus errors either ("not reported by this controller").
- Periodic sends are stopped after Home Assistant restarts: a reboot never starts transmitting on its own.

## Upgrading from 0.1

- Existing interfaces get `*` as "IDs that fire events", so every frame still fires an event (up to 20 a second). Narrow it, or clear it, to write less to the database.
- The last-frame sensors no longer carry a `time` attribute, their attributes are not recorded, and they update at most once a second.

## Development

```bash
pip install homeassistant==2026.10.1 pytest && pytest tests
cd frontend && npm install && npm run build   # the panel (Lit), built into custom_components/woow_can/frontend
```

- `tools/check_can.py`: hardware check, including the controller's internal loopback.
- `tools/sim/can_sim.py`: a Pylontech battery, an inverter, a J1939 engine, NMEA 2000, a CANopen node, an OBD-II ECU and a body controller operated with `6F0#01` (door) and `6F0#02` (light), on a virtual interface.
- `tools/can_live_check.py`: end-to-end check against a running Home Assistant, from the SSH add-on (services, panel websocket, periodic sends, events, recordings).
- `tools/template_check.py`: every template against the simulator, live.
- `tools/analysis_check.py`: the file formats and analysis tools end to end (conversions, an uploaded ASC, finding the battery voltage, the door bit by guided capture, adding to a device).
- `tools/active_check.py`: devices that send, end to end (OBD-II, Daly and CiA 402 polling; CiA 401 NMT start, output switches looped back to inputs, analogue inputs; nothing sent once off).
- `tools/esp/`: an ESP32 test node (ESPHome) that plays the simulator's equipment on a real bus, so the checks above can run against hardware.

## License

MIT
