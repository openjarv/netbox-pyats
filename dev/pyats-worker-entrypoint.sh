#!/usr/bin/env bash
# Entrypoint for the dedicated pyats RQ worker.
#
# Installs the netbox-pyats plugin editable (from the bind-mounted source)
# into NetBox's venv, then starts an rqworker servicing only the queue(s)
# passed as command args (default: `pyats`). The plugin source is mounted at
# /opt/netbox/netbox/netbox_pyats_src by docker-compose.dev.yml so edits are
# picked up on container restart.
set -euo pipefail

# NetBox 4.6 ships `uv` (not pip) in the venv.
uv pip install --python /opt/netbox/venv/bin/python --editable /opt/netbox/netbox/netbox_pyats_src

# Reclaim bind-mount artifacts back to the host user (ATW-298).
# The editable install writes __pycache__/ and netbox_pyats.egg-info into the
# bind-mounted plugin source as root-owned. Without reclaim, `git worktree
# remove --force` on the host fails with Permission denied (ATW-224). chown
# only the gitignored artifact paths. HOST_UID/HOST_GID come from
# docker-compose.dev.yml (defaults 1000:1000; the worktree .env sets the
# real host uid/gid).
reclaim_artifacts() {
  local src="/opt/netbox/netbox/netbox_pyats_src"
  local uid="${HOST_UID:-1000}" gid="${HOST_GID:-1000}"
  local p
  for p in "$src/__pycache__" "$src/netbox_pyats.egg-info" \
           "$src/netbox_pyats/__pycache__" "$src/build" "$src/dist"; do
    [ -e "$p" ] || continue
    chown -R "$uid:$gid" "$p" 2>/dev/null || true
  done
}
reclaim_artifacts

# Hand off to NetBox's own entrypoint so the Django environment, settings,
# and RQ configuration are loaded exactly as the default worker loads them.
# The queue name(s) come from CMD (e.g. `pyats`).
exec /opt/netbox/docker-entrypoint.sh /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py rqworker "$@"