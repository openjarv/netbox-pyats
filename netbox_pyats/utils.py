"""Shared internal helpers — single source for cross-module utilities.

Small helpers that used to be duplicated across :mod:`netbox_pyats.capture`,
:mod:`netbox_pyats.parser_catalog`, and :mod:`netbox_pyats.crypto` live here
so every caller reads from one canonical definition (ATW-906, tech-debt M3+M4).
"""

from __future__ import annotations

from django.conf import settings


def get_plugin_config() -> dict:
    """Return the plugin's ``PLUGINS_CONFIG['netbox_pyats']`` block.

    Empty dict if unset. The conftest configures a minimal
    ``PLUGINS_CONFIG`` for pure-Python tests, so this is safe to call in the
    unit lane.
    """
    return getattr(settings, "PLUGINS_CONFIG", {}).get("netbox_pyats", {}) or {}


def worker_versions() -> tuple[str, str]:
    """Return ``(genie_version, pyats_version)`` from the worker environment.

    Best-effort: returns empty strings if the version cannot be determined
    (e.g. genie installed without metadata, or a stripped wheel). We never
    let a version-lookup failure abort a capture or refresh — the snapshot or
    catalog is still useful without the version strings; they are metadata
    for diagnosing parser-output drift across Genie releases.
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
