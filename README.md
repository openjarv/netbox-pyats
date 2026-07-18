# netbox-pyats

Atw NetBox plugin that brings Cisco **PyATS / Genie** into the NetBox UI: capture
device config & state snapshots, diff them structurally, and run config
compliance checks — all from the device page, with NetBox-native credentials and
multi-vendor coverage bounded by Genie's own parser support.

This is **Phase 1** of the v1 build plan: plugin scaffold, encrypted
credential model, and the dynamic testbed builder that materializes a pyATS
`Testbed` from the NetBox ORM. Snapshot/diff/compliance pipelines ship in
later phases.

## What this phase ships

- `netbox_pyats` plugin package: `PluginConfig`, nav menu, templates, migration.
- `PyatsCredential` model with **field-level Fernet encryption** for `password`
  and `enable_secret`. Key resolved from `PLUGINS_CONFIG['netbox_pyats']['credential_key']`,
  failing over to a slice of NetBox `SECRET_KEY`.
- `build_testbed(device_qs)` utility: builds a pyATS `Testbed` from a NetBox
  `Device` queryset, resolving management IP, platform → pyATS `os`, and the
  matching `PyatsCredential`. Devices whose platform has no Genie parser are
  surfaced as `unsupported - no parser` rather than blocking the run.
- Pure-Python unit tests (encryption round-trip, testbed builder against
  fixture devices with mocked Unicon).

## NetBox compatibility

| NetBox | Python | Status |
|---|---|---|
| 4.6+ (current 4.6.5) | 3.10 / 3.11 / 3.12 | tested (unit) |

## Install (dev)

```bash
pip install -e .[dev]
pytest
```

In NetBox `configuration.py`:

```python
PLUGINS = ["netbox_pyats"]
PLUGINS_CONFIG = {
    "netbox_pyats": {
        # Recommended: dedicated Fernet key. Generate with:
        #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        "credential_key": "REPLACE_ME_FERNET_KEY",
        # Failover key path (only used if credential_key is not set):
        # a slice of NetBox SECRET_KEY is used.
    },
}
```

Run migrations: `python manage.py migrate netbox_pyats`.

## Architecture

```
NetBox ORM (Device/Interface/IPAddress/Platform) + PyatsCredential
        │
        ▼  build_testbed(device_qs)
pyATS Testbed (devices, connections, os, credentials)
        │
        ▼  (later phases: Genie.learn / parsers → JSONB snapshots → diff → compliance)
```

Multi-vendor: the platform → `os` map covers the platforms Genie parsers
support (Cisco IOS/XE/XR/NX-OS, Juniper JunOS, Arista EOS, Nokia SR OS, …).
Platforms outside that map are flagged `unsupported - no parser` and skipped
in batch runs (graceful degradation).

## License

Apache-2.0. See [LICENSE](LICENSE).

## Status

Phase 1 of [ATW-10 build plan](https://github.com/openjarv/netbox-pyats) —
scaffold + credentials + dynamic testbed. Snapshot/diff/compliance follow.