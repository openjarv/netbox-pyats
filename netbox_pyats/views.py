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
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from netbox.views import generic

from . import filtersets, forms, jobs, tables
from .choices import SnapshotKindChoices, SnapshotTriggerChoices
from .models import PyatsCredential, PyatsSnapshot


class PyatsCredentialListView(generic.ObjectListView):
    queryset = PyatsCredential.objects.all()
    table = tables.PyatsCredentialTable
    filterset = filtersets.PyatsCredentialFilterSet
    filterset_form = forms.PyatsCredentialFilterForm


class PyatsCredentialView(generic.ObjectView):
    queryset = PyatsCredential.objects.all()


class PyatsCredentialEditView(generic.ObjectEditView):
    queryset = PyatsCredential.objects.all()
    form = forms.PyatsCredentialForm


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


class PyatsSnapshotView(generic.ObjectView):
    """Detail view for a single snapshot.

    Renders the JSONB ``data`` payload and ``parser_warnings`` via the
    snapshot detail template (a server-side collapsible tree — no JS
    dependency).
    """

    queryset = PyatsSnapshot.objects.all()


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
