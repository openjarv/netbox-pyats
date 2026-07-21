# Graphify MCP HTTP server — multi-host / shared-service runbook

This is the **deferred multi-host upgrade path** from the stdio graphify-mcp
server wired in [ATW-40](/ATW/issues/ATW-40). It containerizes the
`graphify-mcp` Streamable HTTP transport so Atw agents on **other hosts**
can reach a shared code-graph server over the network with a Bearer api-key.

**Do not deploy this on a single dev host.** The stdio server (see
[Graphify MCP](graphify-mcp.md)) is simpler, safer, and already wired
into every `opencode_local` agent's OpenCode MCP config. This HTTP
container only needs to come up when:

- Atw agents span more than one host, or
- The board asks for a centralized graph service ([ATW-42](/ATW/issues/ATW-42)).

Owned by the Infrastructure Engineer. Built in [ATW-42](/ATW/issues/ATW-42).

## What this gives you

- A containerized `graphify-mcp --transport http --stateless` server
  serving the committed `graphify-out/graph.json` over `POST /mcp`.
- Bearer api-key enforcement: unauthenticated requests get `401`, valid
  `Authorization: Bearer <key>` requests get `200` with real graph data.
- Loopback-only publish on the host (`127.0.0.1:8090`) — never the host's
  public IP. Remote hosts reach it over SSH port forwarding or a private
  network.
- An isolated user-defined bridge network (`graphify-net`) separate from
  the dev stack's `devnet`, so the graph server has no path to
  postgres/redis/netbox and vice versa.
- Per-container CPU + memory caps, a healthcheck that verifies both
  liveness and api-key enforcement, and `restart: unless-stopped`.
- File-based secret delivery via compose `secrets:` — the key is never
  baked into the image, never in the process argv, and never in the
  healthcheck command.

## Files

| Path | Purpose |
| --- | --- |
| `dev/graphify-mcp/Dockerfile` | Image: `python:3.12-slim` + uv + `graphifyy[mcp]==0.9.20`, non-root, healthcheck. |
| `dev/graphify-mcp/entrypoint.sh` | Loads `/run/secrets/graphify_api_key` into `GRAPHIFY_API_KEY`, fails fast if missing, execs `graphify-mcp --transport http --stateless`. |
| `dev/graphify-mcp/healthcheck.py` | Unauthenticated POST → expects `401`. Proves the server is up AND enforcing the key. |
| `docker-compose.graphify-mcp.yml` | Compose **overlay** (separate from `docker-compose.dev.yml`). One service, one network, one secret. |
| `scripts/graphify-mcp-key.sh` | Generate / rotate / fingerprint the api-key. Writes `dev/graphify-mcp/api-key` (mode 0600, gitignored). |
| `docs/developer/graphify-mcp-http.md` | This runbook. |

The key file `dev/graphify-mcp/api-key` is **gitignored** — never commit it.
If you ever commit it by accident, rotate immediately and treat the old key
as compromised.

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose`).
- A worktree set up via `scripts/dev-worktree.sh add` (the hard rule from
  [Dev environment bring-up](setup.md) applies — never run compose from
  the trunk working tree).
- The committed `graphify-out/graph.json` in the repo (produced by
  [ATW-39](/ATW/issues/ATW-39), refreshed by the [ATW-41](/ATW/issues/ATW-41)
  nightly routine).

## Bring-up (from a worktree)

```bash
cd /home/hermes/netbox-pyats-wt/<issue-id>

# 1. Generate the api-key (writes dev/graphify-mcp/api-key, mode 0600,
#    gitignored). Keep the printed key — you'll need it for the agent MCP
#    config on each remote host.
scripts/graphify-mcp-key.sh generate
#   → e.g. k7Hm2vQ9xZp4Rf8sN1wL3yB6tD0cJ5aE...

# 2. Build and bring up the graphify-mcp service as an overlay on the dev
#    compose stack. The overlay only declares graphify-mcp + its network +
#    its secret; it does not touch the dev stack's services.
docker compose -f docker-compose.dev.yml \
  -f docker-compose.graphify-mcp.yml up -d --build graphify-mcp

# 3. Wait for the healthcheck to flip to healthy (≤10s start_period).
docker compose -f docker-compose.dev.yml \
  -f docker-compose.graphify-mcp.yml ps graphify-mcp
#   → (healthy)

# 4. Smoke test from the host (loopback):
KEY="$(scripts/graphify-mcp-key.sh show)"
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://127.0.0.1:8090/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}'
#   → 200

# 5. Verify api-key enforcement (unauthenticated):
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://127.0.0.1:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
#   → 401
```

If step 4 returns `401`, the key in the container doesn't match the key on
disk — recreate the container (`--force-recreate graphify-mcp`). If step 5
returns `200`, the server is running unauthenticated: **stop immediately**
and check that `dev/graphify-mcp/api-key` is non-empty and that the
`secrets:` block in the compose overlay is intact.

## Remote agent wiring (Senior Dev Engineer)

On each remote host, point the OpenCode MCP config at the server over HTTP
with the api-key:

```jsonc
// ~/.config/opencode/opencode.jsonc
{
  "mcp": {
    "graphify": {
      "type": "remote",
      "url": "http://<dev-host>:8090/mcp",
      "headers": {
        "Authorization": "Bearer {env:GRAPHIFY_API_KEY}"
      },
      "enabled": true
    }
  }
}
```

`<dev-host>` is reached over SSH port forwarding (`ssh -L
8090:127.0.0.1:8090 <dev-host>`) or a private network — never by widening
the compose `ports:` binding to `0.0.0.0`. The agent's
`GRAPHIFY_API_KEY` env var holds the key (set via the agent's environment,
not committed to config).

Tools are namespaced the same way as the stdio server:
`graphify_query_graph`, `graphify_get_node`, `graphify_get_neighbors`,
`graphify_shortest_path`, `graphify_get_community`, `graphify_god_nodes`,
`graphify_graph_stats`. Per-call `project_path` still works, so one server
can serve any repo that has a committed `graphify-out/graph.json` — but in
HTTP mode the server only has the bind-mounted graph(s) on the dev host;
repos on other hosts are reached by `project_path` pointing at a path that
exists on the dev host (or a shared volume).

## Secret rotation

Owned by the Infrastructure Engineer. Rotate on a schedule (every 90 days
for the dev-time key) or immediately on suspected compromise.

```bash
cd /home/hermes/netbox-pyats-wt/<issue-id>

# Print the current fingerprint for the audit trail (safe to post):
scripts/graphify-mcp-key.sh fingerprint
#   → old: 3f2a1b8c9d0e7f6a

# Rotate:
scripts/graphify-mcp-key.sh rotate
#   → writes a new key, prints the new fingerprint and the rotation steps.

# Recreate the container so it picks up the new secret:
docker compose -f docker-compose.dev.yml \
  -f docker-compose.graphify-mcp.yml up -d --force-recreate graphify-mcp

# Update each remote agent's GRAPHIFY_API_KEY / MCP config headers, then
# restart those agents' heartbeats.

# Post the new fingerprint (NOT the key) to the issue thread for audit:
scripts/graphify-mcp-key.sh fingerprint
#   → new: 8c4d2e1f0a9b7c3d
```

The old key is revoked the moment the container restarts with the new one —
it no longer exists on the server, so it cannot authenticate. There is no
"old key still valid during overlap" window; if you need overlap (e.g.
many remote agents), coordinate the rolling restart so all agents move to
the new key before the container restarts, or run two graphify-mcp
replicas on different ports during the cutover.

## Teardown

```bash
docker compose -f docker-compose.dev.yml \
  -f docker-compose.graphify-mcp.yml down -v
# Removes the graphify-mcp container, its network, and any anonymous
# volumes. Does NOT touch the dev stack's volumes.
```

The `dev/graphify-mcp/api-key` file stays on disk (gitignored). Remove it
manually with `rm dev/graphify-mcp/api-key` if you want a clean slate; the
key is no longer usable once the container is down.

## Hardening summary (audit checklist)

- [x] **No public exposure.** `ports: 127.0.0.1:${GRAPHIFY_MCP_PORT:-8090}:8080`.
      Loopback-only on the host. Remote access via SSH port forwarding or a
      private network, never by widening the binding.
- [x] **Isolated network.** `graphify-net` bridge, separate from `devnet`.
      The graph server cannot reach postgres/redis/netbox and they cannot
      reach it.
- [x] **Secret not in image.** The api-key is a compose file-based secret,
      loaded by the entrypoint shim into `GRAPHIFY_API_KEY` at runtime.
      `docker inspect` on the image shows no key.
- [x] **Secret not in process argv.** The key is read from the env var, not
      passed via `--api-key`, so `docker inspect` on the container's
      process args shows no key.
- [x] **Secret not in healthcheck.** The healthcheck posts an
      unauthenticated request and expects `401`; the key never appears in
      `docker inspect` healthcheck output.
- [x] **Fail-fast on missing secret.** The entrypoint exits 1 if the secret
      file is missing or empty, so the container never starts an
      unauthenticated `0.0.0.0` server by accident.
- [x] **Resource caps.** `cpus: 0.5`, `mem_limit: 256m` by default;
      override via `GRAPHIFY_MCP_CPUS` / `GRAPHIFY_MCP_MEM` env vars.
- [x] **Healthcheck verifies enforcement, not just liveness.** A
      misconfigured server with no api-key returns `200` to the
      unauthenticated probe and is marked unhealthy.
- [x] **Restart policy.** `restart: unless-stopped` self-recovers from
      transient crashes.
- [x] **Non-root runtime.** `USER graphify` (uid 1001); the graph bind
      mount is read-only.
- [x] **Key file gitignored.** `scripts/graphify-mcp-key.sh generate` adds
      `dev/graphify-mcp/api-key` to `.gitignore` automatically.

## Verified during ATW-42

- HTTP transport + `--api-key` + `--stateless` works: unauthenticated
  `POST /mcp` → `401`; `Authorization: Bearer <key>` → `200` with real
  `query_graph` results against `netbox-pyats/graphify-out/graph.json`.
- `graphify-mcp` reads `GRAPHIFY_API_KEY` from the env (no `_FILE`
  variant), so the entrypoint shim is required for compose file-based
  secrets.
- The server logs `api-key required` at startup and warns loudly if bound
  to `0.0.0.0` with no key.

## Decisions

- **stdio remains the default** for single-host setups. This HTTP
  container is the opt-in multi-host path, not a replacement.
- **File-based compose secret over env-var compose secret** because the
  key file is easier to rotate (one file, one `chmod 0600`, one
  `.gitignore` entry) and doesn't leak via `docker inspect` env blocks.
- **Overlay compose file** (`docker-compose.graphify-mcp.yml`, not edits
  to `docker-compose.dev.yml`) so the default dev stack stays lean and
  the HTTP server is an explicit opt-in.
- **`--stateless` always on** so the container is safe behind a load
  balancer / for parallel CI runs; we never need stateful MCP sessions
  for code-graph queries.
- **No swarm / `docker secret`** — the dev host is a single Docker
  engine, not a swarm. Compose file-based secrets work on a standalone
  engine and don't require `docker swarm init`.