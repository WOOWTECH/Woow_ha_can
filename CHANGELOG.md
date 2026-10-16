# Changelog

## 0.1.1 — 2026-10-16

- WOOWTECH brand images (`brand/`): Home Assistant 2026.x shows a custom integration's own icon and logo.

## 0.1.0 — 2026-10-16

First public release (split out of the former woow_bus integration).

- SocketCAN interfaces with bitrate, CAN FD, listen-only, restart-after-bus-off, receive filters and an events-per-second limit, configured over netlink.
- Entities: send frame (text), last received / sent frame, bus state, counters, received-frame event.
- Service `woow_can.send` (optionally waiting for a reply ID), event `woow_can_frame`.
