"""ATW-241 child 1 (ATW-249): add PyatsParserCatalog + the `kind='parse'` choice.

Three changes land in this single linear migration (ADR-0001 §3 — one
migration per schema addition; the two choices additions are schema-neutral
so they ride along with the new model):

1. New :class:`PyatsParserCatalog` model — one row per Genie-supported pyATS
   ``os`` string, holding the cached command list
   (``genie.libs.parser.utils.get_parser_commands`` output) plus the worker
   genie/pyats version strings and a ``refreshed_at`` timestamp. Populated
   by the worker-only ``refresh_parser_catalog`` RQ job; read by the web
   process to render the device-page Parse sub-tab checkbox list without
   importing genie (ADR-0001 §6).
2. The ``kind='parse'`` value is added to ``SnapshotKindChoices`` (choices
   only — ``kind`` is a ``CharField`` with ``choices``, not a FK, so this is
   a schema-neutral change). The new value marks on-demand manual-parse
   :class:`PyatsSnapshot` rows produced by child 3's ``parse_commands_job``.
3. The ``job_type='refresh_catalog'`` value is added to
   ``PyatsJobTypeChoices`` (choices only) so the refresh job tracks on
   :class:`PyatsJob` like the other plugin jobs (ADR-0005 §1). The value
   ``refresh_catalog`` (15 chars) fits the existing ``max_length=20`` — no
   schema widening needed.

Additive only — a new model and two choices values; no existing rows are
rewritten. Field attributes (created/last_updated/custom_field_data
null+encoder, tags as TaggableManager) are reconciled inline following the
convention established in 0004_reconcile_netboxmodel_fields.py so
``makemigrations --check`` reports no drift on the new model. See ATW-32 and
ADR-0003 for the migration conventions.
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
        ("netbox_pyats", "0009_pyatsjob"),
    ]

    operations = [
        # 1. New PyatsParserCatalog model (the schema addition).
        migrations.CreateModel(
            name="PyatsParserCatalog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "pyats_os",
                    models.CharField(
                        help_text=(
                            "pyATS os string this catalog row covers (e.g. 'iosxe', "
                            "'iosxr', 'nxos', 'asa', 'junos', 'sros', 'eos', 'ios'). "
                            "One row per os."
                        ),
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    "commands",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text=(
                            "List of CLI commands Genie can parse for this os, as "
                            "reported by genie.libs.parser.utils.get_parser_commands. "
                            "Populated by the refresh_parser_catalog worker job; read "
                            "by the device-page Parse sub-tab to render its checkbox list."
                        ),
                    ),
                ),
                (
                    "genie_version",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="genie version on the worker at the last refresh (e.g. '26.6').",
                        max_length=50,
                    ),
                ),
                (
                    "pyats_version",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="pyats version on the worker at the last refresh (e.g. '26.6').",
                        max_length=50,
                    ),
                ),
                (
                    "refreshed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the refresh job last populated this row (wall-clock).",
                        null=True,
                    ),
                ),
                ("tags", _TAG_FIELD),
            ],
            options={
                "verbose_name": "PyATS Parser Catalog",
                "verbose_name_plural": "PyATS Parser Catalog",
                "ordering": ("pyats_os",),
            },
        ),
        # 2. Add kind='parse' to SnapshotKindChoices (choices-only, no schema
        #    change — `kind` is a CharField with choices, not a FK). The
        #    AlterField updates the choices list Django stores in migration
        #    state so makemigrations --check stays clean.
        migrations.AlterField(
            model_name="pyatssnapshot",
            name="kind",
            field=models.CharField(
                choices=netbox_pyats.choices.SnapshotKindChoices.choices,
                default="full",
                help_text=(
                    "What was captured: config, state, full (config + state), or " "parse (manual on-demand parse)."
                ),
                max_length=20,
            ),
        ),
        # 3. Add job_type='refresh_catalog' to PyatsJobTypeChoices
        #    (choices-only, no schema change). The refresh job tracks on
        #    PyatsJob like the other plugin jobs (ADR-0005 §1).
        migrations.AlterField(
            model_name="pyatsjob",
            name="job_type",
            field=models.CharField(
                choices=netbox_pyats.choices.PyatsJobTypeChoices.choices,
                help_text=(
                    "Kind of plugin job this row tracks: capture / diff / compliance / "
                    "batch_capture / refresh_catalog."
                ),
                max_length=20,
            ),
        ),
    ]
