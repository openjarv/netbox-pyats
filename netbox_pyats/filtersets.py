from netbox.filtersets import NetBoxModelFilterSet

from .models import PyatsCredential


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
