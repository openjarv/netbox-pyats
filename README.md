# netbox-pyats

An [Atw](https://github.com/openjarv) [NetBox](https://netbox.dev) plugin that brings [Cisco PyATS / Genie](https://developer.cisco.com/pyats/) into the NetBox UI — dynamic testbed building from the NetBox ORM, plugin-local encrypted credentials, device snapshots stored as JSONB, structured snapshot diffs, and (in later phases) config compliance from the device page.

> **Phase 3 (this release):** everything in Phases 1–2, plus the snapshot diff engine — a `PyatsSnapshotDiff` model (JSONB structured diff tree), a `run_diff` RQ job running a pure-Python recursive diff over two snapshots' JSONB on the dedicated `pyats` queue, a diff viewer (server-rendered collapsible tree, no JS), and a "Diff two snapshots" picker on the Device page PyATS tab. Compliance lands in a subsequent phase (see the ATW-10 build plan).

## What it does

Real-world NetBox deployments already have device inventories. PyATS needs a testbed to talk to those devices, but maintaining a static YAML testbed alongside NetBox duplicates the source of truth. `netbox-pyats` builds the testbed directly from the NetBox ORM at runtime — the NetBox device record *is* the testbed.

Phase 3 ships:

- **`PyatsCredential` model** — plugin-local, Fernet-encrypted device credentials (password + enable secret). Never exposed via REST, GraphQL, or the detail view; only ciphertext is persisted.
- **`build_testbed(device_qs)`** — constructs a `pyats.topology.Testbed` from a NetBox Device queryset: maps Platform → pyATS `os`, resolves the management IP from `primary_ip4`/`primary_ip6`, attaches the device's `PyatsCredential`, and **flags unsupported platforms gracefully** (`os = "unsupported - no parser"`) rather than crashing batch runs.
- **`PyatsSnapshot` model + `capture_snapshot` RQ job** — click "Capture snapshot" on a device's PyATS tab and the worker connects via Unicon, runs `device.parse('show running-config')` (config) and/or a small OS-agnostic state command set via `device.parse(...)` (state), and stores the parsed result as JSONB. Devices without Genie parser support are surfaced as `unsupported` in the history (a row is still created) rather than failing the run. Capture errors are recorded as `error` rows with the exception text in `parser_warnings`.
- **`PyatsSnapshotDiff` model + `run_diff` RQ job** — pick any two snapshots of the same device from the PyATS tab and the worker runs a structured recursive diff over their JSONB `data`, storing the diff tree + a flat summary (added/removed/changed/unchanged counts) as a `PyatsSnapshotDiff` row. The diff engine is pure-Python (no Genie needed — the snapshots are already-serialized JSONB, so `Genie.diff` isn't applicable); it degrades gracefully (empty inputs → `status="empty"`, malformed inputs → `status="error"` with a warning, row always created).
- **Dedicated `pyats` RQ queue + worker** — pyATS/Genie work runs on its own queue (declared via `NetBoxPyATSConfig.queues`), isolated from NetBox's default workers. The default NetBox worker does not need pyATS installed; run a second worker pointed at `pyats` (see `dev/Dockerfile.pyats-worker` and [docs/workers.md](docs/workers.md)). The diff job itself needs no pyATS, but runs on the `pyats` queue for isolation and a single worker image.
- **Device-page "PyATS" tab** — capture button (config / state / full), recent-snapshot history with status badges and a warnings indicator, "Diff two snapshots" picker (offered when the device has ≥2 snapshots), and a recent-diffs list.
- **Diff viewer** (`/plugins/pyats/diffs/<pk>/`) — server-rendered collapsible `<details>` tree (no JS): changed subtrees open by default, unchanged ones collapsed; before/after values shown side-by-side for changed leaves; raw-JSON fallback; summary badges; parser warnings.
- **CRUD + REST + GraphQL** for credentials, snapshots, and diffs, all under `/plugins/pyats/`.

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

## Usage (Phase 3)

1. **Add a credential** at **Plugins → PyATS → Add Credential**. Pick a device, enter username + password (+ optional enable secret). The secrets are encrypted with Fernet before they hit the database.
2. **Capture a snapshot** from a device's detail page → **PyATS** tab → pick a kind (config / state / full) → **Capture**. The job is enqueued on the `pyats` queue; the snapshot appears in the tab's recent-snapshots list when the worker finishes.
3. **Diff two snapshots** from the same device's **PyATS** tab → **Diff two snapshots** picker → pick a before and an after snapshot → **Diff**. The job is enqueued on the `pyats` queue; the diff appears in the tab's recent-diffs list when the worker finishes. Open it to see a collapsible tree of added/removed/changed/unchanged leaves, with before/after values side-by-side for changed leaves, plus a flat summary of counts.
4. **Browse snapshots and diffs** under **Plugins → PyATS → PyATS Snapshots** and **PyATS Snapshot Diffs** (filterable by device, status, etc.). The detail views render the JSONB payload and any parser warnings.
5. **Build a testbed programmatically** (the snapshot pipeline does this internally):

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

Unsupported platforms (no Genie parser) are surfaced as `unsupported` snapshot rows in the device-page history rather than failing the capture; capture errors are recorded as `error` rows with the exception text in `parser_warnings`. Diffing two empty (unsupported-platform) snapshots yields a diff row with `status="empty"` (neutral badge) rather than erroring; malformed diff inputs yield `status="error"` with a warning — the diff row is always created so the outcome is visible in-line.

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
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py netbox_pyats/tests/test_diff.py

# Full NetBox test suite (integration)
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## CI

CI runs on every push to `main` and every PR via [.github/workflows/ci.yml](.github/workflows/ci.yml):

- **lint** — `black --check`, `isort --check-only`, `flake8` (Python 3.12).
- **unit** — pure-Python tests on the compatibility-matrix Python versions (3.10 / 3.11 / 3.12) with `pyats[full]` installed so the testbed suite runs instead of skipping. No NetBox / PostgreSQL / Redis required.
- **integration** — full NetBox-dependent suite inside the dev container (`docker-compose.dev.yml`). Wired but **non-gating** until the NetBox 4.6 dev-image compatibility work (ATW-25) lands; the stock `netboxcommunity/netbox:v4.6` image ships Python 3.14, which is outside the plugin's compatibility matrix.

## License

Apache-2.0. See [LICENSE](LICENSE).