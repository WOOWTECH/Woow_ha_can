"""Write the built-in device templates (custom_components/woow_can/templates/*.json).

Every value here comes from public documents and captures, checked by the scripts in the research
notes; the frames in tests/test_templates.py are decoded through these files. Re-run after editing:
    python3 tools/make_templates.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "custom_components" / "woow_can" / "templates"


def T(en: str, zh: str) -> dict[str, str]:
    return {"en": en, "zh-Hant": zh}


def ent(key: str, en: str, zh: str, **extra) -> dict:
    out = {"key": key, "name": T(en, zh)}
    out.update({k: v for k, v in extra.items() if v is not None})
    return out


def sig(name: str, start: int, length: int, *, order: str = "little", signed: bool = False, factor: float = 1,
        offset: float = 0, unit: str = "", values: dict | None = None, invalid=None, kind: str = "int",
        entity: dict | None = None, derive: dict | None = None, decoder_field: str | None = None,
        comment: str = "") -> dict:
    out: dict = {"name": name, "start": start, "length": length, "byte_order": order, "signed": signed}
    if kind != "int":
        out["kind"] = kind
    if factor != 1:
        out["factor"] = factor
    if offset:
        out["offset"] = offset
    if unit:
        out["unit"] = unit
    if values:
        out["values"] = {str(k): v for k, v in values.items()}
    if invalid is not None:
        out["invalid"] = invalid
    if derive:
        out["derive"] = derive
    if decoder_field:
        out["decoder_field"] = decoder_field
    if comment:
        out["comment"] = comment
    if entity:
        out["entity"] = entity
    return out


def bit(name: str, start: int, entity: dict | None = None, **kw) -> dict:
    return sig(name, start, 1, entity=entity, **kw)


# ---- 1. low-voltage battery BMS, 0x35x family --------------------------------------------------------
PYLON_PROTECTIONS = [
    ("P_CellOverVoltage", 1, "Protection: cell over-voltage", "保護：電芯過壓"),
    ("P_CellUnderVoltage", 2, "Protection: cell under-voltage", "保護：電芯欠壓"),
    ("P_CellOverTemperature", 3, "Protection: cell over-temperature", "保護：電芯過溫"),
    ("P_CellUnderTemperature", 4, "Protection: cell under-temperature", "保護：電芯低溫"),
    ("P_DischargeOverCurrent", 7, "Protection: discharge over-current", "保護：放電過流"),
    ("P_ChargeOverCurrent", 8, "Protection: charge over-current", "保護：充電過流"),
    ("P_SystemError", 11, "Protection: system error", "保護：系統錯誤"),
]
PYLON_ALARMS = [
    ("A_CellHighVoltage", 17, "Alarm: cell high voltage", "告警：電芯高壓"),
    ("A_CellLowVoltage", 18, "Alarm: cell low voltage", "告警：電芯低壓"),
    ("A_CellHighTemperature", 19, "Alarm: cell high temperature", "告警：電芯高溫"),
    ("A_CellLowTemperature", 20, "Alarm: cell low temperature", "告警：電芯低溫"),
    ("A_DischargeHighCurrent", 23, "Alarm: high discharge current", "告警：放電電流大"),
    ("A_ChargeHighCurrent", 24, "Alarm: high charge current", "告警：充電電流大"),
    ("A_InternalCommFail", 27, "Alarm: internal communication failure", "告警：內部通訊失敗"),
]
SMA_ITEMS = [
    ("General", "general", "一般"), ("HighVoltage", "battery high voltage", "電池高壓"),
    ("LowVoltage", "battery low voltage", "電池低壓"), ("HighTemperature", "high temperature", "高溫"),
    ("LowTemperature", "low temperature", "低溫"), ("HighTemperatureCharge", "high temperature charging", "充電高溫"),
    ("LowTemperatureCharge", "low temperature charging", "充電低溫"),
    ("HighDischargeCurrent", "high discharge current", "放電電流大"),
    ("HighChargeCurrent", "high charge current", "充電電流大"), ("Contactor", "contactor", "接觸器"),
    ("ShortCircuit", "short circuit", "短路"), ("BmsInternal", "BMS internal", "BMS 內部"),
    ("CellImbalance", "cell imbalance", "電芯不平衡"),
]


def problem(key: str, en: str, zh: str, enabled: bool = False) -> dict:
    return ent(key, en, zh, platform="binary_sensor", device_class="problem", enabled=enabled)


def sma_pairs(kind: str, base: int) -> list[dict]:
    label_en, label_zh = ("Alarm", "告警") if kind == "AL" else ("Warning", "警告")
    out = []
    for i, (name, en, zh) in enumerate(SMA_ITEMS):
        out.append(sig(f"{kind}_{name}", base + 2 * i, 2, invalid=[0, 3],
                       entity=ent(f"battery.sma_{kind.lower()}_{name.lower()}", f"SMA {label_en.lower()}: {en}",
                                  f"SMA {label_zh}：{zh}", platform="binary_sensor", device_class="problem",
                                  on=[1], off=[2], enabled=False)))
    return out


BMS = {
    "id": "bms_lv_0x35x",
    "version": 1,
    "name": T("Low-voltage battery BMS (Pylontech / SMA / Victron 0x35x)", "低壓電池 BMS（Pylontech／SMA／Victron 0x35x）"),
    "category": "battery",
    "description": T(
        "Rack and wall batteries that report to their inverter on 0x351-0x35F (Pylontech, BYD LVS, Seplos, REC, "
        "JK in Pylon mode, most 48 V rack batteries). Listen between the battery and the inverter: state of "
        "charge, voltage, current, power, temperature, charge and discharge limits, alarms.",
        "接在電池和逆變器之間監聽 0x351–0x35F（Pylontech、BYD LVS、Seplos、REC、Pylon 模式的 JK，以及大多數 48 V "
        "機櫃電池）：電量、電壓、電流、功率、溫度、充放電限制和告警。"),
    "bitrate": 500000,
    "transmits": False,
    "manufacturer": "Battery BMS",
    "model": "CAN 0x35x",
    "default_name": T("Battery", "電池"),
    "source": [
        "SMA: Connecting batteries with external BMS to Sunny Island 6.0H-11 (FSS-ConnectingBat-TI-en-10, 2013)",
        "Pylontech: Low Voltage Battery System CANBUS Protocol V1.3 (2019-03-01)",
        "REC BMS manuals for Victron and SMA",
        "dfch/BydCanProtocol (MIT): BYD LVS to Victron capture",
    ],
    "license": "Facts from vendor documents and public captures, written by WOOWTECH; MIT",
    "verified": ["Pylontech US3000 x10 -> Sofar ME3000SP capture (setfirelabs, 2021)",
                 "BYD LVS -> Victron Venus OS 3.00 capture (dfch/BydCanProtocol)"],
    "confidence": "high",
    "notes": T(
        "Current is positive while charging (0x356). The inverter's 0x305 counts the other way round. Victron's "
        "extensions (0x370 and up) are community knowledge: Victron's BMS protocol is under NDA.",
        "電流正值＝充電（0x356）；逆變器的 0x305 正負號相反。Victron 的延伸訊框（0x370 之後）是社群整理的資料，"
        "Victron 的 BMS 協定受保密協議限制。"),
    "params": [],
    "groups": [
        {"id": "pylon", "name": T("Pylontech alarms and requests (0x359, 0x35C)", "Pylontech 告警與請求旗標（0x359、0x35C）")},
        {"id": "sma", "name": T("SMA alarms, warnings and battery data (0x35A, 0x35F)", "SMA 告警、警告與電池資料（0x35A、0x35F）")},
        {"id": "victron", "name": T("Victron / BYD extensions: cell extremes, energy, capacity (0x373, 0x378, 0x379)",
                                    "Victron／BYD 延伸：電芯極值、累計電量、容量（0x373、0x378、0x379）")},
        {"id": "inverter", "name": T("Inverter replies (0x305, 0x306; SMA Sunny Island values)",
                                     "逆變器回覆（0x305、0x306；SMA Sunny Island 的數值）")},
    ],
    "messages": [
        {"name": "BMS_351_Limits", "can_id": "351", "length": 8, "cycle_ms": 1000, "signals": [
            sig("ChargeVoltageLimit", 0, 16, factor=0.1, unit="V", invalid="sma",
                entity=ent("battery.charge_voltage_limit", "Charge voltage limit", "充電電壓上限")),
            sig("ChargeCurrentLimit", 16, 16, signed=True, factor=0.1, unit="A", invalid="sma",
                entity=ent("battery.charge_current_limit", "Charge current limit", "充電電流上限")),
            sig("DischargeCurrentLimit", 32, 16, signed=True, factor=0.1, unit="A", invalid="sma",
                entity=ent("battery.discharge_current_limit", "Discharge current limit", "放電電流上限")),
            sig("DischargeVoltageLimit", 48, 16, factor=0.1, unit="V", invalid="sma",
                entity=ent("battery.discharge_voltage_limit", "Discharge voltage limit", "放電電壓下限")),
        ]},
        {"name": "BMS_355_SOC", "can_id": "355", "length": 8, "cycle_ms": 1000, "signals": [
            sig("SOC", 0, 16, unit="%", invalid="sma",
                entity=ent("battery.soc", "State of charge", "電量", device_class="battery", precision=0)),
            sig("SOH", 16, 16, unit="%", invalid="sma",
                entity=ent("battery.soh", "State of health", "健康度", precision=0, icon="mdi:heart-pulse")),
            sig("SOC_HiRes", 32, 16, factor=0.01, unit="%", invalid="sma",
                entity=ent("battery.soc_fine", "State of charge (0.01 %)", "電量（0.01%）", device_class="battery",
                           enabled=False)),
        ]},
        {"name": "BMS_356_Measurements", "can_id": "356", "length": 8, "cycle_ms": 1000, "signals": [
            sig("BatteryVoltage", 0, 16, signed=True, factor=0.01, unit="V", invalid="sma",
                entity=ent("battery.voltage", "Voltage", "電壓")),
            sig("BatteryCurrent", 16, 16, signed=True, factor=0.1, unit="A", invalid="sma",
                comment="positive while charging",
                entity=ent("battery.current", "Current (positive = charging)", "電流（正＝充電）")),
            sig("BatteryTemperature", 32, 16, signed=True, factor=0.1, unit="degC", invalid="sma",
                entity=ent("battery.temperature", "Temperature", "溫度")),
            sig("BatteryPower", 0, 0, unit="W", derive={"op": "product", "of": ["BatteryVoltage", "BatteryCurrent"]},
                entity=ent("battery.power", "Power (positive = charging)", "功率（正＝充電）", precision=0)),
        ]},
        {"name": "PYLON_359_Alarms", "can_id": "359", "length": 7, "cycle_ms": 1000, "group": "pylon", "signals": [
            *[bit(n, b, problem(f"battery.{n.lower()}", en, zh)) for n, b, en, zh in PYLON_PROTECTIONS],
            *[bit(n, b, problem(f"battery.{n.lower()}", en, zh)) for n, b, en, zh in PYLON_ALARMS],
            sig("ModuleCount", 32, 8, entity=ent("battery.module_count", "Modules", "模組數", icon="mdi:battery-high",
                                                 state_class="measurement", precision=0)),
            sig("ProtectionActive", 0, 0, derive={"op": "any", "of": [p[0] for p in PYLON_PROTECTIONS]},
                entity=problem("battery.protection", "Protection active", "保護動作中", enabled=True)),
            sig("AlarmActive", 0, 0, derive={"op": "any", "of": [a[0] for a in PYLON_ALARMS]},
                entity=problem("battery.alarm", "Alarm active", "告警中", enabled=True)),
        ]},
        {"name": "PYLON_35C_Requests", "can_id": "35C", "length": 2, "cycle_ms": 1000, "group": "pylon", "signals": [
            bit("ChargeEnable", 7, ent("battery.charge_enabled", "Charging allowed", "允許充電",
                                       platform="binary_sensor", icon="mdi:battery-charging")),
            bit("DischargeEnable", 6, ent("battery.discharge_enabled", "Discharging allowed", "允許放電",
                                          platform="binary_sensor", icon="mdi:battery-arrow-down")),
            bit("ForceChargeRequest1", 5, ent("battery.force_charge", "Force charge request", "強制充電請求",
                                              platform="binary_sensor", icon="mdi:battery-alert")),
            bit("ForceChargeRequest2", 4, ent("battery.force_charge_2", "Force charge request II", "強制充電請求 II",
                                              platform="binary_sensor", enabled=False)),
            bit("FullChargeRequest", 3, ent("battery.full_charge_request", "Full charge request", "要求充滿",
                                            platform="binary_sensor", icon="mdi:battery-sync")),
        ]},
        {"name": "BMS_35E_Manufacturer", "can_id": "35E", "length": 8, "cycle_ms": 1000, "signals": [
            sig("Manufacturer", 0, 64, kind="ascii", entity=ent("battery.manufacturer", "Manufacturer", "製造商",
                                                                 icon="mdi:factory", category="diagnostic")),
        ]},
        {"name": "SMA_35A_AlarmsWarnings", "can_id": "35A", "length": 8, "cycle_ms": 1000, "group": "sma",
         "comment": "two bits per item: 01 raised, 10 cleared; AA = all clear", "signals": [
            *sma_pairs("AL", 0),
            *sma_pairs("WA", 32),
            sig("AlarmActive", 0, 0, derive={"op": "any", "of": [f"AL_{n}" for n, _, _ in SMA_ITEMS]},
                entity=problem("battery.sma_alarm", "SMA alarm active", "SMA 告警中", enabled=True)),
            sig("WarningActive", 0, 0, derive={"op": "any", "of": [f"WA_{n}" for n, _, _ in SMA_ITEMS]},
                entity=problem("battery.sma_warning", "SMA warning active", "SMA 警告中", enabled=True)),
        ]},
        {"name": "SMA_35F_BatteryData", "can_id": "35F", "length": 8, "cycle_ms": 1000, "group": "sma", "signals": [
            sig("BatteryType", 0, 16, entity=ent("battery.type_code", "Battery type code", "電池類型代碼",
                                                  format="hex", enabled=False, category="diagnostic")),
            sig("BmsVersion", 16, 16, entity=ent("battery.bms_version", "BMS version", "BMS 版本", format="hex",
                                                  enabled=False, category="diagnostic")),
            sig("Capacity", 32, 16, unit="Ah", entity=ent("battery.capacity", "Capacity", "容量", precision=0,
                                                         icon="mdi:battery-high")),
            sig("ManufacturerId", 48, 16, entity=ent("battery.manufacturer_id", "Manufacturer ID", "製造商代碼",
                                                     format="hex", enabled=False, category="diagnostic")),
        ]},
        {"name": "VICTRON_373_CellExtremes", "can_id": "373", "length": 8, "cycle_ms": 1000, "group": "victron",
         "comment": "community knowledge (BYD capture, JK sources)", "signals": [
            sig("MinCellVoltage", 0, 16, factor=0.001, unit="V",
                entity=ent("battery.cell_voltage_min", "Lowest cell voltage", "最低電芯電壓")),
            sig("MaxCellVoltage", 16, 16, factor=0.001, unit="V",
                entity=ent("battery.cell_voltage_max", "Highest cell voltage", "最高電芯電壓")),
            sig("MinCellTemperature", 32, 16, offset=-273, unit="degC",
                entity=ent("battery.cell_temperature_min", "Lowest cell temperature", "最低電芯溫度")),
            sig("MaxCellTemperature", 48, 16, offset=-273, unit="degC",
                entity=ent("battery.cell_temperature_max", "Highest cell temperature", "最高電芯溫度")),
        ]},
        {"name": "BMS_378_Energy", "can_id": "378", "length": 8, "cycle_ms": 1000, "group": "victron", "signals": [
            sig("ChargedEnergy", 0, 32, factor=0.1, unit="kWh",
                entity=ent("battery.energy_charged", "Energy charged", "累計充電量")),
            sig("DischargedEnergy", 32, 32, factor=0.1, unit="kWh",
                entity=ent("battery.energy_discharged", "Energy discharged", "累計放電量")),
        ]},
        {"name": "VICTRON_379_Capacity", "can_id": "379", "length": 8, "cycle_ms": 1000, "group": "victron", "signals": [
            sig("InstalledCapacity", 0, 16, unit="Ah",
                entity=ent("battery.installed_capacity", "Installed capacity", "安裝容量", precision=0)),
        ]},
        {"name": "INVERTER_305", "can_id": "305", "length": 8, "cycle_ms": 1000, "group": "inverter",
         "comment": "sent by the inverter; current negative while charging (SMA)", "signals": [
            sig("BatteryVoltage", 0, 16, factor=0.1, unit="V", invalid="sma",
                entity=ent("inverter.battery_voltage", "Inverter: battery voltage", "逆變器：電池電壓", enabled=False)),
            sig("BatteryCurrent", 16, 16, signed=True, factor=0.1, unit="A", invalid="sma",
                entity=ent("inverter.battery_current", "Inverter: battery current (negative = charging)",
                           "逆變器：電池電流（負＝充電）", enabled=False)),
            sig("BatteryTemperature", 32, 16, signed=True, factor=0.1, unit="degC", invalid="sma",
                entity=ent("inverter.battery_temperature", "Inverter: battery temperature", "逆變器：電池溫度",
                           enabled=False)),
            sig("SOC", 48, 16, signed=True, factor=0.1, unit="%", invalid="sma",
                entity=ent("inverter.soc", "Inverter: state of charge", "逆變器：電量", device_class="battery",
                           enabled=False)),
        ]},
        {"name": "INVERTER_306", "can_id": "306", "length": 8, "cycle_ms": 1000, "group": "inverter", "signals": [
            sig("SOH", 0, 16, unit="%", invalid="sma"),
            sig("ChargingProcedure", 16, 8),
            sig("OperatingState", 24, 8, values={0: "none", 1: "operating", 3: "warning", 4: "failure"},
                entity=ent("inverter.state", "Inverter state", "逆變器狀態", icon="mdi:solar-power")),
            sig("ActiveError", 32, 16, entity=ent("inverter.error", "Inverter error code", "逆變器錯誤碼",
                                                  format="hex", enabled=False)),
            sig("ChargeVoltageSetpoint", 48, 16, factor=0.1, unit="V", invalid="sma",
                entity=ent("inverter.charge_voltage_setpoint", "Inverter: charge voltage setpoint",
                           "逆變器：充電電壓設定", enabled=False)),
        ]},
    ],
}

# ---- 2. J1939 engine and vehicle --------------------------------------------------------------------
J = "j1939"


def jsig(*args, **kwargs) -> dict:
    kwargs.setdefault("invalid", J)
    return sig(*args, **kwargs)


ENGINE = {
    "id": "j1939_engine_vehicle",
    "version": 1,
    "name": T("J1939 engine and vehicle", "J1939 引擎與車輛"),
    "category": "vehicle",
    "description": T(
        "Trucks, buses, generator sets, farm and marine diesel engines (SAE J1939, FMS): engine speed, torque, "
        "temperatures, oil pressure and level, fuel rate and economy, vehicle speed, battery voltage, engine hours.",
        "卡車、巴士、發電機組、農機與船用柴油引擎（SAE J1939、FMS）：轉速、扭矩、各種溫度、機油壓力與油位、"
        "油耗、車速、電瓶電壓、運轉時數。"),
    "bitrate": 250000,
    "transmits": False,
    "manufacturer": "J1939 ECU",
    "model": "SAE J1939",
    "default_name": T("Engine", "引擎"),
    "source": ["FMS-Standard v02.00 (FMS working group)", "Hatz E1 CAN protocol (2024)",
               "Vector AN-ION-1-3100 Introduction to J1939", "canboat j1939 data (Apache-2.0)",
               "pretty_j1939 (Apache-2.0)"],
    "license": "Facts from public documents, written by WOOWTECH; MIT. The full SPN list (SAE J1939DA) is "
               "licensed by SAE and is not included: import your own DBC for more.",
    "verified": ["Example frames from the FMS standard and Hatz documents"],
    "confidence": "high",
    "notes": T("Fields marked as from open sources only are disabled by default. 0xFE / 0xFF in a field means "
               "error / not available and shows as unavailable.",
               "只有開源資料佐證的欄位預設停用。欄位值 0xFE／0xFF 代表錯誤／無資料，會顯示為無法使用。"),
    "params": [{"key": "source_address", "default": "",
                "description": T("Source address of the ECU in hex (e.g. 00); empty = any",
                                 "ECU 的來源位址（十六進位，例如 00）；空白＝任何")}],
    "groups": [],
    "messages": [
        {"name": "EEC1", "pgn": 61444, "source": "source_address", "length": 8, "cycle_ms": 20, "signals": [
            jsig("DriversDemandTorque", 8, 8, offset=-125, unit="%",
                 entity=ent("engine.demand_torque", "Driver's demand torque", "駕駛需求扭矩", enabled=False)),
            jsig("ActualEngineTorque", 16, 8, offset=-125, unit="%",
                 entity=ent("engine.torque", "Actual engine torque", "引擎實際扭矩", icon="mdi:engine")),
            jsig("EngineSpeed", 24, 16, factor=0.125, unit="rpm",
                 entity=ent("engine.speed", "Engine speed", "引擎轉速", precision=0, icon="mdi:engine")),
            jsig("ControllingDevice", 40, 8,
                 entity=ent("engine.controlling_device", "Torque source address", "扭矩來源位址", format="hex",
                            enabled=False, category="diagnostic")),
            jsig("EngineDemandTorque", 56, 8, offset=-125, unit="%",
                 entity=ent("engine.engine_demand_torque", "Engine demand torque", "引擎需求扭矩", enabled=False)),
        ]},
        {"name": "CCVS1", "pgn": 65265, "source": "source_address", "length": 8, "cycle_ms": 100, "signals": [
            jsig("ParkingBrake", 2, 2, comment="position from open sources only",
                 entity=ent("vehicle.parking_brake", "Parking brake", "手煞車", platform="binary_sensor", enabled=False)),
            jsig("WheelBasedSpeed", 8, 16, factor=1 / 256, unit="km/h",
                 entity=ent("vehicle.speed", "Vehicle speed", "車速", precision=1)),
            jsig("CruiseControlActive", 24, 2,
                 entity=ent("vehicle.cruise_control", "Cruise control", "定速巡航", platform="binary_sensor")),
            jsig("BrakeSwitch", 28, 2,
                 entity=ent("vehicle.brake", "Brake pedal", "煞車踏板", platform="binary_sensor")),
            jsig("ClutchSwitch", 30, 2,
                 entity=ent("vehicle.clutch", "Clutch pedal", "離合器", platform="binary_sensor", enabled=False)),
            jsig("CruiseSetSpeed", 40, 8, unit="km/h", comment="position from open sources only",
                 entity=ent("vehicle.cruise_set_speed", "Cruise set speed", "巡航設定速度", enabled=False)),
            jsig("PtoGovernorState", 48, 5,
                 entity=ent("vehicle.pto_state", "PTO governor state", "PTO 狀態", enabled=False, precision=0,
                            state_class="none")),
        ]},
        {"name": "ET1", "pgn": 65262, "source": "source_address", "length": 8, "cycle_ms": 1000, "signals": [
            jsig("CoolantTemperature", 0, 8, offset=-40, unit="degC",
                 entity=ent("engine.coolant_temperature", "Coolant temperature", "冷卻液溫度")),
            jsig("FuelTemperature", 8, 8, offset=-40, unit="degC",
                 entity=ent("engine.fuel_temperature", "Fuel temperature", "燃油溫度")),
            jsig("OilTemperature", 16, 16, factor=0.03125, offset=-273, unit="degC",
                 entity=ent("engine.oil_temperature", "Oil temperature", "機油溫度", precision=1)),
            jsig("TurboOilTemperature", 32, 16, factor=0.03125, offset=-273, unit="degC",
                 entity=ent("engine.turbo_oil_temperature", "Turbo oil temperature", "渦輪機油溫度",
                            precision=1, enabled=False)),
            jsig("IntercoolerTemperature", 48, 8, offset=-40, unit="degC",
                 entity=ent("engine.intercooler_temperature", "Intercooler temperature", "中冷器溫度", enabled=False)),
            jsig("ThermostatOpening", 56, 8, factor=0.4, unit="%",
                 entity=ent("engine.thermostat_opening", "Thermostat opening", "節溫器開度", enabled=False)),
        ]},
        {"name": "EFL_P1", "pgn": 65263, "source": "source_address", "length": 8, "cycle_ms": 500, "signals": [
            jsig("FuelDeliveryPressure", 0, 8, factor=4, unit="kPa",
                 entity=ent("engine.fuel_pressure", "Fuel delivery pressure", "燃油壓力", enabled=False)),
            jsig("CrankcaseBlowbyPressure", 8, 8, factor=0.05, unit="kPa",
                 entity=ent("engine.blowby_pressure", "Crankcase blow-by pressure", "曲軸箱漏氣壓力", enabled=False)),
            jsig("OilLevel", 16, 8, factor=0.4, unit="%",
                 entity=ent("engine.oil_level", "Oil level", "機油油位", precision=0, icon="mdi:oil-level")),
            jsig("OilPressure", 24, 8, factor=4, unit="kPa",
                 entity=ent("engine.oil_pressure", "Oil pressure", "機油壓力", precision=0)),
            jsig("CrankcasePressure", 32, 16, factor=1 / 128, offset=-250, unit="kPa",
                 entity=ent("engine.crankcase_pressure", "Crankcase pressure", "曲軸箱壓力", precision=1, enabled=False)),
            jsig("CoolantPressure", 48, 8, factor=2, unit="kPa",
                 entity=ent("engine.coolant_pressure", "Coolant pressure", "冷卻液壓力", enabled=False)),
            jsig("CoolantLevel", 56, 8, factor=0.4, unit="%",
                 entity=ent("engine.coolant_level", "Coolant level", "冷卻液液位", precision=0, icon="mdi:coolant-temperature")),
        ]},
        {"name": "LFE1", "pgn": 65266, "source": "source_address", "length": 8, "cycle_ms": 100, "signals": [
            jsig("FuelRate", 0, 16, factor=0.05, unit="L/h",
                 entity=ent("engine.fuel_rate", "Fuel rate", "燃油流率", precision=1, icon="mdi:fuel")),
            jsig("InstantFuelEconomy", 16, 16, factor=1 / 512, unit="km/L",
                 entity=ent("engine.instant_fuel_economy", "Instant fuel economy", "瞬時油耗", precision=1)),
            jsig("AverageFuelEconomy", 32, 16, factor=1 / 512, unit="km/L",
                 entity=ent("engine.average_fuel_economy", "Average fuel economy", "平均油耗", precision=1,
                            enabled=False)),
            jsig("ThrottlePosition", 48, 8, factor=0.4, unit="%",
                 entity=ent("engine.throttle", "Throttle position", "油門開度", precision=0)),
        ]},
        {"name": "VEP1", "pgn": 65271, "source": "source_address", "length": 8, "cycle_ms": 1000, "signals": [
            jsig("BatteryPotential", 32, 16, factor=0.05, unit="V",
                 entity=ent("vehicle.battery_voltage", "Battery voltage", "電瓶電壓")),
            jsig("KeyswitchPotential", 48, 16, factor=0.05, unit="V",
                 entity=ent("vehicle.keyswitch_voltage", "Key switch voltage", "鑰匙開關電壓", enabled=False)),
        ]},
        {"name": "HOURS", "pgn": 65253, "source": "source_address", "length": 8,
         "comment": "some ECUs send it only when asked", "signals": [
            jsig("EngineHours", 0, 32, factor=0.05, unit="h",
                 entity=ent("engine.hours", "Engine hours", "引擎運轉時數", state_class="total_increasing", precision=1)),
            jsig("EngineRevolutions", 32, 32, factor=1000, unit="r",
                 entity=ent("engine.revolutions", "Engine revolutions", "引擎總轉數", state_class="total_increasing",
                            enabled=False)),
        ]},
    ],
}

# ---- 3. J1939 DM1 active faults -----------------------------------------------------------------------
DM1 = {
    "id": "j1939_dm1",
    "version": 1,
    "name": T("J1939 active faults (DM1)", "J1939 作用中故障碼（DM1）"),
    "category": "vehicle",
    "description": T(
        "The warning lamps and active diagnostic trouble codes (SPN, FMI, occurrences) every J1939 ECU "
        "broadcasts, including multi-frame DM1 (transport protocol BAM).",
        "每個 J1939 ECU 都會廣播的警示燈和作用中故障碼（SPN、FMI、次數），包含多封包的 DM1（BAM 傳輸）。"),
    "bitrate": 250000,
    "transmits": False,
    "manufacturer": "J1939 ECU",
    "model": "DM1",
    "default_name": T("Engine faults", "引擎故障"),
    "source": ["SAE J1939-73 summary in public documents", "Scania: Fault codes DM1, issue 6",
               "Linux kernel J1939 documentation", "FMS-Standard v02.00 (BAM example)"],
    "license": "Facts from public documents, written by WOOWTECH; MIT",
    "verified": ["DM1 single frame and BAM transfer examples from the FMS standard"],
    "confidence": "high",
    "notes": T("Fault codes are SPN / FMI numbers; their texts are in the maker's documentation.",
               "故障碼是 SPN／FMI 編號，文字說明要查原廠文件。"),
    "params": [{"key": "source_address", "default": "",
                "description": T("Source address of the ECU in hex; empty = any (faults of several ECUs mix)",
                                 "ECU 的來源位址（十六進位）；空白＝任何（多顆 ECU 的故障會混在一起）")}],
    "groups": [],
    "messages": [
        {"name": "DM1", "pgn": 65226, "source": "source_address", "length": 8, "cycle_ms": 1000,
         "transport": "j1939_tp", "decoder": "j1939_dm1", "signals": [
            sig("MalfunctionLamp", 0, 0, decoder_field="malfunction_lamp",
                entity=problem("faults.malfunction_lamp", "Malfunction lamp (MIL)", "故障指示燈（MIL）", enabled=True)),
            sig("RedStopLamp", 0, 0, decoder_field="red_stop_lamp",
                entity=problem("faults.red_stop_lamp", "Red stop lamp", "紅色停車燈", enabled=True)),
            sig("AmberWarningLamp", 0, 0, decoder_field="amber_warning_lamp",
                entity=problem("faults.amber_warning_lamp", "Amber warning lamp", "琥珀色警告燈", enabled=True)),
            sig("ProtectLamp", 0, 0, decoder_field="protect_lamp",
                entity=problem("faults.protect_lamp", "Protect lamp", "保護燈", enabled=True)),
            sig("ActiveFaults", 0, 0, decoder_field="dtc_count",
                entity=ent("faults.count", "Active faults", "作用中故障數", precision=0, state_class="measurement",
                           icon="mdi:alert-circle")),
            sig("FaultCodes", 0, 0, decoder_field="dtc_text",
                entity=ent("faults.codes", "Fault codes", "故障碼", icon="mdi:format-list-bulleted",
                           attributes=["dtcs"])),
        ]},
    ],
}

# ---- 4. NMEA 2000 DC / battery ---------------------------------------------------------------------
N = "n2k"
N2K = {
    "id": "nmea2000_dc",
    "version": 1,
    "name": T("NMEA 2000 battery / DC status (Victron VE.Can)", "NMEA 2000 電池／直流狀態（Victron VE.Can）"),
    "category": "marine",
    "description": T(
        "Battery monitors, shunts and chargers on NMEA 2000 or Victron VE.Can (Lynx Shunt, BMV via interface, "
        "MPPT): voltage, current, power, temperature (PGN 127508) and state of charge, health, time remaining "
        "(PGN 127506, fast-packet).",
        "NMEA 2000 或 Victron VE.Can 上的電池監測器、分流器、充電器（Lynx Shunt、經介面的 BMV、MPPT）：電壓、"
        "電流、功率、溫度（PGN 127508），以及電量、健康度、剩餘時間（PGN 127506，fast-packet）。"),
    "bitrate": 250000,
    "transmits": False,
    "manufacturer": "NMEA 2000",
    "model": "PGN 127508 / 127506",
    "default_name": T("DC battery", "直流電池"),
    "source": ["canboat (Apache-2.0)", "Victron: Data communication with Victron Energy products (whitepaper rev. 31)"],
    "license": "Facts from canboat (Apache-2.0) and Victron documents, written by WOOWTECH; MIT",
    "verified": ["canboat sample frames for 127508 and 127506"],
    "confidence": "high",
    "notes": T("Several devices may use the same instance: set the source address too.",
               "可能有好幾個設備用同一個 instance，建議也填來源位址。"),
    "params": [
        {"key": "instance", "default": 0, "description": T("Battery / DC instance (0-252)", "電池／直流 instance（0–252）")},
        {"key": "source_address", "default": "",
         "description": T("Source address in hex; empty = any", "來源位址（十六進位）；空白＝任何")},
    ],
    "groups": [],
    "messages": [
        {"name": "BatteryStatus_127508", "pgn": 127508, "source": "source_address", "length": 8, "cycle_ms": 1500,
         "filters": [{"byte": 0, "value": "instance"}], "signals": [
            sig("Instance", 0, 8),
            sig("Voltage", 8, 16, signed=True, factor=0.01, unit="V", invalid=N,
                entity=ent("battery.voltage", "Voltage", "電壓")),
            sig("Current", 24, 16, signed=True, factor=0.1, unit="A", invalid=N,
                entity=ent("battery.current", "Current", "電流")),
            sig("Temperature", 40, 16, factor=0.01, offset=-273.15, unit="degC", invalid=N,
                entity=ent("battery.temperature", "Temperature", "溫度", precision=1)),
            sig("SID", 56, 8),
            sig("Power", 0, 0, unit="W", derive={"op": "product", "of": ["Voltage", "Current"]},
                entity=ent("battery.power", "Power", "功率", precision=0)),
        ]},
        {"name": "DcDetailedStatus_127506", "pgn": 127506, "source": "source_address", "length": 11,
         "cycle_ms": 1500, "transport": "n2k_fast", "filters": [{"byte": 1, "value": "instance"}], "signals": [
            sig("SID", 0, 8),
            sig("Instance", 8, 8),
            sig("DcType", 16, 8, values={0: "battery", 1: "alternator", 2: "converter", 3: "solar_cell", 4: "wind_generator"},
                entity=ent("dc.type", "DC type", "直流類型", enabled=False, category="diagnostic")),
            sig("StateOfCharge", 24, 8, unit="%", invalid=N,
                entity=ent("battery.soc", "State of charge", "電量", device_class="battery", precision=0)),
            sig("StateOfHealth", 32, 8, unit="%", invalid=N,
                entity=ent("battery.soh", "State of health", "健康度", precision=0, icon="mdi:heart-pulse")),
            sig("TimeRemaining", 40, 16, unit="min", invalid=N,
                entity=ent("battery.time_remaining", "Time remaining", "剩餘時間", precision=0)),
            sig("RippleVoltage", 56, 16, factor=0.001, unit="V", invalid=N,
                entity=ent("battery.ripple_voltage", "Ripple voltage", "漣波電壓", enabled=False)),
            sig("RemainingCapacity", 72, 16, unit="Ah", invalid=N,
                entity=ent("battery.remaining_capacity", "Remaining capacity", "剩餘容量", precision=0, enabled=False)),
        ]},
    ],
}

# ---- 5. CANopen node monitor -----------------------------------------------------------------------
CANOPEN = {
    "id": "canopen_node_monitor",
    "version": 1,
    "name": T("CANopen node monitor (heartbeat, emergency)", "CANopen 節點監看（heartbeat、緊急訊息）"),
    "category": "industrial",
    "description": T(
        "Any CANopen device (CiA 301): online / offline from its heartbeat, its NMT state, and emergency "
        "messages with their error code. The node must produce a heartbeat (object 0x1017); many leave the "
        "factory with it off.",
        "任何 CANopen 設備（CiA 301）：由 heartbeat 判斷在線／離線、NMT 狀態，以及緊急訊息與錯誤碼。設備要有開 "
        "heartbeat（物件 0x1017），很多設備出廠是關的。"),
    "bitrate": None,
    "transmits": False,
    "manufacturer": "CANopen",
    "model": "CiA 301 node",
    "default_name": T("CANopen node", "CANopen 節點"),
    "source": ["CiA 301 v4.02 (facts only)", "CANopenNode (Apache-2.0)", "python canopen (MIT)",
               "ICP DAS and maxon EPOS4 manuals (emergency examples)"],
    "license": "Facts from public documents, written by WOOWTECH; MIT",
    "verified": ["Heartbeat and emergency frames from the ICP DAS and maxon manuals"],
    "confidence": "high",
    "notes": T("An error code of 0000 clears the emergency.", "錯誤碼 0000 代表解除緊急狀態。"),
    "params": [
        {"key": "node_id", "default": 1, "description": T("Node ID (1-127)", "節點編號（1–127）")},
        {"key": "heartbeat_ms", "default": 1000,
         "description": T("The node's heartbeat period in ms (object 0x1017)", "節點的 heartbeat 週期，毫秒（物件 0x1017）")},
    ],
    "groups": [],
    "messages": [
        {"name": "Heartbeat", "can_id": "0x700 + node_id", "extended": False, "length": 1, "cycle_ms": "heartbeat_ms",
         "signals": [
            sig("State", 0, 7, values={0: "boot_up", 4: "stopped", 5: "operational", 127: "pre_operational"},
                entity=ent("node.state", "NMT state", "NMT 狀態", icon="mdi:state-machine")),
            sig("Online", 0, 0, derive={"op": "present"},
                entity=ent("node.online", "Online", "在線", platform="binary_sensor", device_class="connectivity",
                           on_timeout="off")),
        ]},
        {"name": "Emergency", "can_id": "0x80 + node_id", "extended": False, "length": 8, "signals": [
            sig("ErrorCode", 0, 16, entity=ent("node.error_code", "Emergency error code", "緊急錯誤碼", format="hex",
                                                icon="mdi:alert")),
            sig("ErrorRegister", 16, 8, entity=ent("node.error_register", "Error register", "錯誤暫存器", format="hex",
                                                    enabled=False)),
            sig("ManufacturerError", 24, 40),
            sig("InError", 0, 0, derive={"op": "nonzero", "of": ["ErrorCode"]},
                entity=problem("node.error", "Error active", "錯誤中", enabled=True)),
        ]},
    ],
}

TEMPLATES = [BMS, ENGINE, DM1, N2K, CANOPEN]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for template in TEMPLATES:
        path = OUT / f"{template['id']}.json"
        path.write_text(json.dumps(template, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(template['messages'])} messages, "
              f"{sum(len(m['signals']) for m in template['messages'])} signals")


if __name__ == "__main__":
    main()
