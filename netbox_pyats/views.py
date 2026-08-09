"""Views for the netbox-pyats plugin.

Phase 1 (ATW-12) shipped standard NetBox CRUD for :class:`PyatsCredential`.
Phase 2 (ATW-13) adds:

- Standard NetBox list/detail views for :class:`PyatsSnapshot` (the JSONB
  payload is rendered server-side as a collapsible tree via the snapshot
  detail template).
- A ``device_capture`` view that the device-page PyATS tab POSTs to; it
  enqueues a :func:`capture_snapshot_job` on the dedicated ``pyats`` RQ
  queue and redirects back to the device page. The view requires
  ``netbox_pyats.add_pyatssnapshot`` so only authorized operators can
  trigger captures.

Phase 3 (ATW-14) adds:

- Standard NetBox list/detail views for :class:`PyatsSnapshotDiff` (the
  JSONB ``diff`` tree is rendered server-side as a collapsible tree via the
  diff detail template — no JS dependency).
- A ``device_diff`` view that the device-page PyATS tab POSTs to; it
  enqueues a :func:`run_diff_job` on the dedicated ``pyats`` RQ queue and
  redirects back to the device page. The view requires
  ``netbox_pyats.add_pyatssnapshotdiff`` so only authorized operators can
  trigger diffs.

Phase 4 (ATW-15) adds:

- Standard NetBox list/detail/edit views for :class:`PyatsGoldenConfig` (the
  ``config_text`` is rendered in a ``<pre>`` block via the golden detail
  template — no JS dependency). Goldens are operator-authored (manual source)
  or promoted from a snapshot.
- Standard NetBox list/detail views for :class:`PyatsComplianceRun` (the
  JSONB ``diff`` tree is rendered server-side via the Phase 3 diff detail
  template's tree partial — reusing the same viewer).
- A ``device_compliance`` view that the device-page PyATS compliance sub-tab
  POSTs to; it enqueues a :func:`run_compliance_job` on the dedicated ``pyats``
  RQ queue and redirects back to the device page. The view requires
  ``netbox_pyats.add_pyatscompliancerun`` so only authorized operators can
  trigger compliance runs.

ATW-393 / ADR-0007: the PyATS device-page surface is a real NetBox object tab
registered via ``register_model_view(Device, 'pyats', path='pyats')`` +
:class:`DevicePyATSTabView` (a GET-only ``ObjectView`` with a ``ViewTab``).
The old ``PluginTemplateExtension`` (``right_page`` card) is removed; the tab
view owns the full capture/diff/compliance UI. No JS, no new models, no new
migrations. The capture/diff/compliance/parse POST endpoints stay unchanged
and redirect back to ``device.get_absolute_url()``.
"""

from dcim.models import Device
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from . import filtersets, forms, jobs, tables
from .choices import CAPTURE_KIND_CHOICES, SnapshotKindChoices, SnapshotTriggerChoices
from .diff import flatten_diff_tree
from .models import (
    PyatsCaptureSchedule,
    PyatsComplianceRun,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsJob,
    PyatsParserCatalog,
    PyatsParserCatalogRefreshSchedule,
    PyatsSnapshot,
    PyatsSnapshotDiff,
)
from .panel_support import resolve_panel_platform_support
from .tab_context import group_snapshots_by_kind
from .testbed import PLATFORM_SLUG_TO_PYATS_OS, UNSUPPORTED_OS, is_supported_os, platform_to_pyats_os

# How many recent snapshots / diffs / compliance runs to show in the
# device-page tab. Kept small so the device page stays fast; the full
# history is on the list views.
DEVICE_PAGE_SNAPSHOT_LIMIT = 5
DEVICE_PAGE_DIFF_LIMIT = 5
DEVICE_PAGE_COMPLIANCE_LIMIT = 5


# --------------------------------------------------------------------------- #
# Device-page PyATS tab (ATW-393, ADR-0007)
# --------------------------------------------------------------------------- #


@register_model_view(Device, "pyats", path="pyats")
class DevicePyATSTabView(generic.ObjectView):
    """PyATS tab on the NetBox Device detail page (ATW-393, ADR-0007).

    A GET-only ``ObjectView`` registered via ``register_model_view`` so it
    appears as a true device-page tab (alongside Inventory, Status, Config
    Context) with its own URL (``/dcim/devices/<id>/pyats/``). Renders the
    capture/diff/compliance forms + recent history tables via
    ``inc/device_tab.html``. The forms POST to the existing
    ``device_capture``/``device_diff``/``device_compliance`` plugin endpoints
    and redirect back to ``device.get_absolute_url()``; the tab re-renders on
    the next GET.

    The ``ViewTab(permission=...)`` gate hides the tab for users without
    ``netbox_pyats.view_pyatssnapshot`` (matches NetBox convention — see
    ``DeviceInventoryView`` ``permission='dcim.view_inventoryitem'``).

    No JS, no new models, no new migrations, no new POST endpoints (ADR-0001
    §4; ADR-0007).
    """

    queryset = Device.objects.all()
    base_template = "dcim/device/base.html"
    template_name = "netbox_pyats/inc/device_tab.html"
    tab = ViewTab(
        label="PyATS",
        weight=550,
        permission="netbox_pyats.view_pyatssnapshot",
    )

    def get_extra_context(self, request, instance):
        snapshots = list(
            PyatsSnapshot.objects.filter(device=instance).order_by("-captured_at")[:DEVICE_PAGE_SNAPSHOT_LIMIT]
        )
        diffs = list(PyatsSnapshotDiff.objects.filter(device=instance).order_by("-created")[:DEVICE_PAGE_DIFF_LIMIT])
        golden_configs = list(PyatsGoldenConfig.objects.filter(device=instance).order_by("name"))
        compliance_runs = list(
            PyatsComplianceRun.objects.filter(device=instance).order_by("-created")[:DEVICE_PAGE_COMPLIANCE_LIMIT]
        )

        # Surface the platform support status so the operator knows before
        # clicking whether captures will succeed. The decision combines the
        # static platform map with the most recent snapshot's observed status
        # so the tab never shows a green supported badge next to a snapshot
        # row marked 'Unsupported platform' (ATW-184).
        platform_supported, os_value = resolve_panel_platform_support(instance, snapshots[0] if snapshots else None)

        # Compliance picker needs at least one golden config and at least one
        # snapshot whose data carries a config payload (config or full kind).
        config_snapshots = [
            s for s in snapshots if s.kind in (SnapshotKindChoices.KIND_CONFIG, SnapshotKindChoices.KIND_FULL)
        ]

        # Diff picker groups snapshots by kind (ATW-241 child 4): a parse row
        # is only diffable against another parse row, and state/full rows only
        # against their own kind. The template renders one <optgroup> per kind
        # so the operator sees the grouping; DeviceDiffForm.clean enforces it.
        diff_snapshots_by_kind = group_snapshots_by_kind(snapshots)

        return {
            "base_template": self.base_template,
            "snapshots": snapshots,
            "diff_snapshots_by_kind": diff_snapshots_by_kind,
            "diffs": diffs,
            "golden_configs": golden_configs,
            "compliance_runs": compliance_runs,
            "config_snapshots": config_snapshots,
            "snapshot_kinds": CAPTURE_KIND_CHOICES,
            "platform_supported": platform_supported,
            "pyats_os": os_value if platform_supported else None,
            "capture_url": _capture_url_for_device(instance),
            "diff_url": _diff_url_for_device(instance),
            "compliance_url": _compliance_url_for_device(instance),
            "snapshot_list_url": _snapshot_list_url_for_device(instance),
            "parse_url": _parse_url_for_device(instance),
        }


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


class PyatsCredentialListView(generic.ObjectListView):
    queryset = PyatsCredential.objects.all()
    table = tables.PyatsCredentialTable
    filterset = filtersets.PyatsCredentialFilterSet
    filterset_form = forms.PyatsCredentialFilterForm


@register_model_view(PyatsCredential)
class PyatsCredentialView(generic.ObjectView):
    queryset = PyatsCredential.objects.all()


@register_model_view(PyatsCredential, "edit")
class PyatsCredentialEditView(generic.ObjectEditView):
    queryset = PyatsCredential.objects.all()
    form = forms.PyatsCredentialForm


@register_model_view(PyatsCredential, "delete")
class PyatsCredentialDeleteView(generic.ObjectDeleteView):
    queryset = PyatsCredential.objects.all()


class PyatsCredentialBulkDeleteView(generic.BulkDeleteView):
    queryset = PyatsCredential.objects.all()
    table = tables.PyatsCredentialTable


# --------------------------------------------------------------------------- #
# Snapshot views (Phase 2, ATW-13)
# --------------------------------------------------------------------------- #


class PyatsSnapshotListView(generic.ObjectListView):
    """List of all PyATS snapshots across all devices.

    Filterable by device, kind, status, and trigger. The device-page PyATS
    panel links here with ``?device_id=<pk>`` for the per-device history.
    """

    queryset = PyatsSnapshot.objects.all()
    table = tables.PyatsSnapshotTable
    filterset = filtersets.PyatsSnapshotFilterSet
    filterset_form = forms.PyatsSnapshotFilterForm


@register_model_view(PyatsSnapshot)
class PyatsSnapshotView(generic.ObjectView):
    """Detail view for a single snapshot.

    Renders the JSONB ``data`` payload and ``parser_warnings`` via the
    snapshot detail template (a server-side collapsible tree — no JS
    dependency).
    """

    queryset = PyatsSnapshot.objects.all()


@register_model_view(PyatsSnapshot, "delete")
class PyatsSnapshotDeleteView(generic.ObjectDeleteView):
    queryset = PyatsSnapshot.objects.all()


class PyatsSnapshotBulkDeleteView(generic.BulkDeleteView):
    queryset = PyatsSnapshot.objects.all()
    table = tables.PyatsSnapshotTable


class DeviceCaptureView(PermissionRequiredMixin, View):
    """Endpoint the device-page PyATS panel POSTs to.

    Accepts a ``kind`` (config / state / full), enqueues a
    :func:`capture_snapshot_job` on the ``pyats`` RQ queue via
    :func:`jobs.enqueue_capture`, flashes a "snapshot queued" message, and
    redirects back to the device page. The actual capture runs on the
    worker; the snapshot row appears in the device-page history list once
    the job completes and the page is refreshed.
    """

    permission_required = "netbox_pyats.add_pyatssnapshot"

    def post(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        form = forms.DeviceCaptureForm(request.POST or {"kind": SnapshotKindChoices.KIND_FULL})
        if not form.is_valid():
            messages.error(request, f"Invalid capture request: {form.errors}")
            return redirect(device.get_absolute_url())

        kind = form.cleaned_data["kind"]
        jobs.enqueue_capture(
            device,
            kind=kind,
            user=request.user,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
        )
        messages.success(
            request,
            f"PyATS {kind} snapshot queued for {device}. It will appear in the PyATS tab when the worker finishes.",
        )
        return redirect(device.get_absolute_url())


# --------------------------------------------------------------------------- #
# Diff views (Phase 3, ATW-14)
# --------------------------------------------------------------------------- #


class PyatsSnapshotDiffListView(generic.ObjectListView):
    """List of all PyATS snapshot diffs across all devices.

    Filterable by device, status, and whether the diff has changes/warnings.
    The device-page PyATS panel links here with ``?device_id=<pk>`` for the
    per-device diff history.
    """

    queryset = PyatsSnapshotDiff.objects.all()
    table = tables.PyatsSnapshotDiffTable
    filterset = filtersets.PyatsSnapshotDiffFilterSet
    filterset_form = forms.PyatsSnapshotDiffFilterForm


@register_model_view(PyatsSnapshotDiff)
class PyatsSnapshotDiffView(generic.ObjectView):
    """Detail view for a single snapshot diff.

    Renders the JSONB ``diff`` tree, the ``summary`` counts, and
    ``parser_warnings`` via the diff detail template. The diff is rendered as
    a flat side-by-side Path / Before / After table (ATW-524/ATW-525) — the
    view flattens ``object.diff`` into ``lines`` via
    :func:`netbox_pyats.diff.flatten_diff_tree` and passes the list to
    ``inc/diff_table.html``. The ``before``/``after`` snapshot rows are linked
    so the operator can drill into either side.
    """

    queryset = PyatsSnapshotDiff.objects.all()

    def get_extra_context(self, request, instance):
        return {"lines": flatten_diff_tree(instance.diff)}


@register_model_view(PyatsSnapshotDiff, "delete")
class PyatsSnapshotDiffDeleteView(generic.ObjectDeleteView):
    queryset = PyatsSnapshotDiff.objects.all()


class PyatsSnapshotDiffBulkDeleteView(generic.BulkDeleteView):
    queryset = PyatsSnapshotDiff.objects.all()
    table = tables.PyatsSnapshotDiffTable


class DeviceDiffView(PermissionRequiredMixin, View):
    """Endpoint the device-page PyATS panel POSTs to.

    Accepts ``before_id`` and ``after_id`` (snapshot pks), validates they both
    belong to the device in the URL, enqueues a :func:`run_diff_job` on the
    ``pyats`` RQ queue via :func:`jobs.enqueue_diff`, flashes a "diff queued"
    message, and redirects back to the device page. The actual diff runs on the
    worker; the diff row appears in the device-page diff history once the job
    completes and the page is refreshed.
    """

    permission_required = "netbox_pyats.add_pyatssnapshotdiff"

    def post(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        form = forms.DeviceDiffForm(request.POST, device=device)
        if not form.is_valid():
            messages.error(request, f"Invalid diff request: {form.errors}")
            return redirect(device.get_absolute_url())

        before_id = form.cleaned_data["before_id"]
        after_id = form.cleaned_data["after_id"]

        # Validate both snapshots exist and belong to this device. We do this
        # in the view (not the job) so the operator gets immediate feedback if
        # they stale-pick a snapshot that was just deleted, or if a malformed
        # request tries to diff snapshots across devices.
        before = PyatsSnapshot.objects.filter(pk=before_id, device=device).first()
        after = PyatsSnapshot.objects.filter(pk=after_id, device=device).first()
        if before is None or after is None:
            messages.error(
                request,
                "Both snapshots must exist and belong to this device. " f"(before_id={before_id}, after_id={after_id})",
            )
            return redirect(device.get_absolute_url())
        if before_id == after_id:
            messages.error(request, "Cannot diff a snapshot against itself.")
            return redirect(device.get_absolute_url())

        jobs.enqueue_diff(device, before_id=before_id, after_id=after_id, user=request.user)
        messages.success(
            request,
            f"PyATS diff queued for {device} ({before_id}→{after_id}). "
            "It will appear in the PyATS tab when the worker finishes.",
        )
        return redirect(device.get_absolute_url())


# --------------------------------------------------------------------------- #
# Compliance views (Phase 4, ATW-15)
# --------------------------------------------------------------------------- #


class PyatsGoldenConfigListView(generic.ObjectListView):
    """List of all PyATS golden configs across all devices.

    Filterable by device and source (manual / from snapshot). The
    device-page PyATS compliance sub-tab links here with ``?device_id=<pk>``
    for the per-device golden history.
    """

    queryset = PyatsGoldenConfig.objects.all()
    table = tables.PyatsGoldenConfigTable
    filterset = filtersets.PyatsGoldenConfigFilterSet
    filterset_form = forms.PyatsGoldenConfigFilterForm


@register_model_view(PyatsGoldenConfig)
class PyatsGoldenConfigView(generic.ObjectView):
    """Detail view for a single golden config.

    Renders the ``config_text`` in a ``<pre>`` block, the source badge, and the
    source_snapshot link (when promoted from a snapshot) via the golden detail
    template — no JS dependency.
    """

    queryset = PyatsGoldenConfig.objects.all()


@register_model_view(PyatsGoldenConfig, "edit")
class PyatsGoldenConfigEditView(generic.ObjectEditView):
    """Create/edit view for a PyATS Golden Config."""

    queryset = PyatsGoldenConfig.objects.all()
    form = forms.PyatsGoldenConfigForm


@register_model_view(PyatsGoldenConfig, "delete")
class PyatsGoldenConfigDeleteView(generic.ObjectDeleteView):
    queryset = PyatsGoldenConfig.objects.all()


class PyatsGoldenConfigBulkDeleteView(generic.BulkDeleteView):
    queryset = PyatsGoldenConfig.objects.all()
    table = tables.PyatsGoldenConfigTable


class PyatsComplianceRunListView(generic.ObjectListView):
    """List of all PyATS compliance runs across all devices.

    Filterable by device, result (compliant / drift / error), and whether the
    run has drift or warnings. The device-page PyATS compliance sub-tab links
    here with ``?device_id=<pk>`` for the per-device compliance history.
    """

    queryset = PyatsComplianceRun.objects.all()
    table = tables.PyatsComplianceRunTable
    filterset = filtersets.PyatsComplianceRunFilterSet
    filterset_form = forms.PyatsComplianceRunFilterForm


@register_model_view(PyatsComplianceRun)
class PyatsComplianceRunView(generic.ObjectView):
    """Detail view for a single compliance run.

    Renders the JSONB ``diff`` tree, the ``summary`` counts, and
    ``parser_warnings`` via the compliance run detail template. The diff is
    rendered as a flat side-by-side Path / Before / After table
    (ATW-524/ATW-525) — the view flattens ``object.diff`` into ``lines`` via
    :func:`netbox_pyats.diff.flatten_diff_tree` and passes the list to
    ``inc/diff_table.html`` (same partial the snapshot-diff view uses). The
    ``golden``/``snapshot`` rows are linked so the operator can drill into
    either side.
    """

    queryset = PyatsComplianceRun.objects.all()

    def get_extra_context(self, request, instance):
        return {"lines": flatten_diff_tree(instance.diff)}


@register_model_view(PyatsComplianceRun, "delete")
class PyatsComplianceRunDeleteView(generic.ObjectDeleteView):
    queryset = PyatsComplianceRun.objects.all()


class PyatsComplianceRunBulkDeleteView(generic.BulkDeleteView):
    queryset = PyatsComplianceRun.objects.all()
    table = tables.PyatsComplianceRunTable


class DeviceComplianceView(PermissionRequiredMixin, View):
    """Endpoint the device-page PyATS compliance sub-tab POSTs to.

    Accepts ``golden_id`` and ``snapshot_id``, validates they both belong to
    the device in the URL, enqueues a :func:`run_compliance_job` on the
    ``pyats`` RQ queue via :func:`jobs.enqueue_compliance`, flashes a
    "compliance run queued" message, and redirects back to the device page.
    The actual compliance run executes on the worker; the compliance row
    appears in the device-page compliance history once the job completes and
    the page is refreshed.
    """

    permission_required = "netbox_pyats.add_pyatscompliancerun"

    def post(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        form = forms.DeviceComplianceForm(request.POST)
        if not form.is_valid():
            messages.error(request, f"Invalid compliance request: {form.errors}")
            return redirect(device.get_absolute_url())

        golden_id = form.cleaned_data["golden_id"]
        snapshot_id = form.cleaned_data["snapshot_id"]
        mode = form.cleaned_data.get("mode")

        # Validate the golden config and snapshot both exist and belong to
        # this device. Done in the view (not the job) so the operator gets
        # immediate feedback on stale-picked or cross-device inputs.
        golden = PyatsGoldenConfig.objects.filter(pk=golden_id, device=device).first()
        snapshot = PyatsSnapshot.objects.filter(pk=snapshot_id, device=device).first()
        if golden is None or snapshot is None:
            messages.error(
                request,
                "Both the golden config and the snapshot must exist and belong to "
                f"this device. (golden_id={golden_id}, snapshot_id={snapshot_id})",
            )
            return redirect(device.get_absolute_url())

        jobs.enqueue_compliance(device, golden_id=golden_id, snapshot_id=snapshot_id, user=request.user, mode=mode)
        messages.success(
            request,
            f"PyATS compliance run queued for {device} (golden #{golden_id} vs "
            f"snapshot #{snapshot_id}). It will appear in the PyATS tab when the "
            "worker finishes.",
        )
        return redirect(device.get_absolute_url())


# --------------------------------------------------------------------------- #
# PyatsJob views + device bulk capture + supported-platforms report (Phase 5, ATW-16)
# --------------------------------------------------------------------------- #


class PyatsJobListView(generic.ObjectListView):
    """Unified list of all PyATS plugin jobs across capture / diff / compliance / batch (Phase 5, ATW-16).

    ADR-0005 §4: a single PyATS-scoped view of "all PyATS work" with links to
    the result rows each job produced, independent of NetBox's ``core.Job``
    retention. Filterable by ``job_type``, ``status``, and ``device``.
    """

    queryset = PyatsJob.objects.select_related(
        "device",
        "related_snapshot",
        "related_diff",
        "related_compliance",
    )
    table = tables.PyatsJobTable
    filterset = filtersets.PyatsJobFilterSet
    filterset_form = forms.PyatsJobFilterForm


@register_model_view(PyatsJob)
class PyatsJobView(generic.ObjectView):
    """Detail view for a single PyatsJob row (Phase 5, ATW-16).

    Renders the job's type/status badge, the targeted device (blank for
    batch_capture), the linked ``core.Job`` row (when not yet purged), the
    result-row link (one of related_snapshot / related_diff /
    related_compliance), the ``error`` text in a ``<pre>`` block (when the
    result row could not be written), and the batch ``summary`` counts (for
    batch_capture jobs). See ADR-0005 §4.
    """

    queryset = PyatsJob.objects.all()


@register_model_view(PyatsJob, "delete")
class PyatsJobDeleteView(generic.ObjectDeleteView):
    """Standard delete view for a PyatsJob row.

    Jobs are append-only history (no edit view, ADR-0005 §4); standard delete
    only — operators can prune old job rows without affecting the result
    rows they produced (the ``related_*`` FKs are ``on_delete=SET_NULL``).
    """

    queryset = PyatsJob.objects.all()


class PyatsJobBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete for PyatsJob rows."""

    queryset = PyatsJob.objects.all()
    table = tables.PyatsJobTable


class DeviceBulkCaptureView(PermissionRequiredMixin, View):
    """Bulk "PyATS capture" action on the NetBox device list (Phase 5, ATW-16).

    The operator selects a set of devices on the NetBox device list and picks
    "PyATS capture" from the bulk-action menu. This view renders a small
    confirmation form (capture kind: config / state / full), then enqueues a
    single :func:`jobs.enqueue_batch_capture` job targeting the selected
    device set. The job runs on the dedicated ``pyats`` queue; the
    :class:`PyatsJob` row (``job_type=batch_capture``) appears in the unified
    PyATS jobs view with status pending -> running -> success/partial.

    Requires ``netbox_pyats.add_pyatsjob`` so only authorized operators can
    trigger batch captures (a batch is a potentially wide fan-out of device
    connections).

    Implemented as a plain ``View`` with ``PermissionRequiredMixin`` rather
    than a NetBox ``Bulk*View`` subclass because this is a custom action
    (enqueue a plugin job), not one of the standard bulk CRUD operations
    NetBox's generic bulk views model. The selected device pks arrive as the
    ``pk`` list in POST (the same shape NetBox's own bulk actions use); we
    re-resolve them against ``dcim.Device`` so a device deleted between the
    list render and the POST is silently dropped (the batch job's summary
    reflects what was actually iterated).
    """

    form = forms.DeviceBulkCaptureForm
    permission_required = "netbox_pyats.add_pyatsjob"
    template_name = "netbox_pyats/device_bulk_capture.html"

    def get(self, request, **kwargs):
        # Render the confirmation form against the selected pks (passed in
        # the query string by the device-list bulk-action menu).
        pks = request.GET.getlist("pk") or request.GET.getlist("_pk")
        form = self.form(initial={"kind": SnapshotKindChoices.KIND_FULL})
        return self._render(request, form, pks)

    def post(self, request, **kwargs):
        from dcim.models import Device

        # NetBox's bulk-action machinery passes the selected pks as `_pk` /
        # `pk` list in POST. We re-resolve them against dcim.Device so a
        # device deleted between the list render and the POST is silently
        # dropped (the batch job's summary reflects what was actually
        # iterated, not the enqueue-time count — see jobs.batch_capture_job).
        pks = request.POST.getlist("pk") or request.POST.getlist("_pk")
        devices_qs = Device.objects.filter(pk__in=pks)
        if not devices_qs.exists():
            messages.error(request, "No devices selected for batch capture.")
            return redirect("plugins:netbox_pyats:pyatsjob_list")

        form = self.form(request.POST)
        if not form.is_valid():
            messages.error(request, f"Invalid batch capture request: {form.errors}")
            return self._render(request, form, pks)

        kind = form.cleaned_data["kind"]
        core_job = jobs.enqueue_batch_capture(devices_qs, kind=kind, user=request.user)
        messages.success(
            request,
            f"PyATS batch {kind} capture queued for {devices_qs.count()} device(s); "
            f"core.Job #{core_job.pk}. It will appear in the PyATS Jobs list when "
            "the worker finishes.",
        )
        return redirect("plugins:netbox_pyats:pyatsjob_list")

    def _render(self, request, form, pks):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {"form": form, "pks": pks, "return_url": "plugins:netbox_pyats:pyatsjob_list"},
        )


class SupportedPlatformsReportView(View):
    """Static "supported platforms" report (Phase 5, ATW-16, Option A).

    ADR-0001 §6 requires the web process to NOT import Genie. This view is
    web-process-safe: it reads the static :data:`netbox_pyats.testbed.PLATFORM_SLUG_TO_PYATS_OS`
    map (a plain Python dict, no Genie import) and renders the supported
    platform slugs + their mapped pyATS os string + a count of NetBox devices
    currently on each platform. Live Genie introspection (Option B) is v2;
    v1 ships the static map the testbed builder actually uses, so the report
    matches what the capture job will do.

    The device counts are computed via a single ``Device.objects.values``
    query grouped by platform slug, so the report stays cheap even on large
    NetBox instances. No DB writes; the view is read-only.
    """

    template_name = "netbox_pyats/supported_platforms.html"

    def get(self, request):
        from collections import Counter

        from dcim.models import Device

        # Group all devices by their platform slug, then intersect with the
        # supported map. Devices with no platform, or a platform not in the
        # supported map, surface as "unsupported" with their count too, so
        # the operator sees the full picture (not just the supported ones).
        device_counts_by_slug = Counter(
            Device.objects.exclude(platform__isnull=True).values_list("platform__slug", flat=True)
        )

        supported_rows = []
        for slug, pyats_os in sorted(PLATFORM_SLUG_TO_PYATS_OS.items()):
            supported_rows.append(
                {
                    "slug": slug,
                    "pyats_os": pyats_os,
                    "device_count": device_counts_by_slug.get(slug, 0),
                }
            )

        # Devices whose platform slug is not in the supported map (or who have
        # no platform at all) — surface as a single "unsupported" row with the
        # total count so the operator knows how many devices will be skipped
        # by a batch capture.
        supported_slugs = set(PLATFORM_SLUG_TO_PYATS_OS.keys())
        unsupported_count = sum(count for slug, count in device_counts_by_slug.items() if slug not in supported_slugs)
        no_platform_count = Device.objects.filter(platform__isnull=True).count()

        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {
                "supported_rows": supported_rows,
                "unsupported_count": unsupported_count,
                "no_platform_count": no_platform_count,
                "unsupported_os_sentinel": UNSUPPORTED_OS,
            },
        )


# --------------------------------------------------------------------------- #
# Device parse views (ATW-241 child 2, ATW-250)
# --------------------------------------------------------------------------- #


def _resolve_parse_context(device):
    """Resolve the pyATS os + catalog row + command choices for a device.

    Web-process-safe: reads :func:`netbox_pyats.testbed.platform_to_pyats_os`
    (the static platform map — no Genie import) and the
    :class:`PyatsParserCatalog` row (DB only). Returns a dict the parse view
    hands to the template:

    - ``pyats_os``: the resolved os string (or :data:`UNSUPPORTED_OS`).
    - ``platform_supported``: True if the os is Genie-supported.
    - ``catalog_row``: the :class:`PyatsParserCatalog` row for this os, or
      ``None`` when the platform is unsupported or no row exists yet.
    - ``command_choices``: list of ``(command, command)`` tuples for the
      ``DeviceParseForm.commands`` MultipleChoiceField, sorted (the catalog
      row's ``commands`` is already sorted by the refresh job; we preserve
      that order). Empty when no catalog row.
    - ``catalog_present``: True if a catalog row exists for this os (False for
      unsupported os or not-yet-refreshed supported os).
    """
    pyats_os = platform_to_pyats_os(getattr(device, "platform", None))
    platform_supported = is_supported_os(pyats_os)
    catalog_row = None
    command_choices: list[tuple[str, str]] = []
    if platform_supported:
        catalog_row = PyatsParserCatalog.objects.filter(pyats_os=pyats_os).first()
        if catalog_row is not None and catalog_row.commands:
            # The catalog row's commands list is already sorted/deduped by
            # the refresh job; preserve that order. Each choice is
            # (value, label) — value == label == the command string.
            command_choices = [(str(c), str(c)) for c in catalog_row.commands]
    return {
        "pyats_os": pyats_os,
        "platform_supported": platform_supported,
        "catalog_row": catalog_row,
        "command_choices": command_choices,
        "catalog_present": catalog_row is not None,
    }


class DeviceParseView(PermissionRequiredMixin, View):
    """Device-page "Parse" sub-tab (ATW-241 child 2, ATW-250).

    A GET form view + POST enqueue (unlike the existing
    ``device_capture``/``device_diff``/``device_compliance`` POST-only
    endpoints — the operator needs to see the cached parser command list and
    pick). On GET, resolves the device's pyATS os, reads the
    :class:`PyatsParserCatalog` row for that os (DB only — no Genie import,
    ADR-0001 §6), builds a :class:`forms.DeviceParseForm` with the command
    choices, and renders :template:`netbox_pyats/device_parse.html`.

    On POST, validates the form (requires at least one of ``commands`` or
    ``manual_command``), builds a de-duplicated, order-preserving command
    list (selected commands first, then the manual command), enqueues the
    parse job via :func:`jobs.enqueue_parse` on the dedicated ``pyats`` RQ
    queue, and redirects back to the device page. The actual parse runs on
    the worker; the result lands as a ``kind='parse'`` :class:`PyatsSnapshot`
    row (ATW-251) and appears in the device-page snapshot history once the
    worker finishes.

    Requires ``netbox_pyats.add_pyatssnapshot`` so only authorized operators
    can trigger on-demand parses. The parse result is stored as a
    ``kind='parse'`` :class:`PyatsSnapshot` row (ATW-251, plan §1.3 — no
    separate ``PyatsParserResult`` model), so the existing per-action
    ``add_pyatssnapshot`` permission is the right gate: NetBox's permission
    resolver (``utilities/permissions.resolve_permission``) splits
    ``<app>.<action>_<model>`` and looks up the matching ``ContentType``, so a
    custom ``add_pyatsparseresult`` codename (with no ``pyatsparseresult``
    model/ContentType) is unresolvable. Reusing ``add_pyatssnapshot`` keeps the
    permission surface to models that actually exist (ATW-250).
    """

    permission_required = "netbox_pyats.add_pyatssnapshot"
    template_name = "netbox_pyats/device_parse.html"

    def get(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        ctx = _resolve_parse_context(device)
        form = forms.DeviceParseForm(command_choices=ctx["command_choices"])
        return self._render(request, device, form, ctx)

    def post(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        ctx = _resolve_parse_context(device)
        form = forms.DeviceParseForm(request.POST, command_choices=ctx["command_choices"])
        if not form.is_valid():
            return self._render(request, device, form, ctx)

        # Build the command list: selected checkbox commands first (in the
        # catalog's order), then the manual command (if any). De-duplicate
        # while preserving order so a manual command that matches a checked
        # box does not run twice.
        commands: list[str] = []
        seen: set[str] = set()
        for cmd in form.cleaned_data.get("commands") or []:
            if cmd and cmd not in seen:
                commands.append(cmd)
                seen.add(cmd)
        manual = (form.cleaned_data.get("manual_command") or "").strip()
        if manual and manual not in seen:
            commands.append(manual)

        # form.clean() guarantees commands is non-empty, but defensive: a
        # malformed POST (e.g. only whitespace in manual_command after strip)
        # should re-render rather than enqueue an empty job.
        if not commands:
            form.add_error(None, "Select at least one parser command or type a manual command.")
            return self._render(request, device, form, ctx)

        core_job = jobs.enqueue_parse(device, commands=commands, user=request.user)
        messages.success(
            request,
            f"PyATS parse queued for {device} ({len(commands)} command(s)); "
            f"core.Job #{core_job.pk}. The result will appear in the PyATS "
            "tab snapshot history when the worker finishes.",
        )
        return redirect(device.get_absolute_url())

    def _render(self, request, device, form, ctx):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {
                "device": device,
                "form": form,
                "pyats_os": ctx["pyats_os"],
                "platform_supported": ctx["platform_supported"],
                "catalog_row": ctx["catalog_row"],
                "catalog_present": ctx["catalog_present"],
                "command_count": len(ctx["command_choices"]),
                "refresh_url": _refresh_parser_catalog_url_for_device(device),
                "device_url": device.get_absolute_url(),
            },
        )


class DeviceRefreshCatalogView(PermissionRequiredMixin, View):
    """Device-page "Refresh parser list" button (ATW-241 child 2, ATW-250).

    A small POST-only endpoint enqueued by the "Refresh parser list" button
    on the parse sub-tab. It calls :func:`jobs.enqueue_refresh_parser_catalog`
    (ATW-249), which enqueues the worker-only catalog refresh on the
    dedicated ``pyats`` RQ queue, then redirects back to the parse page with
    a "refresh queued" message. The refresh covers every Genie-supported os
    (one row per os, not per device — see :func:`jobs.enqueue_refresh_parser_catalog`),
    so the operator only needs to click it once on any device of a given os
    after a ``genie.libs`` upgrade.

    Requires ``netbox_pyats.add_pyatssnapshot`` so the operator who can
    enqueue a parse can also refresh the catalog the parse form reads — same
    permission surface, no separate role.
    """

    permission_required = "netbox_pyats.add_pyatssnapshot"

    def post(self, request, device_id):
        from dcim.models import Device

        device = get_object_or_404(Device, pk=device_id)
        core_job = jobs.enqueue_refresh_parser_catalog(user=request.user)
        messages.success(
            request,
            f"PyATS parser catalog refresh queued (core.Job #{core_job.pk}). "
            "The checkbox list on the Parse tab will populate when the worker "
            "finishes; refresh this page afterwards.",
        )
        return redirect("plugins:netbox_pyats:device_parse", device_id=device.pk)


def _refresh_parser_catalog_url_for_device(device):
    """Return the POST URL for the device-page "Refresh parser list" button."""
    from django.urls import reverse

    return reverse(
        "plugins:netbox_pyats:device_refresh_parser_catalog",
        kwargs={"device_id": device.pk},
    )


# --------------------------------------------------------------------------- #
# Capture schedule views (ATW-433, ADR-0008)
# --------------------------------------------------------------------------- #


class PyatsCaptureScheduleListView(generic.ObjectListView):
    """List of all PyATS capture schedules (ATW-433).

    Filterable by kind, enabled, and name. The operator creates a schedule
    here, then enqueues the ``RunCaptureSchedulesJob`` dispatcher with an
    ``interval`` to run it on a recurring cadence (ADR-0008).
    """

    queryset = PyatsCaptureSchedule.objects.all()
    table = tables.PyatsCaptureScheduleTable
    filterset = filtersets.PyatsCaptureScheduleFilterSet
    filterset_form = forms.PyatsCaptureScheduleFilterForm


@register_model_view(PyatsCaptureSchedule)
class PyatsCaptureScheduleView(generic.ObjectView):
    """Detail view for a single capture schedule (ATW-433)."""

    queryset = PyatsCaptureSchedule.objects.all()


@register_model_view(PyatsCaptureSchedule, "edit")
class PyatsCaptureScheduleEditView(generic.ObjectEditView):
    """Create/edit view for a PyATS Capture Schedule (ATW-433)."""

    queryset = PyatsCaptureSchedule.objects.all()
    form = forms.PyatsCaptureScheduleForm


@register_model_view(PyatsCaptureSchedule, "delete")
class PyatsCaptureScheduleDeleteView(generic.ObjectDeleteView):
    """Standard delete view for a PyatsCaptureSchedule row (ATW-433)."""

    queryset = PyatsCaptureSchedule.objects.all()


class PyatsCaptureScheduleBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete for PyatsCaptureSchedule rows (ATW-433)."""

    queryset = PyatsCaptureSchedule.objects.all()
    table = tables.PyatsCaptureScheduleTable


# --------------------------------------------------------------------------- #
# Parser catalog refresh schedule views (ATW-581)
# --------------------------------------------------------------------------- #


class PyatsParserCatalogRefreshScheduleListView(generic.ObjectListView):
    """List view for the PyatsParserCatalogRefreshSchedule (ATW-581).

    The model is a single-row intent gate, so the list always shows at most
    one row. The operator toggles ``enabled`` via the edit view and enqueues
    ``RunParserCatalogRefreshSchedulesJob`` with an ``interval`` to run it on
    a recurring cadence (mirrors the capture schedule flow / ADR-0008).
    """

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()
    table = tables.PyatsParserCatalogRefreshScheduleTable
    filterset = filtersets.PyatsParserCatalogRefreshScheduleFilterSet
    filterset_form = forms.PyatsParserCatalogRefreshScheduleFilterForm


@register_model_view(PyatsParserCatalogRefreshSchedule)
class PyatsParserCatalogRefreshScheduleView(generic.ObjectView):
    """Detail view for the PyatsParserCatalogRefreshSchedule (ATW-581)."""

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()


@register_model_view(PyatsParserCatalogRefreshSchedule, "edit")
class PyatsParserCatalogRefreshScheduleEditView(generic.ObjectEditView):
    """Create/edit view for the PyatsParserCatalogRefreshSchedule (ATW-581).

    The model is a singleton by convention: the dispatcher reads the row with
    ``pk=1``. To keep the operator from creating a second row via the "Add"
    button, ``get_object`` redirects an empty ``pk`` to the existing row when
    one exists (the singleton is created lazily by the dispatcher on first
    run, but the operator can also create it here).
    """

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()
    form = forms.PyatsParserCatalogRefreshScheduleForm

    def get_object(self, kwargs):
        if not kwargs.get("pk"):
            existing = PyatsParserCatalogRefreshSchedule.objects.first()
            if existing is not None:
                return existing
        return super().get_object(kwargs)


@register_model_view(PyatsParserCatalogRefreshSchedule, "delete")
class PyatsParserCatalogRefreshScheduleDeleteView(generic.ObjectDeleteView):
    """Standard delete view for a PyatsParserCatalogRefreshSchedule row (ATW-581)."""

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()


class PyatsParserCatalogRefreshScheduleBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete for PyatsParserCatalogRefreshSchedule rows (ATW-581)."""

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()
    table = tables.PyatsParserCatalogRefreshScheduleTable


# --------------------------------------------------------------------------- #
# Genie dedicated pages (ATW-728 nav restructure → ATW-729 dedicated Parse,
# ATW-730 dedicated Learn)
# --------------------------------------------------------------------------- #
# The Genie top-level menu (ATW-727) leads with the three primary Genie
# tools: Parse, Learn, Diff. Diff reuses the snapshot-diff list view; Parse
# has a full dedicated page (ATW-729). Learn now has a full dedicated page
# (ATW-730) that combines the parser catalog (the learned capability state)
# with a device picker + Run Learn action and recent learn results.


class GenieLearnView(PermissionRequiredMixin, View):
    """Dedicated Genie Learn page (ATW-730).

    Promotes Learn from the interim landing page (which rendered only the
    parser catalog) to a first-class plugin page directly accessible from
    the Genie menu. The page combines three surfaces on one URL
    (``/genie/learn/``):

    1. The parser catalog — :class:`PyatsParserCatalog` rows, the learned
       capability state Genie has populated for each supported pyATS os (the
       set of CLI commands Genie can parse). This is the evidence of what
       Learn has captured. Read from the DB only — web-process-safe
       (ADR-0001 §6).
    2. A device picker + "Run Learn" action — a ``<select>`` submitted via
       GET (``?device=<pk>``) that reloads the page with the selected device
       highlighted, plus a POST form that enqueues a Genie Ops Learn job via
       :func:`jobs.enqueue_learn`. The Learn job drives the Genie Ops
       framework (``Lookup.from_device(device).ops.<feature>(device).learn()``)
       on the worker and stores a ``kind='learn'`` snapshot. No client-side
       JS (ADR-0001 §4).
    3. Recent learn results — the latest ``kind='learn'`` :class:`PyatsSnapshot`
       rows across all devices, rendered via :class:`tables.PyatsSnapshotTable`
       so the operator sees Learn activity at a glance.

    No new models, no new forms, no Genie import in the web process
    (ADR-0001 §6) — the catalog is read from the DB only; the Learn runs on
    the worker.

    Requires ``netbox_pyats.add_pyatssnapshot`` (the learn result lands as a
    ``kind='learn'`` snapshot, same gate as the parse page) and
    ``netbox_pyats.view_pyatssnapshot`` (the catalog + recent-results table
    read snapshots / the catalog rows).
    """

    permission_required = ("netbox_pyats.add_pyatssnapshot", "netbox_pyats.view_pyatssnapshot")
    template_name = "netbox_pyats/genie_learn.html"

    #: How many recent learn snapshots to show on the page.
    RECENT_LIMIT = 15

    def get(self, request):
        from django.shortcuts import render

        device = None
        device_id = request.GET.get("device")
        if device_id:
            device = get_object_or_404(Device, pk=device_id)

        # Resolve the platform support status for the selected device so the
        # template can show a supported/unsupported badge before the operator
        # clicks Run Learn.
        platform_supported = False
        pyats_os = None
        if device is not None:
            from .testbed import is_supported_os, platform_to_pyats_os

            pyats_os = platform_to_pyats_os(getattr(device, "platform", None))
            platform_supported = is_supported_os(pyats_os)

        recent = list(
            PyatsSnapshot.objects.filter(kind=SnapshotKindChoices.KIND_LEARN)
            .select_related("device")
            .order_by("-captured_at")[: self.RECENT_LIMIT]
        )
        recent_table = tables.PyatsSnapshotTable(recent)

        return render(
            request,
            self.template_name,
            {
                "catalog_rows": PyatsParserCatalog.objects.order_by("pyats_os"),
                "devices": Device.objects.select_related("platform").order_by("name"),
                "selected_device": device,
                "pyats_os": pyats_os,
                "platform_supported": platform_supported,
                "recent_table": recent_table,
                "recent_count": len(recent),
            },
        )

    def post(self, request):
        from django.shortcuts import redirect
        from django.urls import reverse

        device_id = request.POST.get("device")
        if not device_id:
            messages.error(request, "Select a device first.")
            return redirect("plugins:netbox_pyats:genie_learn")

        device = get_object_or_404(Device, pk=device_id)
        core_job = jobs.enqueue_learn(device, user=request.user)
        messages.success(
            request,
            f"PyATS Genie Learn queued for {device}; core.Job #{core_job.pk}. "
            "The result will appear in the recent learn results below when the "
            "worker finishes.",
        )
        return redirect(f"{reverse('plugins:netbox_pyats:genie_learn')}?device={device.pk}")


class GenieParseView(PermissionRequiredMixin, View):
    """Dedicated Genie Parse page (ATW-729).

    Promotes Parse from a device-page sub-tab to a first-class plugin page
    directly accessible from the Genie menu. The page combines three
    surfaces on one URL (``/genie/parse/``):

    1. A device picker — a ``<select>`` submitted via GET (``?device=<pk>``)
       that reloads the page with the selected device's parse form. No
       client-side JS (ADR-0001 §4).
    2. The parse form — the same :class:`forms.DeviceParseForm` the device
       sub-tab uses, populated from the selected device's
       :class:`PyatsParserCatalog` row via :func:`_resolve_parse_context`.
       Renders only when a device is picked. POST enqueues the parse job via
       :func:`jobs.enqueue_parse` (same path as the device sub-tab) and
       redirects back to this page with ``?device=<pk>`` so the operator can
       run another parse immediately.
    3. Recent parse results — the latest ``kind='parse'``
       :class:`PyatsSnapshot` rows across *all* devices (not just the
       selected one), rendered via :class:`tables.PyatsSnapshotTable` so the
       operator sees parse activity at a glance.

    The device-page Parse sub-tab (:class:`DeviceParseView`) stays as a
    convenience link; this page is the primary surface. No new models, no
    new forms, no Genie import in the web process (ADR-0001 §6) —
    :func:`_resolve_parse_context` reads the catalog from the DB only.

    Requires ``netbox_pyats.add_pyatssnapshot`` (the parse result lands as a
    ``kind='parse'`` snapshot, same gate as the device sub-tab) and
    ``netbox_pyats.view_pyatssnapshot`` (the recent-results table reads
    snapshots).
    """

    permission_required = ("netbox_pyats.add_pyatssnapshot", "netbox_pyats.view_pyatssnapshot")
    template_name = "netbox_pyats/genie_parse.html"

    #: How many recent parse snapshots to show on the page.
    RECENT_LIMIT = 15

    def get(self, request):
        from django.shortcuts import render

        device = None
        form = None
        ctx = None
        device_id = request.GET.get("device")
        if device_id:
            device = get_object_or_404(Device, pk=device_id)
            ctx = _resolve_parse_context(device)
            form = forms.DeviceParseForm(command_choices=ctx["command_choices"])

        recent = list(
            PyatsSnapshot.objects.filter(kind=SnapshotKindChoices.KIND_PARSE)
            .select_related("device")
            .order_by("-captured_at")[: self.RECENT_LIMIT]
        )
        recent_table = tables.PyatsSnapshotTable(recent)

        return render(
            request,
            self.template_name,
            {
                "devices": Device.objects.select_related("platform").order_by("name"),
                "selected_device": device,
                "form": form,
                "pyats_os": ctx["pyats_os"] if ctx else None,
                "platform_supported": ctx["platform_supported"] if ctx else False,
                "catalog_row": ctx["catalog_row"] if ctx else None,
                "catalog_present": ctx["catalog_present"] if ctx else False,
                "command_count": len(ctx["command_choices"]) if ctx else 0,
                "refresh_url": _refresh_parser_catalog_url_for_device(device) if device else None,
                "recent_table": recent_table,
                "recent_count": len(recent),
            },
        )

    def post(self, request):
        # The parse form POSTs back to this page with ``device`` (the
        # picker's <select> value) plus the DeviceParseForm fields
        # (commands / manual_command). The device must be selected — a POST
        # without one re-renders the picker with an error.
        device_id = request.POST.get("device")
        if not device_id:
            messages.error(request, "Select a device first.")
            return redirect("plugins:netbox_pyats:genie_parse")

        device = get_object_or_404(Device, pk=device_id)
        ctx = _resolve_parse_context(device)
        form = forms.DeviceParseForm(request.POST, command_choices=ctx["command_choices"])
        if not form.is_valid():
            return self._render_form(request, device, form, ctx)

        # Build the command list: selected checkbox commands first (in the
        # catalog's order), then the manual command (if any). De-duplicate
        # while preserving order so a manual command that matches a checked
        # box does not run twice. Same logic as DeviceParseView.post.
        commands: list[str] = []
        seen: set[str] = set()
        for cmd in form.cleaned_data.get("commands") or []:
            if cmd and cmd not in seen:
                commands.append(cmd)
                seen.add(cmd)
        manual = (form.cleaned_data.get("manual_command") or "").strip()
        if manual and manual not in seen:
            commands.append(manual)

        if not commands:
            form.add_error(None, "Select at least one parser command or type a manual command.")
            return self._render_form(request, device, form, ctx)

        core_job = jobs.enqueue_parse(device, commands=commands, user=request.user)
        messages.success(
            request,
            f"PyATS parse queued for {device} ({len(commands)} command(s)); "
            f"core.Job #{core_job.pk}. The result will appear in the recent "
            "parse results below when the worker finishes.",
        )
        from django.urls import reverse

        return redirect(f"{reverse('plugins:netbox_pyats:genie_parse')}?device={device.pk}")

    def _render_form(self, request, device, form, ctx):
        from django.shortcuts import render

        recent = list(
            PyatsSnapshot.objects.filter(kind=SnapshotKindChoices.KIND_PARSE)
            .select_related("device")
            .order_by("-captured_at")[: self.RECENT_LIMIT]
        )
        return render(
            request,
            self.template_name,
            {
                "devices": Device.objects.select_related("platform").order_by("name"),
                "selected_device": device,
                "form": form,
                "pyats_os": ctx["pyats_os"],
                "platform_supported": ctx["platform_supported"],
                "catalog_row": ctx["catalog_row"],
                "catalog_present": ctx["catalog_present"],
                "command_count": len(ctx["command_choices"]),
                "refresh_url": _refresh_parser_catalog_url_for_device(device),
                "recent_table": tables.PyatsSnapshotTable(recent),
                "recent_count": len(recent),
            },
        )
