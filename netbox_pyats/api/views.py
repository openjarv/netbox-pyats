from netbox.api.viewsets import NetBoxModelViewSet

from netbox_pyats.filtersets import PyatsCredentialFilterSet, PyatsSnapshotDiffFilterSet, PyatsSnapshotFilterSet
from netbox_pyats.models import PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff

from .serializers import PyatsCredentialSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer


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
