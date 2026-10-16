"""Built-in templates: each decodes the verified example frames of its protocol to the documented values."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.woow_can.managed import UNITS, platform_of, snake
from custom_components.woow_can.signals import Message
from custom_components.woow_can.templates import TemplateLibrary, defaults, validate

HERE = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can" / "templates"
TEMPLATES = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in HERE.glob("*.json")}
EFF = 0x80000000


def fb(text: str) -> bytes:
    return bytes.fromhex(text.replace(" ", ""))


def messages(tid: str, **params) -> dict[str, Message]:
    template = TEMPLATES[tid]
    values = {**defaults(template), **params}
    return {m["name"]: Message.from_dict(m, values) for m in template["messages"]}


@pytest.mark.parametrize("tid", sorted(TEMPLATES))
def test_template_is_complete(tid):
    template = TEMPLATES[tid]
    validate(template)
    for key in ("source", "license", "verified", "confidence", "name", "description", "default_name"):
        assert template.get(key), key
    assert template["transmits"] is False  # the first templates only listen
    keys = set()
    for msg in messages(tid).values():
        for sig in msg.signals:
            entity = sig.entity
            if not entity:
                continue
            assert entity["name"]["en"] and entity["name"]["zh-Hant"], sig.name
            assert entity["key"] not in keys, entity["key"]
            keys.add(entity["key"])
            assert snake(entity["key"])
            if platform_of(sig) == "sensor" and sig.unit and not sig.values and sig.kind != "ascii":
                assert sig.unit in UNITS or sig.unit in ("%", "Ah", "rpm", "km/L", "L/h", "r"), sig.unit


def test_battery_bms():
    m = messages("bms_lv_0x35x")
    # Pylontech US3000 x10 -> Sofar ME3000SP (setfirelabs capture)
    assert m["BMS_351_Limits"].decode(fb("14 02 74 0E 74 0E CC 01")) == {
        "ChargeVoltageLimit": 53.2, "ChargeCurrentLimit": 370.0, "DischargeCurrentLimit": 370.0,
        "DischargeVoltageLimit": 46.0}
    assert m["BMS_355_SOC"].decode(fb("0E 00 64 00")) == {"SOC": 14, "SOH": 100, "SOC_HiRes": None}  # DLC 4
    meas = m["BMS_356_Measurements"].decode(fb("02 13 00 00 4A 01"))
    assert meas["BatteryVoltage"] == 48.66 and meas["BatteryTemperature"] == 33.0 and meas["BatteryPower"] == 0
    flags = m["PYLON_359_Alarms"].decode(fb("00 01 02 00 02 50 4E"))
    assert flags["P_ChargeOverCurrent"] == 1 and flags["A_CellHighVoltage"] == 1 and flags["ModuleCount"] == 2
    assert flags["ProtectionActive"] == 1 and flags["AlarmActive"] == 1
    assert m["PYLON_359_Alarms"].decode(fb("00 00 00 00 0A 50 4E"))["ProtectionActive"] == 0
    requests = m["PYLON_35C_Requests"].decode(fb("C0 00"))
    assert requests["ChargeEnable"] == 1 and requests["DischargeEnable"] == 1 and requests["FullChargeRequest"] == 0
    assert m["BMS_35E_Manufacturer"].decode(b"PYLON   ")["Manufacturer"] == "PYLON"
    # BYD LVS -> Victron (dfch/BydCanProtocol, MIT)
    byd = m["BMS_356_Measurements"].decode(fb("BE 14 F9 FF 8C 00 00 00"))
    assert (byd["BatteryVoltage"], byd["BatteryCurrent"], byd["BatteryTemperature"]) == (53.1, -0.7, 14.0)
    assert byd["BatteryPower"] == pytest.approx(-37.17)
    sma = m["SMA_35A_AlarmsWarnings"]
    assert sma.decode(fb("AA AA AA AA AA AA AA AA"))["AlarmActive"] == 0
    raised = sma.decode(fb("10 AA AA AA AA AA AA AA"))
    assert raised["AL_LowVoltage"] == 1 and raised["AL_General"] is None and raised["AlarmActive"] == 1
    assert sma.decode(fb("AA AA AA AA AA 40 AA AA"))["WarningActive"] == 1  # high discharge current warning
    assert m["SMA_35F_BatteryData"].decode(fb("4C 69 01 17 69 00 00 00"))["Capacity"] == 105
    cells = m["VICTRON_373_CellExtremes"].decode(fb("EA 0C 01 0D 1F 01 22 01"))
    assert cells == {"MinCellVoltage": 3.306, "MaxCellVoltage": 3.329, "MinCellTemperature": 14, "MaxCellTemperature": 17}
    assert m["BMS_378_Energy"].decode(fb("40 08 00 00 2B 07 00 00")) == {"ChargedEnergy": 211.2, "DischargedEnergy": 183.5}
    # SMA Sunny Island 0x305 (constructed from the SMA document): current negative while charging
    si = m["INVERTER_305"].decode(fb("14 02 6A FF FB 00 55 03"))
    assert (si["BatteryVoltage"], si["BatteryCurrent"], si["BatteryTemperature"], si["SOC"]) == (53.2, -15.0, 25.1, 85.3)
    assert m["BMS_351_Limits"].decode(fb("FF FF 00 80 00 00 00 00"))["ChargeVoltageLimit"] is None  # SMA "invalid"


def test_j1939_engine():
    m = messages("j1939_engine_vehicle", source_address="00")
    eec1 = m["EEC1"]
    assert eec1.matches(0x0CF00400 | EFF) and not eec1.matches(0x0CF00401 | EFF)
    assert eec1.decode(fb("F0 7D 7D 9A 2E 00 F0 7D"))["EngineSpeed"] == 1491.25
    assert eec1.decode(fb("F1 7D 91 E0 2E 00 F0 7D"))["ActualEngineTorque"] == 20
    ccvs = m["CCVS1"].decode(fb("F7 00 50 14 FF 5A E0 FF"))
    assert ccvs["WheelBasedSpeed"] == 80.0 and ccvs["BrakeSwitch"] == 1 and ccvs["CruiseSetSpeed"] == 90
    assert m["CCVS1"].decode(fb("FF FF FF FF FF FF FF FF"))["WheelBasedSpeed"] is None  # not 255.996 km/h
    et1 = m["ET1"].decode(fb("7D 46 00 2E FF FF FF FF"))
    assert (et1["CoolantTemperature"], et1["FuelTemperature"], et1["OilTemperature"]) == (85, 30, 95.0)
    efl = m["EFL_P1"].decode(fb("FF FF D7 64 FF FF 32 FA"))
    assert (efl["OilLevel"], efl["OilPressure"], efl["CoolantPressure"], efl["CoolantLevel"]) == (86.0, 400, 100, 100.0)
    lfe = m["LFE1"].decode(fb("FA 00 00 06 00 05 64 FF"))
    assert (lfe["FuelRate"], lfe["InstantFuelEconomy"], lfe["AverageFuelEconomy"], lfe["ThrottlePosition"]) == (12.5, 3.0, 2.5, 40.0)
    assert m["VEP1"].decode(fb("82 14 34 02 2D 02 28 02"))["BatteryPotential"] == 27.85
    hours = m["HOURS"].decode(fb("72 60 00 00 79 CC 00 00"))
    assert hours["EngineHours"] == 1234.5 and hours["EngineRevolutions"] == 52345000


def test_j1939_dm1():
    dm1 = messages("j1939_dm1")["DM1"]
    one = dm1.decode(fb("04 FF 64 00 01 03 FF FF"))
    assert one["AmberWarningLamp"] is True and one["ActiveFaults"] == 1 and one["FaultCodes"] == "SPN 100 FMI 1"
    two = dm1.decode(fb("14 FF 64 00 01 03 6E 00 00 01"))  # the BAM payload
    assert two["RedStopLamp"] is True and two["ActiveFaults"] == 2 and two["FaultCodes"] == "SPN 100 FMI 1, SPN 110 FMI 0"


def test_nmea2000_dc():
    m = messages("nmea2000_dc", instance=0)
    status = m["BatteryStatus_127508"]
    assert status.matches(0x19F21423 | EFF, fb("00 70 0A 43 00 31 71 FF"))
    assert not status.matches(0x19F21423 | EFF, fb("05 7A 06 30 00 FF FF 00"))  # instance 5
    values = status.decode(fb("00 70 0A 43 00 31 71 FF"))
    assert (values["Voltage"], values["Current"], values["Temperature"]) == (26.72, 6.7, 16.62)
    assert messages("nmea2000_dc", instance=5)["BatteryStatus_127508"].decode(fb("05 7A 06 30 00 FF FF 00"))["Temperature"] is None
    detailed = messages("nmea2000_dc", instance=1)["DcDetailedStatus_127506"].decode(fb("52 01 00 64 FF 60 32 A5 00"))
    assert detailed["StateOfCharge"] == 100 and detailed["StateOfHealth"] is None and detailed["TimeRemaining"] == 12896
    assert detailed["RippleVoltage"] == 0.165 and detailed["RemainingCapacity"] is None  # 9-byte older layout


def test_canopen_node():
    m = messages("canopen_node_monitor", node_id=10, heartbeat_ms=500)
    assert m["Heartbeat"].can_id == 0x70A and m["Heartbeat"].timeout == 5.0 and m["Emergency"].can_id == 0x8A
    assert m["Heartbeat"].decode(b"\x05") == {"State": "operational", "Online": 1}
    assert m["Heartbeat"].decode(b"\x7f")["State"] == "pre_operational"
    emcy = m["Emergency"].decode(fb("30 81 11 07 00 00 00 00"))  # ICP DAS: heartbeat / life guard error
    assert emcy["ErrorCode"] == 0x8130 and emcy["ErrorRegister"] == 0x11 and emcy["InError"] == 1
    assert m["Emergency"].decode(bytes(8))["InError"] == 0


class _Hass:
    class config:  # noqa: N801
        language = "zh-Hant"

        @staticmethod
        def path(*parts):
            return "/nonexistent/" + "/".join(parts)


def test_instantiate_groups_and_params():
    lib = TemplateLibrary(_Hass())
    lib.templates = TEMPLATES
    bms = lib.get("bms_lv_0x35x")
    seen = {0x351, 0x355, 0x356, 0x359, 0x373}
    device = lib.instantiate(bms, "entry", "", None, None, "zh-Hant", seen)
    assert device["groups"] == ["pylon", "victron"] and device["name"] == "電池"
    assert {m["name"] for m in device["messages"]} >= {"PYLON_359_Alarms", "VICTRON_373_CellExtremes"}
    assert not any(m["name"].startswith("SMA_") for m in device["messages"])
    assert all("group" not in m for m in device["messages"])
    only_core = lib.instantiate(bms, "entry", "Rack", None, [], "en", seen)
    assert only_core["groups"] == [] and len(only_core["messages"]) == 4
    node = lib.instantiate(lib.get("canopen_node_monitor"), "entry", "", {"node_id": 7}, None, "en")
    assert node["params"] == {"node_id": 7, "heartbeat_ms": 1000}
    with pytest.raises(ValueError):
        lib.instantiate(lib.get("canopen_node_monitor"), "entry", "", {"node": 7}, None, "en")
    with pytest.raises(ValueError):
        lib.instantiate(bms, "entry", "", None, ["nope"], "en")
    assert lib.get("J1939 engine and vehicle")["id"] == "j1939_engine_vehicle"
    assert {t["id"] for t in lib.summaries("en", "vehicle")} == {"j1939_engine_vehicle", "j1939_dm1"}
