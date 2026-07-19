#!/usr/bin/env bash
# Dev entrypoint for the netbox-pyats plugin: installs the plugin editable before
# starting NetBox. Mounted into the NetBox container by docker-compose.dev.yml.
set -euo pipefail

# NetBox 4.6 ships `uv` (not pip) in the venv. `uv pip install --python <venv>`
# installs into the NetBox venv without needing a pip binary.
uv pip install --python /opt/netbox/venv/bin/python --editable /opt/netbox/netbox/netbox_pyats_src
exec /opt/netbox/docker-entrypoint.sh "$@"
