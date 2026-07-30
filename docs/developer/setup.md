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

### Base branch policy (ATW-208)

Every new worktree branch is based on the latest `origin/main`, not on
whatever the trunk happens to be checked out to. This keeps issue branches
from silently inheriting an unrelated feature branch's commits, and makes
the base of every worktree auditable.

`scripts/dev-worktree.sh add` enforces this. When you run `add`:

1. It refuses to create the worktree if the trunk working tree is not on
   `main` (or a branch tracking `origin/main`). A detached HEAD or a
   feature branch is rejected with a recovery message:
   ```bash
   git -C /home/hermes/netbox-pyats fetch origin main
   git -C /home/hermes/netbox-pyats branch -f main origin/main
   git -C /home/hermes/netbox-pyats checkout main
   ```
   Then re-run `dev-worktree.sh add`.
2. It runs `git fetch --quiet origin main` so the base is current. If the
   fetch fails (no network), it prints a warning and continues offline from
   local `main` when one exists — it never falls back to `HEAD` or another
   feature branch.
3. It refreshes (fast-forward) or creates local `main` from `origin/main`
   so the trunk worktree can return to it. If local `main` has diverged
   from `origin/main`, it refuses to rewrite local `main` and prints a
   warning instead.
4. It bases the new branch on `origin/main` (online) or local `main`
   (offline only), and prints the base ref and base SHA so the worktree's
   origin is auditable in the issue thread:
   ```
   base:            origin/main
   base SHA:        26797bd2dd1a9833b56fb3aaae428bae6f292d36
   ```

**Alternate base, by exception.** If a piece of work genuinely needs to
build on something other than `origin/main` — a hotfix branched from a
release tag, or work that builds on a merged-but-unreleased feature branch
— record the alternate base and the reason on the originating issue, then
run `git worktree add` by hand. No recorded reason on the issue = base
from `main`. The default has no comment because the default is `main`.

This applies to everyone creating worktrees in this repo, agents and humans
alike. See [ATW-208](/ATW/issues/ATW-208) for the script change that
enforces it and [ATW-200](/ATW/issues/ATW-200) for the policy decision.

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

Run the plugin's tests. There are two lanes:

- **Pure-Python / unit lane** (no Docker): `pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py ...` on the host. Seconds; no NetBox/PostgreSQL/Redis. The fast lane for logic changes (crypto, testbed, diff, compliance).
- **Integration lane** (Docker): the `netbox-test` compose service, which runs the full NetBox-dependent suite (model, view, API) without granian and with `--reuse-db`. See [Test lane (--reuse-db)](#test-lane---reuse-db) below.

## Test lane (`--reuse-db`)

The integration suite runs in a dedicated `netbox-test` compose service
([ATW-357](/ATW/issues/ATW-357), [ATW-351](/ATW/issues/ATW-351) ADR-1) that
runs pytest **without granian** and with pytest-django's `--reuse-db` flag.
This removes both sources of the historical test-iteration friction:

- **No granian** → no web-server connection holding `test_netbox` between
  runs, so the `database "test_netbox" already exists` / `is being accessed
  by other users` race (ATW-85 / ATW-188) cannot occur.
- **`--reuse-db`** → the migrated `test_netbox` schema persists across runs,
  so the ~480s NetBox migration cold start is paid once, not every iteration.
  A second run against the same stack completes in seconds, not 6–9 min.

The `netbox-test` service shares the worktree's `postgres` + `redis` (no
extra DB container), depends on them only (NOT `netbox`), and does not
publish a port or run a healthcheck — it is a one-shot pytest runner. The
web `netbox` UI stays up and reachable during a test run (no lifecycle
coupling), so you can keep iterating in the UI while tests run.

Run the test lane from inside a worktree:

```bash
scripts/dev-worktree.sh test
# equivalent to:
#   docker compose -f docker-compose.dev.yml -f docker-compose.test.yml \
#     --env-file .env up -d --wait postgres redis
#   docker compose -f docker-compose.dev.yml -f docker-compose.test.yml \
#     --env-file .env run --rm -T netbox-test
# (default command: --reuse-db netbox_pyats/tests)
```

The first run pays the migration cold start (~8-9 min) into `test_netbox`.
Re-run `dev-worktree.sh test` immediately after and it skips the migrations
and runs the suite in seconds.

Pass extra args through to pytest to override the default command:

```bash
# force a clean rebuild (drop + recreate test_netbox) when migrations change:
scripts/dev-worktree.sh test --create-db -v
# run a single test file:
scripts/dev-worktree.sh test netbox_pyats/tests/test_models.py
```

Use `--create-db` whenever you change a migration or suspect test-DB
drift — it drops and recreates `test_netbox` from scratch. CI uses
`--create-db` for every run (one-shot, authoritative pre-merge regression
pass); local uses `--reuse-db` for velocity.

The `netbox-test` service counts toward `MAX_CONCURRENT_STACKS` while it
runs ([ATW-356](/ATW/issues/ATW-356)), so two test runs (or a test run + a
web stack) cannot oversubscribe the host. See [Working in
parallel](#working-in-parallel).

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

`remove` reclaims root-owned bind-mount artifacts before `git worktree remove`
so teardown never strands on `Permission denied` (ATW-298). The netbox dev
containers run as root and write `__pycache__/`, `*.egg-info`, and
`.pytest_cache/` into the bind-mounted plugin source as root-owned; `remove`
chowns those gitignored paths back to the host UID/GID (recorded in the
worktree `.env` as `HOST_UID`/`HOST_GID`) via a one-shot root container, so
no host `sudo` is needed. The dev entrypoints also chown those artifacts back
to the host user after the editable install, so a manual `docker compose down`
leaves the worktree clean too.

## Resource limits

Each service has a default CPU + memory cap. Override any of them via shell
environment variables before `up`:

```bash
NETBOX_CPUS=2 NETBOX_MEM=4g \
PYATS_WORKER_CPUS=2 PYATS_WORKER_MEM=3g \
docker compose -f docker-compose.dev.yml up -d
```

| Service              | Var prefix          | Default CPU | Default mem |
| -------------------- | ------------------- | ----------- | ----------- |
| `netbox`             | `NETBOX_`           | 1.0         | 2g          |
| `netbox-worker`      | `WORKER_`           | 1.0         | 1g          |
| `netbox-pyats-worker`| `PYATS_WORKER_`     | 1.5         | 2g          |
| `postgres`           | `POSTGRES_`         | 0.5         | 512m        |
| `redis`              | `REDIS_`            | 0.5         | 256m        |

The `netbox` service also exposes `NETBOX_GRANIAN_WORKERS` (default `1`), which
sets the NetBox image's `GRANIAN_WORKERS` env var controlling how many granian
worker processes the web server spawns. The image's own default is 4 workers,
which is ~1064 MB of RSS before pytest even starts and OOM-kills the container
at the historical 1 GiB `mem_limit` during `docker compose exec netbox pytest`.
1 worker is plenty for local UI iteration and keeps the dev footprint low; raise
it (`NETBOX_GRANIAN_WORKERS=4`) only for local load testing. The `mem_limit`
default was raised from 1g to 2g to match the CI integration lane's
`NETBOX_MEM=2g` so local behaves like CI. See ATW-188 for the root-cause
diagnosis.

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

Quick reference (replace `<port>` with the worktree's `NETBOX_PORT`, and the
`<TAILSCALE_IP>` / `<TAILNET_FQDN>` placeholders with your dev host's Tailscale
values — see [Remote access over Tailscale](remote-access.md)):

```bash
# recommended, on the dev host (auto-HTTPS, tailnet-only):
tailscale serve --bg http://127.0.0.1:<port>
# open on your laptop: https://<TAILNET_FQDN>/
# stop with:          tailscale serve reset

# fallback, from your laptop (SSH tunnel over the Tailscale IP):
ssh -N -L 8000:127.0.0.1:<port> <user>@<TAILSCALE_IP>
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
- **Cap of 1 concurrent active worktree stack.** Each worktree runs its own
  full NetBox stack (postgres, redis, netbox, two workers) with per-service
  resource caps from [ATW-35](/ATW/issues/ATW-35). One stack is ~5.7 GiB of
  `mem_limit`; the host has 7.8 GiB RAM + 2 GiB swap, so 2 concurrent stacks
  (11.4 GiB) exceed total memory and guarantee OOM. The source of truth is
  `MAX_CONCURRENT_STACKS` in `scripts/dev-worktree.sh` (currently 1); this doc
  previously said 3, which was stale. Bump the cap only with CEO sign-off and
  only on a host with more RAM. The transient `netbox-test` service
  ([ATW-357](/ATW/issues/ATW-357)) also counts toward this cap while it runs,
  so two test runs (or a test run + a web stack) cannot oversubscribe the host
  ([ATW-356](/ATW/issues/ATW-356)).
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

> **Update (ATW-357):** the `netbox-test` compose service + `--reuse-db`
> workflow above is the structural fix for this race. Running pytest without
> granian removes the idle connection that held `test_netbox` between runs.
> The recovery steps below remain as a fallback for the legacy
> `docker compose exec netbox pytest` path or a stuck `test_netbox` left by
> an interrupted run.

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

**Root cause (confirmed 2026-07-26, ATW-188):** the `netbox` container runs
granian (the web server) *and* `pytest` in the same container. Granian's
worker processes hold persistent Django DB connections
(`CONN_MAX_AGE: 300` in `dev/configuration/configuration.py`). When pytest
finishes and Django's test runner drops `test_netbox`, a granian worker's
idle connection to `test_netbox` is left `idle in transaction` (verified via
`pg_stat_activity` — the connection's `client_addr` is the `netbox`
container's own IP on the `devnet` bridge). The next `pytest` run then fails:
`CREATE DATABASE test_netbox` → `DuplicateDatabase` (the previous DB wasn't
dropped), retry `DROP DATABASE` → `is being accessed by other users (1 other
session)` → `SystemExit: 2`. This is *not* a mystery monitor — it is the
container's own granian worker reconnecting to `test_netbox` between
`DROP` and `CREATE`. Reproduced deterministically: fresh `down -v && up --wait`
→ first `pytest` passes (~8-9 min); second `pytest` immediately after fails
in ~10s with the exact error above.

The `GRANIAN_WORKERS` default of 1 (set in `docker-compose.dev.yml`, ATW-193)
reduces the race surface to a single idle connection, but does not eliminate
it entirely — 1 worker can still hold `test_netbox`. The reliable workflow is
**one `pytest` run per fresh stack** (below).

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