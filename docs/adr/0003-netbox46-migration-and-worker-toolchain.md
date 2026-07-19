# ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain

- **Status:** Accepted
- **Date:** 2026-07-19
- **Supersedes:** none
- **Related:** [ATW-25](/ATW/issues/ATW-25), [ADR-0001](0001-plugin-layout.md), `netbox_pyats/migrations/*`, `dev/Dockerfile.pyats-worker`

## Context

Standing up the NetBox 4.6 dev env (`netboxcommunity/netbox:v4.6-5.0.2`, Python 3.14, Ubuntu 26.04 slim) surfaced two compatibility blockers that are structural rather than incidental — both would block every operator on NetBox 4.6, not just our dev env:

1. **`pyats[full]==26.6` fails to build on the worker image.** The transitive dep `ruamel-yaml-clib` (0.2.14) has no cp314 wheel and must compile its C extension from source. The slim NetBox image ships no C compiler and no `python3.14-dev` headers, so `Python.h` is missing. The NetBox web container and pure-Python tests still pass; only the dedicated pyats worker (the snapshot-capture container) is affected.

2. **`netbox_pyats` migrations reference a nonexistent dcim migration.** `0001_initial`, `0002_pyatssnapshot`, and `0003_pyatssnapshotdiff` all declared `dependencies = [("dcim", "0050_custom_field_choice_set_remove"), …]`. No such migration exists in any released NetBox 4.6.x image (the highest dcim migration in 4.6.5 is `0237_module_remove_local_context_data`). `manage.py showmigrations` raised `NodeNotFoundError` and the NetBox web container never reached the login screen. The migrations were authored against a different (non-stock or future) NetBox build.

The README compatibility matrix pins **NetBox 4.6.x × Python 3.10/3.11/3.12 × pyATS 26.x (worker only)**. Every `netboxcommunity/netbox:4.6.x` tag on Docker Hub ships the same image digest — Ubuntu 26.04 with Python 3.14. There is no community 4.6.x image that ships Python ≤3.12, so "pin a 3.10/3.11/3.12 NetBox image" (option a) is not available without maintaining our own NetBox base image. Cutting the matrix to drop Python 3.14 (option d) would require CEO sign-off and would not fix the worker build — it would only narrow the support claim.

## Decision

### Migration dependencies (Blocker 2)

**Plugin migrations do not pin to a specific dcim migration.** The initial migration declares `dependencies = []`; subsequent plugin migrations depend only on the prior `netbox_pyats` migration (plus a dcim dependency only when a migration introduces a new FK to a dcim table that did not exist in a prior plugin migration — none today).

This matches the NetBox reference plugin convention (`netbox/netbox/tests/dummy_plugin/migrations/0001_initial.py` uses `dependencies = []`). Pinning to a named dcim migration couples our migration graph to NetBox's migration history; when NetBox squashes dcim migrations (as they have done before, e.g. `ipam/0054_squashed_0067`), the named dependency disappears and `NodeNotFoundError` returns. `dependencies = []` is the most durable choice.

When a future plugin migration introduces a brand-new FK to a dcim table (e.g. a `Module` FK that did not exist before), that migration may declare a dcim dependency at that point — but only if the referenced dcim migration is the one that *creates* the target table, and only after verifying it exists in every supported NetBox minor. The initial migration and the existing follow-ups need no such dependency.

### Worker build toolchain (Blocker 1)

**The dev worker Dockerfile installs `python3.14-dev` + `gcc` before `uv pip install pyats[full]`** so `ruamel-yaml-clib`'s C extension can compile on NetBox 4.6's Python 3.14 slim image.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends python3.14-dev gcc && rm -rf /var/lib/apt/lists/*
ARG PYATS_VERSION=26.6
RUN uv pip install --python /opt/netbox/venv/bin/python --no-cache "pyats[full]==${PYATS_VERSION}"
```

This is dev-only. The compatibility matrix in the README is unchanged — we still claim NetBox 4.6.x × Python 3.10/3.11/3.12 × pyATS 26.x, and we still claim worker-only pyATS. Python 3.14 is the *NetBox community image's* choice, not ours; the build toolchain makes our worker image build against it without us having to broaden the matrix claim. Production operators targeting Python ≤3.12 do not need this layer (a cp312 wheel for `ruamel-yaml-clib` exists).

## Consequences

- `manage.py showmigrations netbox_pyats` and `manage.py migrate netbox_pyats` run cleanly against `netboxcommunity/netbox:v4.6-5.0.2`; the web container reaches the login screen. Verified end-to-end in the dev env.
- `docker compose -f docker-compose.dev.yml build netbox-pyats-worker` succeeds; `ruamel-yaml-clib==0.2.14` compiles its C extension. Verified end-to-end (worker image builds, `pyats[full]==26.6` installs, Genie/Unicon pull in).
- Pure-Python tests: 65 passed, 4 skipped (NetBox-dependent) — no regression from the migration edits.
- The dev worker image is larger (adds `python3.14-dev` + `gcc`, ~150 MB). This is dev-only; production builds targeting Python ≤3.12 do not need the toolchain layer (a cp312 wheel exists).
- Future NetBox dcim squashes do not break our migration graph: we have no dcim dependency to lose.
- If a future `ruamel-yaml-clib` ships a cp314 wheel, we can drop the toolchain layer. We will revisit when that happens.

## Alternatives considered

### Blocker 1 (pyats worker build)

- **(a) Pin the dev NetBox image to a Python 3.10/3.11/3.12 build.** Rejected: no `netboxcommunity/netbox:4.6.x` tag ships Python ≤3.12 (all 4.6.x tags share the same image digest, Ubuntu 26.04 / Python 3.14). Building our own NetBox base image would multiply the maintenance surface and contradict "use the community image."
- **(c) Move the worker off `pyats[full]` to a slimmer pyats install.** Rejected for Phase 3: snapshot capture needs the parser packages and Unicon connection plugins that `pyats[full]` pulls. A slim install would lose parser coverage and break the multi-vendor promise (ADR-0002). Revisit if a future pyATS release ships a slimmer `pyats[parsers]` extra.
- **(d) Cut the compatibility matrix to drop Python 3.14.** Rejected: would require CEO sign-off (matrix change), would not fix the worker build, and would narrow the community claim unnecessarily. The community image's Python version is not under our control; the matrix claims what *we* support, not what the image ships.

### Blocker 2 (migration dependency)

- **Pin to `("dcim", "0237_module_remove_local_context_data")` (latest dcim migration in 4.6.5).** Considered and rejected: it works today, but couples our migration graph to NetBox's dcim history. When NetBox squashes dcim migrations (as they have done for ipam — `ipam/0054_squashed_0067`), the named dependency disappears and `NodeNotFoundError` returns. `dependencies = []` is more durable and matches the reference plugin.
- **(b) Pin the dev NetBox image to whatever build the migrations were authored against.** Rejected: we cannot identify the build (the migration name `0050_custom_field_choice_set_remove` does not match any dcim migration in any released NetBox 4.6.x). Even if we could, pinning the *image* to fix a *migration dependency* is the wrong layer — the migration must apply on any stock 4.6.x image.
- **(c) Document that the dependency is intentional and which build supplies it.** Rejected: the dependency is not intentional; it appears to be an authoring error. There is no build that supplies it.

## References

- [ATW-25](/ATW/issues/ATW-25) — the originating issue.
- [ATW-24](/ATW/issues/ATW-24) — onboarding issue that surfaced both blockers.
- `netbox_pyats/migrations/0001_initial.py`, `0002_pyatssnapshot.py`, `0003_pyatssnapshotdiff.py` — the edited migrations.
- `dev/Dockerfile.pyats-worker` — the edited worker Dockerfile.
- `netbox/netbox/tests/dummy_plugin/migrations/0001_initial.py` (in the NetBox source tree) — the reference plugin uses `dependencies = []`.
- [ADR-0001](0001-plugin-layout.md) — plugin package layout.
- [ADR-0002](0002-graceful-degradation.md) — multi-vendor graceful degradation.