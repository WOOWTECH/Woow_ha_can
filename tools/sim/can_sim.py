"""Traffic for a (virtual) CAN interface: a Pylontech battery, an inverter, a J1939 engine and an OBD-II ECU.

Stdlib only; run it where the interface is visible (on HAOS: inside the Core container):
    python3 can_sim.py vcan0 300

- Pylontech LV battery (setfirelabs capture values): 0x351 0x355 0x356 0x359 0x35C 0x35E once a second;
  the voltage's low byte wanders, a load switches on for 6 s of every 16 (current -25.3 A).
- Inverter: 0x305 once a second.
- 0x0C0 at 50 Hz with a rolling counter in byte 0 (what a counter looks like in the monitor).
- J1939 EEC1 (0x0CF00400) at 20 Hz: engine speed 1491.25-1500 rpm.
- OBD-II: answers 7DF 02 01 0C with 7E8 04 41 0C 1A F8 (1726 rpm), like an ECU would.
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
    0x355: bytes.fromhex("0E006400"),
    0x359: bytes.fromhex("000000000A504E"),
    0x35C: bytes.fromhex("C000"),
    0x35E: b"PYLON   ",
}
NOISE = [0, 1, 0, -1, 1, 0, -1, 0, 1, -1, 0, 1, 0, -1, 1, 0]


def frame(can_id: int, data: bytes) -> bytes:
    return struct.pack("=IB3x8s", can_id, len(data), data)


def main() -> None:
    ifname = sys.argv[1] if len(sys.argv) > 1 else "vcan0"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    sock.bind((ifname,))
    start = time.monotonic()
    next_1hz = next_50hz = next_20hz = start
    step = counter = sent = answered = 0
    while (now := time.monotonic()) - start < seconds:
        if now >= next_1hz:
            k = step % 16
            loaded = 3 <= k < 9
            volt = (0x12EE if loaded else 0x1302) + NOISE[k]
            amps = 0xFF03 if loaded else 0
            temp = 0x14A + (1 if 6 <= k < 12 else 0)
            soc = max(10, 14 - step // 16)
            for can_id, data in PYLON.items():
                if can_id == 0x355:
                    data = bytes([soc, 0, 0x64, 0])
                sock.send(frame(can_id, data))
            sock.send(frame(0x356, struct.pack("<HHH", volt, amps, temp)))
            sock.send(frame(0x305, bytes(8)))
            sent += 7
            step += 1
            next_1hz += 1.0
        if now >= next_50hz:
            counter = (counter + 1) & 0xFF
            sock.send(frame(0x0C0, bytes([counter, 0x10, 0x20, 0, 0, 0, 0, (counter * 7) & 0xFF])))
            sent += 1
            next_50hz += 0.02
        if now >= next_20hz:
            rpm = 0x2E9A if (step % 4) < 2 else 0x2EE0
            sock.send(frame(0x0CF00400 | EFF, bytes([0xF0, 0x7D, 0x7D, rpm & 0xFF, rpm >> 8, 0x00, 0xF0, 0x7D])))
            sent += 1
            next_20hz += 0.05
        wait = max(0.0, min(next_1hz, next_50hz, next_20hz) - time.monotonic())
        ready, _, _ = select.select([sock], [], [], wait)
        if ready:
            buf = sock.recv(16)
            raw, length = struct.unpack_from("=IB", buf)
            data = buf[8:8 + length]
            if raw == 0x7DF and data[:3] == b"\x02\x01\x0c":
                sock.send(frame(0x7E8, bytes.fromhex("04410C1AF8CCCCCC")))
                answered += 1
    print(f"sent {sent} frames, answered {answered} OBD requests in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
