# Upgrade guide

How to upgrade **netbox-pyats** and how to keep the dedicated `pyats` worker aligned when NetBox itself is upgraded. The headline rule first; the ordered steps after.

> **The pyats worker must run the same NetBox version as the web container.** The worker is a NetBox worker — `dev/Dockerfile.pyats-worker` is `FROM docker.io/netboxcommunity/netbox:<tag>` and runs `python manage.py rqworker pyats` — so it shares NetBox's Django models, settings, and migrations. A worker on a different NetBox version than the web container is unsupported (different migration state, different model fields). **pyATS itself is independent of the NetBox version** and only needs to change when the plugin's `pyats` extra raises its minimum or when the NetBox image's Python version forces a rebuild (see [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md)).

## What stays in sync with what

| Container | Shares NetBox version with | Shares plugin version with | Has pyATS? |
|-----------|----------------------------|----------------------------|------------|
| NetBox web | itself (the source of truth) | the pyats worker | no |
| NetBox default RQ worker | the web container | the web container | no |
| pyats worker | **the web container (must match)** | **the web container (must match)** | yes |

The plugin is installed into the **same** virtualenv as NetBox on both the web process and the pyats worker (`pip install netbox-pyats` on the web, `pip install netbox-pyats[pyats]` on the worker). The worker needs the same plugin code as the web process because they share models and migrations. `pyats[full]` is worker-only and is pinned independently — `pyats[full]>=26.0` in `pyproject.toml` — so it is **not** tied to the NetBox version.

The plugin's own migrations live in `netbox_pyats/migrations/` and are independent of NetBox's dcim/ipam migrations (ADR-0003: `dependencies = []` on the initial migration, no dcim pin). A NetBox upgrade does **not** break the plugin's migration graph, and a plugin upgrade runs only the plugin's own migrations.

## Plugin upgrade (NetBox version unchanged)

1. Read the plugin [CHANGELOG](../../CHANGELOG.md) for breaking changes or required manual steps.
2. On the NetBox **web** host:
   ```bash
   pip install -U netbox-pyats
   cd /opt/netbox
   python manage.py migrate netbox_pyats
   sudo systemctl restart netbox netbox-rq
   ```
3. On the **pyats worker** host:
   ```bash
   pip install -U 'netbox-pyats[pyats]'
   ```
   Restart the worker process (`python manage.py rqworker pyats`, or restart the container if you run the shipped image).
4. If the new plugin version raised the `pyats` extra's minimum, the worker's `pip install -U 'netbox-pyats[pyats]'` pulls the new pyATS automatically; otherwise pyATS is unchanged.
5. Verify:
   - **Plugins → PyATS** loads in the web UI.
   - A test capture runs (open a device → **PyATS** tab → **Capture**).
   - The pyats worker shows on the `pyats` queue in **Operations → Background Tasks → Workers**.

> The worker needs the same plugin code as the web process — they share models and migrations. Upgrading the plugin on the web host and not on the worker (or vice versa) leaves them out of sync and is unsupported.

## NetBox upgrade (plugin version unchanged)

1. Read the NetBox release notes for breaking changes.
2. Upgrade NetBox on **both** the web container and the pyats worker container — they must stay on the same NetBox version (same base image tag). The worker image's `FROM` line (`dev/Dockerfile.pyats-worker`) pins the NetBox tag; update it to the new tag and rebuild. For the shipped dev image:
   ```bash
   # Edit the FROM line in dev/Dockerfile.pyats-worker to the new tag, then:
   docker compose -f docker-compose.dev.yml build netbox-pyats-worker
   ```
   (In production, apply the same tag change to your published worker image build and republish.)
3. Run NetBox's own migrations:
   ```bash
   cd /opt/netbox
   python manage.py migrate
   ```
   The plugin's migrations are already applied and unaffected by ADR-0003 (`dependencies = []`).
4. The plugin does **not** need a reinstall unless NetBox's Python version changed in a way that breaks the installed wheel. If the Python interpreter changed (e.g. 3.12 → 3.14 forced a rebuild — see ADR-0003's `ruamel-yaml-clib` toolchain note), reinstall on both hosts:
   ```bash
   # Web host
   pip install netbox-pyats
   # Worker host
   pip install 'netbox-pyats[pyats]'
   ```
5. pyATS does **not** need to change on a NetBox upgrade unless the new NetBox image's Python version lacks a wheel for a pyATS transitive dep (the ADR-0003 case). The `pyats` extra's pin (`pyats[full]>=26.0`) is independent of the NetBox version.
6. Verify:
   - NetBox web UI loads.
   - `python manage.py showmigrations netbox_pyats` shows all plugin migrations applied.
   - A test capture runs.

## Both at once (NetBox + plugin upgrade)

Do the **NetBox upgrade first**, then the plugin upgrade. This keeps the migration graph clean: NetBox's migrations first, then the plugin's.

1. Upgrade NetBox on the web container and rebuild the pyats worker image against the new NetBox tag (same step as [NetBox upgrade](#netbox-upgrade-plugin-version-unchanged) above).
2. `python manage.py migrate` (NetBox's migrations).
3. Upgrade the plugin on both hosts:
   ```bash
   # Web host
   pip install -U netbox-pyats
   python manage.py migrate netbox_pyats
   sudo systemctl restart netbox netbox-rq
   # Worker host
   pip install -U 'netbox-pyats[pyats]'
   # restart the worker
   ```
4. Verify as in the two sections above.

## Troubleshooting an upgrade

See [Troubleshooting](troubleshooting.md) for the operator-facing failure modes (worker not on the `pyats` queue, connection failures, `unsupported` platforms). Two upgrade-specific checks:

- **`showmigrations netbox_pyats` shows an unapplied migration after a plugin upgrade** — run `python manage.py migrate netbox_pyats` on the web host (not the worker; the worker does not run migrations).
- **Capture jobs sit `pending` after a NetBox upgrade** — the worker container is still on the old NetBox image, or it has not been restarted. The worker must match the web container's NetBox version; rebuild and restart it.

## Next steps

- [Installation](installation.md) — first-time install and first capture.
- [Worker deployment](workers.md) — the dedicated `pyats` RQ queue in detail.
- [Troubleshooting](troubleshooting.md) — operator-facing fixes for common failure modes.
- [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md) — why the plugin's migrations do not pin to a dcim migration, and the worker build toolchain rationale.