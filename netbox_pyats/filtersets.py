from netbox.filtersets import NetBoxModelFilterSet

from .models import PyatsComplianceRun, PyatsCredential, PyatsGoldenConfig, PyatsJob, PyatsSnapshot, PyatsSnapshotDiff


class PyatsCredentialFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsCredential model."""

    class Meta:
        model = PyatsCredential
        fields = [
            "id",
            "name",
            "scope",
            "protocol",
            "ssh_port",
            "device_id",
            "created",
        ]


class PyatsSnapshotFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsSnapshot model.

    Lets the snapshot list view be filtered by device, kind, status, and
    whether it carries parser warnings — the axes the device-page history
    and the diff/compliance pickers (Phase 3/4) will query on.
    """

    class Meta:
        model = PyatsSnapshot
        fields = [
            "id",
            "device_id",
            "kind",
            "status",
            "triggered_by",
            "captured_at",
        ]


class PyatsSnapshotDiffFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsSnapshotDiff model (Phase 3, ATW-14).

    Lets the diff list view be filtered by device, status, and the before/after
    snapshot ids — the axes the device-page history and the compliance picker
    (Phase 4) will query on.
    """

    class Meta:
        model = PyatsSnapshotDiff
        fields = [
            "id",
            "device_id",
            "status",
            "before_id",
            "after_id",
            "created",
        ]


class PyatsGoldenConfigFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsGoldenConfig model (Phase 4, ATW-15).

    Lets the golden config list view be filtered by device and source — the
    axes the device-page compliance picker queries on.
    """

    class Meta:
        model = PyatsGoldenConfig
        fields = [
            "id",
            "name",
            "device_id",
            "source",
            "created",
        ]


class PyatsComplianceRunFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsComplianceRun model (Phase 4, ATW-15).

    Lets the compliance run list view be filtered by device, result, and the
    golden/snapshot ids — the axes the device-page compliance history and the
    compliance picker query on.
    """

    class Meta:
        model = PyatsComplianceRun
        fields = [
            "id",
            "device_id",
            "result",
            "golden_id",
            "snapshot_id",
            "created",
        ]


class PyatsJobFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsJob model (Phase 5, ATW-16).

    Lets the unified jobs view be filtered by job_type (capture / diff /
    compliance / batch_capture), status (pending / running / success / error /
    partial), and device — the axes the unified PyATS jobs view is filterable
    on (ADR-0005 §4).
    """

    class Meta:
        model = PyatsJob
        fields = [
            "id",
            "job_type",
            "status",
            "device_id",
            "core_job_id",
            "rq_job_id",
            "created",
        ]
