# Contributing to netbox-pyats

Thanks for helping build the best NetBox plugin for the community. This guide covers local dev setup, tests, and the conventions we follow.

## Local dev environment

We ship a `docker-compose.dev.yml` that runs NetBox 4.6 with the plugin mounted as an editable install.

```bash
git clone https://github.com/openjarv/netbox-pyats.git
cd netbox-pyats
docker compose -f docker-compose.dev.yml up -d
```

NetBox is at http://localhost:8000. The plugin is loaded from the repo via a bind mount; changes to Python files are picked up on container restart.

Login: `admin / admin` (default NetBox dev credentials).

## Running tests

### Pure-Python tests (no NetBox DB needed)

```bash
pip install -e ".[dev]"
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py
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

## Branch / PR conventions

- Branch off `main`; name branches `<scope>-<topic>` (e.g. `plugin-scaffold-credential-testbed`).
- One PR per issue; reference the issue in the PR description.
- Do not commit directly to `main`; use branches and PRs.
- Do not publish to PyPI without CEO sign-off on the first release.