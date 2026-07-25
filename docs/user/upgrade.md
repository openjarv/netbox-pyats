# Upgrade guide

Upgrading **netbox-pyats** follows the same pattern you already use to upgrade NetBox: back up, review the release notes, update the software, apply database migrations, and restart the NetBox services. The one extra rule is the dedicated **pyats worker** — it is a NetBox worker, so it must run the same NetBox release as the web container and the same plugin version as the web process.

> **The pyats worker must run the same NetBox release as the web container.** The worker image (`dev/Dockerfile.pyats-worker`) is built `FROM` the official NetBox image and runs `python manage.py rqworker pyats`, so it shares NetBox's Django models, settings, and migrations. A worker on a different NetBox release than the web container is unsupported — the migration state and model fields will not match. **pyATS itself is independent of the NetBox release** and only needs to change when the plugin's `pyats` extra raises its minimum or when the NetBox image's Python version forces a rebuild (see [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md)).

## Before you begin

As with any NetBox upgrade, **back up your deployment first** — database and configuration. Review the release notes for everything being upgraded:

- NetBox release notes (for a NetBox upgrade).
- The plugin [CHANGELOG](../../CHANGELOG.md) (for a plugin upgrade).

## What stays in sync with what

The plugin is installed into the same virtualenv as NetBox on both the web process and the pyats worker (`pip install netbox-pyats` on the web, `pip install netbox-pyats[pyats]` on the worker). The worker needs the same plugin code as the web process because they share models and migrations.

| Container | NetBox release | Plugin version | Has pyATS? |
|-----------|-----------------|----------------|------------|
| NetBox web | source of truth | must match the worker | no |
| NetBox default RQ worker | must match the web | must match the web | no |
| pyats worker | **must match the web** | **must match the web** | yes |

`pyats[full]` is worker-only and pinned independently (`pyats[full]>=26.0` in `pyproject.toml`), so it is **not** tied to the NetBox release. The plugin's own migrations live in `netbox_pyats/migrations/` and are independent of NetBox's dcim/ipam migrations (ADR-0003: `dependencies = []` on the initial migration). A NetBox upgrade does **not** break the plugin's migration graph, and a plugin upgrade runs only the plugin's own migrations.

## Plugin upgrade (NetBox release unchanged)

The plugin upgrade mirrors the standard NetBox package-upgrade flow: update the package, apply the plugin's database migrations, and restart the NetBox services. Do it on **both** the web host and the pyats worker so they stay in sync.

1. **Review the release notes.** Check the plugin [CHANGELOG](../../CHANGELOG.md) for breaking changes or required manual steps.
2. **Update the plugin on the web host:**
   ```bash
   pip install -U netbox-pyats
   cd /opt/netbox
   python manage.py migrate netbox_pyats
   sudo systemctl restart netbox netbox-rq
   ```
3. **Update the plugin on the pyats worker host** so it runs the same plugin code as the web process:
   ```bash
   pip install -U 'netbox-pyats[pyats]'
   ```
   Restart the worker process (`python manage.py rqworker pyats`, or restart the container if you run the shipped image). If the new plugin version raised the `pyats` extra's minimum, this command pulls the new pyATS automatically; otherwise pyATS is unchanged.
4. **Verify:**
   - **Plugins → PyATS** loads in the web UI.
   - A test capture runs (open a device → **PyATS** tab → **Capture**).
   - The pyats worker shows on the `pyats` queue in **Operations → Background Tasks → Workers**.

> Upgrading the plugin on the web host and not on the worker (or vice versa) leaves them out of sync and is unsupported — they share models and migrations.

## NetBox upgrade (plugin version unchanged)

A NetBox upgrade uses the standard NetBox upgrade procedure on the web container, with one extra step: the pyats worker image must be rebuilt against the new NetBox image tag so it stays on the same release.

1. **Review the NetBox release notes** for breaking changes, and back up your deployment.
2. **Upgrade NetBox on the web container** following the standard NetBox upgrade procedure (release notes → update dependencies → install the latest release → run `./upgrade.sh` or `python manage.py migrate` → restart the NetBox services).
3. **Rebuild the pyats worker image against the new NetBox image tag.** The worker image's `FROM` line (`dev/Dockerfile.pyats-worker`) pins the NetBox tag; update it to the new tag and rebuild so the worker runs the same NetBox release as the web container:
   ```bash
   # Edit the FROM line in dev/Dockerfile.pyats-worker to the new tag, then:
   docker compose -f docker-compose.dev.yml build netbox-pyats-worker
   ```
   (In production, apply the same tag change to your published worker image build and republish.) Restart the worker container.
4. **Apply NetBox's database migrations** (if you did not run `./upgrade.sh`, which does this for you):
   ```bash
   cd /opt/netbox
   python manage.py migrate
   ```
   The plugin's migrations are already applied and unaffected (ADR-0003: `dependencies = []`).
5. **Reinstall the plugin only if the Python interpreter changed** in a way that breaks the installed wheel (e.g. 3.12 → 3.14 forced a rebuild — see ADR-0003's `ruamel-yaml-clib` toolchain note). Otherwise the plugin does not need a reinstall:
   ```bash
   # Web host (only if the Python interpreter changed)
   pip install netbox-pyats
   # Worker host (only if the Python interpreter changed)
   pip install 'netbox-pyats[pyats]'
   ```
6. **pyATS does not need to change** on a NetBox upgrade unless the new NetBox image's Python version lacks a wheel for a pyATS transitive dep (the ADR-0003 case). The `pyats` extra's pin (`pyats[full]>=26.0`) is independent of the NetBox release.
7. **Verify:**
   - NetBox web UI loads.
   - `python manage.py showmigrations netbox_pyats` shows all plugin migrations applied.
   - A test capture runs.

## Both at once (NetBox + plugin upgrade)

Do the **NetBox upgrade first**, then the plugin upgrade. This keeps the migration graph clean: NetBox's migrations first, then the plugin's.

1. **Upgrade NetBox on the web container** (standard NetBox upgrade procedure), and **rebuild the pyats worker image** against the new NetBox tag (same step as [NetBox upgrade](#netbox-upgrade-plugin-version-unchanged) above). Restart both.
2. **Apply NetBox's database migrations:**
   ```bash
   cd /opt/netbox
   python manage.py migrate
   ```
3. **Upgrade the plugin on both hosts:**
   ```bash
   # Web host
   pip install -U netbox-pyats
   python manage.py migrate netbox_pyats
   sudo systemctl restart netbox netbox-rq
   # Worker host
   pip install -U 'netbox-pyats[pyats]'
   # restart the worker
   ```
4. **Verify** as in the two sections above.

## Troubleshooting an upgrade

See [Troubleshooting](troubleshooting.md) for the operator-facing failure modes (worker not on the `pyats` queue, connection failures, `unsupported` platforms). Two upgrade-specific checks:

- **`showmigrations netbox_pyats` shows an unapplied migration after a plugin upgrade** — run `python manage.py migrate netbox_pyats` on the web host (not the worker; the worker does not run migrations).
- **Capture jobs sit `pending` after a NetBox upgrade** — the worker container is still on the old NetBox image, or it has not been restarted. The worker must match the web container's NetBox release; rebuild and restart it.

## Next steps

- [Installation](installation.md) — first-time install and first capture.
- [Worker deployment](workers.md) — the dedicated `pyats` RQ queue in detail.
- [Troubleshooting](troubleshooting.md) — operator-facing fixes for common failure modes.
- [ADR-0003](../adr/0003-netbox46-migration-and-worker-toolchain.md) — why the plugin's migrations do not pin to a dcim migration, and the worker build toolchain rationale.