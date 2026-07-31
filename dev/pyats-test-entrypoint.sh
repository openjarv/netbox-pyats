#!/usr/bin/env bash
# Test entrypoint for the netbox-pyats plugin (ATW-357).
#
# Installs the plugin editable (same install + artifact-reclaim pattern as
# dev/pyats-entrypoint.sh), sets up the NetBox Django environment, then runs
# pytest from the bind-mounted plugin source. The compose `command:`
# supplies the pytest args, defaulting to `--reuse-db netbox_pyats/tests`.
#
# The `netbox-test` compose service (docker-compose.test.yml) does NOT run
# granian, so the granian-connection race that blocked `DROP DATABASE` on
# re-run (ATW-85 / ATW-188) cannot occur. --reuse-db keeps the migrated
# `test_netbox` schema across runs so the ~480s NetBox migration cold start
# is paid once, not every iteration (ATW-351 / ATW-357). Pass --create-db
# to force a clean rebuild when migrations change.
#
# This entrypoint does NOT run the NetBox image's docker-entrypoint.sh init
# (dev-DB migrate, superuser, search index): pytest-django creates and
# migrates `test_netbox` itself via `django_db_setup`, so the dev `netbox` DB
# does not need to exist or be migrated for the test suite to run. Skipping
# the init avoids the entrypoint's `./manage.py`-relative-to-cwd assumption
# (it expects cwd /opt/netbox/netbox) and lets us cd straight to the plugin
# source so `pytest netbox_pyats/tests` resolves. conftest.py's
# `_configure_netbox()` calls `django.setup()` when `netbox` is importable,
# so the app registry is ready without the entrypoint's init.
set -euo pipefail

# NetBox 4.6 ships `uv` (not pip) in the venv. Install the plugin editable
# plus the dev extra (pytest, pytest-django) so the stock NetBox image can
# run the suite. Same install step as dev/pyats-entrypoint.sh.
uv pip install --python /opt/netbox/venv/bin/python \
  --editable "/opt/netbox/netbox/netbox_pyats_src[dev]"

# Reclaim bind-mount artifacts back to the host user (ATW-298). Mirrors the
# reclaim block in dev/pyats-entrypoint.sh; includes .pytest_cache/ which
# the test runner writes into the bind mount as root-owned. Runs on exit so
# artifacts are reclaimed even if pytest fails.
reclaim_artifacts() {
  local src="/opt/netbox/netbox/netbox_pyats_src"
  local uid="${HOST_UID:-1000}" gid="${HOST_GID:-1000}"
  local p
  for p in "$src/__pycache__" "$src/.pytest_cache" "$src/netbox_pyats.egg-info" \
           "$src/netbox_pyats/__pycache__" "$src/build" "$src/dist"; do
    [ -e "$p" ] || continue
    chown -R "$uid:$gid" "$p" 2>/dev/null || true
  done
}
trap reclaim_artifacts EXIT

# Django needs NetBox's settings to load the app registry (models, etc.) for
# the integration suite. The stock image sets this in its environment; set it
# explicitly since we run pytest directly (conftest.py calls django.setup()
# when `netbox` is importable).
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-netbox.settings}"

# Run pytest from the bind-mounted plugin source so `netbox_pyats/tests`
# resolves. pytest-django's `django_db_setup` creates/migrates `test_netbox`
# (kept across runs by --reuse-db); the dev `netbox` DB is not touched.
cd /opt/netbox/netbox/netbox_pyats_src

# We do NOT `exec` pytest: exec would replace this shell and discard the EXIT
# trap above, so reclaim_artifacts would never run after pytest (and pytest
# writes .pytest_cache/ as root into the bind mount). Running it as a child
# lets the trap fire on exit, reclaiming the artifacts pytest wrote. The
# script's exit code is pytest's (propagated by the child), so `docker
# compose run` gates on it correctly.
/opt/netbox/venv/bin/pytest "$@"