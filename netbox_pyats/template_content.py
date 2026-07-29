"""Template extensions injecting the PyATS tab into the NetBox Device page.

Phase 2 (ATW-13) injects a "PyATS" panel into the Device detail page's
right-hand column. The panel renders:

- A "Capture snapshot" form (config / state / full) that POSTs to the
  plugin's enqueue endpoint and redirects back to the device page.
- The most recent N snapshots for this device (kind, status badge, size,
  captured_at, warnings indicator), linked to the snapshot detail view.

Phase 3 (ATW-14) extends the panel with:

- A "Diff two snapshots" picker that POSTs two snapshot ids to the plugin's
  diff endpoint. Only offered when the device has ≥2 snapshots.
- The most recent N diffs for this device (status badge, change indicator,
  before→after links, created_at), linked to the diff detail view.

Phase 4 (ATW-15) extends the panel with:

- A "Run compliance" picker that POSTs a golden config id + snapshot id to
  the plugin's compliance endpoint. Only offered when the device has at least
  one golden config and at least one snapshot with a config payload.
- The most recent N compliance runs for this device (result badge, drift
  indicator, golden vs snapshot links, created_at), linked to the compliance
  run detail view. The diff tree reuses the Phase 3 diff-tree partial.

The panel is read-only on GET (the forms post to separate URLs; no JS is
required). If the device's platform has no Genie parser, the testbed
builder's unsupported flag is surfaced as a banner so the operator knows
captures will be skipped before they click.
"""

from __future__ import annotations

from netbox.plugins import PluginTemplateExtension

from .choices import SnapshotKindChoices
from .panel_support import resolve_panel_platform_support

# How many recent snapshots / diffs / compliance runs to show in the
# device-page panel. Kept small so the device page stays fast; the full
# history is on the list views.
DEVICE_PAGE_SNAPSHOT_LIMIT = 5
DEVICE_PAGE_DIFF_LIMIT = 5
DEVICE_PAGE_COMPLIANCE_LIMIT = 5


class DevicePyATSPanel(PluginTemplateExtension):
    """Inject the PyATS capture/diff/compliance panel + recent history into the Device page."""

    models = ["dcim.device"]

    def right_page(self):
        device = self.context.get("object")
        if device is None:
            return ""

        # Lazy imports: models/views are only importable inside NetBox, and
        # the template extension is only constructed inside a NetBox request.
        from .models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot, PyatsSnapshotDiff

        snapshots = list(
            PyatsSnapshot.objects.filter(device=device).order_by("-captured_at")[:DEVICE_PAGE_SNAPSHOT_LIMIT]
        )
        diffs = list(PyatsSnapshotDiff.objects.filter(device=device).order_by("-created")[:DEVICE_PAGE_DIFF_LIMIT])
        golden_configs = list(PyatsGoldenConfig.objects.filter(device=device).order_by("name"))
        compliance_runs = list(
            PyatsComplianceRun.objects.filter(device=device).order_by("-created")[:DEVICE_PAGE_COMPLIANCE_LIMIT]
        )

        # Surface the platform support status so the operator knows before
        # clicking whether captures will succeed. The decision combines the
        # static platform map with the most recent snapshot's observed status
        # so the panel never shows a green supported badge next to a snapshot
        # row marked 'Unsupported platform' (ATW-184).
        platform_supported, os_value = resolve_panel_platform_support(device, snapshots[0] if snapshots else None)

        # Compliance picker needs at least one golden config and at least one
        # snapshot whose data carries a config payload (config or full kind).
        config_snapshots = [
            s for s in snapshots if s.kind in (SnapshotKindChoices.KIND_CONFIG, SnapshotKindChoices.KIND_FULL)
        ]

        # Diff picker groups snapshots by kind (ATW-241 child 4): a parse row
        # is only diffable against another parse row, and state/full rows only
        # against their own kind. The template renders one <optgroup> per kind
        # so the operator sees the grouping; DeviceDiffForm.clean enforces it.
        diff_snapshots_by_kind = _group_snapshots_by_kind(snapshots)

        return self.render(
            "netbox_pyats/inc/device_panel.html",
            extra_context={
                "device": device,
                "snapshots": snapshots,
                "diff_snapshots_by_kind": diff_snapshots_by_kind,
                "diffs": diffs,
                "golden_configs": golden_configs,
                "compliance_runs": compliance_runs,
                "config_snapshots": config_snapshots,
                "snapshot_kinds": SnapshotKindChoices.choices,
                "platform_supported": platform_supported,
                "pyats_os": os_value if platform_supported else None,
                "capture_url": _capture_url_for_device(device),
                "diff_url": _diff_url_for_device(device),
                "compliance_url": _compliance_url_for_device(device),
                "snapshot_list_url": _snapshot_list_url_for_device(device),
                "parse_url": _parse_url_for_device(device),
            },
        )


def _capture_url_for_device(device):
    """Return the POST URL for the device-page capture form."""
    from django.urls import reverse

    return reverse("plugins:netbox_pyats:device_capture", kwargs={"device_id": device.pk})


def _diff_url_for_device(device):
    """Return the POST URL for the device-page diff form (Phase 3, ATW-14)."""
    from django.urls import reverse

    return reverse("plugins:netbox_pyats:device_diff", kwargs={"device_id": device.pk})


def _compliance_url_for_device(device):
    """Return the POST URL for the device-page compliance form (Phase 4, ATW-15)."""
    from django.urls import reverse

    return reverse("plugins:netbox_pyats:device_compliance", kwargs={"device_id": device.pk})


def _snapshot_list_url_for_device(device):
    """Return the filtered snapshot-list URL for this device."""
    from django.urls import reverse

    return f"{reverse('plugins:netbox_pyats:pyatssnapshot_list')}?device_id={device.pk}"


def _parse_url_for_device(device):
    """Return the GET URL for the device-page Parse sub-tab (ATW-250)."""
    from django.urls import reverse

    return reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": device.pk})


def _group_snapshots_by_kind(snapshots):
    """Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).

    Returns an ordered list of ``(kind_value, kind_label, [snapshots])`` tuples
    so the template can render one ``<optgroup>`` per kind. The order follows
    ``SnapshotKindChoices.choices`` (the single source of truth for kind order);
    kinds with no snapshots are omitted. Keeping the grouping server-side
    avoids any JS in the picker (ADR-0001 §4).
    """
    by_kind = {}
    for snap in snapshots:
        by_kind.setdefault(snap.kind, []).append(snap)
    return [(value, label, by_kind[value]) for value, label in SnapshotKindChoices.choices if value in by_kind]


template_extensions = [DevicePyATSPanel]
