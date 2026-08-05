from netbox.api.viewsets import NetBoxModelViewSet

from netbox_pyats.filtersets import (
    PyatsCaptureScheduleFilterSet,
    PyatsComplianceRunFilterSet,
    PyatsCredentialFilterSet,
    PyatsGoldenConfigFilterSet,
    PyatsJobFilterSet,
    PyatsParserCatalogFilterSet,
    PyatsParserCatalogRefreshScheduleFilterSet,
    PyatsSnapshotDiffFilterSet,
    PyatsSnapshotFilterSet,
)
from netbox_pyats.models import (
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

from .serializers import (
    PyatsCaptureScheduleSerializer,
    PyatsComplianceRunSerializer,
    PyatsCredentialSerializer,
    PyatsGoldenConfigSerializer,
    PyatsJobSerializer,
    PyatsParserCatalogRefreshScheduleSerializer,
    PyatsParserCatalogSerializer,
    PyatsSnapshotDiffSerializer,
    PyatsSnapshotSerializer,
)


class PyatsCredentialViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsCredential model."""

    queryset = PyatsCredential.objects.all()
    serializer_class = PyatsCredentialSerializer
    filterset_class = PyatsCredentialFilterSet


class PyatsSnapshotViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsSnapshot model.

    Read-only in v1 (snapshots are produced by the ``capture_snapshot`` RQ
    job, not by direct API writes). The HTTP methods that would mutate a
    snapshot are restricted via ``NetBoxModelViewSet``'s permission checks;
    the serializer's read-only fields enforce the data-layer constraint.
    """

    queryset = PyatsSnapshot.objects.all()
    serializer_class = PyatsSnapshotSerializer
    filterset_class = PyatsSnapshotFilterSet
    http_method_names = ["get", "head", "options"]


class PyatsSnapshotDiffViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsSnapshotDiff model (Phase 3, ATW-14).

    Read-only in v1 (diffs are produced by the ``run_diff`` RQ job, not by
    direct API writes). The HTTP methods that would mutate a diff are
    restricted via ``NetBoxModelViewSet``'s permission checks; the
    serializer's read-only fields enforce the data-layer constraint.
    """

    queryset = PyatsSnapshotDiff.objects.all()
    serializer_class = PyatsSnapshotDiffSerializer
    filterset_class = PyatsSnapshotDiffFilterSet
    http_method_names = ["get", "head", "options"]


class PyatsGoldenConfigViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsGoldenConfig model (Phase 4, ATW-15).

    Fully editable in v1 (operators can create/update/delete golden configs
    via the API, e.g. to seed from an external config-management tool). The
    compliance runs that compare against a golden are produced by the
    ``run_compliance`` RQ job, not by direct API writes.
    """

    queryset = PyatsGoldenConfig.objects.all()
    serializer_class = PyatsGoldenConfigSerializer
    filterset_class = PyatsGoldenConfigFilterSet


class PyatsComplianceRunViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsComplianceRun model (Phase 4, ATW-15).

    Read-only in v1 (compliance runs are produced by the ``run_compliance``
    RQ job, not by direct API writes). The HTTP methods that would mutate a
    compliance run are restricted via ``NetBoxModelViewSet``'s permission
    checks; the serializer's read-only fields enforce the data-layer constraint.
    """

    queryset = PyatsComplianceRun.objects.all()
    serializer_class = PyatsComplianceRunSerializer
    filterset_class = PyatsComplianceRunFilterSet
    http_method_names = ["get", "head", "options"]


class PyatsJobViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsJob model (Phase 5, ATW-16).

    Read-only in v1 (ADR-0005 §4): jobs are produced by the plugin's
    ``enqueue_*`` helpers, not by direct API writes. The HTTP methods that
    would mutate a job are restricted via ``http_method_names`` and the
    serializer's read-only fields enforce the data-layer constraint.
    """

    queryset = PyatsJob.objects.all()
    serializer_class = PyatsJobSerializer
    filterset_class = PyatsJobFilterSet
    http_method_names = ["get", "head", "options"]


class PyatsParserCatalogViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsParserCatalog model (ATW-241 child 1).

    Read-only in v1 (catalog rows are produced by the worker-only
    ``refresh_parser_catalog`` RQ job, not by direct API writes). The HTTP
    methods that would mutate a catalog row are restricted via
    ``http_method_names``; the serializer's read-only fields enforce the
    data-layer constraint.
    """

    queryset = PyatsParserCatalog.objects.all()
    serializer_class = PyatsParserCatalogSerializer
    filterset_class = PyatsParserCatalogFilterSet
    http_method_names = ["get", "head", "options"]


class PyatsCaptureScheduleViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsCaptureSchedule model (ATW-433).

    Fully editable in v1 (operators can create/update/delete schedules via
    the API, e.g. to seed them from an external config-management tool).
    ``last_run_at`` / ``next_run_at`` are read-only (written by the
    dispatcher job).
    """

    queryset = PyatsCaptureSchedule.objects.all()
    serializer_class = PyatsCaptureScheduleSerializer
    filterset_class = PyatsCaptureScheduleFilterSet


class PyatsParserCatalogRefreshScheduleViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsParserCatalogRefreshSchedule model (ATW-581).

    The model is a single-row intent gate; the only operator-editable field
    is ``enabled`` (and tags). ``last_run_at`` / ``next_run_at`` are
    read-only (written by the dispatcher job).
    """

    queryset = PyatsParserCatalogRefreshSchedule.objects.all()
    serializer_class = PyatsParserCatalogRefreshScheduleSerializer
    filterset_class = PyatsParserCatalogRefreshScheduleFilterSet
