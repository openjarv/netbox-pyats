# Dev environment bring-up

This is the single safe path for any engineer to start the netbox-pyats dev
environment on the dev server. It uses `docker-compose.dev.yml` and the
`scripts/dev-worktree.sh` helper so that multiple engineers (and agents) can
work in parallel without colliding on git branches or Docker stacks.

The compose file is hardened per [ATW-35](/ATW/issues/ATW-35):

- The only published port is `127.0.0.1:<port>` (loopback). The dev UI is never
  reachable on the server's public IP. Use SSH port forwarding for remote
  access (see [Remote access](#remote-access) below).
- All services run on an isolated user-defined bridge network (`devnet`),
  namespaced per compose project.
- Every service has a CPU cap, a memory cap, a healthcheck, and
  `restart: unless-stopped`.

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose`).
- ~6 GB free RAM on the dev host (default caps total ~4.75 GB; leave headroom).
- The trunk working tree at `/home/hermes/netbox-pyats`, on `main`.

## Worktree convention (hard rule)

No feature work happens in the trunk worktree. Every issue gets its own git
worktree under `/home/hermes/netbox-pyats-wt/<issue-id>/`, on its own branch,
with its own isolated compose stack. One issue = one branch = one worktree.

Create a worktree before any repo work, and remove it when the issue reaches a
terminal state (`done`/`cancelled`):

```bash
# from anywhere (the script resolves the trunk repo root itself):
scripts/dev-worktree.sh add <issue-id> <type> <slug>
#   e.g. scripts/dev-worktree.sh add atw-38 fix netbox46-compat-bugs

# then work inside the worktree:
cd /home/hermes/netbox-pyats-wt/<issue-id>
scripts/dev-worktree.sh up

# when the issue is done/cancelled:
scripts/dev-worktree.sh remove <issue-id>
```

`<type>` is one of `feat fix chore docs infra refactor test`. The branch is
named `<type>/<issue-id>-<slug>`. The script writes a per-worktree `.env` with
`COMPOSE_PROJECT_NAME=<issue-id>` and a unique `NETBOX_PORT`, so each worktree's
compose stack is isolated by project name, network, and published port.

Never `git checkout` a feature branch in the trunk worktree at
`/home/hermes/netbox-pyats`. Ad-hoc `docker compose up` from arbitrary
directories is out of bounds — use `dev-worktree.sh up` from a worktree.

## Bring-up

From inside a worktree (after `dev-worktree.sh add`):

```bash
cd /home/hermes/netbox-pyats-wt/<issue-id>
scripts/dev-worktree.sh up
# equivalent to:
#   docker compose -f docker-compose.dev.yml --env-file .env up -d
```

The first run builds the `netbox-pyats-worker` image (installs `pyats[full]` +
`genie`); subsequent runs reuse the cached image. NetBox itself takes ~3–5
minutes to pass its healthcheck on first boot (migrations + superuser + search
index), during which the two RQ workers wait (`depends_on: service_healthy`).

Check status (run from inside the worktree):

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

Open the UI (on the dev host, or via SSH tunnel). The port is the one
`dev-worktree.sh add` assigned and wrote into the worktree's `.env`:

```
http://localhost:<NETBOX_PORT>   (admin / admin)
```

Run the plugin's tests inside the `netbox` container (from the worktree):

```bash
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## Teardown

Stop one worktree's stack (keeps volumes) — run from inside the worktree:

```bash
docker compose -f docker-compose.dev.yml down
```

Stop and delete one worktree's data (volumes included):

```bash
docker compose -f docker-compose.dev.yml down -v
```

When the issue reaches a terminal state (`done`/`cancelled`), remove the
worktree entirely — compose down + volumes + the worktree directory and its
branch reference:

```bash
scripts/dev-worktree.sh remove <issue-id>
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

The dev UI binds to `127.0.0.1:<NETBOX_PORT>` on the dev host only. To reach it
from your laptop, tunnel over SSH rather than widening the binding (replace
`8000` with the port the worktree claimed):

```bash
ssh -L 8000:127.0.0.1:8000 <user>@<dev-host>
# then open http://localhost:8000 on your laptop
```

Do **not** change the port mapping to `0.0.0.0:<port>` or drop the `127.0.0.1`
prefix — that would expose the dev NetBox (default `admin/admin` credentials,
dev `SECRET_KEY`) to the public internet.

## Working in parallel

The worktree convention is what lets multiple engineers (and agents) work on
the plugin at the same time without colliding. The rules:

- **One worktree per issue.** Create it with `dev-worktree.sh add` before any
  repo work; remove it with `dev-worktree.sh remove` when the issue is
  `done`/`cancelled`. Don't leave orphan worktrees around.
- **Cap of 3 concurrent active worktrees.** Each worktree runs its own full
  NetBox stack (postgres, redis, netbox, two workers) with per-service resource
  caps from [ATW-35](/ATW/issues/ATW-35). 3 stacks × ~4.75 GB of caps only peaks
  that high if every service is loaded at once; in practice postgres/redis are
  idle. If the host is tight, drop to 2. Bump the cap with CEO sign-off.
- **Port pool 8001..8010.** `dev-worktree.sh add` scans
  `/home/hermes/netbox-pyats-wt/*/.dev-port` for claimed ports and picks the
  next free one. If the pool is exhausted, the script fails loud — clean up
  stale worktrees.
- **No cross-contamination.** Each worktree's `COMPOSE_PROJECT_NAME` is its
  issue id, so `docker compose down -v` in one worktree only touches that
  worktree's containers, volumes, and network. Another engineer's tests keep
  running untouched.
- **The trunk worktree stays on `main`.** It is only used for pulling latest,
  merging PRs, and creating new worktrees. Never checkout a feature branch in
  `/home/hermes/netbox-pyats`.

## Troubleshooting

- **`netbox` stays `health: starting` then exits 137**: usually a port
  conflict on `127.0.0.1:<NETBOX_PORT>` from another compose project on the
  same host. Run `docker ps` and stop any other stack bound to that port, or
  pick a new worktree with `dev-worktree.sh` (it assigns a free port
  automatically).
- **Workers stuck on `Created`**: they wait for `netbox` to be `healthy`.
  Check `docker compose ps`; if `netbox` is unhealthy, read its logs with
  `docker compose -f docker-compose.dev.yml logs netbox`.
- **`netbox-worker` / `netbox-pyats-worker` show `unhealthy`**: the healthcheck
  uses `pgrep -f "manage.py rqworker"`. Confirm the worker process is running
  with `docker compose exec netbox-worker ps aux | grep rqworker`. If it crashed,
  `restart: unless-stopped` will bring it back; check logs for the cause.
- **Need more memory for NetBox**: NetBox 4.6 with 4 granian workers can
  exceed 1 GB under load. Raise it: `NETBOX_MEM=2g docker compose ... up -d`.