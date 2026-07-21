from netbox.api.viewsets import NetBoxModelViewSet

from netbox_pyats.filtersets import (
    PyatsComplianceRunFilterSet,
    PyatsCredentialFilterSet,
    PyatsGoldenConfigFilterSet,
    PyatsJobFilterSet,
    PyatsSnapshotDiffFilterSet,
    PyatsSnapshotFilterSet,
)
from netbox_pyats.models import (
    PyatsComplianceRun,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsJob,
    PyatsSnapshot,
    PyatsSnapshotDiff,
)

from .serializers import (
    PyatsComplianceRunSerializer,
    PyatsCredentialSerializer,
    PyatsGoldenConfigSerializer,
    PyatsJobSerializer,
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
