import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import PyatsCredential, PyatsSnapshot


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
