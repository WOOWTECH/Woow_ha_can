"""Traffic for a (virtual) CAN interface: the equipment the built-in templates are for.

Stdlib only; run it where the interface is visible (on HAOS: inside the Core container):
    python3 can_sim.py vcan0 300

All values come from the research's verified example frames, so a check can compare entity states
with known numbers:
- Pylontech LV battery (setfirelabs capture): 0x351 0x355 0x356 0x359 0x35C 0x35E once a second; the
  voltage's low byte wanders and a load switches on for 6 s of every 16 (current -25.3 A); Victron / BYD
  extensions 0x373 0x378 0x379 (BYD capture); inverter 0x305 (zeros, as Pylon inverters send).
- 0x0C0 at 50 Hz with a rolling counter in byte 0.
- J1939 engine, source address 00: EEC1 20 Hz (1491.25 / 1500 rpm), CCVS1 10 Hz (80 km/h), ET1, EFL/P1,
  LFE1, VEP1, HOURS (FMS / Hatz examples). DM1 every second: 8 s one fault in a single frame (SPN 100
  FMI 1), then 8 s two faults over a BAM transfer (adds SPN 110 FMI 0).
- NMEA 2000, source address 23, instance 0: PGN 127508 (26.72 V, 6.7 A, 16.62 degC) and PGN 127506 as a
  fast-packet (SOC 87 %, SOH 95 %, 600 min, 0.165 V), every 1.5 s.
- CANopen node 5: heartbeat (operational) every second, silent for 10 s of every 60 (s 40-50); an
  emergency 0x8130 at s 20 of every 60, cleared (0000) at s 30.
- OBD-II: answers 7DF 02 01 0C with 7E8 04 41 0C 1A F8 (1726 rpm).
- A body controller for the reverse engineering tools: 0x3C0 at 10 Hz, byte 0 bit 2 = door open, bit 5 =
  light on, byte 1 a rolling counter, bytes 2-3 cabin temperature 21.5 degC (0.1 degC, little endian), byte 4
  the light level (0, or 80 while the light is on). "Pressing" happens over the bus: 6F0#xx sets the door
  (bit 0) and the light (bit 1), as a test cannot open a real door.
"""

from __future__ import annotations

import select
import socket
import struct
import sys
import time

EFF = 0x80000000
PYLON = {
    0x351: bytes.fromhex("1402740E740ECC01"),
    0x359: bytes.fromhex("000000000A504E"),
    0x35C: bytes.fromhex("C000"),
    0x35E: b"PYLON   ",
    0x373: bytes.fromhex("EA0C010D1F012201"),
    0x378: bytes.fromhex("400800002B070000"),
    0x379: bytes.fromhex("9C00000000000000"),
    0x305: bytes(8),
}
NOISE = [0, 1, 0, -1, 1, 0, -1, 0, 1, -1, 0, 1, 0, -1, 1, 0]
J1939 = {  # (priority, PGN) -> data; source address 00
    (6, 65265): bytes.fromhex("F7005014FF5AE0FF"),  # CCVS1: 80 km/h, brake on
    (6, 65262): bytes.fromhex("7D46002EFFFFFFFF"),  # ET1: 85 / 30 / 95 degC
    (6, 65263): bytes.fromhex("FFFFD764FFFF32FA"),  # EFL/P1: oil 86 %, 400 kPa, coolant 100 %
    (6, 65266): bytes.fromhex("FA00000600 0564FF".replace(" ", "")),  # LFE1: 12.5 L/h, 3 km/L, 40 %
    (6, 65271): bytes.fromhex("8214340 22D022802".replace(" ", "")),  # VEP1: 27.85 V
    (6, 65253): bytes.fromhex("72600000 79CC0000".replace(" ", "")),  # HOURS: 1234.5 h
}


def frame(can_id: int, data: bytes) -> bytes:
    return struct.pack("=IB3x8s", can_id, len(data), data)


def j1939_id(priority: int, pgn: int, sa: int, da: int = 0xFF) -> int:
    pf = (pgn >> 8) & 0xFF
    if pf < 240:
        pgn = (pgn & 0x3FF00) | da
    return EFF | (priority << 26) | (pgn << 8) | sa


def fast_packet(payload: bytes, seq: int) -> list[bytes]:
    """NMEA 2000 fast-packet frames of one message."""
    frames = [bytes([(seq << 5) | 0, len(payload)]) + payload[:6]]
    rest, index = payload[6:], 1
    while rest:
        frames.append(bytes([(seq << 5) | index]) + rest[:7])
        rest, index = rest[7:], index + 1
    return [f.ljust(8, b"\xff") for f in frames]


def main() -> None:
    ifname = sys.argv[1] if len(sys.argv) > 1 else "vcan0"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    sock.bind((ifname,))
    start = time.monotonic()
    next_1hz = next_50hz = next_20hz = next_10hz = next_2hz = next_n2k = start
    next_body = start
    step = counter = sent = answered = n2k_seq = body_counter = body = 0
    queue: list[tuple[float, bytes]] = []  # BAM data packets, 50 ms apart

    def send(can_id: int, data: bytes) -> None:
        nonlocal sent
        sock.send(frame(can_id, data))
        sent += 1

    while (now := time.monotonic()) - start < seconds:
        elapsed = now - start
        if now >= next_1hz:
            k = step % 16
            loaded = 3 <= k < 9
            volt = (0x12EE if loaded else 0x1302) + NOISE[k]
            amps = 0xFF03 if loaded else 0
            temp = 0x14A + (1 if 6 <= k < 12 else 0)
            soc = max(10, 14 - step // 16)
            for can_id, data in PYLON.items():
                send(can_id, data)
            send(0x355, bytes([soc, 0, 0x64, 0]))
            send(0x356, struct.pack("<HHH", volt, amps, temp))
            for (prio, pgn), data in J1939.items():
                if pgn in (65262, 65271, 65253):
                    send(j1939_id(prio, pgn, 0x00), data)
            # DM1: one fault in a single frame, or two over BAM
            if (step // 8) % 2 == 0:
                send(j1939_id(6, 65226, 0x00), bytes.fromhex("04FF64000103FFFF"))
            else:
                send(j1939_id(7, 60416, 0x00), bytes.fromhex("200A0002FFCAFE00"))
                queue.append((now + 0.05, bytes.fromhex("0114FF640001036E")))
                queue.append((now + 0.10, bytes.fromhex("02000001FFFFFFFF")))
            # CANopen node 5
            cycle = elapsed % 60
            if not 40 <= cycle < 50:
                send(0x705, b"\x05")
            if 20 <= cycle < 21:
                send(0x085, bytes.fromhex("3081110700000000"))
            if 30 <= cycle < 31:
                send(0x085, bytes(8))
            step += 1
            next_1hz += 1.0
        for due, data in list(queue):
            if now >= due:
                send(j1939_id(7, 60160, 0x00), data)
                queue.remove((due, data))
        if now >= next_50hz:
            counter = (counter + 1) & 0xFF
            send(0x0C0, bytes([counter, 0x10, 0x20, 0, 0, 0, 0, (counter * 7) & 0xFF]))
            next_50hz += 0.02
        if now >= next_20hz:
            rpm = 0x2E9A if (step % 4) < 2 else 0x2EE0
            send(j1939_id(3, 61444, 0x00), bytes([0xF0, 0x7D, 0x7D, rpm & 0xFF, rpm >> 8, 0x00, 0xF0, 0x7D]))
            next_20hz += 0.05
        if now >= next_10hz:
            for (prio, pgn), data in J1939.items():
                if pgn in (65265, 65266):
                    send(j1939_id(prio, pgn, 0x00), data)
            next_10hz += 0.1
        if now >= next_body:
            body_counter = (body_counter + 1) & 0xFF
            light = bool(body & 2)
            send(0x3C0, bytes([(0x04 if body & 1 else 0) | (0x20 if light else 0), body_counter, 0xD7, 0x00,
                               80 if light else 0, 0, 0, 0]))
            next_body += 0.1
        if now >= next_2hz:
            send(j1939_id(6, 65263, 0x00), J1939[(6, 65263)])
            next_2hz += 0.5
        if now >= next_n2k:
            send(j1939_id(6, 127508, 0x23), bytes.fromhex("00700A43003171FF"))
            detailed = bytes([0x52, 0x00, 0x00, 87, 95]) + struct.pack("<HH", 600, 165) + struct.pack("<H", 0xFFFF)
            for data in fast_packet(detailed, n2k_seq):
                send(j1939_id(6, 127506, 0x23), data)
            n2k_seq = (n2k_seq + 1) & 7
            next_n2k += 1.5
        wait = max(0.0, min([next_1hz, next_50hz, next_20hz, next_10hz, next_2hz, next_n2k, next_body]
                            + [d for d, _ in queue]) - time.monotonic())
        ready, _, _ = select.select([sock], [], [], wait)
        if ready:
            buf = sock.recv(16)
            raw, length = struct.unpack_from("=IB", buf)
            data = buf[8:8 + length]
            if raw == 0x7DF and data[:3] == b"\x02\x01\x0c":
                send(0x7E8, bytes.fromhex("04410C1AF8CCCCCC"))
                answered += 1
            elif raw == 0x6F0 and data:
                body = data[0] & 3
    print(f"sent {sent} frames, answered {answered} OBD requests in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
