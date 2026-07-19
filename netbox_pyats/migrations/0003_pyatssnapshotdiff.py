"""Phase 3 (ATW-14): add the PyatsSnapshotDiff model.

Stores one structured diff between two :class:`PyatsSnapshot` rows of the same
NetBox Device as JSONB, written by the `run_diff` RQ job. See
`netbox_pyats.models.PyatsSnapshotDiff` for the diff-tree shape and the
multi-vendor graceful-degradation contract (empty/error diffs are still
created so the operator sees the outcome in-line, mirroring Phase 2).
"""

from django.db import migrations, models

import netbox_pyats.choices


class Migration(migrations.Migration):

    # See 0001_initial.py for the migration-dependency convention. Follow-up
    # plugin migrations depend only on the prior plugin migration (no dcim
    # pin). See ATW-25 / ADR-0003.
    dependencies = [
        ("netbox_pyats", "0002_pyatssnapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsSnapshotDiff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=netbox_pyats.choices.DiffStatusChoices.choices,
                        default="success",
                        help_text="Outcome of the diff: success, empty inputs, or error.",
                        max_length=20,
                    ),
                ),
                (
                    "diff",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Structured diff tree as JSON. Root is a dict node with children "
                            "keyed by snapshot key; each child is an added/removed/changed/"
                            "unchanged leaf or a nested container. Rendered as a collapsible "
                            "tree in the diff viewer."
                        ),
                    ),
                ),
                (
                    "summary",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Flat counts per status: {added, removed, changed, unchanged}. "
                            "Surfaced as a compact summary in the diff list and viewer header."
                        ),
                    ),
                ),
                (
                    "parser_warnings",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text=(
                            "List of human-readable warnings/errors from the diff: malformed "
                            "input payloads, etc. Empty for clean diffs."
                        ),
                    ),
                ),
                (
                    "size_bytes",
                    models.PositiveBigIntegerField(
                        default=0,
                        help_text="Size of the JSON-serialized `diff` payload in bytes (set by the job).",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        help_text="NetBox device whose snapshots were diffed (must match both before and after).",
                        on_delete=models.deletion.CASCADE,
                        related_name="pyats_snapshot_diffs",
                        to="dcim.device",
                    ),
                ),
                (
                    "before",
                    models.ForeignKey(
                        help_text="The earlier snapshot (the 'before' side of the diff).",
                        on_delete=models.deletion.CASCADE,
                        related_name="diffs_as_before",
                        to="netbox_pyats.pyatssnapshot",
                    ),
                ),
                (
                    "after",
                    models.ForeignKey(
                        help_text="The later snapshot (the 'after' side of the diff).",
                        on_delete=models.deletion.CASCADE,
                        related_name="diffs_as_after",
                        to="netbox_pyats.pyatssnapshot",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True,
                        related_name="extras_tag_netbox_pyats_pyatssnapshotdiff",
                        to="extras.tag",
                    ),
                ),
            ],
            options={
                "verbose_name": "PyATS Snapshot Diff",
                "verbose_name_plural": "PyATS Snapshot Diffs",
                "ordering": ("-created",),
            },
        ),
        migrations.AddIndex(
            model_name="pyatssnapshotdiff",
            index=models.Index(fields=("device", "-created"), name="pyats_diff_dev_created_idx"),
        ),
        migrations.AddIndex(
            model_name="pyatssnapshotdiff",
            index=models.Index(
                fields=("device", "status", "-created"),
                name="pyats_diff_dev_status_idx",
            ),
        ),
    ]
