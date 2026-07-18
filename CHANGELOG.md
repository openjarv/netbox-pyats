# Changelog

All notable changes to netbox-pyats are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/) and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Phase 1 — scaffold, credentials, dynamic testbed builder

- Added `netbox_pyats` plugin package (`PluginConfig`, nav menu, templates, migration).
- Added `PyatsCredential` model with field-level Fernet encryption for `password`
  and `enable_secret`; key from `PLUGINS_CONFIG['netbox_pyats']['credential_key']`
  with failover to a `SECRET_KEY` slice.
- Added `build_testbed(device_qs)` utility that materializes a pyATS `Testbed`
  from NetBox ORM rows + resolved credentials; multi-vendor platform→`os` map;
  unsupported platforms flagged as `unsupported - no parser`.
- Added pure-Python unit tests (encryption round-trip, testbed builder against
  fixture devices with mocked Unicon).