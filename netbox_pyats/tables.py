import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import PyatsComplianceRun, PyatsCredential, PyatsGoldenConfig, PyatsJob, PyatsSnapshot, PyatsSnapshotDiff


class PyatsCredentialTable(NetBoxTable):
    """Table configuration for the PyatsCredential list view."""

    id = tables.LinkColumn()
    name = tables.LinkColumn(verbose_name="Name")
    device = tables.Column(linkify=True)
    scope = tables.Column()
    username = tables.Column()
    protocol = tables.Column()
    ssh_port = tables.Column()
    created = tables.DateTimeColumn()

    class Meta(NetBoxTable.Meta):
        model = PyatsCredential
        fields = (
            "id",
            "name",
            "device",
            "scope",
            "username",
            "protocol",
            "ssh_port",
            "created",
        )
        default_columns = (
            "id",
            "name",
            "device",
            "scope",
            "username",
            "protocol",
            "ssh_port",
            "created",
        )


class PyatsSnapshotTable(NetBoxTable):
    """Table configuration for the PyatsSnapshot list view.

    Renders the snapshot's device, kind, status (as a colored badge), size,
    capture time, and a warnings indicator. The `id` column links to the
    snapshot detail view (which renders the JSONB payload).
    """

    id = tables.LinkColumn(verbose_name="ID")
    device = tables.Column(linkify=True)
    kind = tables.Column(verbose_name="Kind")
    status = tables.TemplateColumn(
        template_code=(
            "{% load helpers %}"
            '<span class="badge bg-{{ record.get_status_color }}">{{ record.get_status_display }}</span>'
        ),
        verbose_name="Status",
    )
    triggered_by = tables.Column(verbose_name="Triggered by")
    size_bytes = tables.Column(verbose_name="Size (bytes)")
    has_warnings = tables.BooleanColumn(verbose_name="Warnings")
    captured_at = tables.DateTimeColumn(verbose_name="Captured at")
    genie_version = tables.Column(verbose_name="Genie")
    pyats_version = tables.Column(verbose_name="pyATS")

    class Meta(NetBoxTable.Meta):
        model = PyatsSnapshot
        fields = (
            "id",
            "device",
            "kind",
            "status",
            "triggered_by",
            "size_bytes",
            "has_warnings",
            "captured_at",
            "genie_version",
            "pyats_version",
        )
        default_columns = (
            "id",
            "device",
            "kind",
            "status",
            "triggered_by",
            "size_bytes",
            "has_warnings",
            "captured_at",
        )


class PyatsSnapshotDiffTable(NetBoxTable):
    """Table configuration for the PyatsSnapshotDiff list view.

    Renders the diff's device, before/after snapshot links, status (as a
    colored badge), a compact summary of added/removed/changed counts, size,
    creation time, and a warnings indicator. The `id` column links to the diff
    detail view (which renders the structured diff tree).
    """

    id = tables.LinkColumn(verbose_name="ID")
    device = tables.Column(linkify=True)
    before = tables.Column(linkify=True, verbose_name="Before")
    after = tables.Column(linkify=True, verbose_name="After")
    status = tables.TemplateColumn(
        template_code=(
            "{% load helpers %}"
            '<span class="badge bg-{{ record.get_status_color }}">{{ record.get_status_display }}</span>'
        ),
        verbose_name="Status",
    )
    has_changes = tables.BooleanColumn(verbose_name="Changes")
    size_bytes = tables.Column(verbose_name="Size (bytes)")
    has_warnings = tables.BooleanColumn(verbose_name="Warnings")
    created = tables.DateTimeColumn(verbose_name="Created at")

    class Meta(NetBoxTable.Meta):
        model = PyatsSnapshotDiff
        fields = (
            "id",
            "device",
            "before",
            "after",
            "status",
            "has_changes",
            "size_bytes",
            "has_warnings",
            "created",
        )
        default_columns = (
            "id",
            "device",
            "before",
            "after",
            "status",
            "has_changes",
            "size_bytes",
            "created",
        )


class PyatsGoldenConfigTable(NetBoxTable):
    """Table configuration for the PyatsGoldenConfig list view (Phase 4).

    Renders the golden's device, name, source badge (manual vs. snapshot), a
    config-text size indicator, and creation time. The `id` column links to the
    golden detail view (which renders the full config text).
    """

    id = tables.LinkColumn(verbose_name="ID")
    device = tables.Column(linkify=True)
    name = tables.Column(linkify=True, verbose_name="Name")
    source = tables.Column(verbose_name="Source")
    source_snapshot = tables.Column(linkify=True, verbose_name="Promoted from")
    created = tables.DateTimeColumn(verbose_name="Created at")

    class Meta(NetBoxTable.Meta):
        model = PyatsGoldenConfig
        fields = (
            "id",
            "device",
            "name",
            "source",
            "source_snapshot",
            "created",
        )
        default_columns = (
            "id",
            "device",
            "name",
            "source",
            "created",
        )


class PyatsComplianceRunTable(NetBoxTable):
    """Table configuration for the PyatsComplianceRun list view (Phase 4).

    Renders the compliance run's device, golden + snapshot links, result (as a
    colored badge), a drift indicator, size, creation time, and a warnings
    indicator. The `id` column links to the compliance run detail view (which
    renders the structured diff tree using the Phase 3 diff-tree partial).
    """

    id = tables.LinkColumn(verbose_name="ID")
    device = tables.Column(linkify=True)
    golden = tables.Column(linkify=True, verbose_name="Golden")
    snapshot = tables.Column(linkify=True, verbose_name="Snapshot")
    result = tables.TemplateColumn(
        template_code=(
            "{% load helpers %}"
            '<span class="badge bg-{{ record.get_result_color }}">{{ record.get_result_display }}</span>'
        ),
        verbose_name="Result",
    )
    has_drift = tables.BooleanColumn(verbose_name="Drift")
    size_bytes = tables.Column(verbose_name="Size (bytes)")
    has_warnings = tables.BooleanColumn(verbose_name="Warnings")
    created = tables.DateTimeColumn(verbose_name="Created at")

    class Meta(NetBoxTable.Meta):
        model = PyatsComplianceRun
        fields = (
            "id",
            "device",
            "golden",
            "snapshot",
            "result",
            "has_drift",
            "size_bytes",
            "has_warnings",
            "created",
        )
        default_columns = (
            "id",
            "device",
            "golden",
            "snapshot",
            "result",
            "has_drift",
            "size_bytes",
            "created",
        )


class PyatsJobTable(NetBoxTable):
    """Table configuration for the PyatsJob list view (Phase 5, ATW-16).

    Renders the job's type + status (as colored badges), the targeted device
    (blank for batch_capture jobs), the result-row link (one of
    related_snapshot / related_diff / related_compliance, resolved via
    :attr:`PyatsJob.related_result`), the rq job id (for operator
    cross-reference with rq-dashboard), and the started/finished timestamps.
    The `id` column links to the job detail view.
    """

    id = tables.LinkColumn(verbose_name="ID")
    job_type = tables.Column(verbose_name="Type")
    status = tables.TemplateColumn(
        template_code=(
            "{% load helpers %}"
            '<span class="badge bg-{{ record.get_status_color }}">{{ record.get_status_display }}</span>'
        ),
        verbose_name="Status",
    )
    device = tables.Column(linkify=True, verbose_name="Device")
    related_result = tables.Column(linkify=True, verbose_name="Result row", accessor="related_result")
    rq_job_id = tables.Column(verbose_name="RQ job id")
    started_at = tables.DateTimeColumn(verbose_name="Started at")
    finished_at = tables.DateTimeColumn(verbose_name="Finished at")
    created = tables.DateTimeColumn(verbose_name="Created at")

    class Meta(NetBoxTable.Meta):
        model = PyatsJob
        fields = (
            "id",
            "job_type",
            "status",
            "device",
            "related_result",
            "rq_job_id",
            "started_at",
            "finished_at",
            "created",
        )
        default_columns = (
            "id",
            "job_type",
            "status",
            "device",
            "related_result",
            "started_at",
            "finished_at",
            "created",
        )
