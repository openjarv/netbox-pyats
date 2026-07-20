# netbox-pyats

An [Atw](https://github.com/openjarv) [NetBox](https://netbox.dev) plugin that brings [Cisco PyATS / Genie](https://developer.cisco.com/pyats/) into the NetBox UI — dynamic testbed building from the NetBox ORM, plugin-local encrypted credentials, device snapshots stored as JSONB, structured snapshot diffs, and config compliance from the device page.

> **Phase 4 (this release):** everything in Phases 1–3, plus the compliance engine — a `PyatsGoldenConfig` model (operator-authored golden running-config text per device), a `PyatsComplianceRun` model (JSONB structured diff tree + summary, same shape as `PyatsSnapshotDiff`), a `run_compliance` RQ job running on the dedicated `pyats` queue, a compliance viewer (reuses the Phase 3 diff-tree partial), and a "Run compliance" picker on the Device page PyATS tab. The golden config text is parsed on the worker with the same Genie parser the snapshot used (no live device connection), so both sides are in the same structured shape and the compliance classification is meaningful. See [ADR-0004](docs/adr/0004-compliance-comparison-shape.md) for the comparison-shape decision.

## What it does

Real-world NetBox deployments already have device inventories. PyATS needs a testbed to talk to those devices, but maintaining a static YAML testbed alongside NetBox duplicates the source of truth. `netbox-pyats` builds the testbed directly from the NetBox ORM at runtime — the NetBox device record *is* the testbed.

Phase 4 ships:

- **`PyatsCredential` model** — plugin-local, Fernet-encrypted device credentials (password + enable secret). Never exposed via REST, GraphQL, or the detail view; only ciphertext is persisted.
- **`build_testbed(device_qs)`** — constructs a `pyats.topology.Testbed` from a NetBox Device queryset: maps Platform → pyATS `os`, resolves the management IP from `primary_ip4`/`primary_ip6`, attaches the device's `PyatsCredential`, and **flags unsupported platforms gracefully** (`os = "unsupported - no parser"`) rather than crashing batch runs.
- **`PyatsSnapshot` model + `capture_snapshot` RQ job** — click "Capture snapshot" on a device's PyATS tab and the worker connects via Unicon, runs `device.parse('show running-config')` (config) and/or a small OS-agnostic state command set via `device.parse(...)` (state), and stores the parsed result as JSONB. Devices without Genie parser support are surfaced as `unsupported` in the history (a row is still created) rather than failing the run. Capture errors are recorded as `error` rows with the exception text in `parser_warnings`. The snapshot's `parsed_os` field records the Genie parser's os for compliance reuse.
- **`PyatsSnapshotDiff` model + `run_diff` RQ job** — pick any two snapshots of the same device from the PyATS tab and the worker runs a structured recursive diff over their JSONB `data`, storing the diff tree + a flat summary (added/removed/changed/unchanged counts) as a `PyatsSnapshotDiff` row. The diff engine is pure-Python (no Genie needed — the snapshots are already-serialized JSONB, so `Genie.diff` isn't applicable); it degrades gracefully (empty inputs → `status="empty"`, malformed inputs → `status="error"` with a warning, row always created).
- **`PyatsGoldenConfig` model + `PyatsComplianceRun` model + `run_compliance` RQ job** — author a golden running-config per device (plain text or promoted from a snapshot), pick a golden + snapshot on the device's PyATS tab, and the worker parses the golden text with the same Genie parser the snapshot used (no live device), diffs golden vs. snapshot config, and classifies as `compliant` / `drift` / `error`. The diff tree reuses the Phase 3 viewer. Compliance history uses `SET_NULL` FKs so it survives golden/snapshot deletion.
- **Dedicated `pyats` RQ queue + worker** — pyATS/Genie work runs on its own queue (declared via `NetBoxPyATSConfig.queues`), isolated from NetBox's default workers. The default NetBox worker does not need pyATS installed; run a second worker pointed at `pyats` (see `dev/Dockerfile.pyats-worker` and [docs/workers.md](docs/workers.md)). The diff job needs no pyATS but runs on the `pyats` queue for isolation; the compliance job needs Genie (to re-parse the golden text) and runs on the `pyats` queue where `pyats[full]` is installed.
- **Device-page "PyATS" tab** — capture button (config / state / full), recent-snapshot history with status badges and a warnings indicator, "Diff two snapshots" picker (offered when the device has ≥2 snapshots), "Run compliance" picker (offered when the device has ≥1 golden config and ≥1 config/full snapshot), and recent-diffs + recent-compliance-runs lists.
- **Diff viewer** (`/plugins/pyats/diffs/<pk>/`) and **compliance viewer** (`/plugins/pyats/compliance/<pk>/`) — server-rendered collapsible `<details>` tree (no JS): changed subtrees open by default, unchanged ones collapsed; before/after values shown side-by-side for changed leaves; raw-JSON fallback; summary badges; parser warnings. The compliance viewer reuses the Phase 3 diff-tree partial.
- **CRUD + REST + GraphQL** for credentials, snapshots, diffs, golden configs, and compliance runs, all under `/plugins/pyats/`.

## Compatibility matrix

| netbox-pyats | NetBox | Python | pyATS |
|-------------|--------|--------|-------|
| 0.1.x       | 4.6.x  | 3.10, 3.11, 3.12 | 26.x (worker only) |

The plugin targets NetBox 4.6+ (current: 4.6.5). `pyats[full]` is **not** an install-time dependency — it is heavy and pulls Cython binaries that may not match every NetBox deployment. Install it on the worker that runs snapshots (see `pip install netbox-pyats[pyats]` or the worker docs). The NetBox web process imports the plugin without pyats installed; the testbed builder imports pyATS lazily.

> **Note on the community Docker image:** `netboxcommunity/netbox:4.6.x` ships Python 3.14 (Ubuntu 26.04). The plugin and its migrations apply cleanly against that image (verified on `v4.6-5.0.2`). The pyats worker image needs `python3.14-dev` + `gcc` to compile `ruamel-yaml-clib` against Python 3.14 — `dev/Dockerfile.pyats-worker` installs them as a dev-only build step. See [ADR-0003](docs/adr/0003-netbox46-migration-and-worker-toolchain.md) for the rationale.

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
5. **Run compliance** from a device's **PyATS** tab → **Run compliance** picker → pick a golden config + a config/full snapshot → **Run**. The worker parses the golden text with the same Genie parser the snapshot used (no live device), diffs golden vs. snapshot config, and classifies as `compliant` / `drift` / `error`. Open the compliance run to see the same collapsible diff tree as the snapshot diff viewer, with before/after values for changed leaves.
6. **Author golden configs** under **Plugins → PyATS → PyATS Golden Configs** (plain text, or promote from a snapshot via the "use snapshot as golden" flow).
7. **Build a testbed programmatically** (the snapshot pipeline does this internally):

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

## Compliance engine

The compliance engine compares an operator-authored **golden config** (the "expected" running config) against a captured **snapshot's** parsed config payload and classifies the device as `compliant` (no drift), `drift` (differences found), or `error` (bad inputs / unsupported platform / job raised). The structured diff tree is stored as JSONB on a `PyatsComplianceRun` row and rendered with the same Phase 3 diff-tree viewer partial — zero new rendering code.

**How the golden is parsed:** the golden config text is a plain text field (operator-authored or promoted from a snapshot). At compliance-run time, the `run_compliance` RQ job parses it on the `pyats` worker with the **same Genie parser the snapshot used** — `parse_golden_config_text(text, os=snapshot.parsed_os)` constructs a minimal in-memory `pyats.topology.Device` with `os=<os>` and calls `device.parse("show running-config", output=text)`. No live device connection is opened; the parser harness feeds the golden text directly. This produces a Genie abstract-config dict in the same shape as `snapshot.data["config"]`, so the Phase 3 `diff_snapshots` engine can diff them directly and the result is meaningful.

**OS provenance:** the snapshot's `parsed_os` field (set at capture time from the device's platform mapping) records which Genie parser was used. Compliance runs use it to select the same parser for the golden text. If the device is deleted after capture, compliance history still works because `parsed_os` is stored on the snapshot row.

**Why not parse on save (Option 2) or line-oriented both sides (Option 3):** see [ADR-0004](docs/adr/0004-compliance-comparison-shape.md). The short version: parse-on-save breaks the ADR-0003 invariant that the web process is Genie-free, and line-oriented-both-sides loses the structured diff tree that is the entire justification for reusing the Phase 3 viewer.

**Compliance history survives deletion:** `PyatsComplianceRun.golden` and `.snapshot` use `on_delete=SET_NULL` (not `CASCADE`) so deleting a golden config or snapshot does not wipe the compliance history — the row stays with `golden=None`/`snapshot=None`, preserving the audit trail.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local dev setup, tests, and lint.

```bash
# Pure-Python tests (no NetBox DB needed)
pip install -e ".[dev,pyats]"
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py netbox_pyats/tests/test_diff.py netbox_pyats/tests/test_capture.py netbox_pyats/tests/test_compliance.py netbox_pyats/tests/test_golden_parse.py

# Full NetBox test suite (integration)
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## CI

CI runs on every push to `main` and every PR via [.github/workflows/ci.yml](.github/workflows/ci.yml):

- **lint** — `black --check`, `isort --check-only`, `flake8` (Python 3.12).
- **unit** — pure-Python tests on the compatibility-matrix Python versions (3.10 / 3.11 / 3.12) with `pyats[full]` installed so the testbed, compliance, and golden-parse suites run instead of skipping. No NetBox / PostgreSQL / Redis required.
- **integration** — full NetBox-dependent suite inside the dev container (`docker-compose.dev.yml`). Gating since ATW-38 resolved the NetBox 4.6.5 compatibility bugs (PR #15) and the dev image builds `pyats[full]` and applies the plugin migrations.

## License

Apache-2.0. See [LICENSE](LICENSE).