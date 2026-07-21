"""Phase 4 follow-up (ATW-15): make PyatsComplianceRun.golden/.snapshot nullable.

The compliance job's DoesNotExist error-row path (``jobs.run_compliance_job``)
writes a :class:`PyatsComplianceRun` row when the golden or snapshot was
deleted between the user clicking "Run compliance" and the worker picking up
the job. With ``on_delete=CASCADE`` and non-nullable FKs, ``full_clean()``
rejects the row because ``golden_id`` / ``snapshot_id`` point at the
just-missing rows (a dangling FK), so the intended in-line error row is never
written — violating the graceful-degradation contract carried from Phase 2/3.

This migration flips both FKs to ``on_delete=SET_NULL`` + ``null=True`` so the
error-row path can persist (recording the missing id in ``parser_warnings``).
This matches the Phase 3 diff job's error-row contract —
``PyatsSnapshotDiff.before`` / ``.after`` are also nullable for the same
reason (see migration 0003_pyatssnapshotdiff.py).

Filed as part of the code-quality re-review of PR #16 (ATW-62 blockers 1-3,
re-applied on the ``phase4-compliance-rereview`` branch as PR #20).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    # Follow-up plugin migrations depend only on the prior plugin migration
    # (no dcim pin). See 0001_initial.py and ADR-0003.
    dependencies = [
        ("netbox_pyats", "0005_compliance_engine"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pyatscompliancerun",
            name="golden",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The golden config this run compared against. Nullable so a "
                    "compliance run whose golden row was deleted between the user "
                    "clicking 'Run compliance' and the worker picking up the job can "
                    "still write an error row (recording the missing id in "
                    "parser_warnings) rather than failing full_clean() on a dangling "
                    "FK. Mirrors the Phase 3 PyatsSnapshotDiff.before/after nullability."
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
                    "The snapshot this run compared against the golden config. "
                    "Nullable for the same reason as `golden` (error-row persistence "
                    "on a dangling snapshot FK)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="compliance_runs",
                to="netbox_pyats.pyatssnapshot",
            ),
        ),
    ]
