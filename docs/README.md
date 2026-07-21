# netbox-pyats documentation

Welcome. This is the documentation hub for the **netbox-pyats** plugin — an [Atw](https://github.com/openjarv) [NetBox](https://netbox.dev) plugin that brings [Cisco PyATS / Genie](https://developer.cisco.com/pyats/) into the NetBox UI.

Pick the path that matches what you are trying to do.

## For operators (running the plugin in NetBox)

You know NetBox. You want to install the plugin, capture a snapshot, diff two snapshots, or run a compliance check against a golden config.

- [Installation](user/installation.md) — install the plugin, configure NetBox, and run your first capture.
- [Usage guide](user/usage.md) — the capture → diff → compliance workflow with exact UI paths.
- [PyATS worker deployment](user/workers.md) — run the dedicated `pyats` RQ queue (required for snapshots, diffs, and compliance).
- [Credential encryption](user/credentials.md) — how plugin-local device credentials are encrypted and rotated.
- [Compliance engine](user/compliance.md) — what the golden-config compliance check classifies and why.
- [Troubleshooting](user/troubleshooting.md) — operator-facing fixes for the most common failure modes.

## For contributors (developing the plugin)

You are an engineer working on the plugin itself. You need the dev environment, the CI lanes, the graph tooling, or the ADRs.

- [Contributing guide](developer/contributing.md) — local dev setup, tests, lint, and the conventions we follow.
- [Dev environment bring-up](developer/setup.md) — the single safe path to start the dev stack on the dev server.
- [CI](developer/ci.md) — the three CI lanes and what each one enforces.
- [Graphify](developer/graphify.md) — the committed code graph and how to query it.
- [Graphify MCP](developer/graphify-mcp.md) — stdio vs HTTP MCP transports for the graph server.
- [Graphify MCP HTTP runbook](developer/graphify-mcp-http.md) — multi-host / shared-service bring-up for the graph server.

## For everyone

- [Architecture Decision Records](adr/README.md) — the locked structural decisions and when a new ADR is required.
- [Changelog](../CHANGELOG.md) — every notable change per release.
- [Project README](../README.md) — the GitHub landing page with the feature overview and compatibility matrix.

## Conventions

- **Audience split.** `docs/user/` assumes the reader knows NetBox but not this plugin. `docs/developer/` assumes the reader is a contributor and already knows the user docs.
- **Voice.** Short intros, numbered steps, code blocks, explicit compatibility notes. No marketing fluff.
- **Links.** Every doc links to its siblings via relative paths. This index is the hub. If you add a doc, add it here.
- **Drift.** Docs that describe shipped behavior must cite the source PR or issue. When a PR changes user-visible behavior, open the matching docs PR in the same heartbeat.