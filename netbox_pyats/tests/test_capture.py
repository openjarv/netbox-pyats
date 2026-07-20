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
- State capture via ``device.parse(<state command>)`` for each command in
  :data:`netbox_pyats.capture.STATE_COMMANDS`; per-command parser misses are
  recorded as warnings.
- Full capture (both halves) → ``data`` has both keys.
- Capture error → ``status="error"`` with traceback in warnings.
- ``CaptureResult.size_bytes`` derives from the JSON-serialized payload.
- Worker version strings are best-effort (empty when metadata missing).
"""

import json

import pytest

pytest.importorskip("pyats")

from netbox_pyats.capture import STATE_COMMANDS, CaptureResult, capture_snapshot
from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices
from netbox_pyats.testbed import UNSUPPORTED_OS


class ParserNotFound(Exception):
    """Duck-type stand-in for ``genie.libs.parser.utils.common.ParserNotFound``.

    The real class is only importable on the worker (where genie is
    installed). :func:`netbox_pyats.capture._capture_state` duck-types the
    exception by class name (``type(exc).__name__ == 'ParserNotFound'``), so we
    name this class identically so the helper treats it the same way.
    """


class FakePyatsDevice:
    """Duck-typed pyATS Device for capture tests.

    Only the attributes/methods :func:`capture_snapshot` reads are stubbed:
    ``name``, ``os``, ``parse``, ``execute``. ``connect``/``disconnect`` are
    only used by the higher-level ``capture_snapshot_for_netbox_device``
    wrapper, not by the pure ``capture_snapshot`` function under test here.

    ``parse(command)`` returns the configured output for the command, or raises
    :class:`FakeParserNotFound` for commands in ``unsupported_commands``, or
    raises ``parse_exc`` for any command if set.
    """

    def __init__(
        self,
        name="rtr01",
        os="iosxe",
        config_output=None,
        state_outputs=None,
        unsupported_commands=None,
        parse_exc=None,
        execute_exc=None,
    ):
        self.name = name
        self.os = os
        self._config_output = config_output if config_output is not None else {"configured": True}
        self._state_outputs = dict(state_outputs or {})
        self._unsupported = set(unsupported_commands or [])
        self._parse_exc = parse_exc
        self._execute_exc = execute_exc

    def parse(self, command):
        if self._parse_exc is not None:
            raise self._parse_exc
        if command in self._unsupported:
            raise ParserNotFound(f"Could not find parser for '{command}' under {self.os}")
        if command == "show running-config":
            return self._config_output
        if command in self._state_outputs:
            return self._state_outputs[command]
        # Default: return an empty-but-typed dict for any state command the
        # test did not explicitly configure. This mirrors how Genie returns
        # an empty-but-typed dict for a parsed-but-empty command.
        return {}

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
        # Both the structured Genie dict (config) and the raw running-config
        # text (config_raw) are captured; compliance uses config_raw.
        assert result.data == {
            "config": {"hostname": "rtr01"},
            "config_raw": "!\nversion 15.6\n!\nend\n",
        }
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
        # config_raw is still populated from the successful execute() call.
        assert result.data["config_raw"] == "!\nversion 15.6\n!\nend\n"

    def test_config_parse_and_execute_both_fail(self):
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("parser boom"),
            execute_exc=RuntimeError("execute boom"),
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        # Both halves failed → error status, empty config, warning recorded.
        # config_raw is "" (execute failed) — compliance against this snapshot
        # classifies as error with "snapshot raw config is empty".
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"config": {}, "config_raw": ""}
        assert any("config capture failed" in w for w in result.warnings)


class TestStateCapture:
    def test_state_kind_captures_each_state_command(self):
        """kind=state runs device.parse() for each command in STATE_COMMANDS."""
        state_outputs = {
            "show version": {"version": "16.12"},
            "show inventory": {"chassis": "C9300"},
            "show ip interface brief": {"Gig0": {"ip": "10.0.0.1"}},
        }
        d = FakePyatsDevice(os="iosxe", state_outputs=state_outputs)
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        # Every state command is captured, keyed by command.
        assert "state" in result.data
        for command in STATE_COMMANDS:
            assert command in result.data["state"]
        assert result.data["state"]["show version"] == {"version": "16.12"}
        assert result.data["state"]["show ip interface brief"] == {"Gig0": {"ip": "10.0.0.1"}}
        assert result.warnings == []

    def test_state_capture_skips_commands_without_a_parser(self):
        """Per-command ParserNotFound is recorded as a warning, not a failure."""
        # 'show inventory' has no parser on this os; the other two do.
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show inventory"],
            state_outputs={
                "show version": {"version": "16.12"},
                "show ip interface brief": {},
            },
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        # The unsupported command is recorded as None in the state dict.
        assert result.data["state"]["show inventory"] is None
        # The supported commands are captured.
        assert result.data["state"]["show version"] == {"version": "16.12"}
        # A warning was recorded for the skipped command.
        assert any("show inventory" in w for w in result.warnings)
        assert any("no Genie parser" in w for w in result.warnings)


class TestFullCapture:
    def test_full_capture_has_both_halves(self):
        d = FakePyatsDevice(
            os="iosxe",
            config_output={"hostname": "rtr01"},
            state_outputs={
                "show version": {"version": "16.12"},
                "show inventory": {},
                "show ip interface brief": {},
            },
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "config" in result.data
        assert "state" in result.data
        assert result.data["config"] == {"hostname": "rtr01"}
        assert "config_raw" in result.data  # captured for compliance
        assert "show version" in result.data["state"]


class TestCaptureError:
    def test_full_capture_with_both_halves_failed_is_error(self):
        # Both config and state fail in a "full" capture → error status with
        # empty halves and warnings for each. The row is still created so the
        # operator sees the failure in the device-page history.
        # parse_exc applies to every parse() call (config + state), and
        # execute_exc applies to the config fallback path.
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("parse boom"),
            execute_exc=RuntimeError("execute boom"),
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        # config_raw is "" (execute failed) — compliance against this
        # snapshot classifies as error with "snapshot raw config is empty".
        assert result.data == {"config": {}, "config_raw": "", "state": {}}
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
