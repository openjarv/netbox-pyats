"""Worker-side golden config text parser — Genie harness, no live device (Phase 4, ATW-15).

:func:`parse_golden_config_text` turns raw golden running-config text into the
same Genie abstract-config dict shape that
:func:`netbox_pyats.capture._capture_config` produces from a live device, so the
compliance engine can diff golden vs. snapshot in the same structured shape via
:func:`netbox_pyats.diff.diff_snapshots`.

This module is **worker-only**: it imports Genie lazily inside the parse
function so the module is importable in the NetBox web process without genie
installed (ADR-0003 invariant: the web process is Genie-free). The compliance
job (:func:`netbox_pyats.jobs.run_compliance_job`) calls this on the ``pyats``
worker, where ``pyats[full]`` (and therefore ``genie``) is installed.

Genie text-input API: ``device.parse("show running-config", output=text)``.
A minimal in-memory :class:`pyats.topology.Device` is constructed with
``os=<os>`` and no connections. ``device.parse`` discovers the right Genie
parser for ``(os, "show running-config")`` and feeds the text through it
without any device round-trip — no connection is opened, no ``execute`` is
called. This is the same parser ``_capture_config`` uses on a live device; the
only difference is the text comes from the golden config field instead of the
device's CLI. See ADR-0004 for the architectural decision (Option 1: Genie
parser harness on the worker) and the rejection of parse-on-save (Option 2)
and line-oriented-both-sides (Option 3).

Args:
    text: the raw golden running-config text (the "expected" config).
    os: the pyATS ``os`` string for the parser selection (e.g. ``"iosxe"``,
        ``"ios"``, ``"nxos"``). Must match the os the snapshot was captured
        with (stored on :attr:`PyatsSnapshot.parsed_os`), so the same Genie
        parser is used on both sides.

Returns:
    The Genie abstract-config dict (the same shape as
    ``snapshot.data["config"]``). JSON-serializable.

Raises:
    GoldenParseError: if the text is empty, the os is unsupported, or the
        Genie parser fails. The caller (the compliance job) catches this and
        records it as a compliance ``error`` row with the message in
        ``parser_warnings``.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class GoldenParseError(Exception):
    """Raised when the golden config text cannot be parsed into a comparable dict."""


def parse_golden_config_text(text: str, *, os: str) -> dict:
    """Parse golden config text into a Genie abstract-config dict (worker-only).

    Uses the same Genie parser the snapshot used, via a parser-only harness: a
    minimal in-memory ``pyats.topology.Device`` with ``os=<os>`` and no
    connections, calling ``device.parse("show running-config", output=text)``.
    No live device connection is opened.

    Args:
        text: the raw golden running-config text. Empty/None text raises
            :class:`GoldenParseError`.
        os: the pyATS ``os`` string (e.g. ``"iosxe"``). Must match the
            snapshot's os so the same parser is used on both sides.

    Returns:
        The Genie abstract-config dict, JSON-serializable.

    Raises:
        GoldenParseError: empty text, unsupported os, or parser failure.
    """
    if not text or not text.strip():
        raise GoldenParseError("golden config text is empty; cannot parse")
    if not os:
        raise GoldenParseError("os is empty; cannot select a Genie parser for the golden config")

    # Lazy import: genie/pyats.topology is heavy and worker-only. The web
    # process imports this module (via jobs.py) without genie installed; the
    # parse function is only called on the worker.
    from pyats.topology import Device

    # Construct a minimal in-memory Device with os set so Genie's parser
    # discovery picks the right parser package. No connections, no testbed —
    # device.parse("show running-config", output=text) feeds the text directly
    # into the parser without opening a connection.
    device = Device(name="golden-parse", os=os)

    try:
        parsed = device.parse("show running-config", output=text)
    except Exception as exc:  # noqa: BLE001 - surface any parser failure as GoldenParseError
        raise GoldenParseError(f"Genie parser failed for os={os!r}: {exc}") from exc

    if not isinstance(parsed, dict):
        raise GoldenParseError(f"Genie parser for os={os!r} returned {type(parsed).__name__}, expected dict")

    return parsed


__all__ = (
    "GoldenParseError",
    "parse_golden_config_text",
)
