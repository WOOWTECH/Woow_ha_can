"""Pre-install check of custom_components/woow_can inside the HA Core container.

Run with `nocan` while Home Assistant owns can0 / can1 (the loopback test needs them free).
"""
import asyncio, glob, importlib, json, py_compile, sys

sys.path.insert(0, "/tmp/wctest")
BASE = "/tmp/wctest/custom_components/woow_can"
import homeassistant  # noqa: F401  (installs probatio as `voluptuous` first, like HA itself does)

for f in sorted(glob.glob(BASE + "/*.py")):
    py_compile.compile(f, doraise=True)
for f in sorted(glob.glob(BASE + "/translations/*.json")) + [BASE + "/manifest.json"]:
    json.load(open(f, encoding="utf-8"))
import yaml
yaml.safe_load(open(BASE + "/services.yaml", encoding="utf-8"))
print("compile / json / yaml: ok")

for m in ("const", "codec", "can_port", "hub", "entity", "text", "sensor", "event", "config_flow", "__init__"):
    importlib.import_module("custom_components.woow_can" + ("" if m == "__init__" else "." + m))
print("imports against this HA version: ok")

from custom_components.woow_can.can_port import (CanConfig, CanFrame, CanPort, link_configure,
                                                 parse_filters, CTRLMODE_LOOPBACK)
for text in ("123#11223344", "18FF50E5#0102", "123#R", "456##1000102030405060708090A0B"):
    f = CanFrame.parse(text)
    if not f.rtr:
        assert CanFrame.unpack(f.pack()) == f, text
assert len(CanFrame.parse("456##1000102030405060708090A").data) == 12  # 11 bytes padded to FD length 12
assert [(hex(i), hex(m)) for i, m in parse_filters("123, 7E0/7F0")] == [("0x123", "0x800007ff"), ("0x7e0", "0x800007f0")]
print("frames / filters: ok")

import probatio
from homeassistant.helpers import config_validation as cv
from custom_components.woow_can import SEND_SCHEMA
from custom_components.woow_can import config_flow as cf
from custom_components.woow_can.const import CAN_DEFAULTS
found = cf.scan_interfaces()
print("  interfaces:", found)
for name, driver in found.items():
    vals = {**CAN_DEFAULTS, "name": name.upper()}
    schema = cf.can_schema(vals, True, driver in cf.FD_DRIVERS)
    fields = probatio.to_field_list(schema, custom_serializer=cv.custom_serializer)
    form = {k: (str(v) if k in ("bitrate", "dbitrate") else v) for k, v in vals.items()}
    if driver not in cf.FD_DRIVERS:
        form.pop("fd"), form.pop("dbitrate")
    print(f"  {name}: {len(fields)} form fields -> {cf.coerce(schema(form))}")
print("  send:", SEND_SCHEMA({"config_entry_id": "x", "can_id": "7DF", "data": "02 01 0C", "wait_id": "7E8", "wait_ms": 500}))
print("config flow / service schema: ok")


async def loopback(ifname, fd):
    got, txs, errs, lost = [], [], [], []
    cfg = CanConfig(ifname, bitrate=500000, fd=fd, dbitrate=2000000, loopback=True, max_rate=100)
    port = CanPort(asyncio.get_running_loop(), cfg, lambda f, over=False: got.append(f), txs.append, errs.append, lost.append)
    await port.open()
    try:
        f = CanFrame.parse("123#11223344")
        assert await port.request(f, lambda r: r.can_id == 0x123 and not r.extended, 1.0) == f
        await port.send(CanFrame.parse("18FF50E5#0102030405060708"))
        if fd:
            await port.send(CanFrame.parse("456##1000102030405060708090A0B"))
        await asyncio.sleep(0.2)
        status = await asyncio.get_running_loop().run_in_executor(None, port.status)
        print(f"  {ifname}: received {[str(x) for x in got]} state={status.get('state')} fd={status.get('fd')}")
        assert len(txs) == (3 if fd else 2) and not lost
    finally:
        await port.close()
        link_configure(ifname, 0, CTRLMODE_LOOPBACK, 0, 0)  # leave the controller out of loopback
    print(f"CAN {ifname} (controller loopback): ok")


if "nocan" not in sys.argv:
    asyncio.run(loopback("can0", False))
    asyncio.run(loopback("can1", True))
