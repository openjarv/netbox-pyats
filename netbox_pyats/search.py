from netbox.search import SearchIndex, register_search

from .models import PyatsCredential, PyatsSnapshot


@register_search
class PyatsCredentialIndex(SearchIndex):
    model = PyatsCredential
    fields = (
        ("name", 100),
        ("username", 200),
    )


@register_search
class PyatsSnapshotIndex(SearchIndex):
    """Search index for PyatsSnapshot.

    Indexes the device name (via the FK) and the kind/status labels so global
    search can surface snapshots. The JSONB ``data`` payload is not indexed
    (too large and not user-facing search terms).
    """

    model = PyatsSnapshot
    fields = (
        ("device__name", 100),
        ("kind", 200),
        ("status", 300),
    )
