"""Built-in templates: each decodes the verified example frames of its protocol to the documented values."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.woow_can.devices import Device
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
    if template["transmits"]:  # sends: requests or command frames, all off until a person turns them on
        assert template.get("requests") or any(m.get("send") for m in template["messages"])
    else:
        assert not template.get("requests") and not any(m.get("send") for m in template["messages"])
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
    assert {t["id"] for t in lib.summaries("en", "vehicle")} == {"j1939_engine_vehicle", "j1939_dm1", "obd2_mode01"}


def device_from(tid: str, **params) -> Device:
    lib = TemplateLibrary(_Hass())
    lib.templates = TEMPLATES
    raw = lib.instantiate(lib.get(tid), "entry", "", params or None, None, "en")
    assert raw["active"] is False and raw["allow_write"] is False  # a template never starts sending by itself
    return Device.from_dict(raw)


def test_obd2_mode01():
    m = messages("obd2_mode01")
    rpm = m["PID_0C"]
    assert rpm.matches(0x7E8, fb("04 41 0C 1A F8 CC CC CC")) and not rpm.matches(0x7E8, fb("03 41 0D 32 CC CC CC CC"))
    assert rpm.decode(fb("04 41 0C 1A F8 CC CC CC")) == {"EngineSpeed": 1726}
    assert m["PID_0D"].matches(0x7E9, fb("03 41 0D 32 AA AA AA AA"))  # the gearbox ECU answers too
    assert m["PID_0D"].decode(fb("03 41 0D 32 CC CC CC CC")) == {"VehicleSpeed": 50}
    assert m["PID_05"].decode(fb("03 41 05 7B CC CC CC CC")) == {"CoolantTemperature": 83}
    assert m["PID_05"].decode(fb("03 41 05 46 00 00 00 00")) == {"CoolantTemperature": 30}  # ELM327 example
    assert m["PID_0F"].decode(fb("03 41 0F 46 CC CC CC CC")) == {"IntakeAirTemperature": 30}
    assert m["PID_11"].decode(fb("03 41 11 33 CC CC CC CC"))["ThrottlePosition"] == pytest.approx(20, abs=0.01)
    assert m["PID_2F"].decode(fb("03 41 2F C0 CC CC CC CC"))["FuelLevel"] == pytest.approx(75.2941, abs=0.001)
    assert m["PID_42"].decode(fb("04 41 42 36 B0 CC CC CC")) == {"ModuleVoltage": 14}
    assert m["PID_5E"].decode(fb("04 41 5E 00 FA CC CC CC")) == {"FuelRate": 12.5}
    assert not rpm.matches(0x7E8, fb("03 7F 01 21 CC CC CC CC"))  # negative response: not a value
    device = device_from("obd2_mode01")
    first = device.requests[0]
    assert (first.raw_id, first.data, first.reply) == (0x7DF, fb("02 01 0C CC CC CC CC CC"), "PID_0C")
    assert sum(1000 / r.period_ms for r in device.requests) < 10  # polite: under 10 requests a second
    wide = device_from("obd2_mode01", request_id="18DB33F1", reply_id="18DAF100", reply_mask="1FFFFF00")
    assert wide.requests[0].raw_id == 0x18DB33F1 | EFF
    assert wide.message("PID_0C").matches(0x18DAF110 | EFF, fb("04 41 0C 0F A0 CC CC CC"))
    assert wide.message("PID_0C").decode(fb("04 41 0C 0F A0 CC CC CC")) == {"EngineSpeed": 1000}


def test_daly_bms():
    device = device_from("daly_bms")
    pack = device.message("Pack_90")
    assert pack.raw_id == 0x18904001 | EFF
    values = pack.decode(fb("02 0D 02 0D 75 9E 03 52"))
    assert (values["TotalVoltage"], values["Current"], values["SOC"]) == (52.5, 11.0, 85.0)
    assert values["Power"] == 577.5
    assert [(r.raw_id, r.data) for r in device.requests[:1]] == [(0x18900140 | EFF, bytes(8))]
    cells = device.message("Cells_91").decode(fb("0D 16 03 0C EE 07 00 00"))
    assert (cells["MaxCellVoltage"], cells["MinCellVoltage"], cells["CellDelta"]) == (3.35, 3.31, 40.0)
    temps = device.message("Temperatures_92").decode(fb("41 01 3F 04 00 00 00 00"))
    assert (temps["MaxTemperature"], temps["MinTemperature"]) == (25, 23)
    mos = device.message("Mos_93").decode(fb("02 01 01 64 00 01 86 A0"))
    assert (mos["State"], mos["ChargeMos"], mos["RemainingCapacity"]) == ("discharging", 1, 100.0)
    assert device.message("Faults_98").decode(bytes(8))["Fault"] == 0


def test_cia401_io():
    device = device_from("cia401_io", node_id=1)
    inputs = device.message("Inputs").decode(fb("37 00"))  # CAN-2053C manual
    assert [i for i in range(16) if inputs[f"DI{i}"]] == [0, 1, 2, 4, 5]
    outputs = device.message("Outputs")
    assert outputs.send and outputs.raw_id == 0x201
    assert outputs.build({"DO0": 1, "DO1": 1, "DO2": 1, "DO4": 1, "DO5": 1}) == fb("37 00")  # CAN-2057C manual
    assert device_from("cia401_io", node_id=5).message("NMT").build({"Command": "start"}) == fb("01 05")
    ai = device.message("AI1_SDO")
    assert ai.matches(0x581, fb("4B 01 64 01 FF 7F D2 23")) and ai.decode(fb("4B 01 64 01 FF 7F D2 23")) == {"AI1": 32767}
    assert not ai.matches(0x581, fb("4B 01 64 02 FF 7F 00 00"))  # sub-index 2
    assert not ai.matches(0x581, fb("80 01 64 01 00 00 02 06"))  # an abort
    read = device.requests[0]
    assert (read.raw_id, read.data, read.reply) == (0x601, fb("40 01 64 01 00 00 00 00"), "AI1_SDO")
    assert not any(platform_of(s) == "switch" for _m, s in device.adopted())  # writing is off
    device.allow_write = True
    assert sum(platform_of(s) == "switch" for _m, s in device.adopted()) == 16
    assert any(platform_of(s) == "button" for _m, s in device.adopted())


def test_cia402_drive_monitor():
    device = device_from("cia402_drive_monitor", node_id=1)
    tpdo = device.message("Statusword_TPDO1")
    for word, state in ((0x0237, "operation_enabled"), (0x0008, "fault"), (0x0040, "switch_on_disabled"),
                        (0x0021, "ready_to_switch_on"), (0x0023, "switched_on"), (0x0007, "quick_stop_active"),
                        (0x000F, "fault_reaction_active"), (0x0000, "not_ready_to_switch_on")):
        assert tpdo.decode(word.to_bytes(2, "little"))["State"] == state, hex(word)
    assert tpdo.decode(fb("08 00"))["Fault"] == 1 and tpdo.decode(fb("37 02"))["Fault"] == 0
    assert device.message("Position_SDO").decode(fb("43 64 60 00 18 FC FF FF")) == {"PositionActual": -1000}
    assert device.message("Torque_SDO").decode(fb("4B 77 60 00 F4 01 00 00")) == {"TorqueActual": 50.0}
    sdo = device.message("Statusword_SDO").decode(fb("4B 41 60 00 37 02 00 00"))
    assert sdo["SdoState"] == "operation_enabled"
    assert device.message("Mode_SDO").decode(fb("4F 61 60 00 03 00 00 00")) == {"ModeDisplay": "profile_velocity"}
    assert not device.writable and all(not m.send for m in device.messages)  # it only reads
