# Usage guide

The plugin adds a **PyATS** tab to every NetBox device page. From that tab you capture snapshots, diff two snapshots, and run compliance checks against a golden config. This guide walks the full workflow with exact UI paths.

## Prerequisites

- The plugin is installed and NetBox has been restarted (see [Installation](installation.md)).
- A pyats worker is servicing the `pyats` queue (see [Worker deployment](workers.md)).
- The target device has a `PyatsCredential` record and a reachable management IP (`primary_ip4` / `primary_ip6`).
- The device's NetBox Platform slug maps to a Genie-supported os (see [Multi-vendor support](#multi-vendor-support) below).

## 1 — Add a credential

**Plugins → PyATS → Add Credential**.

Pick a device, enter username + password (+ optional enable secret). The secrets are encrypted with Fernet before they hit the database — see [Credential encryption](credentials.md). The credential is never returned by the REST API, GraphQL, or the detail view template; only ciphertext is persisted.

## 2 — Capture a snapshot

Open the device's detail page → **PyATS** tab → pick a kind → **Capture**.

| Kind | What the worker runs | Stored on `data` |
|------|----------------------|-------------------|
| `config` | `device.parse('show running-config')` | `config` (Genie structured dict) + `config_raw` (raw text) |
| `state`  | a small OS-agnostic state command set via `device.parse(...)` | `state` (Genie structured dict) |
| `full`   | both | `config` + `config_raw` + `state` |

The job is enqueued on the `pyats` queue. When the worker finishes, the snapshot appears in the tab's recent-snapshots list with a status badge:

- `success` — capture succeeded; `data` carries the parsed payload.
- `unsupported` — the device's platform has no Genie parser; a row is still created with a warning so the device appears in the history.
- `error` — capture raised (connection, parser, etc.); a row is still created with the exception text in `parser_warnings`.

Each snapshot also carries `parsed_os` (the pyATS os string used by the capture, e.g. `iosxe` / `iosxr` / `nxos`) so future structured compliance can pick the right Genie parser even after the device row is deleted.

## 3 — Diff two snapshots

From the same device's **PyATS** tab → **Diff two snapshots** picker (only offered when the device has ≥2 snapshots) → pick a **before** and an **after** snapshot → **Diff**.

The `run_diff` job is enqueued on the `pyats` queue. When the worker finishes, the diff appears in the tab's recent-diffs list. Open it (`/plugins/pyats/diffs/<pk>/`) to see:

- a server-rendered collapsible `<details>` tree (no JS) of added/removed/changed/unchanged leaves,
- before/after values shown side-by-side for changed leaves,
- a flat summary (added / removed / changed / unchanged counts),
- raw-JSON fallback,
- parser warnings.

The diff engine is pure-Python and operates on already-serialized JSONB — no pyATS needed for diffs. Empty/unsupported snapshots yield `status="empty"` (neutral badge); malformed inputs yield `status="error"` with a warning — a diff row is always created so the outcome is visible in-line.

## 4 — Add a golden config

**Plugins → PyATS → Golden Configs → Add** (or open the device's PyATS tab → use the "Run compliance" picker's golden link).

Pick the device, give the golden a name (e.g. `baseline-rtr01`), and paste the expected running-config text. The `source` defaults to `manual`; a "promote from snapshot" flow sets it to `snapshot` and links the originating `PyatsSnapshot` for provenance. Multiple goldens per device are allowed (e.g. `baseline`, `post-maintenance-window`).

Golden configs are fully editable via REST in v1, so you can seed goldens from an external config-management tool.

## 5 — Run compliance

From the device's **PyATS** tab → **Run compliance** picker (shown when the device has ≥1 golden config and ≥1 config/full snapshot) → pick a golden and a snapshot → **Run**.

The `run_compliance` job is enqueued on the `pyats` queue. The worker extracts the golden `config_text` and the snapshot's raw `data["config_raw"]` running-config text, diffs them line-by-line, and classifies the outcome:

- `compliant` — no added/removed lines.
- `drift` — any divergence; the diff tree shows *what* drifted.
- `error` — the golden is empty, the snapshot has no `config_raw` payload, or the snapshot is `unsupported` / `error`. The row is still created with a warning naming the missing input.

The compliance-run viewer (`/plugins/pyats/compliance-runs/<pk>/`) reuses the Phase 3 diff-tree partial, so the same collapsible before/after tree renders the golden-vs-snapshot divergence, plus a result badge and any warnings. See [Compliance engine](compliance.md) for the full classification rules and the v1 line-set diff semantics.

## 6 — Browse everything

**Plugins → PyATS →** the relevant list:

- **PyATS Credentials** — filterable by device.
- **PyATS Snapshots** — filterable by device, kind, status.
- **PyATS Snapshot Diffs** — filterable by device, status.
- **Golden Configs** — filterable by device, source.
- **PyATS Compliance Runs** — filterable by device, result.

Each detail view renders the JSONB payload / diff tree / golden text / compliance diff and any warnings.

## 7 — Build a testbed programmatically

The snapshot pipeline does this internally, but you can call it directly:

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

## Multi-vendor support

Genie parsers cover Cisco IOS/XE/XR/NX-OS/ASA, Juniper JunOS, Arista EOS, and Nokia SR OS. The plugin maps NetBox Platform slugs to pyATS `os` strings (see `netbox_pyats/testbed.py`). Platforms with no matching Genie parser are surfaced with `os = "unsupported - no parser"` and `custom['netbox_pyats']['supported'] = False` — they are included on the testbed by default (`on_unsupported="flag"`) so the UI can show them as unsupported; pass `on_unsupported="skip"` to omit them silently in batch runs.

Adding a slug to the map is a commitment that Genie has real parser coverage for that os; unknown slugs degrade gracefully rather than silently producing empty snapshots.

## REST and GraphQL

| Model | REST | GraphQL |
|-------|------|---------|
| `PyatsCredential` | fully editable | yes (ciphertext fields excluded) |
| `PyatsSnapshot` | read-only in v1 | yes |
| `PyatsSnapshotDiff` | read-only in v1 | yes |
| `PyatsGoldenConfig` | fully editable | deferred |
| `PyatsComplianceRun` | read-only in v1 | deferred |

All routes are under `/plugins/pyats/`. Secrets are never returned by the REST API, GraphQL, or the detail view template.

## Next steps

- [Worker deployment](workers.md) — the dedicated `pyats` RQ queue in detail.
- [Credential encryption](credentials.md) — how secrets are protected and rotated.
- [Compliance engine](compliance.md) — what the golden-config check classifies and why.
- [Troubleshooting](troubleshooting.md) — operator-facing fixes for common failure modes.