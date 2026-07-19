# Reconcile field attributes on the three plugin models with NetBox's
# NetBoxModel base classes (ChangeLoggingMixin, CustomFieldsMixin, TagsMixin).
#
# The initial migrations (0001-0003) were authored outside a NetBox context:
# - `created`/`last_updated`/`custom_field_data` were missing `null=True` /
#   the NetBox JSON encoder, which `makemigrations --check` flagged as drift.
# - `tags` was declared as a plain `ManyToManyField` (auto through-table
#   `netbox_pyats_<model>_tags`) instead of NetBox's `TaggableManager` backed
#   by `extras.TaggedItem`. NetBoxModel defines `tags` as a TaggableManager, so
#   the migration state never matched the model. An `AlterField` cannot swap an
#   M2M for a TaggableManager in place (Django rejects it as an incompatible
#   type change), so this migration removes the M2M field and re-adds it as the
#   correct TaggableManager. Pre-release, the auto through-tables carried no
#   real data; the swap brings the DB in line with NetBoxModel's contract.
#
# The index-rename suggestions Django 5.x emits (cosmetic, from the auto-naming
# convention change) are intentionally NOT applied here: the explicit `name=` on
# the original indexes in 0001-0003 (now also mirrored on the model Meta) is
# the durable form and `makemigrations --check` reports no changes for them.
#
# See ATW-32 and ADR-0003 (plugin migrations carry no dcim/extras deps).

import taggit.managers
import utilities.json
from django.db import migrations, models


_TAG_FIELD = taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_pyats", "0003_pyatssnapshotdiff"),
    ]

    operations = [
        # created / last_updated / custom_field_data — attribute reconciliation.
        migrations.AlterField(
            model_name="pyatscredential",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="pyatscredential",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
        migrations.AlterField(
            model_name="pyatscredential",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="pyatssnapshot",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="pyatssnapshot",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
        migrations.AlterField(
            model_name="pyatssnapshot",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="pyatssnapshotdiff",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="pyatssnapshotdiff",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
        migrations.AlterField(
            model_name="pyatssnapshotdiff",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        # tags — swap the wrong M2M (auto through-table) for NetBox's
        # TaggableManager (through extras.TaggedItem). RemoveField then
        # AddField because AlterField cannot change the field type.
        migrations.RemoveField(
            model_name="pyatscredential",
            name="tags",
        ),
        migrations.AddField(
            model_name="pyatscredential",
            name="tags",
            field=_TAG_FIELD,
        ),
        migrations.RemoveField(
            model_name="pyatssnapshot",
            name="tags",
        ),
        migrations.AddField(
            model_name="pyatssnapshot",
            name="tags",
            field=_TAG_FIELD,
        ),
        migrations.RemoveField(
            model_name="pyatssnapshotdiff",
            name="tags",
        ),
        migrations.AddField(
            model_name="pyatssnapshotdiff",
            name="tags",
            field=_TAG_FIELD,
        ),
    ]
