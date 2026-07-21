# Troubleshooting

Operator-facing fixes for the most common failure modes. If a snapshot, diff, or compliance run shows an unexpected status, start here.

## Snapshot statuses

Every snapshot row is created — even on failure — so the device's history always shows the outcome. Read the `status` badge and the `parser_warnings` field first.

### `unsupported` status

The device's NetBox Platform slug is not in the parser map in `netbox_pyats/testbed.py`.

- Confirm the Platform slug on the NetBox device.
- Check whether Genie has a real parser for that os.
- If yes, ask your plugin maintainer to add the slug to `PLATFORM_SLUG_TO_PYATS_OS` (only if Genie has real parser coverage — silently mapping an unsupported os would produce empty snapshots and mislead operators).
- If no, the device cannot be captured by Genie today; it will keep showing as `unsupported` until Genie adds a parser.

### `error` status with `connection failed`

The worker cannot reach the device's management IP.

- Verify `primary_ip4` / `primary_ip6` on the NetBox device is set and correct.
- From the worker host, confirm network reachability: `ping <mgmt-ip>`, `ssh <user>@<mgmt-ip>` (or the relevant protocol).
- Check any firewall / NAT / bastion rules between the worker and the device.
- Confirm the `PyatsCredential` username / password / enable secret are correct for the device.

### `error` status with `state capture failed: ...`

A state command's parser raised an unexpected exception (not `ParserNotFound`).

- Check the worker's genie install (`pip install netbox-pyats[pyats]` or rebuild the worker image).
- Read the full traceback in the snapshot's `parser_warnings`.
- If the parser is genuinely missing for that os, the device may need a higher Genie version or a different os mapping.

### "PyATS snapshot queued" but no row appears

The `pyats` worker is not running or not servicing the `pyats` queue.

- In the NetBox UI, **Operations → Background Tasks → Workers** should list a worker listening on `pyats`. If none, start the worker (see [Worker deployment](workers.md)).
- Check the worker logs for crash loops or import errors.
- If the worker is up but the job is stuck in `queued`, the worker may not have pyats installed — the capture job imports pyATS lazily and will fail with an import error in the worker logs.

## Diff statuses

### `empty` status

Both snapshots were empty (e.g. two `unsupported`-platform snapshots). This is a neutral outcome, not a failure — a diff row is still created so the device history shows the attempt.

### `error` status

Malformed diff inputs. Read `parser_warnings` for the cause. The diff row is always created so the outcome is visible in-line. Common causes:

- one or both snapshots were deleted between the user clicking "Diff" and the worker picking up the job (the `DoesNotExist` branch now sets `before=None` / `after=None` and records the missing ids in `parser_warnings` — see [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md) and the migration `0008` note in the [changelog](../../CHANGELOG.md)).

## Compliance results

### `error` result with "missing golden config" / "snapshot has no config payload"

- The golden's `config_text` is empty — edit the golden and paste the expected running-config.
- The chosen snapshot is `unsupported` / `error` or has no `config_raw` payload — re-capture a config/full snapshot of a supported platform.

### `drift` when you expected `compliant`

The golden text does not normalize to the same line set as the snapshot's raw running-config text.

- Open the compliance-run detail view; the diff tree shows exactly which leaves diverged — start there.
- v1 is **order-independent** line-set diff: a re-ordered config is still `compliant`, but any added/removed line is `drift`. If you expected order-insensitive compliance and got `drift`, the device really is carrying a line the golden does not (or is missing a line the golden has).
- Trailing whitespace, blank lines, and lone `!` delimiter lines are stripped as noise — those do not cause `drift`.
- If you need order-sensitive compliance (e.g. ACL entry order), that is v2 — see [Compliance engine](compliance.md) for the v1 vs v2 distinction.

### `compliant` when you expected `drift`

The golden and the snapshot's raw text normalize to the same line set. If you expected `drift` from a re-ordered config, that is the v1 order-independent semantics — see [Compliance engine](compliance.md). Order-sensitive drift is deferred to v2.

## Worker / queue

### No worker listening on `pyats`

Start one — see [Worker deployment](workers.md). The default NetBox worker does **not** service the `pyats` queue by design; pyats work is isolated from NetBox's housekeeping jobs.

### Worker is up but jobs are stuck in `queued`

The worker may not have pyats installed. The capture job imports pyATS lazily; a missing install shows as an import error in the worker logs, not as a snapshot `error` row. Install `netbox-pyats[pyats]` on the worker and restart it.

## Still stuck

- Read the job's `parser_warnings` / `parser_warnings` field first — the plugin always records the cause.
- Check the worker logs (`docker compose -f docker-compose.dev.yml logs netbox-pyats-worker` for the dev stack).
- File an issue with the snapshot / diff / compliance-run id, the `parser_warnings`, the worker logs excerpt, and the NetBox + plugin + pyats versions.