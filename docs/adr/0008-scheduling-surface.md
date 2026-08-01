# ADR-0008: Scheduling surface for recurring snapshot capture

Date: 2026-08-01
Status: Accepted (CTO structural direction; CEO scope sign-off via [ATW-447](/ATW/issues/ATW-447) confirmation)
Supersedes: —
Superseded by: —

## Context

The plugin ships manual and batch snapshot capture (ATW-13, ATW-16) but no
scheduling surface — no way to say "capture device-set X every night at
02:00." Nightly baseline capture is the friction-reducer for drift detection
that the plugin's value prop promises ("historical comparison for config
compliance and pre/post change checks"). ATW-433 (GAP FILLING, MEDIUM) asks
for scheduled/recurring snapshot capture.

Four candidate surfaces were considered (see the [ATW-447 plan
document](/ATW/issues/ATW-447#document-plan)):

1. NetBox custom jobs + a plugin intent model + NetBox's native `Job` interval (originally framed as a "ScheduledJob" surface; verified in 4.6 to be the `JobRunner` + `Job.enqueue(interval=...)` mechanism — there is no standalone `ScheduledJob` model).
2. `rq-scheduler` integration (plugin owns the scheduler).
3. A NetBox custom job the operator triggers via external cron.
4. Defer to a future release.

## Decision

**Option 1: NetBox Custom Job + `PyatsCaptureSchedule` intent model + a
`JobRunner` subclass for recurring cadence — no `rq-scheduler` dependency.**

A plugin **intent model** (`PyatsCaptureSchedule`) owns the *what* (device
filter, capture kind, enabled, last_run/next_run display); a **registered
NetBox `JobRunner` subclass** (`RunCaptureSchedulesJob`) owns the *dispatch*
(read enabled schedules, fan out `enqueue_batch_capture` per schedule on the
`pyats` queue); **NetBox's native `core.models.Job`** with `interval` owns
the *when* (operator sets `schedule_at` / `interval` at enqueue time, and
`JobRunner.handle` auto-reschedules recurring runs). No `rq-scheduler`
dependency, no plugin-side cron worker.

### Why this fits the locked architecture

- **ADR-0001 §6 holds exactly** — all capture work still runs on the `pyats`
  queue via `core.models.Job.enqueue`. The scheduler never bypasses
  `enqueue_*`; it *calls* them.
- **ADR-0005 §3 plumbing contract unchanged** — `enqueue_capture` /
  `enqueue_batch_capture` signatures are untouched. The custom job is just a
  new caller of existing helpers. `triggered_by=SnapshotTriggerChoices.TRIGGER_JOB`
  is already wired (choices.py:67) — scheduled captures get
  `triggered_by='job'` with zero new choice values.
- **ADR-0001 §1/§2** — one new model in `models.py`, one migration (`0011`,
  linear after `0010`), choices stay in `choices.py`, single source of truth
  per concern.
- **ADR-0001 §5** — REST + GraphQL generated from the model via the standard
  router/type registration; the schedule is an operator-authored object, so
  it gets full CRUD (unlike `PyatsJob` which is append-only).
- **No new runtime dependency** — `rq-scheduler` is NOT added to
  `pyproject.toml`. NetBox already ships `django-rq` and its own
  `JobRunner` recurring-scheduling machinery; we reuse it. This keeps the
  plugin install-light.

### Structural shape

- `PyatsCaptureSchedule(NetBoxModel)`: `name` (unique), `device_filter`
  (JSONField — a serialized ORM filter spec, re-resolved at run time, NOT a
  M2M to Device because devices drift), `kind` (reuse
  `SnapshotKindChoices`), `enabled` (BooleanField), `last_run_at` /
  `next_run_at` (nullable DateTimeField, display-only, written by the
  dispatcher). Full CRUD + REST + GraphQL + search index.
- `run_capture_schedules_job` (plain function callable in `jobs.py`) plus
  `RunCaptureSchedulesJob` (a `netbox.jobs.JobRunner` subclass wrapping it):
  reads `PyatsCaptureSchedule(enabled=True)`, re-resolves each schedule's
  `device_filter` to a Device queryset, calls `enqueue_batch_capture` per
  schedule on `pyats`. Runs on NetBox's **default** queue (the one justified
  exception to "all plugin work on `pyats`": the dispatcher does no pyATS work
  — it only enqueues, so it fires even if no pyats worker is online; the
  captures queue up on `pyats` and run when the worker comes up — the existing
  "capture sits on pyats queue until a worker comes online" behaviour
  documented in workers.md:57). The plain-function wrapper supports one-shot
  enqueue via `core.models.Job.enqueue`; the `JobRunner` subclass is what
  makes the dispatcher **recurring** — `JobRunner.handle`'s `finally` block
  re-enqueues the next run when enqueued with `interval` (see
  `netbox/jobs.py`). A plain function alone does not auto-reschedule.
- Cadence: the operator enqueues `RunCaptureSchedulesJob` with
  `schedule_at` / `interval` (e.g. via the NetBox shell or a plugin view),
  and NetBox's `Job` row carries the `scheduled`/`interval` fields;
  `JobRunner.handle` drives the recurrence. NetBox 4.x has no separate
  `ScheduledJob` model and no generic "schedule any callable" UI — recurring
  execution is a property of `JobRunner` subclasses enqueued with `interval`,
  not of a standalone scheduler object. The plugin owns no cron worker.

## Consequences

- **Positive:** nightly baseline capture is the headline friction-reducer for
  drift detection; the surface is small (one model + one migration + one
  registered job + one doc page) and reuses every existing primitive.
- **Positive:** the plugin owns no cron worker and adds no `rq-scheduler`
  dependency — cadence stays in NetBox's standard UI, matching the
  install-light philosophy.
- **Positive:** `device_filter` as a re-resolved filter spec (not a M2M) means
  devices that drift between schedule creation and dispatch are picked up or
  dropped automatically, mirroring `enqueue_batch_capture`'s re-resolve-by-id
  pattern.
- **Negative:** the operator must configure the cadence in two places (create
  the schedule in the plugin UI, then enqueue the `RunCaptureSchedulesJob`
  dispatcher with `schedule_at`/`interval`). NetBox 4.x has no generic
  "schedule any callable" UI for arbitrary `JobRunner` subclasses (only
  Custom Scripts get the native `_schedule_at`/`_interval` form fields), so
  the recurring enqueue is initiated via the NetBox shell or a plugin view.
  This is documented in `docs/user/scheduled-captures.md` and is the
  trade-off for staying inside the NetBox `Job` primitive and avoiding
  `rq-scheduler`.

## Alternatives considered

- **Option 2 (raw `rq-scheduler`)** — Rejected. Adds a runtime dependency and
  a plugin-owned scheduler worker that duplicates NetBox's native
  `JobRunner` recurrence. Violates "don't hack around the plugin contract" and
  the install-light philosophy.
- **Option 3 (external cron → custom job)** — Rejected as the *primary* path.
  It works, but it pushes the cadence config out of NetBox (operator edits a
  host crontab / k8s CronJob), which is the friction we exist to reduce. Kept
  as a *fallback* for operators who already run an external scheduler —
  `run_capture_schedules_job` is callable via `Job.enqueue` from the NetBox
  shell, so external cron can trigger it without anything plugin-specific.
- **Option 4 (defer)** — Rejected. Nightly baseline capture is the headline
  friction-reducer; deferring it weakens the v1 value prop. The surface is
  small and reuses every existing primitive. Cost is low; payoff is high.

## References

- [ATW-433](/ATW/issues/ATW-433) — scheduled/recurring snapshot capture
  (implementation)
- [ATW-447](/ATW/issues/ATW-447#document-plan) — CTO scope decision (this ADR
  records the locked structure)
- ADR-0001 §1/§2/§5/§6 — model layout, REST/GraphQL, queue isolation
- ADR-0005 §3 — PyatsJob plumbing contract (unchanged)