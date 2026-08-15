## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Contributing

The contributor guide, dev environment, test lanes, and PR/ADR conventions live in the docs tree. These are the entry points:

- Contributor guide: [CONTRIBUTING.md](CONTRIBUTING.md) → [docs/developer/contributing.md](docs/developer/contributing.md)
- Dev environment bring-up: [docs/developer/setup.md](docs/developer/setup.md)
- Worktree workflow: `scripts/dev-worktree.sh add <issue-id> <type> <slug>` then `scripts/dev-worktree.sh up` / `test` / `remove`
- Lint: `black --check netbox_pyats && isort --check-only netbox_pyats && flake8 netbox_pyats`
- Unit tests (no NetBox): `scripts/test-unit.sh` (or `make test-unit`)
- Integration tests (NetBox): `scripts/dev-worktree.sh test`
- CI lanes reference: [docs/developer/ci.md](docs/developer/ci.md)
- Branch / PR conventions + PR-body hygiene (ATW-159): [docs/developer/contributing.md#branch--pr-conventions](docs/developer/contributing.md)
- ADR process: [docs/adr/](docs/adr/) and [docs/developer/contributing.md#architectural-decisions-adrs](docs/developer/contributing.md)
