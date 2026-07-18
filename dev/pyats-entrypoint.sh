#!/usr/bin/env bash
# Dev entrypoint for the netbox-pyats plugin: installs the plugin editable before
# starting NetBox. Mounted into the NetBox container by docker-compose.dev.yml.
set -euo pipefail

pip install --editable /opt/netbox/netbox/netbox_pyats_src
exec /opt/netbox/docker-entrypoint.sh "$@"