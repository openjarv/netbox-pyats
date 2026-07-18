"""FilterSets for the netbox_pyats plugin."""

try:
    from netbox.filtersets import NetBoxModelFilterSet
except ModuleNotFoundError:  # pragma: no cover - importable without netbox
    NetBoxModelFilterSet = None  # type: ignore[assignment]

from .models import PyatsCredential

if NetBoxModelFilterSet is not None:

    class PyatsCredentialFilterSet(NetBoxModelFilterSet):
        """FilterSet for the PyatsCredential model."""

        class Meta:
            model = PyatsCredential
            fields = ["id", "name", "device", "username", "protocol"]
