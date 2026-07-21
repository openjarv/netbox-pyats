# Graphify MCP

OpenCode agents in this repo query the committed code graph
(`graphify-out/graph.json`) through a `graphify-mcp` MCP server. This file
documents the two transports and when to use each. For the graph itself
(contents, refresh, hooks) see [GRAPHIFY.md](GRAPHIFY.md); for the HTTP
container runbook see [docs/graphify-mcp-http.md](docs/graphify-mcp-http.md).

## When to use which transport

| Transport | When | Owned by |
| --- | --- | --- |
| `local` / stdio | Single dev host. All Atw agents are `opencode_local` on one host. Default. | Senior Dev Engineer ([ATW-40](/ATW/issues/ATW-40)) |
| `remote` / HTTP | Atw agents span more than one host, or the board asks for a centralized graph service. Opt-in. | Infrastructure Engineer ([ATW-42](/ATW/issues/ATW-42)) |

Do **not** switch to HTTP just because the HTTP container exists. The stdio
server is simpler and safer on a single host — no network surface, no
api-key, no container. Switch only when there is a concrete multi-host need.

## Tools exposed (both transports)

Identical tool surface, namespaced `graphify_*`:

- `graphify_query_graph` — natural-language / keyword search (BFS or DFS)
- `graphify_get_node` — full details for a node by label or id
- `graphify_get_neighbors` — direct neighbors with edge details
- `graphify_shortest_path` — shortest path between two concepts
- `graphify_get_community` — all nodes in a community by id
- `graphify_god_nodes` — most connected nodes (core abstractions)
- `graphify_graph_stats` — node / edge / community summary

Per-call `project_path` works in both transports. In stdio mode it points at
a local repo path; in HTTP mode it points at a path mounted on the server
host (or a shared volume).

## stdio config (single-host, default)

Wired in [ATW-40](/ATW/issues/ATW-40). The agent spawns `graphify-mcp` as a
child process; no network, no api-key.

```jsonc
// ~/.config/opencode/opencode.jsonc
{
  "mcp": {
    "graphify": {
      "type": "local",
      "command": [
        "graphify-mcp",
        "--transport",
        "stdio",
        "--graph",
        "/home/hermes/netbox-pyats/graphify-out/graph.json"
      ],
      "enabled": true
    }
  }
}
```

Prerequisites on the host:

- `uv tool install graphifyy[mcp]` (one-time; matches the version pinned in
  the HTTP container — see `dev/graphify-mcp/Dockerfile`).
- The committed `graphify-out/graph.json` at the path in `--graph`.

The `--graph` path is absolute, so each host's config points at its own
working copy. The graph stays current via the post-commit / post-checkout
hooks (see [GRAPHIFY.md](GRAPHIFY.md)).

## remote / HTTP config (multi-host, opt-in)

Switch to this only when a second Atw agent host comes online. Brings up the
containerized `graphify-mcp --transport http --stateless` server from
[ATW-42](/ATW/issues/ATW-42) and points each remote agent at it over HTTP
with a Bearer api-key.

```jsonc
// ~/.config/opencode/opencode.jsonc  (on each remote host)
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

- `<dev-host>` is reached over SSH port forwarding
  (`ssh -L 8090:127.0.0.1:8090 <dev-host>`) or a private network — never
  by widening the compose `ports:` binding to `0.0.0.0`.
- `GRAPHIFY_API_KEY` is set in each remote agent's environment, not
  committed to config. The key is generated on the dev host by
  `scripts/graphify-mcp-key.sh generate` and rotated by `... rotate`.
- The compose binding stays `127.0.0.1:8090` (loopback-only).

Full bring-up, smoke test, secret rotation, and hardening audit checklist:
[docs/graphify-mcp-http.md](docs/graphify-mcp-http.md).

## Switching from stdio to HTTP

When a second host comes online, on each affected host:

1. Bring up the HTTP server on the dev host (runbook:
   [docs/graphify-mcp-http.md](docs/graphify-mcp-http.md)).
2. Generate / obtain the api-key and set `GRAPHIFY_API_KEY` in the remote
   agent's environment.
3. Replace the `mcp.graphify` block in `~/.config/opencode/opencode.jsonc`
   with the `remote` config above.
4. Smoke test from a heartbeat: `graphify_query_graph` / `graphify_get_node`
   / `graphify_get_neighbors` / `graphify_shortest_path` return real
   results against the shared server.

Switching back to stdio is the reverse: replace the `remote` block with the
`local` block above and unset `GRAPHIFY_API_KEY`. The HTTP container can be
torn down independently (it does not touch the dev stack's volumes).