"""Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.

:func:`refresh_parser_catalog_for_os` is the pure-Python core of the
ATW-241 (child 1) parser-discovery refresh. It takes a pyATS ``os`` string,
builds a minimal stub ``pyats.topology.Device`` with only ``.os`` set (no
connection — ``genie.libs.parser.utils.get_parser_commands`` only reads
``device.os``, confirmed in source), calls ``get_parser_commands``, and
returns a :class:`CatalogRefreshResult` carrying the command list plus the
worker's genie/pyats version strings.

This module is deliberately NetBox- and RQ-free so it can be unit-tested with
a fake device (no DB, no RQ, no NetBox) — the same pattern as
:mod:`netbox_pyats.capture`. Genie is imported lazily inside
:func:`refresh_parser_catalog_for_os` so this module is importable in the
NetBox web process without genie installed (ADR-0001 §6/§7).

Multi-vendor graceful degradation: an os Genie has no parser package for
returns an empty command list with a warning rather than raising, so the
refresh job can still write a row (or skip) rather than aborting the whole
batch — consistent with the snapshot pipeline's unsupported/error contract
(ADR-0002).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

from .testbed import PLATFORM_SLUG_TO_PYATS_OS, UNSUPPORTED_OS, is_supported_os
from .utils import worker_versions

logger = logging.getLogger(__name__)


@dataclass
class CatalogRefreshResult:
    """Outcome of a single :func:`refresh_parser_catalog_for_os` call.

    The :func:`netbox_pyats.jobs.refresh_parser_catalog_job` runner writes
    this to a :class:`~netbox_pyats.models.PyatsParserCatalog` row:
    ``commands`` → ``commands``, the version strings → the corresponding
    model fields, and ``refreshed_at`` is set by the job to ``now()``.
    ``warnings`` is recorded for the unsupported-os path (an empty catalog
    row may still be written so the UI can show "no parsers" rather than
    "no row").
    """

    pyats_os: str
    commands: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    genie_version: str = ""
    pyats_version: str = ""


def _stub_pyats_device(pyats_os: str):
    """Build a minimal ``pyats.topology.Device`` with only ``.os`` set.

    ``genie.libs.parser.utils.get_parser_commands`` only reads
    ``device.os`` — it does not connect, parse, or read any other attribute
    (confirmed against ``genie.libs.parser.utils.common``). A stub Device
    with just ``os`` set is the cheapest valid input; no testbed, no
    connections, no credentials. Local import so this module stays importable
    in the web process (ADR-0001 §6).
    """
    from pyats.topology import Device

    return Device(name=f"catalog-stub-{pyats_os}", os=pyats_os)


def refresh_parser_catalog_for_os(pyats_os: str) -> CatalogRefreshResult:
    """Discover the parseable command list for one pyATS os.

    Worker-only: lazily imports ``genie.libs.parser.utils`` (which imports
    ``genie.libs.parsers``, the package ADR-0001 §6 forbids in the web
    process). The caller (the RQ job) is responsible for persisting the
    result as a :class:`~netbox_pyats.models.PyatsParserCatalog` row.

    Graceful degradation: if ``pyats_os`` is the unsupported sentinel or not
    a string Genie has a parser package for, returns a
    :class:`CatalogRefreshResult` with an empty ``commands`` list and a
    warning rather than raising — the job can still write an empty row (or
    skip) so the UI surfaces "no parsers" rather than a missing row.

    Args:
        pyats_os: a pyATS ``os`` string (e.g. ``"iosxe"``, ``"nxos"``).

    Returns:
        The :class:`CatalogRefreshResult` for this os.
    """
    if not is_supported_os(pyats_os):
        return CatalogRefreshResult(
            pyats_os=pyats_os,
            commands=[],
            warnings=[f"unsupported os {pyats_os!r}: no Genie parser package"],
        )

    # Lazy import: genie.libs.parser.utils imports genie.libs.parsers, which
    # is heavy and worker-only (ADR-0001 §6).
    from genie.libs.parser.utils import get_parser_commands

    try:
        device = _stub_pyats_device(pyats_os)
    except Exception as exc:  # noqa: BLE001 - pyats.topology missing/unusable
        return CatalogRefreshResult(
            pyats_os=pyats_os,
            commands=[],
            warnings=[f"could not build stub device: {exc}"],
        )

    warnings: list = []
    try:
        commands = list(get_parser_commands(device))
    except Exception as exc:  # noqa: BLE001 - parser registry load failure is a warning
        logger.warning("netbox_pyats: get_parser_commands failed for %s: %s", pyats_os, exc)
        return CatalogRefreshResult(
            pyats_os=pyats_os,
            commands=[],
            warnings=[f"get_parser_commands failed: {exc}"],
        )

    # Defensive: get_parser_commands may return a set/tuple/generator —
    # normalize to a sorted list of strings for deterministic storage and
    # stable checkbox ordering. Drop any non-string entries defensively.
    commands = sorted({str(c) for c in commands if c})

    genie_version, pyats_version = worker_versions()
    return CatalogRefreshResult(
        pyats_os=pyats_os,
        commands=commands,
        warnings=warnings,
        genie_version=genie_version,
        pyats_version=pyats_version,
    )


def supported_os_values() -> Iterable[str]:
    """Return the deduplicated set of Genie-supported pyATS os strings.

    Derived from :data:`netbox_pyats.testbed.PLATFORM_SLUG_TO_PYATS_OS` (the
    single source of truth for which platforms map to a Genie os). The
    refresh job iterates these so the catalog covers every os the plugin
    will resolve a NetBox Device to.
    """
    # dict.values() preserves insertion order in Py3.7+; de-dup while keeping
    # the first-seen order so the job's iteration is deterministic.
    seen: set = set()
    for os_value in PLATFORM_SLUG_TO_PYATS_OS.values():
        if os_value in seen or not is_supported_os(os_value):
            continue
        seen.add(os_value)
        yield os_value


__all__ = (
    "CatalogRefreshResult",
    "refresh_parser_catalog_for_os",
    "supported_os_values",
    "UNSUPPORTED_OS",
)
