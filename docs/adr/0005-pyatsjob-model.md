# ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension

Date: 2026-07-21
Status: Accepted (CEO plan confirmation accepted on [ATW-16](/ATW/issues/ATW-16); implementation handed to SDE)
Supersedes: —
Superseded by: —
Related: [ADR-0002](0002-graceful-degradation.md) (status vocabulary extension), [ADR-0001](0001-plugin-layout.md) (single model home)

## Context

Phase 5 ([ATW-16](/ATW/issues/ATW-16)) requires a unified jobs view that lists all capture/diff/compliance jobs with status and links to the result rows they produced. NetBox's `core.models.Job` already tracks every RQ run we enqueue via `Job.enqueue` — it carries status, log entries, the `object_id` link, and the generic NetBox jobs UI. The plugin needs more than that:

- A plugin-scoped, filterable list of "all PyATS work" across capture / diff / compliance / batch, with typed foreign keys to the plugin's own result rows (`PyatsSnapshot`, `PyatsSnapshotDiff`, `PyatsComplianceRun`). The NetBox jobs UI is generic; operators want a single PyATS-scoped view that links a job to the result row it produced.
- The result-row FK is set by the worker *after* the job runs (the result row is created inside the job), so it cannot live on `core.models.Job` (which is created before enqueue). A plugin model is the bridge.
- A stable per-job error field for the cases where the job raised and the result row could not be written (e.g. `full_clean()` failure on the ADR-0002 error-row path — currently swallowed in `jobs.py` and only visible in RQ logs).
- A batch-job summary (`{supported, unsupported, errored, total}`) and a `partial` status for batches that did not crash but had per-device failures.

ADR-0002's status vocabulary table is locked and explicitly states "New status values may be added only via a follow-up ADR that extends this table." This ADR is that follow-up.

## Decision

### 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2)

`PyatsJob(NetBoxModel)` with:

- `job_type` (`PyatsJobTypeChoices`: `capture | diff | compliance | batch_capture`)
- `status` (`PyatsJobStatusChoices`: `pending | running | success | error | partial`)
- `device` (nullable FK to `dcim.Device`; null for batch jobs)
- `core_job` (nullable FK to `core.Job`, `on_delete=SET_NULL` — `core.Job` rows are purged by NetBox's retention; `PyatsJob` is plugin data and survives)
- `rq_job_id` (CharField, for operator cross-reference with rq-dashboard)
- `related_snapshot` / `related_diff` / `related_compliance` (nullable FKs to the plugin result rows, `on_delete=SET_NULL` — exactly one is set per job on success, by `job_type`)
- `started_at` / `finished_at` (nullable DateTimeFields)
- `error` (TextField, populated only when the result row could not be written — not a duplicate of the result row's `parser_warnings`)
- `summary` (JSONField, batch counts only; empty for single-device jobs)

Subclasses `NetBoxModel` (tags, custom fields, changelog). One migration: `0009_pyatsjob.py`, linear after `0008`. No backfill (see Consequences).

### 2. Status vocabulary extension (extends ADR-0002's table)

| Path | Status | Meaning | Color intent |
|---|---|---|---|
| PyatsJob | `pending` | Created at enqueue, not yet picked up by the worker | neutral |
| PyatsJob | `running` | Worker has started the job callable | info/blue |
| PyatsJob | `success` | Job completed; result-row FK is set | green |
| PyatsJob | `error` | Job raised and the result row could *not* be written; `error` TextField populated; re-raised so `core.Job` is also marked failed | red |
| PyatsJob | `partial` | Batch job completed without crashing, but some per-device captures errored or were unsupported; `summary` carries the counts | warning |

`success` and `error` reuse ADR-0002's color intent; `pending`/`running`/`partial` are new. The per-result-row statuses (`PyatsSnapshot.status`, `PyatsSnapshotDiff.status`, `PyatsComplianceRun.result`) are **unchanged** — ADR-0002's contract on the result rows holds exactly. `PyatsJob.status` is the job-level mirror; the result row is the outcome-level record. They are consistent but not identical: a `PyatsJob` can be `success` while a per-device result row is `unsupported` (the job ran fine; the device's platform was unsupported — that is a successful job producing an `unsupported` row, per ADR-0002).

### 3. Plumbing contract (non-breaking)

Each `enqueue_*` helper creates a `PyatsJob(status=pending)` *before* `Job.enqueue`, passes its pk to the job callable as `pyats_job_id`, and the callable:

1. Sets `status=running`, `started_at=now()` at entry.
2. On success: sets the relevant `related_*` FK to the created result row, `status=success`, `finished_at=now()`.
3. On the ADR-0002 "always write an error row" path: the result row is still created, so `status=error` + the result-row FK is set.
4. On the `raise` paths (`DoesNotExist`, device mismatch, `full_clean()` failure on the error row): sets `status=error` + `error` TextField, *then* re-raises so RQ/`core.Job` is marked failed. Wrapped in a top-level `try/finally` on the callable.

Existing `enqueue_capture`/`enqueue_diff`/`enqueue_compliance` signatures are unchanged; the `PyatsJob` write is additive. Tests calling the callables directly get a `PyatsJob` row as a side effect.

### 4. Unified jobs view

`PyatsJobListView` (generic `ObjectListView`, filterable by `job_type`/`status`/`device`) + `PyatsJobView` (detail, links to `core_job` + result row + `error` in `<pre>` + `summary`). Navigation entry "PyATS Jobs". Jobs are append-only history — no edit view; standard delete only. Read-only REST viewset (`http_method_names = ["get","head","options"]`) + graphene type, per ADR-0001 §5.

## Consequences

- **Positive:** operators get a single PyATS-scoped view of all work with links to the result rows, independent of NetBox's `core.Job` retention. Per-device and batch outcomes are traceable end-to-end.
- **Positive:** the swallowed-error path in `jobs.py` (the inner `except` that currently logs and re-raises) becomes visible: `PyatsJob.error` records it even when the result-row write failed.
- **Positive:** batch capture is the first multi-device op; its `summary` + `partial` status give operators a clear "X of Y devices captured, Z unsupported, W errored" without scanning rows.
- **Negative:** one additional row per plugin job (storage cost is small — one `PyatsJob` per capture/diff/compliance/batch). This is the price of plugin-scoped tracking independent of NetBox's job retention.
- **Negative:** **no backfill.** Pre-ATW-16 captures/diffs/compliance do not get retroactive `PyatsJob` rows. Historical result rows remain visible on their own list views; the unified jobs view starts populated from ATW-16 forward. Backfill would depend on `core.Job` rows that may already be purged and is not worth a data migration for v1.
- **Negative:** the `status` field on `PyatsJob` partially mirrors `core.Job.status` (pending/running/success/error). They can drift if the worker crashes between updating `PyatsJob` and `core.Job`. The detail view links both so the operator can reconcile; `core.Job` is the RQ-level source of truth, `PyatsJob` is the plugin-level result link.

## Alternatives considered

- **Extend `core.models.Job` with plugin fields.** Rejected: `core.Job` is NetBox's, not ours to extend; it would break on NetBox upgrades and violate the plugin contract (ADR-0001: no NetBox core changes).
- **A single `PyatsRun` table that subclasses the result rows.** Rejected: breaks the per-result-type FKs (a run is not a snapshot, a diff, or a compliance run — it *produces* one of them) and ADR-0001's single-model-home convention. The FK-from-job-to-result pattern is clearer.
- **Drop `core.Job` and track only on `PyatsJob`.** Rejected: `core.Job` gives us NetBox UI integration, notifications, and log entries for free; `PyatsJob` is the plugin bridge, not a replacement.
- **Put `parser_warnings` on `PyatsJob` too.** Rejected: the result row already carries `parser_warnings`; duplicating it risks drift. `PyatsJob.error` is only for the failure-to-write-result-row path, which is the one case the result row's `parser_warnings` cannot cover.

## References

- [ATW-16](/ATW/issues/ATW-16) plan (`#document-plan`)
- [ADR-0002](0002-graceful-degradation.md) — status vocabulary (extended here)
- [ADR-0001](0001-plugin-layout.md) — plugin layout (single model home; no core changes)
- `netbox_pyats/jobs.py` — existing `enqueue_*` + job callables (extended non-breakingly)