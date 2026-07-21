"""Add PyatsSnapshot.parsed_os (ATW-70).

A new CharField carrying the pyATS os string used by the capture (e.g.
``iosxe``, ``iosxr``, ``nxos``), populated at capture time from the testbed's
device os. v1 raw-text compliance does not consume ``parsed_os``; it is the
salvageable v2-compliance-enabler piece extracted from the now-closed PR #22
(``feat/atw-64-reland-compliance-genie-parse``) — see ADR-0004 Option 3 and the
ATW-64 closing comment ``fdaeda84``: *"parsed_os is not used by the v1
raw-text compliance path but is cheap to carry and unblocks v2 structured
compliance."* When v2 introduces a real Genie ``show running-config`` parser
(or a standalone config parser), compliance runs against a deleted device
will need the os provenance to pick the right parser; storing it now (cheap,
additive) avoids a backfill migration later.

Additive only — a new nullable-with-default column, no existing rows are
rewritten. Old snapshots keep ``parsed_os=""`` and remain usable on the v1
compliance path; v2 will classify os-less snapshots as error (mirroring the
existing empty-config-raw error path) rather than crashing.

Filed as follow-up to ATW-64 (PR #22 closing). Depends on
``0006_compliance_run_nullable_fks`` (the migration already on ``main`` from
PR #20).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    # Follow-up plugin migrations depend only on the prior plugin migration
    # (no dcim pin). See 0001_initial.py and ADR-0003.
    dependencies = [
        ("netbox_pyats", "0006_compliance_run_nullable_fks"),
    ]

    operations = [
        migrations.AddField(
            model_name="pyatssnapshot",
            name="parsed_os",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "pyATS os string used by the capture (e.g. 'iosxe', 'iosxr', "
                    "'nxos'). Carried from the testbed at capture time so v2 "
                    "structured compliance can pick the right Genie parser for a "
                    "snapshot whose device has since been deleted. Not consumed by "
                    "the v1 raw-text compliance path."
                ),
                max_length=50,
            ),
        ),
    ]
