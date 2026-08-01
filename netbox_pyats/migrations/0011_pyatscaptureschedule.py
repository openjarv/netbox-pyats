"""ATW-433: add the PyatsCaptureSchedule intent model (scheduled captures).

A single additive migration (ADR-0001 §3 — one migration per schema addition,
linear after 0010). The new ``PyatsCaptureSchedule`` model is an
operator-authored intent: ``name``, ``device_filter`` (JSONField filter spec),
``kind`` (reuses :class:`SnapshotKindChoices`), ``enabled``, and
display-only ``last_run_at`` / ``next_run_at`` (written by the dispatcher
job, not by the scheduler). The cadence is owned by NetBox's native
``ScheduledJob`` (Operations → Jobs); the plugin owns no cron worker and adds
no ``rq-scheduler`` dependency (ADR-0008).

No new choices values are introduced — ``SnapshotKindChoices`` is reused for
``kind`` and ``SnapshotTriggerChoices.TRIGGER_JOB`` (choices.py:67) is the
trigger value for scheduled captures. No schema-neutral AlterField rides
along.

Field attributes (created/last_updated/custom_field_data null+encoder, tags as
TaggableManager) are reconciled inline following the convention established
in 0004_reconcile_netboxmodel_fields.py so ``makemigrations --check`` reports
no drift on the new model. See ATW-32 and ADR-0003.
"""

import taggit.managers
import utilities.json
from django.db import migrations, models

import netbox_pyats.choices

_TAG_FIELD = taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")


class Migration(migrations.Migration):

    # Follow-up plugin migrations depend only on the prior plugin migration
    # (no dcim pin). See 0001_initial.py and ADR-0003.
    dependencies = [
        ("netbox_pyats", "0010_parser_catalog_and_parse_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsCaptureSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Operator label, e.g. 'Edge-routers nightly baseline'.",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "device_filter",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            'Serialized ORM filter spec (e.g. {"region_id__in": [1, 2]} or '
                            '{"id__in": [10, 20]}). Re-resolved to a Device queryset at run '
                            "time so devices that drift between schedule creation and dispatch "
                            "are picked up or dropped automatically."
                        ),
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=netbox_pyats.choices.SnapshotKindChoices.choices,
                        default="full",
                        help_text="Capture kind dispatched per run: config / state / full.",
                        max_length=20,
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Operator toggle to pause a schedule without deleting it.",
                    ),
                ),
                (
                    "last_run_at",
                    models.DateTimeField(
                        blank=True,
                        help_text=("When the dispatcher last ran this schedule " "(display-only, written by the job)."),
                        null=True,
                    ),
                ),
                (
                    "next_run_at",
                    models.DateTimeField(
                        blank=True,
                        help_text=(
                            "When the next ScheduledJob firing is expected " "(display-only, written by the job)."
                        ),
                        null=True,
                    ),
                ),
                ("tags", _TAG_FIELD),
            ],
            options={
                "verbose_name": "PyATS Capture Schedule",
                "verbose_name_plural": "PyATS Capture Schedules",
                "ordering": ("name",),
                "indexes": [
                    models.Index(fields=("enabled", "name"), name="pyats_sched_enabled_name_idx"),
                ],
            },
        ),
    ]
