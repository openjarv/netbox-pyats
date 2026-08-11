# Scheduled captures

Scheduled captures are the plugin's nightly-baseline value prop: define *what*
to capture (a device filter + capture kind) once, then let NetBox's native
scheduler fire it on a cadence. This enables drift detection and pre/post
change checks without manually triggering captures every night.

## How it works

The plugin splits scheduling into three pieces (ADR-0008):

1. **`PyatsCaptureSchedule`** (the *what*) — an operator-authored model in the
   plugin UI: a name, a device filter (JSON ORM spec), a capture kind
   (config / state / full), and an enabled flag.
2. **`RunCaptureSchedulesJob`** (the *dispatch*) — a NetBox `JobRunner`
   subclass (`netbox_pyats/jobs.py`) that reads enabled schedules, re-resolves
   each device filter to a live Device queryset, and enqueues one batch
   capture per schedule on the `pyats` RQ queue (the same queue manual and
   bulk captures use). The dispatcher runs on NetBox's **default** RQ queue
   (it does no pyATS work — it only enqueues the real captures onto `pyats`).
3. **NetBox `Job` `schedule_at`/`interval`** (the *when*) — the operator
   enqueues the dispatcher with a recurrence interval (in minutes) and an
   optional first-run time. NetBox's `JobRunner.handle` auto-reschedules the
   next run after each execution, so the dispatch recurs without a
   plugin-side cron worker and without `rq-scheduler`.

## Creating a schedule

1. Navigate to **PyATS/Genie → Automation → Add Capture Schedule**.
2. Enter a **name** (e.g. "Edge-routers nightly baseline").
3. Pick a **kind** (config / state / full).
4. Enter a **device_filter** as a JSON ORM filter spec. Examples:
   - All devices in regions 1 and 2: `{"region_id__in": [1, 2]}`
   - Specific devices by id: `{"id__in": [10, 20, 30]}`
   - All devices with platform slug `cisco_ios`: `{"platform__slug": "cisco_ios"}`
   - All devices with a platform that maps to `iosxe`:
     `{"platform__slug__in": ["cisco_ios", "cisco_iosxe"]}`
5. Leave **enabled** checked (uncheck to pause without deleting).
6. Save.

The device filter is re-resolved at run time, so devices that drift between
schedule creation and dispatch are picked up or dropped automatically.

## Scheduling the dispatcher job

After creating one or more schedules, enqueue the dispatcher as a recurring
NetBox `Job`. NetBox 4.x has no generic "schedule any callable" form in the
web UI (only Custom Scripts get the native `_schedule_at`/`_interval` form
fields), so the recurring enqueue is initiated from the NetBox shell (or a
one-off plugin view). The dispatcher is a `JobRunner` subclass
(`RunCaptureSchedulesJob`), so once enqueued with an `interval`,
`JobRunner.handle` auto-reschedules each subsequent run — you only enqueue
once.

### Via the NetBox shell (recurring)

```bash
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import RunCaptureSchedulesJob
from django.utils import timezone
from datetime import timedelta

# Run nightly at 02:00 — first run in ~hours from now, then every 1440 min.
first_run = timezone.now().replace(hour=2, minute=0, second=0, microsecond=0)
if first_run <= timezone.now():
    first_run = first_run + timedelta(days=1)
Job.enqueue(
    RunCaptureSchedulesJob.handle,
    name='PyATS nightly capture schedules',
    schedule_at=first_run,
    interval=1440,  # minutes (24h)
)
"
```

### One-shot dispatch (run now)

To fire the dispatcher immediately (e.g. to test the schedules you just
created), enqueue it without `schedule_at`/`interval`:

```bash
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import run_capture_schedules_job
Job.enqueue(run_capture_schedules_job, name='PyATS capture schedules (one-shot)')
"
```

The captures queue up on `pyats` and run when the pyats worker comes online
(see [workers.md](workers.md) § "capture sits on pyats queue until a worker
comes online").

## Verifying a scheduled run

1. After the dispatcher fires, navigate to **PyATS/Genie → Jobs & Platforms → Jobs** — you will see
   one `batch_capture` `PyatsJob` row per enabled schedule.
2. The schedule's **Last run** timestamp is updated after each dispatch.
3. The snapshot rows appear in **PyATS/Genie → Snapshots** (or the device-page PyATS
   tab) once the pyats worker finishes the captures.

## External cron fallback

If you already run an external scheduler (host crontab, k8s CronJob), you can
trigger a one-shot dispatch on your own cadence instead of using NetBox's
`interval` recurrence:

```bash
# Trigger a one-shot dispatch via the NetBox shell (example):
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import run_capture_schedules_job
Job.enqueue(run_capture_schedules_job, name='PyATS capture schedules (cron)')
"
```

The dispatcher is the same callable the `interval` path fires, so the
behavior is identical. The documented happy path is NetBox's `interval`
recurrence (it keeps the cadence in NetBox's single pane of glass); the
external-cron path is a fallback for operators who already have one.

## See also

- [ADR-0008](../adr/0008-scheduling-surface.md) — structural decision
- [workers.md](workers.md) — the `pyats` RQ queue and worker setup
- [usage.md](usage.md) — manual capture / diff / compliance flows