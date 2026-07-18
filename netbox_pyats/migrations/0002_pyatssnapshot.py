"""Phase 2 (ATW-13): add the PyatsSnapshot model.

Stores one captured config/state/full snapshot per NetBox Device as JSONB,
written by the `capture_snapshot` RQ job. See
`netbox_pyats.models.PyatsSnapshot` for the payload shape and the
multi-vendor graceful-degradation contract (unsupported/error rows are still
created so the device-page PyATS tab can surface them in the history).
"""

from django.db import migrations, models

import netbox_pyats.choices


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "0050_custom_field_choice_set_remove"),
        ("netbox_pyats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "kind",
                    models.CharField(
                        choices=netbox_pyats.choices.SnapshotKindChoices.choices,
                        default="full",
                        help_text="What was captured: config, state, or full (config + state).",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=netbox_pyats.choices.SnapshotStatusChoices.choices,
                        default="success",
                        help_text=("Outcome of the capture: success, unsupported platform, or error."),
                        max_length=20,
                    ),
                ),
                (
                    "triggered_by",
                    models.CharField(
                        choices=netbox_pyats.choices.SnapshotTriggerChoices.choices,
                        default="user",
                        help_text=("Who/what initiated the capture: a user (manual) or a job (automated)."),
                        max_length=20,
                    ),
                ),
                (
                    "captured_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="When the snapshot was captured (set on row creation)."
                    ),
                ),
                (
                    "data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Captured snapshot payload as JSON. Shape depends on kind: "
                            "config -> {config: ...}, state -> {state: ...}, full -> {config, state}. "
                            "Empty for unsupported/error rows."
                        ),
                    ),
                ),
                (
                    "parser_warnings",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text=(
                            "List of human-readable warnings/errors from the capture: parser "
                            "unsupported messages, Unicon connection issues, exception text. "
                            "Surfaced in the UI as a 'warnings' indicator on the snapshot row."
                        ),
                    ),
                ),
                (
                    "genie_version",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="genie version on the worker at capture time (e.g. '26.6').",
                        max_length=50,
                    ),
                ),
                (
                    "pyats_version",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="pyats version on the worker at capture time (e.g. '26.6').",
                        max_length=50,
                    ),
                ),
                (
                    "size_bytes",
                    models.PositiveBigIntegerField(
                        default=0,
                        help_text="Size of the JSON-serialized `data` payload in bytes (set by the job).",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        help_text="NetBox device this snapshot was captured from.",
                        on_delete=models.deletion.CASCADE,
                        related_name="pyats_snapshots",
                        to="dcim.device",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True,
                        related_name="extras_tag_netbox_pyats_pyatssnapshot",
                        to="extras.tag",
                    ),
                ),
            ],
            options={
                "verbose_name": "PyATS Snapshot",
                "verbose_name_plural": "PyATS Snapshots",
                "ordering": ("-captured_at",),
            },
        ),
        migrations.AddIndex(
            model_name="pyatssnapshot",
            index=models.Index(fields=("device", "-captured_at"), name="pyats_snap_dev_capt_idx"),
        ),
        migrations.AddIndex(
            model_name="pyatssnapshot",
            index=models.Index(
                fields=("device", "kind", "-captured_at"),
                name="pyats_snap_dev_kind_idx",
            ),
        ),
    ]
