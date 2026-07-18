"""Views for the netbox_pyats plugin.

Phase 1 ships standard CRUD for :class:`PyatsCredential` so operators can
create, list, view, edit, and delete credentials from the NetBox UI. Later
phases add the snapshot, diff, and compliance views.
"""

try:
    from netbox.views import generic
except ModuleNotFoundError:  # pragma: no cover - importable without netbox
    generic = None  # type: ignore[assignment]

from . import filtersets, forms, tables
from .models import PyatsCredential

if generic is not None:

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
