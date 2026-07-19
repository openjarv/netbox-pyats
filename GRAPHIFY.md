# Graphify

This repo has a committed [Graphify](https://pypi.org/project/graphifyy/) code graph at
`graphify-out/`. Agents and humans query the graph instead of re-grepping every heartbeat.

## What is committed

- `graphify-out/graph.json` — raw graph data (nodes, edges, communities).
- `graphify-out/graph.html` — interactive visualization; open in a browser.
- `graphify-out/GRAPH_REPORT.md` — audit report with god nodes, community structure,
  surprising connections, and suggested questions.
- `graphify-out/manifest.json` — file fingerprints used by `graphify update`.

## What is NOT committed (gitignored)

- `graphify-out/cost.json` — cumulative token cost tracker (regenerable).
- `graphify-out/cache/` — AST/semantic extraction cache (regenerable).
- `graphify-out/.graphify_*` — internal run state (regenerable).
- `graphify-out/20*/` — dated backups created by the post-checkout hook.

## How the graph stays current

A post-commit and post-checkout git hook (installed via `graphify hook install`)
auto-rebuilds the AST graph on every commit and branch switch. No LLM cost.

A `.gitattributes` merge driver unions `graph.json` cleanly across branches:

```
graphify-out/graph.json merge=graphify
```

## How to query the graph

```bash
# Broad context, BFS traversal
graphify query "How does snapshot capture flow from the device tab to the RQ job?"

# Trace a specific path between two concepts
graphify path "PyatsSnapshot" "run_diff"

# Plain-language explanation of a node and its neighbors
graphify explain "PyatsCredential"
```

OpenCode agents in this repo are nudged (via `.opencode/plugins/graphify.js` and
`AGENTS.md`) to query the graph before raw file reads.

## How to refresh manually

```bash
# Incremental rebuild (AST-only, no API cost) after code changes
graphify update .

# Re-cluster only (regenerate GRAPH_REPORT.md / graph.html from existing graph.json)
graphify cluster-only .

# Full rebuild from scratch
graphify . --code-only
```

## Setup (already done — for reference)

```bash
uv tool install graphifyy                 # one-time install on the dev host
graphify . --code-only                    # build the AST graph
graphify cluster-only .                   # generate GRAPH_REPORT.md + graph.html
graphify hook install                     # post-commit / post-checkout auto-rebuild
graphify opencode install --project       # .opencode/ integration + AGENTS.md nudge
```

## Notes

- Code-only graph (no API key) for now — covers all plugin Python/Django code.
  Community names stay as `Community N` placeholders until an LLM backend
  (`GOOGLE_API_KEY` / `GEMINI_API_KEY`) is configured for `graphify label`.
- MCP server (`graphifyy[mcp]`) is out of scope for this repo; tracked in
  [ATW-40](/ATW/issues/ATW-40).