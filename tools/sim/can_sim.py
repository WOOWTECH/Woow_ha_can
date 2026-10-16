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
- OBD-II (Service 01, request 7DF): 7E8 answers PIDs 04 05 0C 0D 0F 11 2F 42 46 5E with the research's
  example values (1726 rpm, 50 km/h, 83 degC ...), 7E9 (gearbox) answers 0D too; PID 5C gets no answer.
- CANopen node 5 is also a CiA 402 drive: statusword on TPDO1 (0x185, every 200 ms; "operation enabled",
  "fault" while its emergency is active) and an SDO server (0x605 / 0x585) for 6041, 6061 (3 = profile
  velocity), 6064 (position, counting), 606C (1500 rpm), 6077 (50.0 %), 603F, 1000; other objects abort.
- CANopen node 7, a CiA 401 I/O module: boot-up, then heartbeat; inputs on TPDO1 (0x187) only while
  operational (NMT 000#01 07 or 000#01 00), DI0 toggling every 4 s and DI8-15 wired to DO0-7 (RPDO1 0x207);
  analogue inputs by SDO (0x607 / 0x587, 6401:01-04 = 16383, -16383, a ramp, 0).
- Daly BMS (29-bit, BMS 01 / host 40): answers 0x18<id>0140 with 0x18<id>4001 for 90 (52.5 V, +11.0 A,
  85.0 %), 91, 92, 93 and 98.
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


OBD = {  # PID -> data bytes A (B), the research's example values
    0x04: b"\x80", 0x05: b"\x7B", 0x0C: b"\x1A\xF8", 0x0D: b"\x32", 0x0F: b"\x46", 0x11: b"\x33",
    0x2F: b"\xC0", 0x42: b"\x36\xB0", 0x46: b"\x41", 0x5E: b"\x00\xFA",
}
DALY = {  # data id -> reply data (big endian)
    0x90: bytes.fromhex("020D020D759E0352"), 0x91: bytes.fromhex("0D16030CEE070000"),
    0x92: bytes.fromhex("41013F0400000000"), 0x93: bytes.fromhex("0201016400 0186A0".replace(" ", "")),
    0x98: bytes(8),
}


def sdo_value(cmd: int, index: int, sub: int, value: int, size: int) -> bytes:
    return bytes([cmd, index & 0xFF, index >> 8, sub]) + (value & ((1 << (8 * size)) - 1)).to_bytes(4, "little")


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
    next_body = next_402 = next_401 = start
    step = counter = sent = answered = n2k_seq = body_counter = body = 0
    io_operational, io_do, io_booted = False, 0, False
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
        if now >= next_402:  # CiA 402 statusword on TPDO1 of node 5
            fault = 20 <= elapsed % 60 < 30
            send(0x185, (0x0008 if fault else 0x0237).to_bytes(2, "little"))
            next_402 += 0.2
        if now >= next_401:  # CiA 401 node 7: boot-up, heartbeat, inputs while operational
            if not io_booted:
                send(0x707, b"\x00")
                io_booted = True
            elif int(elapsed * 2) % 2 == 0:
                send(0x707, b"\x05" if io_operational else b"\x7f")
            if io_operational:
                send(0x187, bytes([0x01 if int(elapsed / 4) % 2 else 0x00, io_do & 0xFF]))
            next_401 += 0.5
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
        wait = max(0.0, min([next_1hz, next_50hz, next_20hz, next_10hz, next_2hz, next_n2k, next_body, next_402,
                             next_401]
                            + [d for d, _ in queue]) - time.monotonic())
        ready, _, _ = select.select([sock], [], [], wait)
        if ready:
            buf = sock.recv(16)
            raw, length = struct.unpack_from("=IB", buf)
            data = buf[8:8 + length]
            if raw == 0x7DF and len(data) >= 3 and data[:2] == b"\x02\x01":
                pid = data[2]
                if pid in OBD:
                    value = OBD[pid]
                    send(0x7E8, (bytes([2 + len(value), 0x41, pid]) + value).ljust(8, b"\xcc"))
                    answered += 1
                    if pid == 0x0D:  # the gearbox answers the vehicle speed too
                        send(0x7E9, (bytes([3, 0x41, pid]) + value).ljust(8, b"\xaa"))
            elif raw == 0x6F0 and data:
                body = data[0] & 3
            elif raw == 0x000 and len(data) >= 2 and data[1] in (0, 7):  # NMT for node 7
                if data[0] == 0x01:
                    io_operational = True
                elif data[0] in (0x02, 0x80):
                    io_operational = False
            elif raw == 0x207 and data:
                io_do = data[0] | (data[1] << 8 if len(data) > 1 else 0)
            elif raw == 0x605 and len(data) >= 4 and data[0] == 0x40:  # SDO read, node 5 (CiA 402)
                index, sub = data[1] | data[2] << 8, data[3]
                fault = 20 <= elapsed % 60 < 30
                objects = {(0x6041, 0): (0x4B, 0x0008 if fault else 0x0237, 2), (0x6061, 0): (0x4F, 3, 1),
                           (0x6064, 0): (0x43, int(elapsed * 1000), 4), (0x606C, 0): (0x43, 1500, 4),
                           (0x6077, 0): (0x4B, 500, 2), (0x603F, 0): (0x4B, 0x8130 if fault else 0, 2),
                           (0x1000, 0): (0x43, 0x00020192, 4)}
                if (index, sub) in objects:
                    cmd, value, size = objects[(index, sub)]
                    send(0x585, sdo_value(cmd, index, sub, value, size))
                else:
                    send(0x585, bytes([0x80, data[1], data[2], sub]) + (0x06020000).to_bytes(4, "little"))
            elif raw == 0x607 and len(data) >= 4 and data[0] == 0x40:  # SDO read, node 7 (CiA 401)
                index, sub = data[1] | data[2] << 8, data[3]
                analog = {1: 16383, 2: -16383, 3: int(elapsed * 100) % 32768, 4: 0}
                if index == 0x6401 and sub in analog:
                    send(0x587, sdo_value(0x4B, index, sub, analog[sub], 2))
                else:
                    send(0x587, bytes([0x80, data[1], data[2], sub]) + (0x06020000).to_bytes(4, "little"))
            elif raw & EFF and (raw & 0x1F00FFFF) == 0x18000140:  # Daly request: 18 <id> 01 (BMS) 40 (host)
                data_id = (raw >> 16) & 0xFF
                if data_id in DALY:
                    send(EFF | 0x18004001 | data_id << 16, DALY[data_id])
    print(f"sent {sent} frames, answered {answered} OBD requests in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
