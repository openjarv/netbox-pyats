#!/usr/bin/env bash
# Dev entrypoint for the netbox-pyats plugin: installs the plugin editable before
# starting NetBox. Mounted into the NetBox container by docker-compose.dev.yml.
set -euo pipefail

# NetBox 4.6 ships `uv` (not pip) in the venv. `uv pip install --python <venv>`
# installs into the NetBox venv without needing a pip binary.
#
# Install the plugin editable plus the dev extra (pytest, pytest-django) so
# `docker compose exec netbox pytest netbox_pyats/tests` works inside the
# stock NetBox image, which does not ship pytest. The dev extra is pinned in
# pyproject.toml; production deployments never run tests inside the web
# container, so this only adds test-time packages to the dev/CI container.
# uv resolves extras via the `<dir>[extra]` source spec, not `--extra`.
uv pip install --python /opt/netbox/venv/bin/python \
  --editable "/opt/netbox/netbox/netbox_pyats_src[dev]"

# Reclaim bind-mount artifacts back to the host user (ATW-298).
# The editable install (and pytest, when run) writes __pycache__/,
# netbox_pyats.egg-info, and .pytest_cache/ into the bind-mounted plugin
# source as root-owned. Without reclaim, `git worktree remove --force` on
# the host fails with Permission denied and strands the worktree (ATW-224).
# chown only the gitignored artifact paths, never the whole bind mount, so
# tracked source files (already host-owned via the bind mount) are untouched.
# HOST_UID/HOST_GID come from docker-compose.dev.yml (defaults 1000:1000; the
# worktree .env sets the real host uid/gid).
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
reclaim_artifacts

exec /opt/netbox/docker-entrypoint.sh "$@"
