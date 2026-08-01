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

from netbox_pyats.capture import STATE_COMMANDS, CaptureResult, capture_snapshot, resolve_state_commands
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
        execute_outputs=None,
    ):
        self.name = name
        self.os = os
        self._config_output = config_output if config_output is not None else {"configured": True}
        self._state_outputs = dict(state_outputs or {})
        self._unsupported = set(unsupported_commands or [])
        self._parse_exc = parse_exc
        self._execute_exc = execute_exc
        self._execute_outputs = dict(execute_outputs or {})

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
        if command in self._execute_outputs:
            return self._execute_outputs[command]
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

    def test_config_capture_carries_parsed_os(self):
        # ATW-70: parsed_os is populated from the device's os at capture time
        # so v2 structured compliance can pick the right Genie parser later,
        # even after the device row is deleted.
        d = FakePyatsDevice(os="iosxe", config_output={"hostname": "rtr01"})
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        assert result.parsed_os == "iosxe"

    def test_full_capture_carries_parsed_os(self):
        d = FakePyatsDevice(
            os="nxos",
            config_output={"hostname": "rtr01"},
            state_outputs={
                "show version": {"version": "9.3"},
                "show inventory": {},
                "show ip interface brief": {},
            },
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.parsed_os == "nxos"

    def test_unsupported_capture_carries_parsed_os(self):
        # Even on the unsupported path, parsed_os is carried so v2 can
        # distinguish "unsupported os string" rows by os.
        d = FakePyatsDevice(os=UNSUPPORTED_OS)
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        assert result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert result.parsed_os == UNSUPPORTED_OS

    def test_error_capture_carries_parsed_os(self):
        # Capture errors still carry parsed_os so the row records provenance.
        d = FakePyatsDevice(
            os="iosxr",
            parse_exc=RuntimeError("parse boom"),
            execute_exc=RuntimeError("execute boom"),
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_CONFIG)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.parsed_os == "iosxr"

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
            "show interfaces": {"Gig0": {"oper_status": "up"}},
            "show ip route": {"10.0.0.0/8": {"protocol": "connected"}},
            "show cdp neighbors": {"Gig0": {"neighbors": ["sw01"]}},
            "show lldp neighbors": {"Gig0": {"neighbors": ["sw01"]}},
            "show arp": {"10.0.0.2": {"mac": "00:11:22:33:44:55"}},
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
        assert result.data["state"]["show interfaces"] == {"Gig0": {"oper_status": "up"}}
        assert result.data["state"]["show ip route"] == {"10.0.0.0/8": {"protocol": "connected"}}
        assert result.data["state"]["show cdp neighbors"] == {"Gig0": {"neighbors": ["sw01"]}}
        assert result.data["state"]["show lldp neighbors"] == {"Gig0": {"neighbors": ["sw01"]}}
        assert result.data["state"]["show arp"] == {"10.0.0.2": {"mac": "00:11:22:33:44:55"}}
        assert result.warnings == []

    def test_state_capture_skips_commands_without_a_parser(self):
        """Per-command ParserNotFound is recorded as a warning, not a failure."""
        # 'show inventory' and the v1-expansion commands have no parser on
        # this os; the rest do. The skip-with-warning contract must hold
        # uniformly across old and new commands (no per-OS gating).
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show inventory", "show cdp neighbors", "show lldp neighbors", "show arp"],
            state_outputs={
                "show version": {"version": "16.12"},
                "show ip interface brief": {},
                "show interfaces": {},
                "show ip route": {},
            },
        )
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        # The unsupported commands are recorded as None in the state dict.
        assert result.data["state"]["show inventory"] is None
        assert result.data["state"]["show cdp neighbors"] is None
        assert result.data["state"]["show lldp neighbors"] is None
        assert result.data["state"]["show arp"] is None
        # The supported commands are captured.
        assert result.data["state"]["show version"] == {"version": "16.12"}
        # A warning was recorded for each skipped command.
        for skipped in ("show inventory", "show cdp neighbors", "show lldp neighbors", "show arp"):
            assert any(skipped in w for w in result.warnings)
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

    def test_parse_kind_without_commands_raises(self):
        # kind='parse' requires an explicit command list — programmer error
        # otherwise (the view always passes one; this guards the contract).
        d = FakePyatsDevice(os="iosxe")
        with pytest.raises(ValueError):
            capture_snapshot(d, kind=SnapshotKindChoices.KIND_PARSE)

    def test_parse_kind_with_empty_commands_raises(self):
        d = FakePyatsDevice(os="iosxe")
        with pytest.raises(ValueError):
            capture_snapshot(d, kind=SnapshotKindChoices.KIND_PARSE, commands=[])


class TestParseCapture:
    """kind='parse' runs device.parse() per user-supplied command and writes
    the same data["state"] shape the automated state capture writes, so the
    existing snapshot detail template, diff engine, and compliance engine
    work unchanged (ATW-241 child 3).
    """

    def test_parse_kind_writes_state_shape_keyed_by_command(self):
        # The parsed outputs are merged into data["state"] keyed by command —
        # the same shape automated state capture produces.
        d = FakePyatsDevice(
            os="iosxe",
            state_outputs={
                "show version": {"version": "16.12"},
                "show ip interface brief": {"Gig0": {"ip": "10.0.0.1"}},
            },
        )
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show version", "show ip interface brief"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "state" in result.data
        assert result.data["state"] == {
            "show version": {"version": "16.12"},
            "show ip interface brief": {"Gig0": {"ip": "10.0.0.1"}},
        }
        assert result.warnings == []

    def test_parse_kind_carries_parsed_os(self):
        d = FakePyatsDevice(os="iosxe", state_outputs={"show version": {}})
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_PARSE, commands=["show version"])
        assert result.parsed_os == "iosxe"

    def test_parser_not_found_falls_back_to_raw_execute(self):
        # Board-confirmed plan §5: when a command has no Genie parser (the
        # manual text-box case), fall back to raw device.execute() output
        # wrapped as {"raw": <text>} — matching `genie parse` CLI behavior.
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show platform"],
            execute_outputs={"show platform": "Platform: c9300\n"},
        )
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show version", "show platform"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        # The parsed command is structured; the no-parser command is raw text.
        assert result.data["state"]["show platform"] == {"raw": "Platform: c9300\n"}
        assert "show version" in result.data["state"]
        assert result.warnings == []

    def test_parser_and_execute_both_fail_records_warning(self):
        # If a command raises neither a parseable result nor a clean execute,
        # record it in parser_warnings and omit it from the state dict — one
        # bad command does not abort the whole capture.
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show bad"],
            execute_exc=RuntimeError("execute boom"),
            state_outputs={"show version": {"version": "16.12"}},
        )
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show version", "show bad"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.data["state"]["show version"] == {"version": "16.12"}
        assert "show bad" not in result.data["state"]
        assert any("show bad" in w for w in result.warnings)
        assert any("execute failed" in w for w in result.warnings)

    def test_parse_kind_non_parser_exception_is_warning(self):
        # A non-ParserNotFound parse exception (e.g. a real device error) is
        # recorded as a warning, not a fatal re-raise — same graceful-
        # degradation contract as the automated state path.
        d = FakePyatsDevice(
            os="iosxe",
            parse_exc=RuntimeError("device disconnected"),
        )
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show version"],
        )
        # The command failed to parse (non-ParserNotFound) and is omitted;
        # state is empty → error status with a warning.
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"state": {}}
        assert any("parse failed" in w for w in result.warnings)

    def test_parse_kind_all_commands_failed_is_error(self):
        # If every command failed (no parser + execute failed), the capture
        # produced no data → error status, mirroring the automated state path.
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show bad1", "show bad2"],
            execute_exc=RuntimeError("execute boom"),
        )
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show bad1", "show bad2"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"state": {}}
        assert len(result.warnings) == 2

    def test_parse_kind_unsupported_platform_short_circuits(self):
        # Unsupported os → unsupported status, no parse attempt — same
        # contract as the other kinds.
        d = FakePyatsDevice(os=UNSUPPORTED_OS, parse_exc=AssertionError("parse must not be called"))
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show version"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert result.data == {}
        assert "parse must not be called" not in json.dumps(result.warnings)

    def test_parse_kind_non_dict_output_wrapped_as_raw(self):
        # If device.parse() returns a non-dict (some Genie parsers return
        # lists/strings for edge commands), wrap it as {"raw": <str>} so the
        # state dict stays JSON-serializable with a consistent shape.
        d = FakePyatsDevice(os="iosxe", state_outputs={"show clock": "14:32:01.123 UTC Mon"})
        result = capture_snapshot(
            d,
            kind=SnapshotKindChoices.KIND_PARSE,
            commands=["show clock"],
        )
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.data["state"]["show clock"] == {"raw": "14:32:01.123 UTC Mon"}


class TestResolveStateCommands:
    """ATW-432: resolve_state_commands picks per-OS command sets from
    PLUGINS_CONFIG, falling back to the OS-agnostic STATE_COMMANDS default.
    """

    def test_no_config_returns_default(self):
        assert resolve_state_commands("iosxe") == STATE_COMMANDS

    def test_unknown_os_returns_default(self):
        assert resolve_state_commands("nonsenseos") == STATE_COMMANDS

    def test_per_os_config_returns_matching_set(self):
        from django.test import override_settings

        per_os = {"nxos": ["show version", "show vlan"]}
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            assert resolve_state_commands("nxos") == ("show version", "show vlan")

    def test_per_os_config_unknown_os_falls_back(self):
        from django.test import override_settings

        per_os = {"nxos": ["show vlan"]}
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            assert resolve_state_commands("iosxe") == STATE_COMMANDS

    def test_per_os_config_replaces_not_extends(self):
        from django.test import override_settings

        per_os = {"nxos": ["show vlan"]}
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            assert resolve_state_commands("nxos") == ("show vlan",)
            assert resolve_state_commands("nxos") != STATE_COMMANDS


class TestPerOsStateCapture:
    """ATW-432: capture_snapshot with kind='state' uses the per-OS command
    set when PLUGINS_CONFIG provides one for the device's os.
    """

    def test_state_capture_uses_per_os_commands(self):
        from django.test import override_settings

        per_os = {"nxos": ["show version", "show vlan"]}
        state_outputs = {
            "show version": {"version": "9.3"},
            "show vlan": {"vlans": {"1": {"name": "default"}}},
        }
        d = FakePyatsDevice(os="nxos", state_outputs=state_outputs)
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert set(result.data["state"].keys()) == {"show version", "show vlan"}
        assert result.data["state"]["show vlan"] == {"vlans": {"1": {"name": "default"}}}
        assert result.warnings == []

    def test_full_capture_uses_per_os_commands_for_state_half(self):
        from django.test import override_settings

        per_os = {"iosxe": ["show version", "show platform"]}
        state_outputs = {
            "show version": {"version": "16.12"},
            "show platform": {"platform": "c9300"},
        }
        d = FakePyatsDevice(os="iosxe", config_output={"hostname": "rtr01"}, state_outputs=state_outputs)
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_FULL)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert set(result.data["state"].keys()) == {"show version", "show platform"}

    def test_per_os_graceful_degradation_for_missing_parser(self):
        from django.test import override_settings

        per_os = {"iosxe": ["show version", "show bad"]}
        d = FakePyatsDevice(
            os="iosxe",
            unsupported_commands=["show bad"],
            state_outputs={"show version": {"version": "16.12"}},
        )
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"state_commands_per_os": per_os}}):
            result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_STATE)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert result.data["state"]["show bad"] is None
        assert any("show bad" in w for w in result.warnings)
