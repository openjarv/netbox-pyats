from netbox.graphql.types import NetBoxObjectType

from netbox_pyats.models import (
    PyatsCaptureSchedule,
    PyatsComplianceRun,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsJob,
    PyatsParserCatalog,
    PyatsParserCatalogRefreshSchedule,
    PyatsSnapshot,
    PyatsSnapshotDiff,
)


class PyatsCredentialType(NetBoxObjectType):
    """GraphQL type for the PyatsCredential model.

    ``password`` and ``enable_secret`` ciphertext fields are excluded from the
    GraphQL schema entirely — secrets are never readable via GraphQL, only
    set via REST/UI.
    """

    class Meta:
        model = PyatsCredential
        fields = (
            "id",
            "name",
            "scope",
            "device",
            "username",
            "protocol",
            "ssh_port",
            "tags",
            "created",
            "last_updated",
        )


class PyatsSnapshotType(NetBoxObjectType):
    """GraphQL type for the PyatsSnapshot model.

    Exposes the full JSONB ``data`` payload (it is the snapshot) plus the
    capture metadata. Read-only by nature (snapshots are produced by the
    capture job).
    """

    class Meta:
        model = PyatsSnapshot
        fields = (
            "id",
            "device",
            "kind",
            "status",
            "triggered_by",
            "captured_at",
            "data",
            "parser_warnings",
            "genie_version",
            "pyats_version",
            "size_bytes",
            "tags",
            "created",
            "last_updated",
        )


class PyatsSnapshotDiffType(NetBoxObjectType):
    """GraphQL type for the PyatsSnapshotDiff model (Phase 3, ATW-14).

    Exposes the full JSONB ``diff`` tree and ``summary`` counts (they are the
    diff) plus the before/after snapshot links and metadata. Read-only by
    nature (diffs are produced by the ``run_diff`` job).
    """

    class Meta:
        model = PyatsSnapshotDiff
        fields = (
            "id",
            "device",
            "before",
            "after",
            "status",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "tags",
            "created",
            "last_updated",
        )


class PyatsJobType(NetBoxObjectType):
    """GraphQL type for the PyatsJob model (Phase 5, ATW-16).

    Exposes the job-tracking fields: type, status, the targeted device, the
    linked ``core.Job`` row, the result-row FKs (one of related_snapshot /
    related_diff / related_compliance is set per job on success), the
    ``error`` text (for the swallowed-exception path), and the batch
    ``summary`` counts. Read-only by nature (jobs are produced by the
    plugin's enqueue helpers, not by direct writes — ADR-0005 §4).
    """

    class Meta:
        model = PyatsJob
        fields = (
            "id",
            "job_type",
            "status",
            "device",
            "core_job",
            "rq_job_id",
            "related_snapshot",
            "related_diff",
            "related_compliance",
            "started_at",
            "finished_at",
            "error",
            "summary",
            "tags",
            "created",
            "last_updated",
        )


class PyatsParserCatalogType(NetBoxObjectType):
    """GraphQL type for the PyatsParserCatalog model (ATW-241 child 1).

    Exposes the full JSONB ``commands`` list (it is the catalog) plus the
    worker version strings and ``refreshed_at``. Read-only by nature (catalog
    rows are produced by the worker-only refresh_parser_catalog job —
    ADR-0001 §5/§6).
    """

    class Meta:
        model = PyatsParserCatalog
        fields = (
            "id",
            "pyats_os",
            "commands",
            "genie_version",
            "pyats_version",
            "refreshed_at",
            "tags",
            "created",
            "last_updated",
        )


class PyatsCaptureScheduleType(NetBoxObjectType):
    """GraphQL type for the PyatsCaptureSchedule model (ATW-433).

    Exposes the schedule's name, device_filter spec, kind, enabled flag, and
    the display-only last_run_at / next_run_at timestamps. Read-only by
    nature via GraphQL (operators create/update schedules via REST/UI;
    GraphQL v1 does not define mutations).
    """

    class Meta:
        model = PyatsCaptureSchedule
        fields = (
            "id",
            "name",
            "device_filter",
            "kind",
            "enabled",
            "last_run_at",
            "next_run_at",
            "tags",
            "created",
            "last_updated",
        )


class PyatsParserCatalogRefreshScheduleType(NetBoxObjectType):
    """GraphQL type for the PyatsParserCatalogRefreshSchedule model (ATW-581).

    Exposes the enabled flag and the display-only last_run_at / next_run_at
    timestamps. Read-only by nature via GraphQL (operators toggle the
    schedule via REST/UI; GraphQL v1 does not define mutations). The model is
    a single-row intent gate, so the only operator-relevant field is
    ``enabled``.
    """

    class Meta:
        model = PyatsParserCatalogRefreshSchedule
        fields = (
            "id",
            "enabled",
            "last_run_at",
            "next_run_at",
            "tags",
            "created",
            "last_updated",
        )


class PyatsGoldenConfigType(NetBoxObjectType):
    """GraphQL type for the PyatsGoldenConfig model (Phase 4, ATW-15).

    Exposes the operator's golden / reference running-config (``config_text``
    is free text, not a secret — secrets live only on PyatsCredential which
    excludes password/enable_secret), the ``source`` provenance choice, and
    the nullable ``source_snapshot`` link set when the golden was promoted
    from a snapshot. Read-only by nature via GraphQL (operators author
    goldens via REST/UI; GraphQL v1 does not define mutations).
    """

    class Meta:
        model = PyatsGoldenConfig
        fields = (
            "id",
            "device",
            "name",
            "config_text",
            "source",
            "source_snapshot",
            "tags",
            "created",
            "last_updated",
        )


class PyatsComplianceRunType(NetBoxObjectType):
    """GraphQL type for the PyatsComplianceRun model (Phase 4, ATW-15).

    Exposes one compliance-check result: the ``result`` classification
    (compliant / drift / error), the ``mode`` comparison semantics, the
    nullable ``golden`` / ``snapshot`` links (nullable for the error-row
    persistence contract — see PyatsSnapshotDiff.before/after), the full
    JSONB ``diff`` tree + ``summary`` counts + ``parser_warnings`` list
    (same shape as PyatsSnapshotDiff), and ``size_bytes``. Read-only by
    nature (compliance runs are produced by the run_compliance job).
    """

    class Meta:
        model = PyatsComplianceRun
        fields = (
            "id",
            "device",
            "golden",
            "snapshot",
            "result",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "mode",
            "tags",
            "created",
            "last_updated",
        )
