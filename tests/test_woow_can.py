"""Unit tests of WOOW CAN's logic (no Home Assistant instance or CAN hardware needed)."""

from __future__ import annotations

import pytest

from custom_components.woow_can import SEND_SCHEMA
from custom_components.woow_can import config_flow as cf
from custom_components.woow_can.can_port import CanFrame, parse_filters, parse_id
from custom_components.woow_can.const import CAN_DEFAULTS


@pytest.mark.parametrize("text", ["123#11223344", "18FF50E5#0102", "456##1000102030405060708090A0B"])
def test_frames_round_trip(text):
    frame = CanFrame.parse(text)
    assert CanFrame.unpack(frame.pack()) == frame
    assert str(frame) == text


def test_frame_details():
    assert CanFrame.parse("123#R").rtr
    assert len(CanFrame.parse("456##1000102030405060708090A").data) == 12  # 11 bytes padded to FD length 12
    assert parse_id("7E8") == (0x7E8, False) and parse_id("18FF50E5") == (0x18FF50E5, True)
    assert CanFrame.parse("18FF50E5#0102").as_dict()["id_hex"] == "18FF50E5"
    with pytest.raises(ValueError):
        CanFrame.parse("123#112233445566778899")  # 9 bytes on classic CAN


def test_filters():
    assert [(hex(i), hex(m)) for i, m in parse_filters("123, 7E0/7F0")] == [("0x123", "0x800007ff"), ("0x7e0", "0x800007f0")]
    assert parse_filters("") == []
    with pytest.raises(ValueError):
        parse_filters("XYZ")


def test_form_and_service_schema():
    import probatio
    from homeassistant.helpers import config_validation as cv

    for fd in (False, True):
        vals = {**CAN_DEFAULTS, "name": "CAN0"}
        schema = cf.can_schema(vals, True, fd)
        probatio.to_field_list(schema, custom_serializer=cv.custom_serializer)
        form = {k: (str(v) if k in ("bitrate", "dbitrate") else v) for k, v in vals.items()}
        if not fd:
            form.pop("fd"), form.pop("dbitrate")
        assert cf.coerce(schema(form))["bitrate"] == 500000
    assert cf.filters_error({"filters": "123, nope"}) == {"filters": "bad_filter"}
    sent = SEND_SCHEMA({"config_entry_id": "x", "can_id": "7DF", "data": "02 01 0C", "wait_id": "7E8", "wait_ms": 500})
    assert sent["fd"] is False and sent["wait_ms"] == 500
