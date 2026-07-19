# ADR-0002: Multi-vendor graceful degradation pattern

Date: 2026-07-19
Status: Accepted (CTO; CEO sign-off via [ATW-23](/ATW/issues/ATW-23) confirmation `26b21df4`)
Supersedes: —
Superseded by: —

## Context

The plugin's core promise is reducing NetBox population friction across **real-world, multi-vendor** estates. Real estates contain unsupported platforms, parser gaps, and devices that are temporarily unreachable. If the capture/diff pipeline crashed on any of these, operators would lose the per-device history they came here for, and a single bad device would poison a batch run.

Phase 2 (capture) and Phase 3 (diff) shipped a graceful-degradation pattern that always writes a row, never crashes the worker, and surfaces outcomes through a status badge in the UI. This ADR locks that pattern so every future code path — compliance runs, batch capture, global credential resolution — follows it without redesign.

## Decision

Every code path that reaches out to a device, parses output, or compares two snapshots **always writes a row** and **never raises** into the worker. Outcomes are communicated via a `status` `TextChoices` field with a NetBox color mapping, plus a `parser_warnings` JSONB field for diagnostics.

### Status vocabulary (locked)

| Path | Status | Meaning | Color intent |
|---|---|---|---|
| capture | `success` | Clean capture, all commands parsed | green |
| capture | `unsupported` | NetBox Platform slug not in `PLATFORM_SLUG_TO_PYATS_OS`; no connection attempted | neutral/grey |
| capture | `error` | Connection failure or unhandled exception; traceback in `parser_warnings` | red |
| diff | `success` | Clean diff produced | green |
| diff | `empty` | One or both inputs empty (e.g. first snapshot, or unsupported source) — neutral, not an error | neutral |
| diff | `error` | Malformed inputs, or same-device invariant violated; row still written | red |

New status values may be added only via a follow-up ADR that extends this table.

### Testbed builder (`testbed.py`)

- `PLATFORM_SLUG_TO_PYATS_OS` maps NetBox Platform slugs → pyATS `os`. **A slug is added only when Genie has real parser coverage.** Silently mapping an unsupported os produces empty snapshots and misleads operators.
- Unknown/unsupported platforms map to `os = "unsupported - no parser"` with `custom['netbox_pyats']['supported'] = False`.
- The builder accepts `on_unsupported`:
  - `"flag"` (default) — the device is included with the unsupported flag; visible in the UI; used for interactive per-device runs.
  - `"skip"` — the device is silently excluded; used for batch runs where the operator only wants supported devices.
- A re-key/rotation of this map (e.g. renaming a slug) is a data migration, not a code-only change.

### Capture path (`capture.py` + `jobs.py`)

- Unsupported device → `status="unsupported"` row is written; **no connection is attempted**.
- Parser miss on an individual command → per-command warning is appended to `parser_warnings`, the value for that command is `None`, and the row is still `success` (partial capture is better than no row).
- Connection failure → `status="error"` row is written with the full traceback in `parser_warnings`.
- Unhandled exception in the job callable → `status="error"` row is written; the exception is never re-raised into the worker.

### Diff path (`diff.py` + `jobs.py`)

- Empty inputs (one or both snapshots missing, or one is `unsupported`) → `status="empty"` (neutral badge). **This is not an error** — the operator's first snapshot legitimately has nothing to diff against.
- Malformed inputs → `status="error"` with a warning in `parser_warnings`.
- Same-device invariant: a diff is only valid between two snapshots of the **same device**. A cross-device diff attempt still writes a row with `status="error"` and a clear warning, rather than raising.

### UI contract

- The device-page "PyATS" tab and the list tables render `status` with `get_status_color()` mapped to NetBox color labels.
- `parser_warnings` is viewable from the detail page (collapsible). It is never empty for `error` rows.
- An operator scanning the device page can always tell, at a glance, what happened on the last run — without opening a log.

## Consequences

- **Positive:** batch runs are resilient: one bad device never aborts a 500-device sweep. The per-device history is always intact. Operators can trust the UI as the source of truth for "what happened last time".
- **Positive:** the pattern composes — the upcoming compliance run model will reuse the exact same status vocabulary and write-a-row contract, so ADR-0003 (compliance) inherits this instead of redesigning it.
- **Negative:** the data model carries a `parser_warnings` JSONB on every row, including success rows (empty). This is intentional: diagnostics must be co-located with the outcome, not in a separate log the operator has to find.
- **Negative:** the "always write a row" contract means callers that enqueue a job cannot assume a missing row means "not run yet" — it can also mean "enqueued but not yet persisted". The UI uses the NetBox `Job` status (from `core.models.Job.enqueue`) for the in-flight state, and the plugin row for the persisted outcome.

## Alternatives considered

- **Crash-on-error and let RQ retry.** Rejected: RQ retry does not produce a persisted row, so the operator loses per-device history on the exact devices that are most likely to fail (unsupported, unreachable). The whole point of the plugin is that the row survives.
- **Silent skip for unsupported devices.** Rejected for the default path: operators need to *see* that a device was skipped and why, especially in interactive per-device runs. `on_unsupported="skip"` exists as an opt-in for batch runs where the operator has already filtered.
- **Separate `Error` model for diagnostics.** Rejected: co-locating `parser_warnings` on the outcome row keeps the UI query to a single table and avoids a join for the common case. The JSONB is small in practice (only populated on `error`/partial).

## References

- Architecture overview, §2.7: [ATW-23 architecture document](/ATW/issues/ATW-23#document-architecture)
- `netbox_pyats/testbed.py`, `netbox_pyats/capture.py`, `netbox_pyats/diff.py`, `netbox_pyats/jobs.py`
- Related: ADR-0001 (plugin layout), future ADR-0003 (compliance model — expected to extend this status vocabulary)