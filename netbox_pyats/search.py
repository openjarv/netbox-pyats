from netbox.search import SearchIndex, register_search

from .models import PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff


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

    Indexes the device (FK stringified to its ``__str__``, which is the
    device name) and the kind/status labels so global search can surface
    snapshots. The JSONB ``data`` payload is not indexed (too large and
    not user-facing search terms).
    """

    model = PyatsSnapshot
    fields = (
        ("device", 100),
        ("kind", 200),
        ("status", 300),
    )


@register_search
class PyatsSnapshotDiffIndex(SearchIndex):
    """Search index for PyatsSnapshotDiff (Phase 3, ATW-14).

    Indexes the device (FK stringified to its ``__str__``, which is the
    device name) and the status label so global search can surface diffs.
    The JSONB ``diff`` tree is not indexed (too large and not user-facing
    search terms).
    """

    model = PyatsSnapshotDiff
    fields = (
        ("device", 100),
        ("status", 200),
    )
