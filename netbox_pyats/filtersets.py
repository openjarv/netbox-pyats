import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

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


def _has_changes_q():
    """Q matching rows whose summary JSON has a non-zero added/removed/changed count.

    Mirrors ``PyatsSnapshotDiff.has_changes`` / ``PyatsComplianceRun.has_drift``,
    which return ``bool(s.get("added") or s.get("removed") or s.get("changed"))``.
    """
    return Q(summary__added__gt=0) | Q(summary__removed__gt=0) | Q(summary__changed__gt=0)


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
    (Phase 4) query on.
    """

    has_changes = django_filters.BooleanFilter(method="filter_has_changes", label="Only diffs with changes")
    has_warnings = django_filters.BooleanFilter(method="filter_has_warnings", label="Only diffs with warnings")

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

    def filter_has_changes(self, queryset, name, value):
        if value:
            return queryset.filter(_has_changes_q())
        return queryset

    def filter_has_warnings(self, queryset, name, value):
        if value:
            return queryset.exclude(parser_warnings=[]).exclude(parser_warnings__isnull=True)
        return queryset


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

    Lets the compliance run list view be filtered by device, result, mode, and
    the golden/snapshot ids — the axes the device-page compliance history and
    the compliance picker query on.
    """

    has_drift = django_filters.BooleanFilter(method="filter_has_drift", label="Only runs with drift")
    has_warnings = django_filters.BooleanFilter(method="filter_has_warnings", label="Only runs with warnings")

    class Meta:
        model = PyatsComplianceRun
        fields = [
            "id",
            "device_id",
            "result",
            "mode",
            "golden_id",
            "snapshot_id",
            "created",
        ]

    def filter_has_drift(self, queryset, name, value):
        if value:
            return queryset.filter(_has_changes_q())
        return queryset

    def filter_has_warnings(self, queryset, name, value):
        if value:
            return queryset.exclude(parser_warnings=[]).exclude(parser_warnings__isnull=True)
        return queryset


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


class PyatsParserCatalogFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsParserCatalog model (ATW-241 child 1).

    Lets the catalog list view be filtered by ``pyats_os`` — the axis the
    device-page Parse sub-tab queries on (one row per os).
    """

    class Meta:
        model = PyatsParserCatalog
        fields = [
            "id",
            "pyats_os",
            "genie_version",
            "pyats_version",
            "created",
        ]


class PyatsCaptureScheduleFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsCaptureSchedule model (ATW-433).

    Lets the schedule list view be filtered by ``kind``, ``enabled``, and
    ``name`` — the axes the operator is most likely to filter on when
    managing recurring captures.
    """

    class Meta:
        model = PyatsCaptureSchedule
        fields = [
            "id",
            "name",
            "kind",
            "enabled",
            "created",
        ]


class PyatsParserCatalogRefreshScheduleFilterSet(NetBoxModelFilterSet):
    """FilterSet for the PyatsParserCatalogRefreshSchedule model (ATW-581).

    Lets the refresh schedule list view be filtered by ``enabled`` — the
    only operator-relevant axis on a single-row intent model.
    """

    class Meta:
        model = PyatsParserCatalogRefreshSchedule
        fields = [
            "id",
            "enabled",
            "created",
        ]
