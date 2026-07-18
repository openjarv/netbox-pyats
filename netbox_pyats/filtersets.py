from netbox.filtersets import NetBoxModelFilterSet

from .models import PyatsCredential, PyatsSnapshot


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
