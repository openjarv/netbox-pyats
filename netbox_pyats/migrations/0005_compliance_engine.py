"""Phase 4 (ATW-15): add the PyatsGoldenConfig and PyatsComplianceRun models.

``PyatsGoldenConfig`` stores the operator's golden/reference running-config
text per device. ``PyatsComplianceRun`` stores one compliance-check result
(golden vs. snapshot) as JSONB — the structured diff tree (same shape as
``PyatsSnapshotDiff.diff``) plus a flat summary of counts, written by the
``run_compliance`` RQ job.

Field attributes (created/last_updated/custom_field_data null+encoder, tags as
TaggableManager) are reconciled inline following the convention established in
0004_reconcile_netboxmodel_fields.py so ``makemigrations --check`` reports no
drift on the new models. See ATW-32 and ADR-0003 for the migration conventions.
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
        ("netbox_pyats", "0004_reconcile_netboxmodel_fields"),
    ]

    operations = [
        # ----------------------------------------------------------------- #
        # PyatsGoldenConfig
        # ----------------------------------------------------------------- #
        migrations.CreateModel(
            name="PyatsGoldenConfig",
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
                        help_text="Human-readable label, e.g. 'baseline-rtr01'.",
                        max_length=100,
                    ),
                ),
                (
                    "config_text",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Golden running-config text (the 'expected' device config). "
                            "Diffed against a snapshot's parsed config payload by the "
                            "compliance pipeline. May be empty only for a placeholder golden; "
                            "compliance runs against an empty golden classify as 'error'."
                        ),
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=netbox_pyats.choices.GoldenConfigSourceChoices.choices,
                        default="manual",
                        help_text="How the golden config was authored: typed manually or promoted from a snapshot.",
                        max_length=20,
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        help_text="NetBox device this golden config applies to.",
                        on_delete=models.deletion.CASCADE,
                        related_name="pyats_golden_configs",
                        to="dcim.device",
                    ),
                ),
                (
                    "source_snapshot",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "When source=snapshot, the PyatsSnapshot row this golden config was "
                            "promoted from. Null for manually-authored goldens. Kept for "
                            "provenance so the compliance history can link back to the "
                            "known-good snapshot."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="golden_configs_promoted_from",
                        to="netbox_pyats.pyatssnapshot",
                    ),
                ),
                (
                    "tags",
                    _TAG_FIELD,
                ),
            ],
            options={
                "verbose_name": "PyATS Golden Config",
                "verbose_name_plural": "PyATS Golden Configs",
                "ordering": ("device__name", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="pyatsgoldenconfig",
            constraint=models.UniqueConstraint(
                fields=("device", "name"),
                name="netbox_pyats_goldenconfig_unique_per_device",
            ),
        ),
        # ----------------------------------------------------------------- #
        # PyatsComplianceRun
        # ----------------------------------------------------------------- #
        migrations.CreateModel(
            name="PyatsComplianceRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "result",
                    models.CharField(
                        choices=netbox_pyats.choices.ComplianceResultChoices.choices,
                        default="error",
                        help_text="Compliance outcome: compliant, drift, or error.",
                        max_length=20,
                    ),
                ),
                (
                    "diff",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Structured diff tree as JSON (same shape as PyatsSnapshotDiff.diff) "
                            "showing golden vs. snapshot config differences. Empty for compliant "
                            "and error runs (no tree to render). Rendered with the Phase 3 "
                            "diff-tree viewer partial."
                        ),
                    ),
                ),
                (
                    "summary",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Flat counts per diff status: {added, removed, changed, unchanged}. "
                            "All zero for compliant runs; non-zero for drift; empty for error."
                        ),
                    ),
                ),
                (
                    "parser_warnings",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text=(
                            "List of human-readable warnings/errors from the compliance run: "
                            "unsupported platform, empty golden, snapshot missing config, "
                            "diff engine errors. Empty for clean compliant/drift runs."
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
                        help_text="NetBox device this compliance run checked (must match both golden and snapshot).",
                        on_delete=models.deletion.CASCADE,
                        related_name="pyats_compliance_runs",
                        to="dcim.device",
                    ),
                ),
                (
                    "golden",
                    models.ForeignKey(
                        help_text="The golden config this run compared against.",
                        on_delete=models.deletion.CASCADE,
                        related_name="compliance_runs",
                        to="netbox_pyats.pyatsgoldenconfig",
                    ),
                ),
                (
                    "snapshot",
                    models.ForeignKey(
                        help_text="The snapshot this run compared against the golden config.",
                        on_delete=models.deletion.CASCADE,
                        related_name="compliance_runs",
                        to="netbox_pyats.pyatssnapshot",
                    ),
                ),
                (
                    "tags",
                    _TAG_FIELD,
                ),
            ],
            options={
                "verbose_name": "PyATS Compliance Run",
                "verbose_name_plural": "PyATS Compliance Runs",
                "ordering": ("-created",),
            },
        ),
        migrations.AddIndex(
            model_name="pyatscompliancerun",
            index=models.Index(fields=("device", "-created"), name="pyats_compl_dev_created_idx"),
        ),
        migrations.AddIndex(
            model_name="pyatscompliancerun",
            index=models.Index(
                fields=("device", "result", "-created"),
                name="pyats_compl_dev_result_idx",
            ),
        ),
    ]
