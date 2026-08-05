"""ATW-581: add the PyatsParserCatalogRefreshSchedule intent model.

A single additive migration (ADR-0001 §3 — one migration per schema addition,
linear after 0012). The new ``PyatsParserCatalogRefreshSchedule`` model is an
opt-in intent model for recurring parser catalog refresh: ``enabled`` (the
on/off switch), and display-only ``last_run_at`` / ``next_run_at`` (written
by the dispatcher job, not by the scheduler). The cadence is owned by
NetBox's native ``Job`` interval via ``RunParserCatalogRefreshSchedulesJob``;
the plugin owns no cron worker and adds no ``rq-scheduler`` dependency.

Field attributes (created/last_updated/custom_field_data null+encoder, tags as
TaggableManager) are reconciled inline following the convention established
in 0004_reconcile_netboxmodel_fields.py so ``makemigrations --check`` reports
no drift on the new model. See ATW-32 and ADR-0003.
"""

import taggit.managers
import utilities.json
from django.db import migrations, models

_TAG_FIELD = taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_pyats", "0012_compliance_run_mode"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsParserCatalogRefreshSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=False,
                        help_text="When enabled, the dispatcher fires a catalog refresh on each run.",
                    ),
                ),
                (
                    "last_run_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the dispatcher last ran this schedule (display-only, written by the job).",
                        null=True,
                    ),
                ),
                (
                    "next_run_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the next recurring dispatch is expected (display-only, written by the job).",
                        null=True,
                    ),
                ),
                ("tags", _TAG_FIELD),
            ],
            options={
                "verbose_name": "PyATS Parser Catalog Refresh Schedule",
                "verbose_name_plural": "PyATS Parser Catalog Refresh Schedules",
            },
        ),
    ]
