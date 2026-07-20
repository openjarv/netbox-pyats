# PyATS worker deployment

The netbox-pyats plugin runs snapshot captures, structured diffs, and compliance checks as RQ jobs on a **dedicated `pyats` queue**, isolated from NetBox's default RQ workers. This document covers why the queue is separate, how to run a worker for it, and how to verify it is wired up.

## Why a separate queue

pyATS/Genie is a heavy dependency (`pyats[full]` pulls Cython binaries, parser packages, and Unicon connection plugins) that the default NetBox worker container does not — and should not — have installed. Snapshot captures also make outbound SSH/Telnet connections to real devices and can run for tens of seconds per device (each capture runs `device.parse('show running-config')` plus a small state command set, sequentially). Running that work on NetBox's default queue would block NetBox's own housekeeping jobs (datasource syncs, changelog pruning, release checks) behind slow device captures.

The plugin declares the `pyats` queue via `NetBoxPyATSConfig.queues = ["pyats"]`, so NetBox creates it at startup. Operators run a second worker pointed at `pyats` only; the default worker continues to service NetBox's own queue. The diff (`run_diff`) and compliance (`run_compliance`) jobs themselves need no pyATS — they operate on already-serialized JSONB — but run on the `pyats` queue for isolation and a single worker image. An operator who only wants diffs/compliance can run the default worker if they prefer (no `pyats[full]` install needed for diffs/compliance alone).

## Running the worker

### Option A: the shipped worker image (dev / reference)

A ready-to-build worker image is in `dev/Dockerfile.pyats-worker`. It layers `pyats[full]` onto the official NetBox image so the worker shares NetBox's Django environment (models, settings, RQ) and has Genie installed. The dev compose file wires it up:

```bash
docker compose -f docker-compose.dev.yml up -d --build netbox-pyats-worker
```

The worker services the `pyats` queue only (see `docker-compose.dev.yml` → `netbox-pyats-worker` → `command: ["pyats"]`).

### Option B: install pyats into your own worker

If you already run NetBox's worker in your own container or host, install the pyats extra there and start a second rqworker pointed at `pyats`:

```bash
pip install netbox-pyats[pyats]        # pulls pyats[full] >= 26.0
python manage.py rqworker pyats
```

The worker needs the same NetBox configuration (`configuration.py`, `PLUGINS`, `PLUGINS_CONFIG`) and database/Redis access as the default worker — it is a NetBox worker, just with pyats installed and a different queue argument.

## Verifying the queue and worker

After starting the worker, confirm it is registered on the `pyats` queue:

```bash
python manage.py rqworker --url redis://redis:6379/0 pyats   # foreground, for debugging
```

In the NetBox UI, **Operations → Background Tasks → Workers** lists registered workers and the queues they service; you should see one worker listening on `pyats`. The **Jobs** tab shows queued/running jobs on the queue — capture jobs (`PyATS snapshot: <device> (<kind>)`), diff jobs (`PyATS diff: <device> (#before vs #after)`), and compliance jobs (`PyATS compliance: <device> (golden #<id> vs snapshot #<id>)`).

## Capturing a snapshot

1. Add a `PyatsCredential` for the device (**Plugins → PyATS → Add Credential**).
2. Open the device's detail page → **PyATS** tab.
3. Pick a kind (config / state / full) and click **Capture**.
4. The job is enqueued on `pyats`. When the worker finishes, the snapshot appears in the tab's recent-snapshots list and under **Plugins → PyATS → PyATS Snapshots**.

If the device's platform has no Genie parser, the job writes an `unsupported` snapshot row (no data, a warning explaining the skip) so the device still appears in the history. Capture errors are written as `error` rows with the exception text in `parser_warnings`.

## Diffing two snapshots

1. From the device's **PyATS** tab, capture at least two snapshots of the same device (the "Diff two snapshots" picker is only offered then).
2. Pick a **before** and an **after** snapshot → **Diff**.
3. The `run_diff` job is enqueued on `pyats`. When the worker finishes, the diff appears in the tab's recent-diffs list and under **Plugins → PyATS → PyATS Snapshot Diffs**.

The diff engine is pure-Python (no pyATS needed); empty/unsupported snapshots yield `status="empty"` and malformed inputs yield `status="error"` — a diff row is always created so the outcome is visible in-line.

## Running compliance (golden vs snapshot)

1. Add a `PyatsGoldenConfig` for the device (**Plugins → PyATS → Golden Configs → Add**): give it a name and paste the expected running-config text. Multiple goldens per device are allowed (e.g. `baseline`, `post-maintenance-window`).
2. Capture at least one **config** or **full** snapshot of the device (compliance compares the golden against the snapshot's parsed `data["config"]`).
3. From the device's **PyATS** tab → **Run compliance** picker (shown when the device has ≥1 golden and ≥1 config/full snapshot), pick a golden and a snapshot → **Run**.
4. The `run_compliance` job is enqueued on `pyats`. When the worker finishes, the compliance run appears in the tab's recent-compliance-runs list and under **Plugins → PyATS → PyATS Compliance Runs**.

The compliance engine reuses the Phase 3 diff engine, so the run's detail view renders the same collapsible before/after tree as the diff viewer, plus a `compliant` / `drift` / `error` result badge. An `error` result is recorded (with a warning naming the missing input) when the golden is empty, the snapshot has no `config` payload, or the snapshot is `unsupported`/`error` — the run row is always created.

## Troubleshooting

- **"PyATS snapshot queued" but no row appears:** the `pyats` worker is not running or not servicing the `pyats` queue. Check **Operations → Background Tasks → Workers** and the worker logs.
- **`error` status with `connection failed` in warnings:** the worker cannot reach the device's management IP. Verify `primary_ip4`/`primary_ip6` on the NetBox device and that the worker host has network reachability to it.
- **`unsupported` status for a platform you expect to be supported:** the NetBox Platform slug is not in the map in `netbox_pyats/testbed.py`. Add it (only if Genie has a real parser for that os) and redeploy.
- **`error` status with `state capture failed: ...`:** a state command's parser raised an unexpected exception (not `ParserNotFound`). Check the worker's genie install (`pip install netbox-pyats[pyats]` or rebuild the worker image) and the full traceback in the snapshot's `parser_warnings`.
- **Compliance run result `error` with "missing golden config" / "snapshot has no config payload":** the golden's `config_text` is empty, or the chosen snapshot is `unsupported`/`error` or has no `config` key. Re-capture a config/full snapshot of a supported platform and ensure the golden has non-empty text.
- **Compliance run result `drift` when you expected `compliant`:** the golden text does not parse to the same structure as the snapshot's Genie-parsed config. The run's diff tree shows exactly which leaves diverged — start there.