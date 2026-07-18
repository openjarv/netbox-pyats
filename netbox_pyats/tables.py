import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import PyatsCredential


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
