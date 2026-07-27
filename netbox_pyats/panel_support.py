"""Platform-support decision for the device-page PyATS panel (ATW-184).

Pure-Python, no NetBox or Genie import: this module is importable in the
NetBox web process and in unit tests without the rest of the plugin's
NetBox-bound template-extension machinery. It owns one decision — whether the
panel should show a green supported badge or a warning — combining the static
platform map with the most recent snapshot's observed status so the panel
never contradicts itself.
"""

from __future__ import annotations

from .choices import SnapshotStatusChoices
from .testbed import UNSUPPORTED_OS, platform_to_pyats_os


def resolve_panel_platform_support(device, latest_snapshot):
    """Return ``(platform_supported, os_value)`` for the device-page panel.

    Combines the static platform map with observed capture reality so the
    panel never contradicts itself (ATW-184):

    - Start from :func:`platform_to_pyats_os`: a slug in the map claims
      support; anything else is unsupported.
    - If the most recent snapshot is ``unsupported``, override to unsupported
      regardless of the static map. The static map can be stale (platform slug
      edited after a capture) or wrong (overly permissive); the most recent
      capture is the ground truth the operator just saw in the snapshot row.

    ``latest_snapshot`` is the single most recent snapshot for the device
    (ordered by ``-captured_at``), or ``None`` if the device has no snapshots.
    It is passed in rather than queried here so the panel view can reuse the
    snapshot list it already fetched, avoiding an extra DB round-trip.

    Returns:
        A tuple ``(platform_supported: bool, os_value: str)``. When
        ``platform_supported`` is False, ``os_value`` is the
        :data:`UNSUPPORTED_OS` sentinel.
    """
    os_value = platform_to_pyats_os(getattr(device, "platform", None))
    platform_supported = os_value != UNSUPPORTED_OS
    if latest_snapshot is not None and latest_snapshot.status == SnapshotStatusChoices.STATUS_UNSUPPORTED:
        platform_supported = False
        os_value = UNSUPPORTED_OS
    return platform_supported, os_value
