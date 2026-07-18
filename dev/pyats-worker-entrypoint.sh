#!/usr/bin/env bash
# Entrypoint for the dedicated pyats RQ worker.
#
# Installs the netbox-pyats plugin editable (from the bind-mounted source)
# into NetBox's venv, then starts an rqworker servicing only the queue(s)
# passed as command args (default: `pyats`). The plugin source is mounted at
# /opt/netbox/netbox/netbox_pyats_src by docker-compose.dev.yml so edits are
# picked up on container restart.
set -euo pipefail

pip install --editable /opt/netbox/netbox/netbox_pyats_src

# Hand off to NetBox's own entrypoint so the Django environment, settings,
# and RQ configuration are loaded exactly as the default worker loads them.
# The queue name(s) come from CMD (e.g. `pyats`).
exec /opt/netbox/docker-entrypoint.sh /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py rqworker "$@"