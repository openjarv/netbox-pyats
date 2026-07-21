# Installation

This guide walks a working NetBox administrator through installing **netbox-pyats**, configuring NetBox to load it, and running a first snapshot capture end-to-end.

## Compatibility

| netbox-pyats | NetBox | Python | pyATS |
|-------------|--------|--------|-------|
| 0.1.x (Phases 1–4) | 4.6.x  | 3.10, 3.11, 3.12 | 26.x (worker only) |

The plugin targets NetBox 4.6+ (current: 4.6.5). `pyats[full]` is **not** an install-time dependency — it is heavy and pulls Cython binaries that may not match every NetBox deployment. Install it only on the worker that runs snapshots (see [Worker setup](#step-3-set-up-the-pyats-worker) below). The NetBox web process imports the plugin without pyats installed; the testbed builder imports pyATS lazily. The diff and compliance engines are pure-Python and need no pyATS.

> **Note on the community Docker image:** `netboxcommunity/netbox:4.6.x` ships Python 3.14 (Ubuntu 26.04). The plugin and its migrations apply cleanly against that image (verified on `v4.6-5.0.2`). The pyats worker image needs `python3.14-dev` + `gcc` to compile `ruamel-yaml-clib` against Python 3.14 — `dev/Dockerfile.pyats-worker` installs them as a dev-only build step. See [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md) for the rationale.

## Step 1 — Install the plugin

```bash
pip install netbox-pyats
```

## Step 2 — Configure NetBox

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

After restart, **Plugins → PyATS** appears in the NetBox navigation menu.

## Step 3 — Set up the pyats worker

Captures, diffs, and compliance checks run as RQ jobs on a dedicated `pyats` queue, isolated from NetBox's default workers. The NetBox web UI (credential CRUD, list/detail views, snapshot list) works without pyATS — but to actually capture snapshots, the worker that runs pyATS jobs needs pyATS installed.

Install the pyats extra on the worker host (or build the worker image — see [Worker deployment](workers.md) for the full guide):

```bash
pip install netbox-pyats[pyats]   # pulls pyats[full] >= 26.0
python manage.py rqworker pyats
```

The worker needs the same NetBox configuration (`configuration.py`, `PLUGINS`, `PLUGINS_CONFIG`) and database/Redis access as the default worker — it is a NetBox worker, just with pyats installed and a different queue argument.

## Step 4 — Verify the install

1. Add a `PyatsCredential` at **Plugins → PyATS → Add Credential**. Pick a device, enter username + password (+ optional enable secret). The secrets are encrypted with Fernet before they hit the database.
2. Open the device's detail page → **PyATS** tab. You should see the capture button (config / state / full) and an empty recent-snapshots list.
3. Click **Capture** (config kind is enough for a smoke test). The job is enqueued on the `pyats` queue.
4. When the worker finishes, the snapshot appears in the tab's recent-snapshots list and under **Plugins → PyATS → PyATS Snapshots**.

If the snapshot shows `unsupported` status, the device's NetBox Platform slug is not in the parser map — see [Troubleshooting](troubleshooting.md). If it shows `error` with `connection failed`, the worker cannot reach the device's management IP.

## Next steps

- [Usage guide](usage.md) — the full capture → diff → compliance workflow.
- [Worker deployment](workers.md) — the dedicated `pyats` RQ queue in detail.
- [Credential encryption](credentials.md) — how secrets are protected and rotated.
- [Compliance engine](compliance.md) — what the golden-config check classifies and why.
- [Troubleshooting](troubleshooting.md) — operator-facing fixes for common failure modes.