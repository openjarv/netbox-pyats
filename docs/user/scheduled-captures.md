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
2. **`run_capture_schedules_job`** (the *dispatch*) — a custom job callable
   that reads enabled schedules, re-resolves each device filter to a live
   Device queryset, and enqueues one batch capture per schedule on the `pyats`
   RQ queue (the same queue manual and bulk captures use).
3. **NetBox `ScheduledJob`** (the *when*) — NetBox's native scheduler
   (Operations → Jobs) fires the dispatcher on a crontab or interval. The
   plugin owns no cron worker and adds no `rq-scheduler` dependency.

## Creating a schedule

1. Navigate to **PyATS → Capture Schedules → Add**.
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

After creating one or more schedules, schedule the dispatcher in NetBox's
native jobs UI:

1. Navigate to **Operations → Jobs**.
2. Click **Schedule a job** (or the equivalent in your NetBox version).
3. Select the job **RunCaptureSchedules** (category PyATS).
4. Pick a schedule type: **immediately** (one-off), **interval** (every N
   minutes), or **custom** (crontab expression, e.g. `0 2 * * *` for 02:00
   daily).
5. Save.

The dispatcher runs on NetBox's **default** RQ queue (it does no pyATS work —
it only enqueues the real captures onto the `pyats` queue). The captures
queue up on `pyats` and run when the pyats worker comes online (see
[workers.md](workers.md) § "capture sits on pyats queue until a worker comes
online").

## Verifying a scheduled run

1. After the dispatcher fires, navigate to **PyATS → Jobs** — you will see
   one `batch_capture` `PyatsJob` row per enabled schedule.
2. The schedule's **Last run** timestamp is updated after each dispatch.
3. The snapshot rows appear in **PyATS → Snapshots** (or the device-page PyATS
   tab) once the pyats worker finishes the captures.

## External cron fallback

If you already run an external scheduler (host crontab, k8s CronJob), you can
trigger the dispatcher via the NetBox CLI or API instead of the native
ScheduledJob:

```bash
# Trigger the dispatcher via the NetBox management CLI (example):
python manage.py runjob --job netbox_pyats.run_capture_schedules_job
```

The dispatcher is the same callable the native ScheduledJob fires, so the
behavior is identical. The documented happy path is NetBox's native
ScheduledJob (it keeps the cadence in NetBox's single pane of glass); the
external-cron path is a fallback for operators who already have one.

## See also

- [ADR-0008](../adr/0008-scheduling-surface.md) — structural decision
- [workers.md](workers.md) — the `pyats` RQ queue and worker setup
- [usage.md](usage.md) — manual capture / diff / compliance flows