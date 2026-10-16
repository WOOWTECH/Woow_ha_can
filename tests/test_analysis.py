"""Reverse engineering helpers: bit activity, finding a value, comparing an idle and an action period.

The modules are loaded from their files so this runs without Home Assistant installed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys
import types

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can"
_pkg = types.ModuleType("woow_can_pure")
_pkg.__path__ = [str(BASE)]
sys.modules.setdefault("woow_can_pure", _pkg)


def _load(name: str):
    if f"woow_can_pure.{name}" in sys.modules:
        return sys.modules[f"woow_can_pure.{name}"]
    spec = importlib.util.spec_from_file_location(f"woow_can_pure.{name}", BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"woow_can_pure.{name}"] = module
    spec.loader.exec_module(module)
    return module


_load("signals")
analysis = _load("analysis")


def hexid(key: int) -> str:
    return f"{key:03X}"


def test_bit_activity_counts_changes_and_ones():
    datas = [bytes([i % 2 << 3, i, 0x55]) for i in range(10)]  # bit 3 toggles, byte 1 counts, byte 2 constant
    act = analysis.bit_activity(datas)
    assert act["frames"] == 10 and act["length"] == 3
    assert act["changes"][3] == 9 and act["ones"][3] == 5
    assert act["changes"][8] == 9  # the counter's lowest bit changes every frame
    assert act["changes"][9] == 4  # ... the next one every other frame
    assert sum(act["changes"][16:24]) == 0 and act["ones"][16] == 10 and act["ones"][17] == 0
    assert act["bytes"][1] == {"min": 0, "max": 9, "distinct": 10}
    assert analysis.bit_activity([])["length"] == 0


def test_fields_cover_bytes_words_nibbles_and_bits():
    fields = set(analysis.fields_for(8))
    assert (0, 8, "little") in fields and (8, 16, "little") in fields and (15, 16, "big") in fields
    assert (7, 32, "big") in fields and (32, 32, "little") in fields and (39, 32, "big") in fields
    assert (47, 32, "big") not in fields and (40, 32, "little") not in fields  # beyond 8 bytes
    assert (4, 12, "little") in fields and (63, 1, "little") in fields
    assert len(analysis.fields_for(64)) == len(analysis.fields_for(16))  # CAN FD: the first 16 bytes


def test_signal_bits_match_the_candidate_reader():
    rnd = random.Random(3)
    for _ in range(200):
        data = bytes(rnd.randrange(256) for _ in range(8))
        for start, length, order in rnd.sample(analysis.fields_for(8), 5):
            cand = analysis.Candidate(0x100, start, length, order, False, 1.0, 0.0, 0.0)
            sig = cand.signal()
            assert cand.read(data) == sig.raw(data)


def test_find_a_scaled_value_in_two_steps():
    search = analysis.Search()
    other = {0x200: bytes([0x01, 0x02, 0x03, 0x04]), 0x300: bytes(range(8))}
    search.start({0x123: bytes([0x10, 0x27, 0, 0, 0, 0, 0, 0]), **other}, value=1000, tol=0.05)  # 0x2710 x 0.1
    found = [(c.key, c.start, c.length, c.order, c.factor, c.offset) for c in search.candidates]
    assert (0x123, 0, 16, "little", 0.1, 0.0) in found
    assert search.steps[0]["left"] == len(search.candidates)
    search.narrow({0x123: bytes([0x74, 0x27, 0, 0, 0, 0, 0, 0]), **other}, "equals", 1010, 0.05)  # 10100 x 0.1
    best = search.candidates[0]
    assert (best.key, best.start, best.length, best.order, best.factor) == (0x123, 0, 16, "little", 0.1)
    assert len(search.candidates) < 10
    summary = search.summary(5, hexid)
    assert summary["candidates"][0]["id"] == "123" and summary["candidates"][0]["value"] == 1010


def test_find_a_temperature_with_offset_and_a_signed_current():
    search = analysis.Search()
    search.start({0x18FEEE00: bytes([0x7D, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])}, value=85, tol=0.5)
    assert any(c.start == 0 and c.length == 8 and c.offset == -40.0 and c.factor == 1.0 for c in search.candidates)
    search = analysis.Search()
    current = (-125).to_bytes(2, "little", signed=True)  # -12.5 A at 0.1 A
    search.start({0x356: bytes([0x14, 0x14]) + current + bytes([0xFA, 0x00])}, value=-12.5, tol=0.05)
    assert any(c.start == 16 and c.length == 16 and c.signed and c.factor == 0.1 for c in search.candidates)


def test_relative_search_finds_a_counter_free_level():
    rnd = random.Random(5)

    def frames(level: int) -> dict[int, bytes]:
        return {0x100: bytes([rnd.randrange(256), level, 0x00, 0x11]), 0x101: bytes([1, 2, 3, 4])}

    search = analysis.Search()
    search.start(frames(10))
    search.narrow(frames(10), "unchanged")
    search.narrow(frames(20), "increased")
    search.narrow(frames(5), "decreased")
    search.narrow(frames(5), "unchanged")
    keys = {(c.key, c.start, c.length, c.order) for c in search.candidates}
    assert (0x100, 8, 8, "little") in keys
    assert all(c.key == 0x100 for c in search.candidates)
    assert search.steps[-1]["mode"] == "unchanged"


def test_compare_finds_a_switch_and_ignores_counters():
    def frame(i: int, switch: int, level: int) -> bytes:
        return bytes([switch << 2, level, 0x00, 0x00, 0x00, 0x00, 0x00, i & 0xFF])

    idle = {0x200: [frame(i, 0, 10) for i in range(50)], 0x300: [bytes([1, 2]) for _ in range(50)]}
    action = {0x200: [frame(i, 1, 40) for i in range(50, 100)], 0x300: [bytes([1, 2]) for _ in range(50)],
              0x7E8: [bytes([3, 0x41, 0x0C, 0x1A])]}
    back = {0x200: [frame(i, 0, 10) for i in range(100, 150)]}
    result = analysis.compare([idle, action, back], hexid)
    assert result[0]["id"] == "200"
    flips = result[0]["flipped"]
    assert [(f["byte"], f["bit"], f["idle"], f["action"], f["confirmed"]) for f in flips if f["byte"] == 0] == [
        (0, 2, 0, 1, True)]
    assert all(f["byte"] != 7 for f in flips)  # the counter moves in both phases
    assert {r["id"] for r in result} == {"200", "7E8"}  # 0x300 never changed
    only = next(r for r in result if r["id"] == "7E8")
    assert only["only_in"] == "action"


def test_signed_twin_survives_until_the_value_goes_negative():
    search = analysis.Search()
    search.start({0x400: (50).to_bytes(2, "little") + bytes(6)}, value=5.0, tol=0.01)  # 50 x 0.1
    shown = search.summary(50, hexid)["candidates"]
    assert not any(c["signed"] and c["start"] == 0 and c["length"] == 16 for c in shown)  # same reading: hidden
    search.narrow({0x400: (-30).to_bytes(2, "little", signed=True) + bytes(6)}, "equals", -3.0, 0.01)
    left = {(c.start, c.length, c.signed, c.factor) for c in search.candidates}
    assert (0, 16, True, 0.1) in left and (0, 16, False, 0.1) not in left


def test_compare_tolerates_people_acting_a_moment_late():
    idle = {0x3C0: [bytes([0x00, i]) for i in range(30)]}
    late = {0x3C0: [bytes([0x00, i]) for i in range(4)] + [bytes([0x04, i]) for i in range(4, 30)]}  # 4 old frames
    early = {0x3C0: [bytes([0x04, i]) for i in range(2)] + [bytes([0x00, i]) for i in range(2, 30)]}
    result = analysis.compare([idle, late, early], hexid)
    flips = [(f["byte"], f["bit"], f["confirmed"]) for f in result[0]["flipped"]]
    assert flips == [(0, 2, True)]
    toggling = {0x3C0: [bytes([(i % 2) << 2, 0]) for i in range(30)]}  # blinks during the action
    result = analysis.compare([idle, toggling], hexid)
    assert result[0]["flipped"] == [] and [m["start"] for m in result[0]["moving"]] == [2]


def test_counter_bits_follow_the_carry():
    plain = [i & 0xFF for i in range(300)]
    assert analysis.counter_bits(plain, 8) == set(range(8))
    alive = [(i % 16) << 4 | 0x05 for i in range(100)]  # upper nibble counts, lower nibble fixed flags
    assert analysis.counter_bits(alive, 8) == {4, 5, 6, 7}
    big = [int.from_bytes(i.to_bytes(2, "big"), "little") for i in range(0, 1200)]  # 16-bit big endian
    # low byte (byte 1: bits 8-15), carrying into the high byte (byte 0), which only reaches 4 (bit 2 once)
    assert analysis.counter_bits(big, 16) == set(range(8, 16)) | {0, 1, 2}
    switch_by_counter = [(i & 1) | (4 if 20 <= i < 40 else 0) for i in range(60)]  # bit 2: a switch, not a carry
    assert 2 not in analysis.counter_bits(switch_by_counter, 8)


def test_repeating_the_action_rules_out_coincidences():
    def phase(door: int, load: int, start: int) -> dict[int, list[bytes]]:
        return {0x3C0: [bytes([door << 2, (start + i) & 0xFF]) for i in range(25)],
                0x356: [bytes([0x02, 0x13, 0xFF if load else 0, 0x03 if load else 0]) for _ in range(25)]}

    # the battery load happens to switch on with the first action, then keeps its own rhythm
    phases = [phase(0, 0, 0), phase(1, 1, 25), phase(0, 1, 50), phase(1, 0, 75), phase(0, 0, 100)]
    result = analysis.compare(phases, hexid)
    assert result[0]["id"] == "3C0" and [(f["start"], f["confirmed"]) for f in result[0]["flipped"]] == [(2, True)]
    assert not any(r["id"] == "356" and r.get("flipped") for r in result)
    assert result[0]["counter_bits"] == list(range(8, 15))  # bit 15 never changed


def test_slow_upper_counter_bits_in_a_short_capture():
    values = [0x70 + i for i in range(40)]  # 0x70 .. 0x97: bits 4-6 fall and bit 7 rises once, at 0x7F -> 0x80
    assert {0, 1, 2, 3, 4, 5, 6, 7} <= analysis.counter_bits(values, 8)
