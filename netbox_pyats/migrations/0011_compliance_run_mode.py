"""ATW-434: add PyatsComplianceRun.mode (v2 ordered vs v1 set compliance).

v2 compliance (ATW-434) introduces an order-sensitive line diff as the default
comparison mode, with the v1 order-independent set diff retained as an explicit
opt-in. The mode that produced each run is recorded on the row so the operator
can see which semantics classified the result (an ordered run that flagged
re-ordered ACL entries as drift vs a set run that classified them compliant).

This migration adds the non-null ``mode`` CharField with the two
:class:`~netbox_pyats.choices.ComplianceModeChoices` values; existing rows
backfill to ``ordered`` (the new default), which is the more informative
comparison and a safe default for rows whose original mode was never recorded.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_pyats", "0010_parser_catalog_and_parse_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="pyatscompliancerun",
            name="mode",
            field=models.CharField(
                choices=[("ordered", "Ordered (sequence-aware)"), ("set", "Set (order-independent, v1)")],
                default="ordered",
                help_text=(
                    "Comparison mode used for this run: `ordered` (v2, default) is a "
                    "sequence-aware line diff that catches ACL/route-map/interface "
                    "order drift; `set` (v1) is an order-independent set diff. Set by "
                    "the enqueue path from the operator's choice; recorded on the row "
                    "so the operator can see which semantics produced the result."
                ),
                max_length=10,
            ),
        ),
    ]
