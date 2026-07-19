# Dev environment bring-up

This is the single safe path for any engineer to start the netbox-pyats dev
environment on the dev server. It uses `docker-compose.dev.yml` at the repo
root, which is hardened per [ATW-35](/ATW/issues/ATW-35):

- The only published port is `127.0.0.1:8000` (loopback). The dev UI is never
  reachable on the server's public IP. Use SSH port forwarding for remote
  access (see [Remote access](#remote-access) below).
- All services run on an isolated user-defined bridge network (`devnet`).
- Every service has a CPU cap, a memory cap, a healthcheck, and
  `restart: unless-stopped`.

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose`).
- ~6 GB free RAM on the dev host (default caps total ~4.75 GB; leave headroom).
- This repo checked out, on a branch that includes the hardened compose file
  (e.g. `infra/atw-35-harden-compose` or any descendant that merges it).

## Bring-up

From the repo root:

```bash
docker compose -f docker-compose.dev.yml up -d
```

The first run builds the `netbox-pyats-worker` image (installs `pyats[full]` +
`genie`); subsequent runs reuse the cached image. NetBox itself takes ~3–5
minutes to pass its healthcheck on first boot (migrations + superuser + search
index), during which the two RQ workers wait (`depends_on: service_healthy`).

Check status:

```bash
docker compose -f docker-compose.dev.yml ps
```

All five services should reach `healthy`:

| Service              | Healthcheck                       |
| -------------------- | --------------------------------- |
| `netbox`             | `curl -f http://localhost:8080/login/` |
| `netbox-worker`      | `pgrep -f "manage.py rqworker"`   |
| `netbox-pyats-worker`| `pgrep -f "manage.py rqworker.*pyats"` |
| `postgres`           | `pg_isready`                      |
| `redis`              | `valkey-cli ping`                 |

Open the UI (on the dev host, or via SSH tunnel):

```
http://localhost:8000   (admin / admin)
```

Run the plugin's tests inside the `netbox` container:

```bash
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## Teardown

Stop the stack (keeps volumes):

```bash
docker compose -f docker-compose.dev.yml down
```

Stop and delete all dev data (volumes included):

```bash
docker compose -f docker-compose.dev.yml down -v
```

## Resource limits

Each service has a default CPU + memory cap. Override any of them via shell
environment variables before `up`:

```bash
NETBOX_CPUS=2 NETBOX_MEM=2g \
PYATS_WORKER_CPUS=2 PYATS_WORKER_MEM=3g \
docker compose -f docker-compose.dev.yml up -d
```

| Service              | Var prefix          | Default CPU | Default mem |
| -------------------- | ------------------- | ----------- | ----------- |
| `netbox`             | `NETBOX_`           | 1.0         | 1g          |
| `netbox-worker`      | `WORKER_`           | 1.0         | 1g          |
| `netbox-pyats-worker`| `PYATS_WORKER_`     | 1.5         | 2g          |
| `postgres`           | `POSTGRES_`         | 0.5         | 512m        |
| `redis`              | `REDIS_`            | 0.5         | 256m        |

## Remote access

The dev UI binds to `127.0.0.1:8000` on the dev host only. To reach it from
your laptop, tunnel over SSH rather than widening the binding:

```bash
ssh -L 8000:127.0.0.1:8000 <user>@<dev-host>
# then open http://localhost:8000 on your laptop
```

Do **not** change the port mapping to `0.0.0.0:8000` or drop the `127.0.0.1`
prefix — that would expose the dev NetBox (default `admin/admin` credentials,
dev `SECRET_KEY`) to the public internet.

## Troubleshooting

- **`netbox` stays `health: starting` then exits 137**: usually a port
  conflict on `127.0.0.1:8000` from another compose project on the same host.
  Run `docker ps` and stop any other stack bound to `:8000`, then
  `docker compose -f docker-compose.dev.yml up -d`.
- **Workers stuck on `Created`**: they wait for `netbox` to be `healthy`.
  Check `docker compose ps`; if `netbox` is unhealthy, read its logs with
  `docker compose -f docker-compose.dev.yml logs netbox`.
- **`netbox-worker` / `netbox-pyats-worker` show `unhealthy`**: the healthcheck
  uses `pgrep -f "manage.py rqworker"`. Confirm the worker process is running
  with `docker compose exec netbox-worker ps aux | grep rqworker`. If it crashed,
  `restart: unless-stopped` will bring it back; check logs for the cause.
- **Need more memory for NetBox**: NetBox 4.6 with 4 granian workers can
  exceed 1 GB under load. Raise it: `NETBOX_MEM=2g docker compose ... up -d`.