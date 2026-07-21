# Contributing to netbox-pyats

Thanks for helping build the best NetBox plugin for the community. This guide covers local dev setup, tests, and the conventions we follow.

## Local dev environment

We ship a `docker-compose.dev.yml` that runs NetBox 4.6 with the plugin mounted as an editable install. The single safe path to start it is in [Dev environment bring-up](setup.md) — do not run `docker compose up` from arbitrary directories.

```bash
git clone https://github.com/openjarv/netbox-pyats.git
cd netbox-pyats
# create a worktree for your issue (see setup.md):
scripts/dev-worktree.sh add atw-XX <type> <slug>
cd ../netbox-pyats-wt/atw-XX
scripts/dev-worktree.sh up
```

NetBox is at `http://localhost:<NETBOX_PORT>` (the port the worktree claimed). The plugin is loaded from the repo via a bind mount; changes to Python files are picked up on container restart.

Login: `admin / admin` (default NetBox dev credentials).

## Running tests

### Pure-Python tests (no NetBox DB needed)

```bash
pip install -e ".[dev]"
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py \
       netbox_pyats/tests/test_diff.py netbox_pyats/tests/test_compliance.py
```

These run anywhere with Python 3.10+, Django, pyATS, and `cryptography` available (no PostgreSQL/Redis required). They are the fast lane for iterating on the credential encryption and the testbed builder. The `test_testbed.py` suite uses `pytest.importorskip("pyats")` so it skips cleanly if pyATS isn't installed.

### Full NetBox test suite (integration)

```bash
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

Runs the full suite (model, view, API) inside the NetBox container where the NetBox models are importable. The model/view/API tests use `pytest.importorskip("netbox")` and skip cleanly outside a NetBox environment.

## Lint and format

```bash
pip install -e ".[dev]"
black --check netbox_pyats
isort --check-only netbox_pyats
flake8 netbox_pyats
```

## Adding a supported platform

Edit `PLATFORM_SLUG_TO_PYATS_OS` in `netbox_pyats/testbed.py`. Only add a slug if Genie has real parser coverage for that os — unknown slugs degrade gracefully to "unsupported - no parser" by design, and silently mapping an unsupported os would produce empty snapshots and mislead operators.

## Adding a model

Follow the pattern of `PyatsCredential`:

1. Model in `models.py` (subclass `NetBoxModel`).
2. Migration in `migrations/` (one migration per schema change).
3. Choices in `choices.py`.
4. Form + filter form in `forms.py`.
5. Table in `tables.py`, filterset in `filtersets.py`, search index in `search.py`.
6. Views in `views.py`, URLs in `urls.py`.
7. REST serializer + viewset + router in `api/`.
8. GraphQL type in `graphql/schema.py`.
9. Detail template in `templates/netbox_pyats/`.
10. Navigation entries in `navigation.py`.
11. Tests: pure-Python where possible (skip with `pytest.importorskip("netbox")` for NetBox-dependent cases).

## Architectural decisions (ADRs)

Structural changes (package layout, background-work patterns, new model storage strategies, release process) are recorded as short ADRs in `docs/adr/`. See [docs/adr/README.md](../adr/README.md) for when an ADR is required and the format. The current locked ADRs are:

- [ADR-0001 — Plugin package layout](../adr/0001-plugin-layout.md)
- [ADR-0002 — Multi-vendor graceful degradation pattern](../adr/0002-graceful-degradation.md)
- [ADR-0003 — NetBox 4.6 migration dependencies and worker build toolchain](../adr/0003-netbox46-migration-and-worker-toolchain.md)
- [ADR-0004 — Compliance golden-config comparison shape](../adr/0004-compliance-golden-parse-shape.md)

The architectural baseline is the [architecture overview](https://github.com/openjarv/netbox-pyats) tracked on [ATW-23](/ATW/issues/ATW-23). Non-trivial PRs must fit the locked structure; if a PR would change it, open an ADR first and get CTO sign-off.

## Branch / PR conventions

- Branch off `main`; name branches `<type>/<issue-id>-<slug>` (e.g. `docs/atw-82-docs-update`). The `scripts/dev-worktree.sh add` helper does this for you.
- One PR per issue; reference the issue in the PR description.
- Do not commit directly to `main`; use branches and PRs.
- Do not publish to PyPI without CEO sign-off on the first release.

## CI

See [CI](ci.md) for the three lanes and what each one enforces. Keep `lint` and `unit` green on every PR. Do not merge if either is red.