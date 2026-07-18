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
- Unit tests: crypto round-trip + key resolution + rotation contract; testbed builder covering platform mapping, mgmt IP resolution, credential attachment, unsupported-flag vs skip, report summary. NetBox-dependent model/view/API tests skip cleanly when NetBox is absent.
- Local dev environment via `docker-compose.dev.yml` (NetBox 4.6 + PostgreSQL + Redis).
- CI workflow (GitHub Actions) running the test matrix.

### Compatibility

- NetBox 4.6.x (current: 4.6.5)
- Python 3.10, 3.11, 3.12
- pyATS 26.x (worker only; not required for the web UI)