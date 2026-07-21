"""Phase 3 follow-up (ATW-68): make PyatsSnapshotDiff.before/.after nullable.

The diff job's ``DoesNotExist`` error-row path (``jobs.run_diff_job``) writes a
:class:`PyatsSnapshotDiff` row when the before or after snapshot was deleted
between the user clicking "Diff" and the worker picking up the job. With
``on_delete=CASCADE`` and non-nullable FKs (as shipped in
``0003_pyatssnapshotdiff.py``), ``full_clean()`` rejects the row because
``before_id`` / ``after_id`` point at just-missing rows (a dangling FK), so the
intended in-line error row is never written — the original ``DoesNotExist``
re-raises and NetBox marks the Job failed. This is the same latent bug ATW-62
blocker 3 filed for Phase 4 and PR #20 fixed via ``0006_compliance_run_nullable_fks``;
Phase 3 has had it since ``0003_pyatssnapshotdiff.py`` shipped.

This migration flips both FKs to ``on_delete=SET_NULL`` + ``null=True`` so the
error-row path can persist (recording the missing ids in ``parser_warnings``).
This makes the Phase 4 compliance PR's ``0006_compliance_run_nullable_fks``
docstring claim — "matches the Phase 3 diff job's error-row contract
(``PyatsSnapshotDiff.before`` / ``.after`` are also nullable)" — true
retroactively; it was false when written because this migration had not yet
landed (see ATW-68).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    # Follow-up plugin migrations depend only on the prior plugin migration
    # (no dcim pin). See 0001_initial.py and ADR-0003.
    dependencies = [
        ("netbox_pyats", "0007_snapshot_parsed_os"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pyatssnapshotdiff",
            name="before",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The earlier snapshot (the 'before' side of the diff). "
                    "Nullable so a diff whose before snapshot was deleted between "
                    "the user clicking 'Diff' and the worker picking up the job "
                    "can still write an error row (recording the missing id in "
                    "parser_warnings) rather than failing full_clean() on a "
                    "dangling FK. Mirrors the Phase 4 PyatsComplianceRun.golden/"
                    "snapshot nullability (migration 0006)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="diffs_as_before",
                to="netbox_pyats.pyatssnapshot",
            ),
        ),
        migrations.AlterField(
            model_name="pyatssnapshotdiff",
            name="after",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The later snapshot (the 'after' side of the diff). Nullable "
                    "for the same reason as `before` (error-row persistence on a "
                    "dangling snapshot FK)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="diffs_as_after",
                to="netbox_pyats.pyatssnapshot",
            ),
        ),
    ]
