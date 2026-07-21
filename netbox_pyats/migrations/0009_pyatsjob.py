"""Phase 5 (ATW-16): add the PyatsJob model.

ADR-0005 (Accepted, branch ``docs/atw-16-adr0005-pyatsjob``) introduces a
plugin-scoped job-tracking row that bridges NetBox's ``core.models.Job`` (the
RQ-level tracking row) and the plugin's result rows (PyatsSnapshot,
PyatsSnapshotDiff, PyatsComplianceRun). Each ``enqueue_*`` helper creates a
``PyatsJob(status=pending)`` before ``Job.enqueue``; the job callable sets
``running`` at entry, ``success`` / ``error`` / ``partial`` on exit, and the
relevant ``related_*`` FK to the produced result row on success. See ADR-0005
§3 for the plumbing contract.

Additive only — a new model, no existing rows are rewritten. No backfill
(ADR-0005 §Consequences): pre-ATW-16 captures/diffs/compliance do not get
retroactive ``PyatsJob`` rows; the unified jobs view starts populated from
ATW-16 forward.

Field attributes (created/last_updated/custom_field_data null+encoder, tags as
TaggableManager) are reconciled inline following the convention established in
0004_reconcile_netboxmodel_fields.py so ``makemigrations --check`` reports no
drift on the new model. See ATW-32 and ADR-0003 for the migration conventions.
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
        ("core", "__first__"),
        ("netbox_pyats", "0008_pyatssnapshotdiff_nullable_fks"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "job_type",
                    models.CharField(
                        choices=netbox_pyats.choices.PyatsJobTypeChoices.choices,
                        help_text=(
                            "Kind of plugin job this row tracks: capture / diff / compliance / " "batch_capture."
                        ),
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=netbox_pyats.choices.PyatsJobStatusChoices.choices,
                        default="pending",
                        help_text=(
                            "Lifecycle status: pending (enqueued, not yet picked up), running "
                            "(worker started the callable), success (result-row FK set), error "
                            "(job raised and the result row could not be written; see `error` "
                            "field), partial (batch completed without crashing but had per-device "
                            "failures; see `summary`)."
                        ),
                        max_length=20,
                    ),
                ),
                (
                    "rq_job_id",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="RQ job id for operator cross-reference with rq-dashboard.",
                        max_length=100,
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the worker started the job callable (set to now() at entry).",
                        null=True,
                    ),
                ),
                (
                    "finished_at",
                    models.DateTimeField(
                        blank=True, help_text="When the job callable returned (success/error/partial).", null=True
                    ),
                ),
                (
                    "error",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Exception text for the case where the job raised and the result "
                            "row could not be written (the swallowed-exception path in "
                            "jobs.py). Not a duplicate of the result row's parser_warnings; "
                            "this field covers the one case the result row's parser_warnings "
                            "cannot (no result row was written)."
                        ),
                    ),
                ),
                (
                    "summary",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Batch counts only: {supported, unsupported, errored, total}. "
                            "Empty for single-device jobs (capture/diff/compliance)."
                        ),
                    ),
                ),
                (
                    "core_job",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "NetBox core.Job row tracking the RQ run. on_delete=SET_NULL "
                            "because core.Job rows are purged by NetBox's retention; PyatsJob "
                            "is plugin data and survives."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="pyats_jobs",
                        to="core.job",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "NetBox device this job targeted. Null for batch_capture jobs "
                            "(which target a queryset, not a single device)."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="pyats_jobs",
                        to="dcim.device",
                    ),
                ),
                (
                    "related_compliance",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "For job_type=compliance: the PyatsComplianceRun row this job "
                            "produced. Set on success. Null for capture/diff/batch_capture jobs."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="pyats_jobs",
                        to="netbox_pyats.pyatscompliancerun",
                    ),
                ),
                (
                    "related_diff",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "For job_type=diff: the PyatsSnapshotDiff row this job produced. "
                            "Set on success. Null for capture/compliance/batch_capture jobs."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="pyats_jobs",
                        to="netbox_pyats.pyatssnapshotdiff",
                    ),
                ),
                (
                    "related_snapshot",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "For job_type=capture: the PyatsSnapshot row this job produced. "
                            "Set on success. Null for diff/compliance/batch_capture jobs."
                        ),
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="pyats_jobs",
                        to="netbox_pyats.pyatssnapshot",
                    ),
                ),
                (
                    "tags",
                    _TAG_FIELD,
                ),
            ],
            options={
                "verbose_name": "PyATS Job",
                "verbose_name_plural": "PyATS Jobs",
                "ordering": ("-created",),
            },
        ),
        migrations.AddIndex(
            model_name="pyatsjob",
            index=models.Index(fields=("job_type", "-created"), name="pyats_job_type_created_idx"),
        ),
        migrations.AddIndex(
            model_name="pyatsjob",
            index=models.Index(fields=("status", "-created"), name="pyats_job_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="pyatsjob",
            index=models.Index(fields=("device", "-created"), name="pyats_job_dev_created_idx"),
        ),
    ]
