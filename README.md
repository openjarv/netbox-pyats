# netbox-pyats

An [Atw](https://github.com/openjarv) [NetBox](https://netbox.dev) plugin that brings [Cisco PyATS / Genie](https://developer.cisco.com/pyats/) into the NetBox UI — dynamic testbed building from the NetBox ORM, plugin-local encrypted credentials, device snapshots stored as JSONB, and (in later phases) structured diffs and config compliance from the device page.

> **Phase 2 (this release):** everything in Phase 1, plus the snapshot capture pipeline — a `PyatsSnapshot` model (JSONB), a `capture_snapshot` RQ job running `Genie.learn` + parser-based config capture on a dedicated `pyats` RQ queue, and a "PyATS" tab on the Device detail page with a "Capture snapshot" button and recent-snapshot history. Diff and compliance land in subsequent phases (see the ATW-10 build plan).

## What it does

Real-world NetBox deployments already have device inventories. PyATS needs a testbed to talk to those devices, but maintaining a static YAML testbed alongside NetBox duplicates the source of truth. `netbox-pyats` builds the testbed directly from the NetBox ORM at runtime — the NetBox device record *is* the testbed.

Phase 2 ships:

- **`PyatsCredential` model** — plugin-local, Fernet-encrypted device credentials (password + enable secret). Never exposed via REST, GraphQL, or the detail view; only ciphertext is persisted.
- **`build_testbed(device_qs)`** — constructs a `pyats.topology.Testbed` from a NetBox Device queryset: maps Platform → pyATS `os`, resolves the management IP from `primary_ip4`/`primary_ip6`, attaches the device's `PyatsCredential`, and **flags unsupported platforms gracefully** (`os = "unsupported - no parser"`) rather than crashing batch runs.
- **`PyatsSnapshot` model + `capture_snapshot` RQ job** — click "Capture snapshot" on a device's PyATS tab and the worker connects via Unicon, runs `Genie.learn` (state) and/or parser-based config capture, and stores the result as JSONB. Devices without Genie parser support are surfaced as `unsupported` in the history (a row is still created) rather than failing the run. Capture errors are recorded as `error` rows with the exception text in `parser_warnings`.
- **Dedicated `pyats` RQ queue + worker** — pyATS/Genie work runs on its own queue (declared via `NetBoxPyATSConfig.queues`), isolated from NetBox's default workers. The default NetBox worker does not need pyATS installed; run a second worker pointed at `pyats` (see `dev/Dockerfile.pyats-worker` and [docs/workers.md](docs/workers.md)).
- **Device-page "PyATS" tab** — capture button (config / state / full) + the most recent snapshots for the device, with status badges and a warnings indicator.
- **CRUD + REST + GraphQL** for credentials and snapshots, all under `/plugins/pyats/`.

## Compatibility matrix

| netbox-pyats | NetBox | Python | pyATS |
|-------------|--------|--------|-------|
| 0.1.x       | 4.6.x  | 3.10, 3.11, 3.12 | 26.x (worker only) |

The plugin targets NetBox 4.6+ (current: 4.6.5). `pyats[full]` is **not** an install-time dependency — it is heavy and pulls Cython binaries that may not match every NetBox deployment. Install it on the worker that runs snapshots (see `pip install netbox-pyats[pyats]` or the worker docs). The NetBox web process imports the plugin without pyats installed; the testbed builder imports pyATS lazily.

## Installation

```bash
pip install netbox-pyats
```

Add the plugin to your NetBox configuration (`/etc/netbox/configuration.py`):

```python
PLUGINS = [
    "netbox_pyats",
]

PLUGINS_CONFIG = {
    "netbox_pyats": {
        # Recommended: a dedicated Fernet key for encrypting credential secrets.
        # Generate one with:
        #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        # If unset, the plugin derives a key from a slice of SECRET_KEY (dev only; warns).
        "credential_key": "",
    },
}
```

Run database migrations and restart NetBox:

```bash
cd /opt/netbox
python manage.py migrate
sudo systemctl restart netbox netbox-rq
```

### Installing pyATS on the worker (required for snapshots)

The plugin's web UI (credential CRUD, list/detail views, snapshot list) works without pyATS. To actually capture snapshots, the RQ worker that runs pyATS jobs needs pyATS installed. The plugin declares a dedicated `pyats` RQ queue (via `NetBoxPyATSConfig.queues`) so pyATS work is isolated from NetBox's default workers — run a second worker pointed at the `pyats` queue:

```bash
# On the worker host (or build the worker image — see dev/Dockerfile.pyats-worker):
pip install netbox-pyats[pyats]   # pulls pyats[full] >= 26.0
python manage.py rqworker pyats
```

See [docs/workers.md](docs/workers.md) for the full worker deployment guide, and `dev/Dockerfile.pyats-worker` for a ready-to-build worker image.

## Usage (Phase 2)

1. **Add a credential** at **Plugins → PyATS → Add Credential**. Pick a device, enter username + password (+ optional enable secret). The secrets are encrypted with Fernet before they hit the database.
2. **Capture a snapshot** from a device's detail page → **PyATS** tab → pick a kind (config / state / full) → **Capture**. The job is enqueued on the `pyats` queue; the snapshot appears in the tab's recent-snapshots list when the worker finishes.
3. **Browse snapshots** under **Plugins → PyATS → PyATS Snapshots** (filterable by device, kind, status). The detail view renders the JSONB payload and any parser warnings.
4. **Build a testbed programmatically** (the snapshot pipeline does this internally):

```python
from netbox_pyats.testbed import build_testbed
from dcim.models import Device

device_qs = Device.objects.filter(site__slug="ams01")
testbed, report = build_testbed(device_qs)
print(report.summary())   # "2 supported, 1 unsupported (3 total)"
for entry in report.unsupported:
    print(entry["name"], entry["reason"])
# pyATS Testbed is ready for `testbed.connect()` / `Genie(device).learn(...)`.
```

Unsupported platforms (no Genie parser) are surfaced as `unsupported` snapshot rows in the device-page history rather than failing the capture; capture errors are recorded as `error` rows with the exception text in `parser_warnings`.

## Credential encryption

- **Recommended:** set `PLUGINS_CONFIG['netbox_pyats']['credential_key']` to a dedicated Fernet key (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
- **Dev fallback:** if `credential_key` is unset, the plugin derives a stable key from a slice of NetBox's `SECRET_KEY` and emits a `RuntimeWarning`. This is acceptable for dev but **must not** ship to production.
- **Rotation:** changing `credential_key` means existing ciphertext can no longer be decrypted (Fernet is symmetric + authenticated). Re-key credentials after rotating (v1 ships a management note; an automated re-key command is planned).
- Secrets are **never** returned by the REST API, GraphQL, or the detail view template. Only the ciphertext is persisted; only the in-memory pyATS `Testbed` object (built on the worker) ever holds plaintext, for the lifetime of the connection.

## Multi-vendor support

Genie parsers cover Cisco IOS/XE/XR/NX-OS/ASA, Juniper JunOS, Arista EOS, and Nokia SR OS. The plugin maps NetBox Platform slugs to pyATS `os` strings (see `netbox_pyats/testbed.py`). Platforms with no matching Genie parser are surfaced with `os = "unsupported - no parser"` and `custom['netbox_pyats']['supported'] = False` — they are included on the testbed by default (`on_unsupported="flag"`) so the UI can show them as unsupported; pass `on_unsupported="skip"` to omit them silently in batch runs.

Adding a slug to the map is a commitment that Genie has real parser coverage for that os; unknown slugs degrade gracefully rather than silently producing empty snapshots.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local dev setup, tests, and lint.

```bash
# Pure-Python tests (no NetBox DB needed)
pip install -e ".[dev]"
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py

# Full NetBox test suite (integration)
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## License

Apache-2.0. See [LICENSE](LICENSE).