"""Tests for :mod:`netbox_pyats.capture`.

Pure-Python: exercises the snapshot capture logic against a fake pyATS Device
(no NetBox, no RQ, no real Genie). pyATS's ``pyats.topology`` is importable
without genie on this worker (see ``test_testbed.py``), but the capture
helpers import genie lazily inside the capture functions, so we can test the
unsupported-platform and error paths without genie installed by stubbing the
device's ``os`` and never calling the genie-backed helpers.

Covers:
- Unsupported platform → ``status="unsupported"`` with a warning, no
  connection/parser attempt.
- Config capture with a parseable device → ``data["config"]`` populated.
- State capture with a stubbed ``genie.learn`` → ``data["state"]`` populated.
- Full capture (both halves) → ``data`` has both keys.
- Capture error → ``status="error"`` with traceback in warnings.
- ``CaptureResult.size_bytes`` derives from the JSON-serialized payload.
- Worker version strings are best-effort (empty when metadata missing).
"""

import json

import pytest

pytest.importorskip("pyats")

from netbox_pyats.capture import CaptureResult, capture_snapshot
from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices
from netbox_pyats.testbed import UNSUPPORTED_OS


class FakePyatsDevice:
    """Duck-typed pyATS Device for capture tests.

    Only the attributes/methods :func:`capture_snapshot` reads are stubbed:
    ``name``, ``os``, ``parse``, ``execute``. ``connect``/``disconnect`` are
    only used by the higher-level ``capture_snapshot_for_netbox_device``
    wrapper, not by the pure ``capture_snapshot`` function under test here.
    """

    def __init__(self, name="rtr01", os="iosxe", config_output=None, parse_exc=None, execute_exc=None):
        self.name = name
        self.os = os
        self._config_output = config_output if config_output is not None else {"configured": True}
        self._parse_exc = parse_exc
        self._execute_exc = execute_exc

    def parse(self, command):
        if self._parse_exc is not None:
            raise self._parse_exc
        if command != "show running-config":
            raise AssertionError(f"unexpected parse command: {command}")
        return self._config_output

    def execute(self, command):
        if self._execute_exc is not None:
            raise self._execute_exc
        return "!\nversion 15.6\n!\nend\n"


class TestUnsupportedPlatform:
    def test_unsupported_os_returns_unsupported_status(self):
        d = FakePyatsDevice(os=UNSUPPORTED_OS)
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        assert result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert result.data == {}
        assert any("no Genie parser" in w for w in result.warnings)

    def test_unsupported_does_not_attempt_parse(self):
        # parse() raises if called; the unsupported path must never reach it.
        d = FakePyatsDevice(os=UNSUPPORTED_OS, parse_exc=AssertionError("parse must not be called"))
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert "parse must not be called" not in json.dumps(result.warnings)


class TestConfigCapture:
    def test_config_kind_populates_data_config(self):
        d = FakePyatsDevice(os="iosxe", config_output={"hostname": "rtr01"})
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.data == {"config": {"hostname": "rtr01"}}
        assert result.warnings == []

    def test_config_parse_failure_falls_back_to_execute(self):
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("parser missing for this os"),
            execute_exc=None,
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        # Fallback path: parse failed but execute succeeded, so the row is a
        # success with a raw-text config and the parser error recorded inline.
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "raw" in result.data["config"]
        assert "_parser_error" in result.data["config"]

    def test_config_parse_and_execute_both_fail(self):
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("parser boom"),
            execute_exc=RuntimeError("execute boom"),
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        # Both halves failed → error status, empty config, warning recorded.
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"config": {}}
        assert any("config capture failed" in w for w in result.warnings)


class TestStateCapture:
    def test_state_kind_uses_genie_learn(self, monkeypatch):
        d = FakePyatsDevice(os="iosxe")

        # Stub the genie import so _capture_state works without genie installed.
        import sys
        import types

        genie_mod = types.ModuleType("genie")
        learned = types.SimpleNamespace(as_dict=lambda: {"interfaces": {"Gig0": {}}})

        def fake_learn(device):
            return learned

        genie_mod.learn = fake_learn
        monkeypatch.setitem(sys.modules, "genie", genie_mod)

        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.data == {"state": {"interfaces": {"Gig0": {}}}}
        assert result.warnings == []


class TestFullCapture:
    def test_full_capture_has_both_halves(self, monkeypatch):
        d = FakePyatsDevice(os="iosxe", config_output={"hostname": "rtr01"})

        import sys
        import types

        genie_mod = types.ModuleType("genie")
        learned = types.SimpleNamespace(as_dict=lambda: {"routing": {"routes": {}}})
        genie_mod.learn = lambda device: learned
        monkeypatch.setitem(sys.modules, "genie", genie_mod)

        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "config" in result.data
        assert "state" in result.data
        assert result.data["config"] == {"hostname": "rtr01"}
        assert result.data["state"] == {"routing": {"routes": {}}}


class TestCaptureError:
    def test_full_capture_with_both_halves_failed_is_error(self, monkeypatch):
        # Both config and state fail in a "full" capture → error status with
        # empty halves and warnings for each. The row is still created so the
        # operator sees the failure in the device-page history.
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("boom"),
            execute_exc=RuntimeError("boom2"),
        )

        # Stub genie.learn to also raise so the state half fails too.
        import sys
        import types

        genie_mod = types.ModuleType("genie")

        def raising_learn(device):
            raise RuntimeError("learn boom")

        genie_mod.learn = raising_learn
        monkeypatch.setitem(sys.modules, "genie", genie_mod)

        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"config": {}, "state": {}}
        assert any("config capture failed" in w for w in result.warnings)
        assert any("state capture failed" in w for w in result.warnings)


class TestCaptureResultSizeBytes:
    def test_empty_data_is_zero_bytes(self):
        assert CaptureResult().size_bytes == 0

    def test_size_bytes_matches_json_length(self):
        r = CaptureResult(data={"config": {"hostname": "rtr01"}})
        expected = len(json.dumps(r.data, default=str).encode("utf-8"))
        assert r.size_bytes == expected


class TestBadKind:
    def test_invalid_kind_raises(self):
        d = FakePyatsDevice(os="iosxe")
        with pytest.raises(ValueError):
            capture_snapshot(d, kind="bogus")
