# WOOW CAN test node (ESP32 + CAN transceiver)

[`woow_can_test_node.yaml`](woow_can_test_node.yaml) turns an ESP32 into the equipment the simulator plays, on a real bus, so the end-to-end checks can run against hardware:

| Frames | What it does |
|---|---|
| 0x3C0, every 100 ms | body controller: byte 0 bit 2 door, bit 5 light, byte 1 counter, bytes 2–3 21.5 °C, byte 4 light level; `6F0#01` / `6F0#02` set door / light, the BOOT button opens the door |
| 0x356, every second | battery voltage (0.01 V, little endian), wandering between 48.65 and 48.67 V |
| 7DF → 7E8 | OBD-II Service 01 for PIDs 05, 0C, 0D; engine speed comes from Home Assistant; other PIDs get no answer |
| 0x707, 0x187, 0x207, 0x000 | CANopen node 7 (CiA 401): boot-up, heartbeat, NMT start / stop, inputs while operational (DI0 = BOOT button, DI8–15 = outputs), outputs (DO0 = the board's LED) |

Door, light, engine speed and the button are also Home Assistant entities (ESPHome integration), so a script can operate the "equipment".

**Wiring**: ESP32 TX pin (GPIO5) → transceiver TXD, RX pin (GPIO4) → RXD; a 3.3 V transceiver (SN65HVD230, TJA1051T/3); CANH / CANL to the Pi's CAN HAT; 120 Ω at both ends; common ground. Use the same bit rate on both sides (`bit_rate`, default 500 kbit/s). Other boards: change `board` and the pins under `substitutions`.

**Flashing**: copy `secrets.example.yaml` to `secrets.yaml`, fill it in, then `esphome run woow_can_test_node.yaml`.

**Checks against hardware** (in the SSH add-on, the CAN interface instead of the virtual one):

```bash
python3 analysis_check.py CAN0   # formats, find_signal (0x356), guided_capture (door via 6F0), add_signal
python3 active_check.py CAN0     # needs the simulator's other equipment; the OBD-II and CiA 401 parts work with this node
```

The interface must not be listen-only for the checks that send; with the node on the bus, frames are acknowledged and the interface stays error-active.
