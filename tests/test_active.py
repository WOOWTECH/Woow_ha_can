"""Devices that send: requests and their scheduler, writable signals and their checks."""

from __future__ import annotations

import types

import pytest

from custom_components.woow_can import polling as req_mod
from custom_components.woow_can.devices import Device, is_write
from custom_components.woow_can.signals import DefinitionError, Message


def device(**extra) -> Device:
    raw = {"name": "Test", "interface": "entry", "messages": [
        {"name": "ReplyA", "can_id": "581", "filters": [{"byte": 0, "values": ["0x4B", "0x43"]}],
         "signals": [{"name": "A", "start": 32, "length": 16}]},
        {"name": "ReplyB", "can_id": "582", "signals": [{"name": "B", "start": 0, "length": 8}]},
    ], "requests": [
        {"name": "Ask A", "can_id": "601", "data": "40 41 60 00 00 00 00 00", "period_ms": 100, "reply": "ReplyA",
         "timeout_ms": 50},
        {"name": "Ask B", "can_id": "602", "data": [1, 2], "period_ms": 1000, "reply": "ReplyB", "timeout_ms": 50},
    ], "active": True}
    raw.update(extra)
    return Device.from_dict(raw)


def test_filters_take_value_lists():
    msg = Message.from_dict({"name": "x", "can_id": "581", "filters": [{"byte": 0, "values": ["0x4B", 0x43]},
                                                                       {"byte": 1, "value": "0x41"}], "signals": []})
    assert msg.matches(0x581, bytes([0x4B, 0x41])) and msg.matches(0x581, bytes([0x43, 0x41]))
    assert not msg.matches(0x581, bytes([0x4F, 0x41])) and not msg.matches(0x581, bytes([0x4B, 0x42]))
    assert msg.as_dict()["filters"] == [{"byte": 0, "values": [0x4B, 0x43]}, {"byte": 1, "value": 0x41}]
    assert Message.from_dict(msg.as_dict()).filters == msg.filters


def test_masked_lookup():
    msg = Message.from_dict({"name": "x", "can_id": "181", "signals": [
        {"name": "Word", "start": 0, "length": 16},
        {"name": "State", "start": 0, "length": 0, "derive": {"op": "masked_lookup", "of": ["Word"], "table": [
            ["0x006F", "0x0027", "operation_enabled"], ["0x004F", "0x0008", "fault"]]}}]})
    assert msg.decode(bytes([0x37, 0x02]))["State"] == "operation_enabled"
    assert msg.decode(bytes([0x08, 0x00]))["State"] == "fault"
    assert msg.decode(bytes([0x40, 0x00]))["State"] is None


def test_send_messages_keep_their_fixed_bytes():
    msg = Message.from_dict({"name": "Write", "can_id": "601", "send": True, "data": "2B 40 60 00 00 00 00 00",
                             "signals": [{"name": "Controlword", "start": 32, "length": 16}]}, {})
    assert msg.build({"Controlword": 6}) == bytes.fromhex("2B40600006000000")
    assert msg.build({"Controlword": 15}, bytes.fromhex("2B40600006000000")) == bytes.fromhex("2B4060000F000000")
    assert Message.from_dict(msg.as_dict()).base == msg.base


def test_device_round_trip_and_checks():
    dev = device()
    again = Device.from_dict(dev.as_dict())
    assert again.requests == dev.requests and again.active and not again.allow_write
    assert dev.requests[1].data == b"\x01\x02" and dev.requests[0].raw_id == 0x601
    with pytest.raises(DefinitionError, match="unknown_reply"):
        device(requests=[{"name": "x", "can_id": "601", "period_ms": 100, "reply": "Nope"}])
    with pytest.raises(DefinitionError, match="bad_request"):
        device(requests=[{"name": "x", "can_id": "601", "period_ms": 10}])  # faster than 100 ms
    with pytest.raises(DefinitionError, match="bad_max_rate"):
        device(max_rate=500)


def writable(entity: dict, *, send: bool = True, extra_signal: dict | None = None) -> Device:
    sig = {"name": "Out", "start": 0, "length": 8, "entity": entity, **(extra_signal or {})}
    return Device.from_dict({"name": "W", "interface": "entry", "messages": [
        {"name": "Cmd", "can_id": "201", "send": send, "signals": [sig]}]})


def test_writable_signals_are_checked_and_gated():
    sw = writable({"platform": "switch"})
    assert sw.writable and is_write(sw.messages[0].signals[0])
    assert sw.adopted() == []  # writing not allowed: no entity
    sw.allow_write = True
    assert len(sw.adopted()) == 1
    with pytest.raises(DefinitionError, match="no_write_target"):
        writable({"platform": "switch"}, send=False)
    with pytest.raises(DefinitionError, match="number_needs_range"):
        writable({"platform": "number"})
    writable({"platform": "number", "min": 0, "max": 100})
    with pytest.raises(DefinitionError, match="select_needs_values"):
        writable({"platform": "select"})
    writable({"platform": "select"}, extra_signal={"values": {"0": "off", "1": "auto"}})
    with pytest.raises(DefinitionError, match="button_needs_press"):
        writable({"platform": "button"})
    feedback = Device.from_dict({"name": "F", "interface": "entry", "messages": [
        {"name": "Status", "can_id": "181", "signals": [
            {"name": "Relay", "start": 0, "length": 1, "entity": {"platform": "switch",
                                                                  "write": {"message": "Cmd", "signal": "Out"}}}]},
        {"name": "Cmd", "can_id": "201", "send": True, "signals": [{"name": "Out", "start": 0, "length": 1}]}]})
    assert feedback.writable


# ---- the scheduler ----------------------------------------------------------------------------------
class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


class FakeHass:
    loop = types.SimpleNamespace(call_later=lambda delay, cb: types.SimpleNamespace(cancel=lambda: None))

    def async_create_task(self, coro, name=None, eager_start=True):
        coro.close()


class FakeManager:
    def __init__(self, *devices: Device) -> None:
        self.devices = {d.id: d for d in devices}
        self.blocked: str | None = None
        self.pushed = 0

    def cannot_send(self, entry_id: str) -> str | None:
        return self.blocked

    async def async_send(self, entry_id, frame) -> None:  # pragma: no cover - the fake loop never runs it
        pass

    def push_requests(self) -> None:
        self.pushed += 1


@pytest.fixture
def run(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(req_mod.time, "monotonic", clock)

    def make(*devices: Device):
        manager = FakeManager(*devices)
        sched = req_mod.RequestScheduler(FakeHass(), manager)
        sent: list[tuple[float, str]] = []
        original = sched._send

        def record(dev, st, now):
            sent.append((round(now - 1000, 3), st.request.name))
            original(dev, st, now)

        sched._send = record
        sched.start()

        def advance(seconds: float, reply: dict[str, float] | None = None) -> None:
            """Tick every 50 ms; `reply` answers a request this long after it was sent."""
            end = clock.t + seconds
            while clock.t < end - 1e-9:
                clock.t = round(clock.t + req_mod.TICK, 6)
                if reply:
                    for st in sched.states.values():
                        delay = reply.get(st.request.name)
                        if delay is not None and st.pending_since is not None and clock.t - st.pending_since >= delay:
                            sched.on_message(st.device_id, st.request.reply)
                sched._tick()

        return sched, manager, sent, advance

    return make


def test_one_pending_request_per_device_and_periods(run):
    sched, _m, sent, advance = run(device())
    advance(2.0, reply={"Ask A": 0.05, "Ask B": 0.05})
    names = [n for _t, n in sent]
    assert names.count("Ask B") == 2  # every second
    assert 15 <= names.count("Ask A") <= 20  # every 100 ms, now and then after B's reply
    status = {s["name"]: s for s in sched.status(next(iter(sched.by_device)))}
    assert status["Ask A"]["state"] == "ok" and status["Ask A"]["sent"] - status["Ask A"]["replies"] <= 1  # one in flight
    pending_together = [t for t, n in sent if n == "Ask B" and (t, "Ask A") in sent]
    assert not pending_together  # never two requests of one device at the same moment


def test_missing_replies_back_off_and_recover(run):
    sched, _m, sent, advance = run(device(requests=[{"name": "Ask B", "can_id": "602", "period_ms": 200,
                                                     "reply": "ReplyB", "timeout_ms": 50}]))
    advance(1.0)  # no replies at all
    st = next(iter(sched.states.values()))
    assert st.misses >= 3 and st.backoff >= 1 and st.status(0)["state"] == "no_reply"
    before = len(sent)
    advance(3.0)
    assert len(sent) - before <= 4  # backed off: far fewer than 15
    assert st.period > 0.2
    advance(15.0, reply={"Ask B": 0.02})
    assert st.backoff == 0 and st.misses == 0 and st.status(0)["state"] == "ok"


def test_rate_cap_and_pause(run):
    fast = device(max_rate=2, requests=[{"name": "Ask A", "can_id": "601", "period_ms": 100}])  # no reply expected
    sched, manager, sent, advance = run(fast)
    advance(3.0)
    assert 5 <= len(sent) <= 8  # 2 a second (plus the first token), not 30
    manager.blocked = "listen-only"
    before = len(sent)
    advance(2.0)
    assert len(sent) == before and next(iter(sched.states.values())).status(0)["state"] == "paused"


def test_inactive_devices_send_nothing(run):
    sched, _m, sent, advance = run(device(active=False))
    advance(1.0)
    assert sent == [] and sched.states == {}


def test_writable_entities_keep_the_state_writer():
    """SignalEntity._write publishes the state; a writable entity must not replace it (0.5.0 development bug)."""
    from custom_components.woow_can import managed

    for cls in (managed.SignalSwitch, managed.SignalNumber, managed.SignalSelect, managed.SignalButton):
        assert cls._write is managed.SignalEntity._write, cls.__name__
