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
exec /opt/netbox/docker-entrypoint.sh "$@"
