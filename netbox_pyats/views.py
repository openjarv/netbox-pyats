"""Views for the netbox-pyats plugin.

Phase 1 (ATW-12) shipped standard NetBox CRUD for :class:`PyatsCredential`.
Phase 2 (ATW-13) adds:

- Standard NetBox list/detail views for :class:`PyatsSnapshot` (the JSONB
  payload is rendered server-side as a collapsible tree via the snapshot
  detail template).
- A ``device_capture`` view that the device-page PyATS panel POSTs to; it
  enqueues a :func:`capture_snapshot_job` on the dedicated ``pyats`` RQ
  queue and redirects back to the device page. The view requires
  ``netbox_pyats.add_pyatssnapshot`` so only authorized operators can
  trigger captures.

Phase 3 (ATW-14) adds:

- Standard NetBox list/detail views for :class:`PyatsSnapshotDiff` (the
  JSONB ``diff`` tree is rendered server-side as a collapsible tree via the
  diff detail template — no JS dependency).
- A ``device_diff`` view that the device-page PyATS panel POSTs to; it
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
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from netbox.views import generic
from utilities.views import register_model_view

from . import filtersets, forms, jobs, tables
from .choices import SnapshotKindChoices, SnapshotTriggerChoices
from .models import PyatsComplianceRun, PyatsCredential, PyatsGoldenConfig, PyatsSnapshot, PyatsSnapshotDiff


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
    ``parser_warnings`` via the diff detail template (a server-side collapsible
    tree — no JS dependency). The ``before``/``after`` snapshot rows are linked
    so the operator can drill into either side.
    """

    queryset = PyatsSnapshotDiff.objects.all()


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
        form = forms.DeviceDiffForm(request.POST)
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
    ``parser_warnings`` via the compliance run detail template (which reuses
    the Phase 3 ``inc/diff_tree.html`` partial — no JS dependency). The
    ``golden``/``snapshot`` rows are linked so the operator can drill into
    either side.
    """

    queryset = PyatsComplianceRun.objects.all()


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

        jobs.enqueue_compliance(device, golden_id=golden_id, snapshot_id=snapshot_id, user=request.user)
        messages.success(
            request,
            f"PyATS compliance run queued for {device} (golden #{golden_id} vs "
            f"snapshot #{snapshot_id}). It will appear in the PyATS tab when the "
            "worker finishes.",
        )
        return redirect(device.get_absolute_url())
