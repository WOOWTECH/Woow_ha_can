# WOOW CAN

[繁體中文](README.md)

Brings Linux SocketCAN interfaces (CAN / CAN FD) into Home Assistant: one device per interface to send and receive frames and watch the bus state, with received frames available as automation triggers. No extra packages.

For RS485 / RS232, use [WOOW Serial](https://github.com/WOOWTECH/Woow_ha_serial).

## Features

- Finds the host's CAN interfaces (MCP2515, MCP2518FD, ...).
- Interface settings: bitrate, CAN FD and data bitrate (on FD-capable controllers), listen-only, restart after bus-off, receive filter (`123, 7E0/7F0, 18FF50E5`), max events per second.
  - HAOS's `ip` cannot set CAN bitrates, so this integration sets them over netlink itself.
- Entities per interface:

| Entity | Purpose |
|---|---|
| `text.<if>_send_frame` | Type a frame in cansend notation and it is sent: `123#11223344`, `18FF50E5#0102`, `123#R`, `456##1AABB` (CAN FD) |
| `sensor.<if>_last_frame` / `_last_sent_frame` | Last received / sent frame; ID, data and length in the attributes |
| `sensor.<if>_bus_state` | Error active, error warning, error passive, bus off, stopped |
| `event.<if>_rx_frame` | Fires once per received frame |
| Frame counters, bus errors | Diagnostics |

- Service `woow_can.send`: send one frame, optionally waiting for a reply ID (`wait_id`, `wait_ms`); the reply comes back in the service response.
- Event `woow_can_frame` for every received frame, with `name`, `interface`, `id`, `id_hex`, `data`, `length`, `extended`, `fd`, `brs`, `rtr`.

## Requirements

- Home Assistant 2026.10 or later on a host with SocketCAN interfaces (e.g. a Raspberry Pi 5 with a CAN HAT enabled in HAOS's `config.txt`).

## Installation

**HACS**: add `https://github.com/WOOWTECH/Woow_ha_can` as a custom repository (category Integration), download, restart.

**Manual**: copy `custom_components/woow_can` into `custom_components/` and restart.

Then Settings → Devices & services → Add integration → WOOW CAN, pick the interface and set the bitrate.

## Examples

```yaml
triggers:
  - trigger: event
    event_type: woow_can_frame
    event_data:
      name: CAN0
      id_hex: "18FF50E5"
```

```yaml
action: woow_can.send
data:
  config_entry_id: <the interface>
  can_id: "7DF"
  data: "02 01 0C"
  wait_id: "7E8"
  wait_ms: 500
response_variable: r   # r.reply.data
```

## Notes

- With no other node on the bus, nothing acknowledges a frame: the controller keeps retransmitting and goes error passive. Reloading the interface clears it.
- Terminate both ends of the bus with 120 Ω and use one bitrate on every node.
- On busy buses, use the receive filter and the events-per-second limit; frames beyond it are only counted.

## Development

```bash
pip install homeassistant==2026.10.1 pytest && pytest tests
```

`tools/check_can.py` is the on-device check, including a controller loopback test.

## License

MIT
