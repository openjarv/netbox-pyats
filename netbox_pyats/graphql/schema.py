from netbox.graphql.types import NetBoxObjectType

from netbox_pyats.models import PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff


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


class Query:
    pass
