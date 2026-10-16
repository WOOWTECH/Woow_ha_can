"""Our DBC reader and signal codec against cantools (CI only: pip install cantools; skipped elsewhere).

The modules are loaded from their files so this runs without Home Assistant installed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys
import types

import pytest

cantools = pytest.importorskip("cantools")

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can"
_pkg = types.ModuleType("woow_can_pure")
_pkg.__path__ = [str(BASE)]
sys.modules.setdefault("woow_can_pure", _pkg)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"woow_can_pure.{name}", BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"woow_can_pure.{name}"] = module
    spec.loader.exec_module(module)
    return module


signals = _load("signals")
dbc = _load("dbc")

CORPUS = r'''VERSION ""
NS_ :
BS_:
BU_: A B
BO_ 291 Mixed: 8 A
 SG_ IntelU : 0|12@1+ (0.5,-10) [-10|2037.5] "V" B
 SG_ IntelS : 12|4@1- (1,0) [-8|7] "" B
 SG_ MotoU : 23|16@0+ (0.1,0) [0|6553.5] "A" B
 SG_ MotoS : 39|11@0- (2,5) [-2043|2051] "" B
 SG_ Odd : 50|3@1+ (1,0) [0|7] "" B
 SG_ Flag : 63|1@0+ (1,0) [0|1] "" B
BO_ 2565865201 Wide: 8 B
 SG_ Big64 : 7|64@0+ (1,0) [0|0] "" A
BO_ 1024 Muxed: 8 A
 SG_ Sel M : 0|4@1+ (1,0) [0|15] "" B
 SG_ OnOne m1 : 8|16@1+ (0.01,0) [0|655.35] "" B
 SG_ OnTwo m2 : 8|8@1- (1,0) [-128|127] "" B
BO_ 1280 Floats: 8 A
 SG_ F32 : 0|32@1- (1,0) [0|0] "" B
 SG_ F32M : 39|32@0- (1,0) [0|0] "" B
BA_DEF_ BO_ "VFrameFormat" ENUM "StandardCAN","ExtendedCAN","reserved","J1939PG";
BA_DEF_DEF_ "VFrameFormat" "StandardCAN";
BA_ "VFrameFormat" BO_ 2565865201 1;
SIG_VALTYPE_ 1280 F32 : 1;
SIG_VALTYPE_ 1280 F32M : 1;
'''


def test_against_cantools():
    ours = {m["name"]: signals.Message.from_dict(m) for m in dbc.parse(CORPUS).messages}
    theirs = cantools.database.load_string(CORPUS, database_format="dbc")
    rng = random.Random(1234)
    for message in theirs.messages:
        mine = ours[message.name]
        for _ in range(300):
            data = bytes(rng.getrandbits(8) for _ in range(message.length))
            got = mine.decode(data)
            try:
                expected = message.decode(data, decode_choices=False, scaling=True, allow_truncated=True)
            except cantools.database.errors.DecodeError:  # a multiplexer value with no signals behind it
                assert set(got) == {"Sel"}, (message.name, got)
                continue
            for name, value in expected.items():
                if isinstance(value, float) and value != value:  # NaN floats
                    continue
                assert got.get(name) == pytest.approx(value, rel=1e-9, abs=1e-6), (message.name, name, data.hex())
            for name in set(got) - set(expected):
                assert got[name] is None, (message.name, name)


def test_cantools_reads_our_dbc():
    ours = {m["name"]: signals.Message.from_dict(m) for m in dbc.parse(CORPUS).messages}
    written = dbc.dump(list(ours.values()))
    theirs = cantools.database.load_string(written, database_format="dbc")
    assert {m.name for m in theirs.messages} == set(ours)
    data = bytes(range(1, 9))  # multiplexer 1
    for message in theirs.messages:
        expected = message.decode(data, decode_choices=False, allow_truncated=True)
        got = ours[message.name].decode(data)
        for name, value in expected.items():
            if isinstance(value, float) and value != value:
                continue
            assert got[name] == pytest.approx(value, rel=1e-9, abs=1e-6), (message.name, name)
