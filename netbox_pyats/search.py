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

    Indexes the device FK and the kind/status labels so global search can
    surface snapshots. ``get_field_value`` stringifies the FK target (the
    device ``__str__``, i.e. its name), so we index ``device`` directly rather
    than traversing ``device__name`` — NetBox 4.6's ``SearchIndex.to_cache``
    calls ``_meta.get_field`` which does not traverse ``__`` lookups. The
    JSONB ``data`` payload is not indexed (too large and not user-facing).
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

    Indexes the device FK and the status label so global search can surface
    diffs. See :class:`PyatsSnapshotIndex` for why ``device`` is indexed
    directly rather than via ``device__name``. The JSONB ``diff`` tree is not
    indexed (too large and not user-facing search terms).
    """

    model = PyatsSnapshotDiff
    fields = (
        ("device", 100),
        ("status", 200),
    )
