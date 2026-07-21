from netbox.search import SearchIndex, register_search

from .models import PyatsComplianceRun, PyatsCredential, PyatsGoldenConfig, PyatsJob, PyatsSnapshot, PyatsSnapshotDiff


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


@register_search
class PyatsGoldenConfigIndex(SearchIndex):
    """Search index for PyatsGoldenConfig (Phase 4, ATW-15).

    Indexes the device and the golden name so global search can surface
    golden configs. The ``config_text`` body is not indexed (too large and
    not user-facing search terms).
    """

    model = PyatsGoldenConfig
    fields = (
        ("device", 100),
        ("name", 200),
    )


@register_search
class PyatsComplianceRunIndex(SearchIndex):
    """Search index for PyatsComplianceRun (Phase 4, ATW-15).

    Indexes the device and the result label so global search can surface
    compliance runs. The JSONB ``diff`` tree is not indexed (too large and
    not user-facing search terms).
    """

    model = PyatsComplianceRun
    fields = (
        ("device", 100),
        ("result", 200),
    )


@register_search
class PyatsJobIndex(SearchIndex):
    """Search index for PyatsJob (Phase 5, ATW-16).

    Indexes the device (FK stringified to its ``__str__``, which is the device
    name) and the job_type / status labels so global search can surface plugin
    jobs. The ``error`` text and batch ``summary`` are not indexed (large and
    not user-facing search terms).
    """

    model = PyatsJob
    fields = (
        ("device", 100),
        ("job_type", 200),
        ("status", 300),
    )
