"""Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.

:func:`capture_snapshot` is the pure-Python core of the Phase 2 snapshot
pipeline. It takes a pyATS ``Testbed`` (built by :func:`netbox_pyats.testbed.build_testbed`)
plus a capture spec (which device, what ``kind``) and returns a
:class:`CaptureResult` with the JSON-serializable payload, parser warnings,
and the genie/pyats version strings from the worker environment.

This module is deliberately NetBox- and RQ-free so it can be unit-tested with
a fake testbed (no DB, no RQ, no NetBox). The NetBox ``JobRunner`` wrapper in
:mod:`netbox_pyats.jobs` calls this function, persists the result as a
:class:`PyatsSnapshot` row, and handles job lifecycle.

Multi-vendor graceful degradation is enforced here: if the device's ``os`` is
the unsupported sentinel (see :data:`netbox_pyats.testbed.UNSUPPORTED_OS`), we
return a :class:`CaptureResult` with ``status="unsupported"`` and a warning
rather than raising — so the caller can still write a row and the UI can
surface "unsupported" in the history. Connection/parser errors are caught and
returned as ``status="error"`` with the exception text in ``warnings``.

Genie is imported lazily inside :func:`capture_snapshot` so this module is
importable in the NetBox web process without genie installed (the web process
only needs to *enqueue* jobs; the worker runs them with genie present).
"""

from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass, field
from typing import Any

from .choices import SnapshotKindChoices, SnapshotStatusChoices
from .testbed import UNSUPPORTED_OS, is_supported_os

logger = logging.getLogger(__name__)

# OS-agnostic state commands captured for kind='state' / kind='full'. Each
# command must have a Genie parser for every os in testbed.PLATFORM_SLUG_TO_PYATS_OS
# or the per-command parse is skipped (and recorded as None in the state dict
# so the caller's warnings can flag it). The set is intentionally conservative:
# adding a command here is a commitment that Genie has real parser coverage for
# it across the supported OS matrix (Cisco IOS/XE/XR/NX-OS/ASA, Juniper JunOS,
# Arista EOS, Nokia SR OS).
STATE_COMMANDS: tuple[str, ...] = (
    "show version",
    "show inventory",
    "show ip interface brief",
)


@dataclass
class CaptureResult:
    """Outcome of a single :func:`capture_snapshot` call.

    The :class:`~netbox_pyats.jobs.CaptureSnapshotJob` runner writes this to a
    :class:`netbox_pyats.models.PyatsSnapshot` row: ``data`` → ``data``,
    ``warnings`` → ``parser_warnings``, ``status`` → ``status``, and the
    version strings → the corresponding model fields. ``size_bytes`` is
    derived from the JSON-serialized ``data`` so the UI can render it without
    re-serializing. ``parsed_os`` carries the pyATS os string used by the Genie
    parser, stored on the snapshot so compliance runs can re-parse a golden
    config with the same parser even after the device is deleted.
    """

    status: str = SnapshotStatusChoices.STATUS_SUCCESS
    data: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    genie_version: str = ""
    pyats_version: str = ""
    parsed_os: str = ""

    @property
    def size_bytes(self) -> int:
        """Length of the JSON-serialized ``data`` payload, in bytes."""
        if not self.data:
            return 0
        return len(json.dumps(self.data, default=str).encode("utf-8"))


def _worker_versions() -> tuple[str, str]:
    """Return ``(genie_version, pyats_version)`` from the worker environment.

    Best-effort: returns empty strings if the version cannot be determined
    (e.g. genie installed without metadata, or a stripped wheel). We never
    let a version-lookup failure abort a capture — the snapshot is still
    useful without the version strings; they're metadata for diagnosing
    parser-output drift across Genie releases.
    """
    genie_version = ""
    pyats_version = ""
    try:
        import importlib.metadata as md

        try:
            genie_version = md.version("genie")
        except Exception:  # noqa: BLE001 - metadata lookups are best-effort
            pass
        try:
            pyats_version = md.version("pyats")
        except Exception:  # noqa: BLE001 - metadata lookups are best-effort
            pass
    except Exception:  # noqa: BLE001 - importlib.metadata itself missing (very old Py)
        pass
    return genie_version, pyats_version


def _capture_config(pyats_device) -> dict:
    """Run parser-based config capture on a connected pyATS Device.

    Uses ``pyats.utils.parser`` to parse ``show running-config`` into a
    structured dict. Falls back to a raw-text capture if the parser is
    unavailable for this os (recorded as a warning by the caller). The
    returned dict is JSON-serializable.
    """
    # Local import: genie/pyats.parser is heavy and worker-only.
    from pyats.connections import BaseConnection  # noqa: F401 - ensures connection plugin registry loaded

    config = {}
    try:
        # The canonical "show running-config" parser exists for every os we
        # map in testbed.PLATFORM_SLUG_TO_PYATS_OS. We use the parser util so
        # the output is structured (Genie abstract config) rather than raw
        # text, which is what makes later diffing meaningful.
        output = pyats_device.parse("show running-config")
        config = output if isinstance(output, dict) else {"raw": str(output)}
    except Exception as exc:  # noqa: BLE001 - parser failures are surfaced as warnings
        logger.warning("netbox_pyats: parse('show running-config') failed for %s: %s", pyats_device.name, exc)
        # Fallback: grab the raw text so the snapshot is still useful, and
        # let the caller record the parser failure as a warning.
        try:
            raw = pyats_device.execute("show running-config")
            config = {"raw": str(raw), "_parser_error": str(exc)}
        except Exception as exc2:  # noqa: BLE001 - both parser and execute failed
            raise RuntimeError(f"config capture failed: parser={exc}; execute={exc2}") from exc2
    return config


def _capture_state(pyats_device) -> dict:
    """Run parser-based state capture on a connected pyATS Device.

    Runs a small, OS-agnostic set of state commands via
    ``pyats_device.parse(<command>)`` — the verified Genie "service" that
    returns a structured dict for a CLI command. Each command's parsed output
    is merged into a single dict keyed by command; commands whose parser is
    missing for the device's os are skipped with a warning (recorded by the
    caller).

    Why not ``Genie.learn(device)``: the verified Genie API has no top-level
    ``genie.learn(device)`` function. ``genie`` is a namespace package whose
    top-level ``__init__`` does not export a ``learn`` callable, and
    ``genie.libs`` (shipped by the separate ``genielibs`` wheel) does not
    export one either — the only ``learn`` in the installed ``genie`` wheel
    is :meth:`genie.ops.base.base.Base.ops.learn` (a per-feature instance
    method) and the compiled ``genie.cli.commands.learn`` CLI entry point.
    Enumerating per-OS feature Ops classes (``Lookup.from_device(device).ops.<feature>(device).learn()``)
    is brittle for a v1 "capture everything" snapshot. ``device.parse(...)`` is
    the Genie primitive that returns a structured dict for a CLI command, with
    a clean ``ParserNotFound`` exception for unsupported OSes — the right
    primitive for a v1 that ships and degrades gracefully (see the ATW-10
    build plan §6.1: "multi-vendor bounded by Genie parser availability").
    """
    state: dict[str, Any] = {}
    for command in STATE_COMMANDS:
        try:
            output = pyats_device.parse(command)
        except Exception as exc:  # noqa: BLE001 - per-command parser miss is a warning, not fatal
            # Duck-type ParserNotFound by class name so we don't import genie
            # (which is only present on the worker) just to check the type.
            if type(exc).__name__ == "ParserNotFound":
                logger.debug("netbox_pyats: no parser for %r on %s, skipping", command, pyats_device.name)
                # Record the skip in the state dict so the caller's warnings
                # list can surface it; the per-command key is set to None to
                # signal "no parser" distinctly from "parsed but empty".
                state[command] = None
                continue
            # Any other exception is a real failure for this command — re-raise
            # so the caller's try/except records it as a state-capture warning.
            raise
        state[command] = output if isinstance(output, dict) else {"raw": str(output)}
    return state


def capture_snapshot(pyats_device, *, kind: str = SnapshotKindChoices.KIND_FULL) -> CaptureResult:
    """Capture a snapshot from a single, already-connected pyATS Device.

    This is the pure-Python core. The caller (the RQ job) is responsible for
    building the testbed, connecting the device, and disconnecting afterward;
    this function only runs the capture and packages the result.

    Multi-vendor graceful degradation: if ``pyats_device.os`` is the
    unsupported sentinel, returns a :class:`CaptureResult` with
    ``status="unsupported"`` and a warning — no attempt to connect or parse
    is made. Connection/parser errors are caught and returned as
    ``status="error"`` with the traceback in ``warnings``; the caller still
    gets a :class:`CaptureResult` to persist so the failure is visible in the
    UI history.

    Args:
        pyats_device: a connected ``pyats.topology.Device`` (or a duck-typed
            object with ``name``, ``os``, ``parse``, ``execute`` for tests).
        kind: one of :class:`SnapshotKindChoices` — ``config``, ``state``, or
            ``full``.

    Returns:
        A :class:`CaptureResult` with the payload, warnings, and worker
        version strings. Never raises for unsupported platforms or capture
        errors; only raises for programmer error (bad ``kind``).
    """
    if kind not in SnapshotKindChoices.values:
        raise ValueError(f"kind must be one of {list(SnapshotKindChoices.values)}, got {kind!r}")

    genie_version, pyats_version = _worker_versions()
    os_value = getattr(pyats_device, "os", "") or ""
    if not is_supported_os(os_value):
        return CaptureResult(
            status=SnapshotStatusChoices.STATUS_UNSUPPORTED,
            data={},
            warnings=[f"platform os={os_value!r} has no Genie parser; skipped"],
            genie_version=genie_version,
            pyats_version=pyats_version,
            parsed_os=os_value,
        )

    warnings: list = []
    data: dict[str, Any] = {}

    try:
        if kind in (SnapshotKindChoices.KIND_CONFIG, SnapshotKindChoices.KIND_FULL):
            try:
                data["config"] = _capture_config(pyats_device)
            except Exception as exc:  # noqa: BLE001 - config capture failure is a warning, not fatal
                warnings.append(f"config capture failed: {exc}")
                data["config"] = {}
        if kind in (SnapshotKindChoices.KIND_STATE, SnapshotKindChoices.KIND_FULL):
            try:
                state = _capture_state(pyats_device)
                # _capture_state records per-command parser misses as None.
                # Surface those as warnings so the UI shows which state
                # commands were skipped on this device's os.
                for cmd, value in state.items():
                    if value is None:
                        warnings.append(f"no Genie parser for {cmd!r} on os={os_value!r}; skipped")
                data["state"] = state
            except Exception as exc:  # noqa: BLE001 - state capture failure is a warning, not fatal
                warnings.append(f"state capture failed: {exc}")
                data["state"] = {}
    except Exception as exc:  # noqa: BLE001 - any uncaught error → error status with traceback
        return CaptureResult(
            status=SnapshotStatusChoices.STATUS_ERROR,
            data={},
            warnings=[f"capture error: {exc}", traceback.format_exc()],
            genie_version=genie_version,
            pyats_version=pyats_version,
            parsed_os=os_value,
        )

    # If both halves failed in a "full" capture, treat the whole thing as an
    # error so the UI shows a red badge rather than a green-but-empty row.
    status = SnapshotStatusChoices.STATUS_SUCCESS
    if kind == SnapshotKindChoices.KIND_FULL and not data.get("config") and not data.get("state"):
        status = SnapshotStatusChoices.STATUS_ERROR
    elif kind == SnapshotKindChoices.KIND_CONFIG and not data.get("config"):
        status = SnapshotStatusChoices.STATUS_ERROR
    elif kind == SnapshotKindChoices.KIND_STATE and not data.get("state"):
        status = SnapshotStatusChoices.STATUS_ERROR
    if status == SnapshotStatusChoices.STATUS_ERROR and not warnings:
        warnings.append("capture produced no data")

    return CaptureResult(
        status=status,
        data=data,
        warnings=warnings,
        genie_version=genie_version,
        pyats_version=pyats_version,
        parsed_os=os_value,
    )


def capture_snapshot_for_netbox_device(
    netbox_device,
    *,
    kind: str = SnapshotKindChoices.KIND_FULL,
    credential_resolver=None,
) -> CaptureResult:
    """Build a single-device testbed, connect, capture, disconnect.

    Convenience wrapper for the common case: the RQ job has a NetBox Device
    row and wants a snapshot. This builds a one-device testbed via
    :func:`netbox_pyats.testbed.build_testbed`, connects it, runs
    :func:`capture_snapshot`, and disconnects — returning the
    :class:`CaptureResult` for the caller to persist.

    Unsupported platforms short-circuit before any connection attempt (the
    testbed builder flags them, and :func:`capture_snapshot` returns
    ``unsupported`` without connecting). Connection failures surface as
    ``status="error"`` with the connection exception in ``warnings``.
    """
    from .testbed import build_testbed  # lazy: avoids pyats import in web process

    tb, report = build_testbed([netbox_device], on_unsupported="flag", credential_resolver=credential_resolver)
    if not report.supported:
        # No supported device on the testbed → unsupported result, no connect.
        return CaptureResult(
            status=SnapshotStatusChoices.STATUS_UNSUPPORTED,
            data={},
            warnings=["platform has no Genie parser; skipped"],
        )

    pyats_device = tb.devices[report.supported[0]["pyats_device_name"]]
    try:
        # Connect via Unicon. This is where SSH/Telnet actually happens.
        pyats_device.connect()
    except Exception as exc:  # noqa: BLE001 - connection failure is an error status, not a crash
        genie_version, pyats_version = _worker_versions()
        return CaptureResult(
            status=SnapshotStatusChoices.STATUS_ERROR,
            data={},
            warnings=[f"connection failed: {exc}", traceback.format_exc()],
            genie_version=genie_version,
            pyats_version=pyats_version,
        )

    try:
        return capture_snapshot(pyats_device, kind=kind)
    finally:
        try:
            pyats_device.disconnect()
        except Exception:  # noqa: BLE001 - best-effort cleanup; never mask the result
            logger.debug("netbox_pyats: disconnect failed for %s", pyats_device.name, exc_info=True)


# Re-export for callers that want the sentinel without importing testbed.
__all__ = (
    "CaptureResult",
    "capture_snapshot",
    "capture_snapshot_for_netbox_device",
    "UNSUPPORTED_OS",
)
