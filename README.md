# netbox-pyats

> **⚠️ Early development — AI-built.**
> This plugin is in **very early development**, is **built purely by AI**, and has **not yet been hardened or audited**. Use it **at your own risk**, and do not deploy it against production NetBox instances without thorough review and your own validation.

An [Atw](https://github.com/openjarv) [NetBox](https://netbox.dev) plugin that brings [Cisco PyATS / Genie](https://developer.cisco.com/pyats/) into the NetBox UI — dynamic testbed building from the NetBox ORM, plugin-local encrypted credentials, device snapshots stored as JSONB, structured snapshot diffs, and config compliance (golden config vs. snapshot) from the device page.

## What it does

**netbox-pyats** turns your NetBox device inventory into a live PyATS testbed — no static YAML testbed to maintain. From each device's page you can capture running-config and state snapshots, diff any two snapshots, and check a captured config against a golden config for compliance. Every snapshot, diff, and compliance run is stored inside NetBox as a first-class record, so you get a permanent, queryable history for pre/post-change checks and config-compliance audits.

Real-world NetBox deployments already have device inventories. PyATS needs a testbed to talk to those devices, but maintaining a static YAML testbed alongside NetBox duplicates the source of truth. `netbox-pyats` builds the testbed directly from the NetBox ORM at runtime — the NetBox device record *is* the testbed.

v0.1 ships:

### Capture

- **`PyatsCredential` model** — plugin-local, Fernet-encrypted device credentials (password + enable secret). Never exposed via REST, GraphQL, or the detail view; only ciphertext is persisted.
- **`build_testbed(device_qs)`** — constructs a `pyats.topology.Testbed` from a NetBox Device queryset: maps Platform → pyATS `os`, resolves the management IP from `primary_ip4`/`primary_ip6`, attaches the device's `PyatsCredential`, and **flags unsupported platforms gracefully** (`os = "unsupported - no parser"`) rather than crashing batch runs.
- **`PyatsSnapshot` model + `capture_snapshot` RQ job** — click "Capture snapshot" on a device's PyATS tab and the worker connects via Unicon, runs `device.parse('show running-config')` (config) and/or a small OS-agnostic state command set via `device.parse(...)` (state), and stores the parsed result as JSONB. Devices without Genie parser support are surfaced as `unsupported` in the history (a row is still created) rather than failing the run. Capture errors are recorded as `error` rows with the exception text in `parser_warnings`. Each snapshot also carries `parsed_os` (the pyATS os string used by the capture, e.g. `iosxe`/`iosxr`/`nxos`) so future v2 structured compliance can pick the right Genie parser even after the device row is deleted.
- **Batch capture** — select a set of devices on the NetBox device list and pick "PyATS capture" from the bulk-action menu; the worker iterates the device set, reuses `build_testbed(on_unsupported="skip")` + `capture_snapshot_for_netbox_device`, and writes one `PyatsSnapshot` per supported device. Unsupported platforms and per-device capture failures are counted (`{supported, unsupported, errored, total}`) and the `PyatsJob` is `partial` when any device did not capture cleanly, `success` when all did. Deleted-between-enqueue-and-run devices are silently skipped.
- **Supported-platforms report** (`/plugins/pyats/supported-platforms/`) — web-process-safe (no Genie import, per ADR-0001 §6): renders the static `PLATFORM_SLUG_TO_PYATS_OS` map the testbed builder uses, with a per-slug NetBox device count and an "unsupported" + "no platform" summary count so operators can see what a batch capture will reach. Live Genie introspection is v2; v1 ships the static map the capture job actually uses.
- **Dedicated `pyats` RQ queue + worker** — pyATS/Genie work runs on its own queue (declared via `NetBoxPyATSConfig.queues`), isolated from NetBox's default workers. The default NetBox worker does not need pyATS installed; run a second worker pointed at `pyats` (see `dev/Dockerfile.pyats-worker` and [docs/user/workers.md](docs/user/workers.md)). The diff and compliance jobs themselves need no pyATS (they operate on already-serialized JSONB), but run on the `pyats` queue for isolation and a single worker image. An operator who only wants diffs/compliance can run the default worker if they prefer.

### Compare

- **`PyatsSnapshotDiff` model + `run_diff` RQ job** — pick any two snapshots of the same device from the PyATS tab and the worker runs a structured recursive diff over their JSONB `data`, storing the diff tree + a flat summary (added/removed/changed/unchanged counts) as a `PyatsSnapshotDiff` row. The diff engine is pure-Python (no Genie needed — the snapshots are already-serialized JSONB, so `Genie.diff` isn't applicable); it degrades gracefully (empty inputs → `status="empty"`, malformed inputs → `status="error"` with a warning, row always created).
- **Diff viewer** (`/plugins/pyats/diffs/<pk>/`) — server-rendered collapsible `<details>` tree (no JS): changed subtrees open by default, unchanged ones collapsed; before/after values shown side-by-side for changed leaves; raw-JSON fallback; summary badges; parser warnings.

### Compliance & Jobs

- **`PyatsGoldenConfig` model** — an operator-authored "expected" running-config for a NetBox device (typed/pasted as free text, or promoted from a known-good snapshot). Multiple goldens per device are allowed (e.g. `baseline`, `post-maintenance-window`). The `source` field records provenance (`manual` vs. `snapshot`) so the compliance history can trace back to the originating snapshot. Fully editable via REST in v1 (operators can seed goldens from an external config-management tool).
- **`PyatsComplianceRun` model + `run_compliance` RQ job** — from the device-page PyATS tab, pick a golden config and a captured config/full snapshot; the worker extracts the golden `config_text` and the snapshot's raw `data["config_raw"]` running-config text, diffs them line-by-line (line-set diff), and classifies the outcome as `compliant` (no added/removed lines), `drift` (any divergence), or `error` (missing/empty golden, no raw config on the snapshot, unsupported snapshot, etc.). The run row stores the diff tree + summary counts + warnings and is **always created** so the operator sees the outcome in-line. v1 is order-independent (a re-ordered config is still compliant); ordered/structured compliance rules (e.g. "interface X must have MTU 1500") are deferred to v2.
- **Compliance-run viewer** (`/plugins/pyats/compliance-runs/<pk>/`) — reuses the diff-tree partial so the same collapsible before/after tree renders the golden-vs-snapshot divergence, with a result badge (compliant / drift / error), drift indicator, and any warnings.
- **`PyatsJob` model + unified jobs view** (`/plugins/pyats/jobs/`) — one plugin-scoped row per capture / diff / compliance / batch-capture job, with typed FKs to the result row it produced (`related_snapshot` / `related_diff` / `related_compliance`), a `pending` → `running` → `success` / `error` / `partial` status lifecycle, an `error` TextField for the swallowed-exception path (no result row written), and a `summary` JSONField for batch counts. Bridges NetBox's `core.Job` (which is purged on retention) and the plugin's result rows (which survive). Filterable by type / status / device; read-only via REST and GraphQL; append-only history (no edit view, standard delete only). See [ADR-0005](docs/adr/0005-pyatsjob-model.md).
- **CRUD + REST** for credentials, snapshots, diffs, golden configs, and compliance runs, all under `/plugins/pyats/`, plus **GraphQL** types for credentials, snapshots, diffs, and jobs (GraphQL for golden configs and compliance runs is deferred — see the [changelog](CHANGELOG.md)). (Snapshots, diffs, compliance runs, and jobs are read-only in v1; credentials and golden configs are fully editable.)

### Device-page UI

- **Device-page "PyATS" tab** — capture button (config / state / full), recent-snapshot history with status badges and a warnings indicator, "Diff two snapshots" picker (offered when the device has ≥2 snapshots), a "Run compliance" picker (offered when the device has ≥1 golden config and ≥1 config/full snapshot), and recent-diffs / recent-compliance-runs lists with status/result badges.

## Compatibility matrix

| netbox-pyats | NetBox | Python | PostgreSQL | Redis / Valkey | pyATS |
|-------------|--------|--------|------------|----------------|-------|
| 0.1.x (Phases 1–5) | 4.6.x  | 3.10, 3.11, 3.12 | 15, 16, 17, 18 | Redis 6, Redis 7, Valkey 9.1 | 26.x (worker only) |

The plugin targets NetBox 4.6+ (current: 4.6.5). `pyats[full]` is **not** an install-time dependency — it is heavy and pulls Cython binaries that may not match every NetBox deployment. Install it on the worker that runs snapshots (see `pip install netbox-pyats[pyats]` or the [worker docs](docs/user/workers.md)). The NetBox web process imports the plugin without pyats installed; the testbed builder imports pyATS lazily. The diff and compliance engines are pure-Python and need no pyATS.

> **Note on the community Docker image:** `netboxcommunity/netbox:4.6.x` ships Python 3.14 (Ubuntu 26.04). The plugin and its migrations apply cleanly against that image (verified on `v4.6-5.0.2`). The pyats worker image needs `python3.14-dev` + `gcc` to compile `ruamel-yaml-clib` against Python 3.14 — `dev/Dockerfile.pyats-worker` installs them as a dev-only build step. See [ADR-0003](docs/adr/0003-netbox46-migration-and-worker-toolchain.md) for the rationale.

CI runs the integration suite against the default backend versions (PostgreSQL 18 + Valkey 9.1) on every PR (see [CI docs](docs/developer/ci.md)). The backend-version sweep was collapsed to a single cell: the plugin has no direct PostgreSQL or Redis surface, so sweeping backend versions tests NetBox's infrastructure rather than the plugin.

## Documentation

Full documentation lives under [docs/](docs/README.md). The quick paths:

**For operators (running the plugin in NetBox):**

- [Installation](docs/user/installation.md) — install, configure NetBox, first capture.
- [Usage guide](docs/user/usage.md) — the capture → diff → compliance workflow with exact UI paths.
- [PyATS worker deployment](docs/user/workers.md) — the dedicated `pyats` RQ queue.
- [Credential encryption](docs/user/credentials.md) — how secrets are protected and rotated.
- [Compliance engine](docs/user/compliance.md) — what the golden-config check classifies and why.
- [Troubleshooting](docs/user/troubleshooting.md) — operator-facing fixes for common failure modes.

**For contributors (developing the plugin):**

- [Contributing guide](docs/developer/contributing.md) — local dev setup, tests, lint, conventions.
- [Dev environment bring-up](docs/developer/setup.md) — the single safe path to start the dev stack.
- [CI](docs/developer/ci.md) — the three CI lanes and what each one enforces.
- [Graphify](docs/developer/graphify.md) — the committed code graph and how to query it.
- [Graphify MCP](docs/developer/graphify-mcp.md) — stdio vs HTTP MCP transports for the graph server.
- [Graphify MCP HTTP runbook](docs/developer/graphify-mcp-http.md) — multi-host / shared-service bring-up.
- [Architecture Decision Records](docs/adr/README.md) — the locked structural decisions.

## Quick install

> **NetBox 4.6+ required.** The `pyats` worker (Step 3 below) also needs the `pyats[full]` extra installed — see [Worker deployment](docs/user/workers.md).

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

> ⚠️ **First capture needs the pyats worker running.** "Capture snapshot" enqueues on the dedicated `pyats` RQ queue; with no worker on that queue the job sits pending and the snapshot never appears. Start one with `python manage.py rqworker pyats` (pyats installed) — see [Worker deployment](docs/user/workers.md).

The full install + first-capture walkthrough (including the pyats worker setup) is in [docs/user/installation.md](docs/user/installation.md).

## Getting help

- **Bugs and feature requests:** open an issue on [the GitHub issue tracker](https://github.com/openjarv/netbox-pyats/issues).
- **Common failure modes** (unsupported platform, connection failed, stuck `pending`): see [Troubleshooting](docs/user/troubleshooting.md).

## License

Apache-2.0. See [LICENSE](LICENSE).