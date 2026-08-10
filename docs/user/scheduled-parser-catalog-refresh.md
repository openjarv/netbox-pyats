# Scheduled parser-catalog refresh

The plugin caches Genie's parser-discovery surface (the list of CLI commands
`device.parse()` can run per pyATS `os`) in `PyatsParserCatalog` rows. After a
worker `genie.libs` upgrade the cached rows go stale and the device-page Parse
sub-tab silently shows the old command list until someone clicks "Refresh
parser list". The scheduled refresh lets the catalog track the upgrade
automatically on a cadence, instead of relying on a manual click per device.

## How it works

The scheduling mirrors the [scheduled captures](scheduled-captures.md) flow
(ADR-0008) — three pieces:

1. **`PyatsParserCatalogRefreshSchedule`** (the *what*) — a single-row
   operator-authored intent model in the plugin UI with an `enabled` flag and
   display-only `last_run_at` / `next_run_at` timestamps. The model is a
   singleton by convention (the dispatcher reads the row with `pk=1`); the
   "Add" view redirects to the existing row's edit view when one already
   exists, so the operator cannot create a second row.
2. **`RunParserCatalogRefreshSchedulesJob`** (the *dispatch*) — a NetBox
   `JobRunner` subclass (`netbox_pyats/jobs.py`) that reads the schedule row
   and, when `enabled=True`, enqueues one
   `enqueue_refresh_parser_catalog()` on the `pyats` RQ queue. The dispatcher
   runs on NetBox's **default** RQ queue (it does no pyATS work — it only
   enqueues the real refresh onto `pyats`).
3. **NetBox `Job` `schedule_at`/`interval`** (the *when*) — the operator
   enqueues the dispatcher with a recurrence interval (in minutes) and an
   optional first-run time. NetBox's `JobRunner.handle` auto-reschedules the
   next run after each execution, so the dispatch recurs without a
   plugin-side cron worker and without `rq-scheduler`.

## Enabling the schedule

1. Navigate to **Genie → Parser Catalog → Catalog Refresh Schedule** (or
   **Edit Refresh Schedule** — both land on the same single row).
2. Tick **enabled**.
3. Save.

The row is created lazily by the dispatcher on its first run if the operator
has not created it first, so you can also enable it after you schedule the
dispatcher (below).

## Scheduling the dispatcher job

After enabling the schedule, enqueue the dispatcher as a recurring NetBox
`Job`. As with capture schedules, NetBox 4.x has no generic "schedule any
callable" form in the web UI, so the recurring enqueue is initiated from the
NetBox shell.

### Via the NetBox shell (recurring)

```bash
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import RunParserCatalogRefreshSchedulesJob
from django.utils import timezone
from datetime import timedelta

# Run nightly at 03:00 — first run in ~hours from now, then every 1440 min.
first_run = timezone.now().replace(hour=3, minute=0, second=0, microsecond=0)
if first_run <= timezone.now():
    first_run = first_run + timedelta(days=1)
Job.enqueue(
    RunParserCatalogRefreshSchedulesJob.handle,
    name='PyATS nightly parser-catalog refresh',
    schedule_at=first_run,
    interval=1440,  # minutes (24h)
)
"
```

### One-shot dispatch (run now)

To fire the dispatcher immediately (e.g. to test the schedule you just
enabled), enqueue it without `schedule_at`/`interval`:

```bash
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job
Job.enqueue(run_parser_catalog_refresh_schedules_job, name='PyATS parser-catalog refresh (one-shot)')
"
```

The refresh queues up on `pyats` and runs when the pyats worker comes online
(see [workers.md](workers.md) § "capture sits on pyats queue until a worker
comes online").

## Verifying a scheduled run

1. After the dispatcher fires, navigate to **PyATS Jobs & Platforms → Jobs** — you will see
   one `refresh_catalog` `PyatsJob` row per dispatch.
2. The schedule's **Last run** timestamp is updated after each dispatch.
3. The `PyatsParserCatalog` rows (one per supported `os`) are upserted with
   the new command list and the worker's `genie_version` / `pyats_version`.

## External cron fallback

If you already run an external scheduler, trigger a one-shot dispatch on your
own cadence instead of using NetBox's `interval` recurrence:

```bash
docker compose -f docker-compose.dev.yml exec netbox python manage.py shell -c "
from core.models import Job
from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job
Job.enqueue(run_parser_catalog_refresh_schedules_job, name='PyATS parser-catalog refresh (cron)')
"
```

The dispatcher is the same callable the `interval` path fires, so the
behavior is identical. The documented happy path is NetBox's `interval`
recurrence (it keeps the cadence in NetBox's single pane of glass); the
external-cron path is a fallback for operators who already have one.

## See also

- [ADR-0008](../adr/0008-scheduling-surface.md) — structural decision
- [scheduled-captures.md](scheduled-captures.md) — the analogous capture flow
- [workers.md](workers.md) — the `pyats` RQ queue and worker setup