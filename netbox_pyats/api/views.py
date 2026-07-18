from netbox.api.viewsets import NetBoxModelViewSet

from netbox_pyats.filtersets import PyatsCredentialFilterSet
from netbox_pyats.models import PyatsCredential

from .serializers import PyatsCredentialSerializer


class PyatsCredentialViewSet(NetBoxModelViewSet):
    """API viewset for the PyatsCredential model."""

    queryset = PyatsCredential.objects.all()
    serializer_class = PyatsCredentialSerializer
    filterset_class = PyatsCredentialFilterSet
