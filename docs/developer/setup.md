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

Create a worktree before any repo work, and remove it when the issue reaches
a terminal state (`done`/`cancelled`):

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

### Image overrides (compatibility sweeps)

The `postgres` and `redis` image tags are overridable so compatibility-matrix
CI (and local sweeps) can test the plugin against multiple backend versions
without editing the compose file:

```bash
PG_VERSION=16-alpine REDIS_IMAGE=redis:7-alpine \
  docker compose -f docker-compose.dev.yml up -d
```

| Service    | Var            | Default                      | Example values                          |
| ---------- | -------------- | ---------------------------- | --------------------------------------- |
| `postgres` | `PG_VERSION`   | `18-alpine`                  | `14-alpine`, `16-alpine`, `17-alpine`   |
| `redis`    | `REDIS_IMAGE`  | `valkey/valkey:9.1-alpine`   | `redis:6-alpine`, `redis:7-alpine`      |

`PG_VERSION` is just the tag (the `postgres:` prefix is fixed).
`REDIS_IMAGE` is the full `repo:tag` so it can swap between `redis:*` and
`valkey:*` images. The `redis` service auto-detects the server binary
(`valkey-server` or `redis-server`) via a shell-form fallback, so no
`REDIS_SERVER` override is needed. The healthcheck uses both `valkey-cli`
and `redis-cli` so it works across either image family.

## Remote access

The dev UI binds to `127.0.0.1:<NETBOX_PORT>` on the dev host only. To reach it
from your laptop, **do not** widen the binding (that would expose the dev
NetBox with `admin/admin` credentials and the dev `SECRET_KEY` to the public
internet). Instead, proxy the loopback port out through the tailnet without
ever publishing it on eth0.

For the full repeatable runbook — recommended `tailscale serve` path,
SSH-tunnel-over-Tailscale fallback, host facts, aliases, and a verification
checklist — see [Remote access over Tailscale](remote-access.md).

Quick reference (replace `<port>` with the worktree's `NETBOX_PORT`):

```bash
# recommended, on the dev host (auto-HTTPS, tailnet-only):
tailscale serve --bg http://127.0.0.1:<port>
# open on your laptop: https://vmi3285403.tail4085b5.ts.net/
# stop with:          tailscale serve reset

# fallback, from your laptop (SSH tunnel over the Tailscale IP):
ssh -N -L 8000:127.0.0.1:<port> <user>@100.127.35.6
# open on your laptop: http://localhost:8000
```

Do **not** change the port mapping to `0.0.0.0:<port>` or drop the `127.0.0.1`
prefix — that would expose the dev NetBox (default `admin/admin` credentials,
dev `SECRET_KEY`) to the public internet, violating [ATW-35](/ATW/issues/ATW-35).

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

### `test_netbox` already exists / `EOFError` / "terminating connection due to administrator command" (ATW-85)

Symptom: `docker compose exec netbox pytest ...` (or
`python manage.py test ...`) fails during test-DB creation with one of:

- `django.db.utils.ProgrammingError: database "test_netbox" already exists`
- `EOFError: EOF when reading a line` (from Django's
  `Type 'yes' if you would like to try deleting the test database…` prompt)
- `django.db.utils.OperationalError: terminating connection due to
  administrator command`

**There is no environmental monitor killing the test runner.** The dev
container has no cron, no supervisor, and no background process that touches
`test_netbox`. The container's `restart: unless-stopped` policy does not
restart it while it is healthy. Verified on 2026-07-21 (ATW-85): container
`OOMKilled=false`, `RestartCount=0`, `docker inspect` shows no OOM kills
across the atw-83 stack; a clean `python manage.py test
netbox_pyats.tests.test_models` run created `test_netbox`, ran all
migrations, ran the tests, and Django tore the test DB down — no SIGKILL.

The real cause, in order of likelihood:

1. **A previous test run is still holding `test_netbox` open.** The Django
   test runner creates `test_netbox` and tears it down at the end. If the
   previous run was killed mid-migration (host `timeout`, lost SSH session,
   container restart while a test run was in flight, an agent's
   `docker compose exec` got disconnected), the postgres backend is left
   `idle in transaction` against `test_netbox`. The next run then sees
   `database "test_netbox" already exists`, prompts `Type 'yes'…`, and
   because `docker compose exec -T` has no stdin it gets `EOFError` —
   leaving *another* idle connection behind.
2. **Two test runs racing the same worktree's container.** If two shells
   (or two agents) `docker compose exec` into the same worktree's `netbox`
   container and both start a test run, the second one's
   `CREATE DATABASE test_netbox` collides with the first one's. The loser
   hangs on `input()` and leaves a stuck connection. On this dev host this
   is the most common way a stuck `test_netbox` appears — a sibling agent
   or shell loop-spawning `pytest` against the same worktree.
3. **An operator ran `pg_terminate_backend(pid) WHERE datname='test_netbox'`
   while a test run was actively migrating.** That kills the migration
   mid-statement and surfaces as
   `OperationalError: terminating connection due to administrator command`
   — which looks like a "monitor" killing the test runner but is the
   operator's own cleanup command hitting the live test run.

Recover (run from inside the worktree):

```bash
# 1. Kill any leftover test run still alive inside the container.
docker compose -f docker-compose.dev.yml exec -T netbox \
  bash -c "pkill -9 -f 'manage.py test' || true; pkill -9 -f 'pytest netbox_pyats' || true"

# 2. Drop the leftover idle connections holding test_netbox, then drop the DB.
docker compose -f docker-compose.dev.yml exec -T postgres \
  psql -U netbox -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='test_netbox';"
docker compose -f docker-compose.dev.yml exec -T postgres \
  psql -U netbox -d postgres -c "DROP DATABASE IF EXISTS test_netbox;"

# 3. Confirm it's gone, then re-run your test.
docker compose -f docker-compose.dev.yml exec -T postgres \
  psql -U netbox -d postgres -c "SELECT datname FROM pg_database WHERE datname LIKE 'test%';"
```

Prevention:

- **Don't run two test invocations against the same worktree's container at
  the same time.** Each worktree is one isolated compose stack; the
  container is single-tenant for test runs. If a second agent or shell
  needs to run tests, it should create its own worktree with
  `scripts/dev-worktree.sh add` and run against its own container.
- **Let a started test run finish.** The first run after a fresh stack
  takes ~5–8 minutes: it has to run ~200 NetBox migrations into
  `test_netbox` before any test code runs. Killing it mid-migration leaves
  the stuck `test_netbox` that the next run will trip on. If you must
  interrupt, run the recovery block above before starting another test run.
- **Never run `pg_terminate_backend` against `test_netbox` while a test
  run is in flight.** Check `pg_stat_activity` first: if you see an
  `active` (not `idle`) backend on `test_netbox`, a test run is migrating —
  wait for it.