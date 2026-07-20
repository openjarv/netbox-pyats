"""Phase 4 re-land (ATW-64): add PyatsSnapshot.parsed_os + soften compliance FKs.

- ``PyatsSnapshot.parsed_os``: the pyATS os string used by the Genie parser at
  capture time, so compliance runs can re-parse a golden config with the same
  parser even after the device is deleted.
- ``PyatsComplianceRun.golden`` / ``.snapshot``: change ``on_delete`` from
  ``CASCADE`` to ``SET_NULL`` (with ``null=True``) so compliance history
  survives golden/snapshot deletion (audit contract, consistent with
  ``source_snapshot``).

See ADR-0004 for the compliance comparison-shape decision.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_pyats", "0005_compliance_engine"),
    ]

    operations = [
        migrations.AddField(
            model_name="pyatssnapshot",
            name="parsed_os",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "The pyATS os string used by the Genie parser at capture time "
                    "(e.g. 'iosxe'). Stored so compliance runs can re-parse a golden "
                    "config with the same parser even after the device is deleted."
                ),
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="pyatscompliancerun",
            name="golden",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The golden config this run compared against. Null if the golden "
                    "was deleted after the run (the compliance history is preserved)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="compliance_runs",
                to="netbox_pyats.pyatsgoldenconfig",
            ),
        ),
        migrations.AlterField(
            model_name="pyatscompliancerun",
            name="snapshot",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The snapshot this run compared against the golden config. Null "
                    "if the snapshot was deleted after the run (the compliance "
                    "history is preserved)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="compliance_runs",
                to="netbox_pyats.pyatssnapshot",
            ),
        ),
    ]
