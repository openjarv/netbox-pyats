"""ATW-241 child 2 (ATW-250): add the `netbox_pyats.add_pyatsparseresult` permission.

The on-demand parse UI enqueues a parse job whose result is stored as a
`PyatsSnapshot` row with `kind='parse'` (plan ATW-241 §1.3 — no separate
`PyatsParserResult` model). The per-action permission
`netbox_pyats.add_pyatsparseresult` is declared as a custom permission on
`PyatsSnapshot.Meta.permissions`; Django's post-migrate signal creates the
`auth_permission` row from the new `Meta.permissions` tuple.

This migration carries only the `AlterModelOptions` so `makemigrations
--check` stays clean. Additive only — no schema change, no data rewrite.
"""

from django.db import migrations


class Migration(migrations.Migration):
    """Add the `add_pyatsparseresult` custom permission to PyatsSnapshot.Meta."""

    dependencies = [
        ("netbox_pyats", "0010_parser_catalog_and_parse_kind"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="pyatssnapshot",
            options={
                "ordering": ("-captured_at",),
                "verbose_name": "PyATS Snapshot",
                "verbose_name_plural": "PyATS Snapshots",
                "permissions": (("add_pyatsparseresult", "Can enqueue an on-demand PyATS parse run"),),
            },
        ),
    ]
