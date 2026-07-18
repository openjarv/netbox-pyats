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
- Unit tests: crypto round-trip + key resolution + rotation contract; testbed builder covering platform mapping, mgmt IP resolution, credential attachment, unsupported-flag vs skip, report summary; capture logic covering unsupported/config/state/full/error paths with a stubbed genie. NetBox-dependent model/view/API/snapshot tests skip cleanly when NetBox is absent.
- Local dev environment via `docker-compose.dev.yml` (NetBox 4.6 + PostgreSQL + Redis + dedicated pyats worker).
- CI workflow (GitHub Actions) running the test matrix.

### Compatibility

- NetBox 4.6.x (current: 4.6.5)
- Python 3.10, 3.11, 3.12
- pyATS 26.x (worker only; not required for the web UI)