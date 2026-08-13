# PyATS worker deployment

> **Most NetBox plugins need no extra setup — this one needs a second worker.**
> Snapshot captures make outbound SSH/Telnet connections to your real devices and run Cisco's PyATS/Genie parsers, which are heavy and not part of the default NetBox worker. If you skip this worker, clicking **Capture snapshot** in the UI silently never runs — the job sits on a queue with nothing to pick it up. The rest of this page explains how to run it.

The netbox-pyats plugin runs snapshot captures, structured diffs, and compliance checks as RQ jobs on a **dedicated `pyats` queue**, isolated from NetBox's default RQ workers. This guide covers why the queue is separate, how to run a worker for it, and how to verify it is wired up.

## Why a separate queue

pyATS/Genie is a heavy dependency (`pyats[full]` pulls Cython binaries, parser packages, and Unicon connection plugins) that the default NetBox worker container does not — and should not — have installed. Snapshot captures also make outbound SSH/Telnet connections to real devices and can run for tens of seconds per device (each capture runs `device.parse('show running-config')` plus a small state command set, sequentially). Running that work on NetBox's default queue would block NetBox's own housekeeping jobs (datasource syncs, changelog pruning, release checks) behind slow device captures.

The plugin declares the `pyats` queue via `NetBoxPyATSConfig.queues = ["pyats"]`, so NetBox creates it at startup. Operators run a second worker pointed at `pyats` only; the default worker continues to service NetBox's own queue. The diff (`run_diff`) and compliance (`run_compliance`) jobs themselves need no pyATS — they operate on already-serialized JSONB — but run on the `pyats` queue for isolation and a single worker image. An operator who only wants diffs/compliance can run the default worker if they prefer (no `pyats[full]` install needed for diffs/compliance alone).

## Running the worker

### Option A — install pyats into your own worker

If you already run NetBox's worker in your own container or host, install the pyats extra there and start a second rqworker pointed at `pyats`:

```bash
pip install netbox-pyats[pyats]        # pulls pyats[full] >= 26.0
python manage.py rqworker pyats
```

The worker needs the same NetBox configuration (`configuration.py`, `PLUGINS`, `PLUGINS_CONFIG`) and database/Redis access as the default worker — it is a NetBox worker, just with pyats installed and a different queue argument.

For upgrading the plugin or NetBox (the worker must match the web container's NetBox version), see [Upgrade guide](upgrade.md).

### Option B — the shipped worker image (reference / dev)

A ready-to-build worker image is in `dev/Dockerfile.pyats-worker`. It layers `pyats[full]` onto the official NetBox image so the worker shares NetBox's Django environment (models, settings, RQ) and has Genie installed. The dev compose file wires it up:

```bash
docker compose -f docker-compose.dev.yml up -d --build netbox-pyats-worker
```

The worker services the `pyats` queue only (see `docker-compose.dev.yml` → `netbox-pyats-worker` → `command: ["pyats"]`). This is the reference image for contributors — see [Dev environment bring-up](../developer/setup.md) for the full dev stack.

## Verifying the queue and worker

After starting the worker, confirm it is registered on the `pyats` queue:

```bash
python manage.py rqworker --url redis://redis:6379/0 pyats   # foreground, for debugging
```

In the NetBox UI, **Operations → Background Tasks → Workers** lists registered workers and the queues they service; you should see one worker listening on `pyats`. The **Jobs** tab shows queued/running jobs on the queue — capture jobs (`PyATS snapshot: <device> (<kind>)`), diff jobs (`PyATS diff: <device> (#before vs #after)`), and compliance jobs (`PyATS compliance: <device> (golden #<id> vs snapshot #<id>)`).

## Worker status badge

Every plugin page that triggers pyATS work shows a small **Worker online / offline** badge near the top of the form area, next to the action button. It is a quick at-a-glance check so you know the worker state *before* you click Capture / Parse / Learn / Diff — instead of finding out the hard way when a job sits on the queue and nothing happens.

The badge appears on six pages:

- the device **PyATS** tab (capture form)
- the device **Parse** sub-tab
- the **Genie Parse** page
- the **Genie Learn** page
- the **Genie Diff** page
- the **Bulk capture** action on the device list

### What the colors mean

- **Green — Worker online.** At least one RQ worker is listening on the `pyats` queue. Hover the badge for the count, e.g. `1 worker on pyats`.
- **Red — Worker offline.** No worker is on the `pyats` queue, Redis is unreachable, or RQ is not installed. Hover the badge for the reason, e.g. `no workers on pyats queue`, `redis unreachable`, or `RQ not installed`.

### The ~15-second cache

The status is cached for about 15 seconds on the NetBox server, so a freshly started or stopped worker may not show up for up to ~15 seconds. This is on purpose — one Redis check every ~15 seconds, not one per page render — so the badge stays cheap on a busy device tab. If you just started a worker and the badge is still red, give it a few seconds and refresh the page.

### The badge is informational only

A red badge does **not** block the form. You can still click Capture / Parse / Learn / Diff and the job is enqueued as usual — it just sits on the `pyats` queue until a worker comes online, the same as before the badge existed. The badge is a heads-up, not a gate. To turn it green, start a worker — see [Running the worker](#running-the-worker) above.

## What runs on the `pyats` queue

| Job | Needs pyATS? | Why it is on `pyats` |
|-----|--------------|----------------------|
| `capture_snapshot` | yes | connects to a real device and runs Genie parsers. |
| `run_diff` | no | operates on already-serialized JSONB; on `pyats` for isolation and a single worker image. |
| `run_compliance` | no | operates on persisted text; on `pyats` for the same reason. |

An operator who only wants diffs/compliance and does not want to install pyats can run the default worker to service those jobs — but the capture jobs will then sit on the `pyats` queue until a pyats worker comes online.

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for the operator-facing failure modes (worker not running, connection failures, `unsupported` platforms, compliance `error` results, unexpected `drift`).