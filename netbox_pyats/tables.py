"""Tables for the netbox_pyats plugin."""

import django_tables2 as tables

try:
    from netbox.tables import NetBoxTable
except ModuleNotFoundError:  # pragma: no cover - importable without netbox
    NetBoxTable = None  # type: ignore[assignment]

from .models import PyatsCredential

if NetBoxTable is not None:

    class PyatsCredentialTable(NetBoxTable):
        id = tables.LinkColumn()
        name = tables.LinkColumn()
        device = tables.Column(linkify=True)
        username = tables.Column()
        protocol = tables.Column()
        ssh_port = tables.Column()
        created = tables.DateTimeColumn()

        class Meta(NetBoxTable.Meta):
            model = PyatsCredential
            fields = ("id", "name", "device", "username", "protocol", "ssh_port", "created")
            default_columns = ("id", "name", "device", "username", "protocol", "ssh_port", "created")
