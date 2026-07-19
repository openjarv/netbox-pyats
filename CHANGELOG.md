# Changelog

All notable changes to netbox-pyats are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- NetBox plugin scaffold (`netbox_pyats/`): `PluginConfig`, `PLUGINS_CONFIG` schema, entry point, navigation menu (PyATS Credentials, Add Credential).
- `PyatsCredential` model with Fernet field-level encryption (`netbox_pyats.crypto`): `password` and `enable_secret` stored as ciphertext; plaintext only lives in-memory on the pyATS `Testbed` built by the worker. Key from `PLUGINS_CONFIG['netbox_pyats']['credential_key']` (recommended) with a documented `SECRET_KEY`-derived dev fallback (warns).
- `PyatsCredential` CRUD views + templates, REST API viewset (write-only secrets — never returned), GraphQL type (ciphertext fields excluded), search index, filterset, table.
- `build_testbed(device_qs)` bridge: materializes a `pyats.topology.Testbed` from a NetBox Device queryset — maps Platform slug → pyATS `os`, resolves mgmt IP from `primary_ip4`/`primary_ip6`, attaches the device's `PyatsCredential`, and **flags unsupported platforms gracefully** (`os = "unsupported - no parser"`) instead of raising. `on_unsupported="flag"` (default) vs `"skip"`.
- `TestbedBuildReport` summary (supported/unsupported counts + reasons) so callers can surface a UI summary without re-iterating the testbed.
- `PyatsSnapshot` model (Phase 2, ATW-13): JSONB `data` + `parser_warnings`, `kind` (config/state/full), `status` (success/unsupported/error), `triggered_by`, `genie_version`/`pyats_version`, `size_bytes`. Indexed by `(device, -captured_at)` and `(device, kind, -captured_at)` for the device-page history and the diff/compliance pickers.
- `capture_snapshot` RQ job (`netbox_pyats.jobs`): builds a one-device testbed, connects via Unicon, runs parser-based config capture (`device.parse('show running-config')`) and/or state capture (a small OS-agnostic command set via `device.parse(...)`, see `STATE_COMMANDS` in `netbox_pyats.capture`), serializes to JSONB, and stores a `PyatsSnapshot` row. Per-command parser misses are recorded as warnings; unsupported platforms short-circuit to an `unsupported` row; capture errors are recorded as `error` rows with the exception text in `parser_warnings` — the row is always created so the device-page history shows the outcome.
- Dedicated `pyats` RQ queue (declared via `NetBoxPyATSConfig.queues`) + worker Dockerfile (`dev/Dockerfile.pyats-worker`) + dev compose service (`netbox-pyats-worker`), isolating pyATS/Genie work from NetBox's default workers. Worker deployment guide in `docs/workers.md`.
- Device-page "PyATS" tab (`PluginTemplateExtension`): capture button (config / state / full) + recent-snapshot history with status badges and a warnings indicator. Unsupported platforms surface a banner before the operator clicks.
- `PyatsSnapshot` list/detail views + templates (JSONB rendered server-side via the `|json` filter), REST API viewset (read-only in v1), GraphQL type, search index, filterset, table.
- `PyatsSnapshotDiff` model (Phase 3, ATW-14): JSONB `diff` (structured tree) + `summary` (added/removed/changed/unchanged counts) + `parser_warnings`, `status` (success/empty/error), `size_bytes`. FKs to `device`, `before` snapshot, `after` snapshot. Indexed by `(device, -created)` and `(device, status, -created)`.
- `diff_snapshots` pure-Python diff engine (`netbox_pyats.diff`): recursive structured diff over the two snapshots' JSONB `data` dicts — added/removed/changed/unchanged leaves, nested dicts, positional lists. JSON-serializable end-to-end, deterministic, testable without Genie installed. Graceful degradation: empty inputs → `status="empty"`, malformed inputs → `status="error"` with a warning.
- `run_diff` RQ job (`netbox_pyats.jobs`): loads two `PyatsSnapshot` rows of the same device, runs `diff_snapshots`, persists a `PyatsSnapshotDiff` row. Enqueued on the dedicated `pyats` queue via `enqueue_diff` (the diff engine itself needs no pyATS, but the queue is shared for isolation and a single worker image). Same-device invariant enforced; missing-snapshot and device-mismatch paths still write an error row.
- Diff viewer view + template (`/plugins/pyats/diffs/<pk>/`): server-rendered collapsible `<details>` tree (no JS) with before/after values for changed leaves, summary badges, raw-JSON fallback, and parser warnings.
- Device-page "PyATS" tab diff picker: select two snapshots of the same device → enqueues `run_diff`. Only offered when the device has ≥2 snapshots. Recent-diffs list with status badges and before→after links.
- `PyatsSnapshotDiff` list/detail/delete/bulk-delete views + REST API viewset (read-only in v1) + GraphQL type + search index + filterset + table + nav menu entry.
- Unit tests: crypto round-trip + key resolution + rotation contract; testbed builder covering platform mapping, mgmt IP resolution, credential attachment, unsupported-flag vs skip, report summary; capture logic covering unsupported/config/state/full/error paths with a stubbed genie; diff engine covering added/removed/changed/unchanged, nested dicts, positional lists, empty/error inputs, JSON-serializability, realistic snapshot payloads. NetBox-dependent model/view/API/snapshot/diff tests skip cleanly when NetBox is absent.
- Local dev environment via `docker-compose.dev.yml` (NetBox 4.6 + PostgreSQL + Redis + dedicated pyats worker).
- CI workflow (GitHub Actions) running the test matrix.

### Compatibility

- NetBox 4.6.x (current: 4.6.5)
- Python 3.10, 3.11, 3.12
- pyATS 26.x (worker only; not required for the web UI)

### Fixed

- Dropped bogus `("dcim", "0050_custom_field_choice_set_remove")` dependency from all three plugin migrations (`0001_initial`, `0002_pyatssnapshot`, `0003_pyatssnapshotdiff`). That dcim migration does not exist in any released NetBox 4.6.x image and raised `NodeNotFoundError` on `manage.py migrate netbox_pyats`. Initial migration now uses `dependencies = []`; later migrations depend only on the prior `netbox_pyats` migration — the NetBox reference-plugin convention (no coupling to NetBox's dcim migration history, which NetBox periodically squashes). See ATW-25 and [ADR-0003](docs/adr/0003-netbox46-migration-and-worker-toolchain.md).
- Added `0004_reconcile_netboxmodel_fields` migration to reconcile the three plugin models with NetBox's `NetBoxModel` base classes, so `manage.py makemigrations netbox_pyats --check --dry-run` reports `No changes` inside NetBox 4.6. The initial migrations (0001-0003) were authored outside a NetBox context and were missing attributes NetBox adds to the inherited `created` / `last_updated` / `custom_field_data` fields (`null=True`, `CustomFieldJSONEncoder`). They also declared `tags` as a plain `ManyToManyField` (auto through-table `netbox_pyats_<model>_tags`) instead of NetBox's `TaggableManager` backed by `extras.TaggedItem`; the new migration swaps the field via `RemoveField`+`AddField` (an `AlterField` cannot change M2M to `TaggableManager`). The Django 5.x cosmetic index-rename suggestions are intentionally NOT applied — the explicit `name=` on the original indexes (now mirrored on the model `Meta`) is the durable form and suppresses the rename suggestions. No model behavior changes. See ATW-32.

### Dev

- `dev/Dockerfile.pyats-worker`: install `python3.14-dev` + `gcc` before `uv pip install pyats[full]` so `ruamel-yaml-clib`'s C extension can build on NetBox 4.6's Python 3.14 slim image. Dev-only build-dep install; the supported runtime matrix (Python 3.10–3.12) is unchanged (cp312 wheel exists for production). See ATW-25 and [ADR-0003](docs/adr/0003-netbox46-migration-and-worker-toolchain.md).