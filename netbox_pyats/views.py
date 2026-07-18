"""Views for the netbox-pyats plugin.

Phase 1 ships standard NetBox CRUD for :class:`PyatsCredential` so operators
can create, list, view, edit, and delete encrypted device credentials from the
NetBox UI under ``/plugins/pyats/``. The PyATS tab on the Device detail page
(Phase 2, ATW-13) will surface the snapshot capture button on top of these
credentials.
"""

from netbox.views import generic

from . import filtersets, forms, tables
from .models import PyatsCredential


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
