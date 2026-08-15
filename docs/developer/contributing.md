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
make test-unit            # 204 tests, ~3s, no Docker
# or directly:
scripts/test-unit.sh
```

The full module list lives in `scripts/test-unit.sh` and stays in sync with the CI `unit` lane (`.github/workflows/ci.yml`). If you prefer to invoke `pytest` directly, read the module list from that script rather than copying a command from here — the long-form list drifts as new pure-Python modules are added.

These run anywhere with Python 3.10+, Django, pyATS, and `cryptography` available (no PostgreSQL/Redis required). They are the fast lane for iterating on the diff engine, testbed builder, capture parser, compliance comparison, and credential crypto. The `test_testbed.py` suite uses `pytest.importorskip("pyats")` so it skips cleanly if pyATS isn't installed. See [setup.md — Test lane split](setup.md#test-lane-split) for when to use the unit vs integration lane.

### Full NetBox test suite (integration)

```bash
# from a worktree (see setup.md):
scripts/dev-worktree.sh test
```

Runs the full suite (model, view, API) inside a dedicated `netbox-test`
container that runs pytest without granian and with `--reuse-db`, so the
migrated `test_netbox` schema persists across runs (the ~480s migration cold
start is paid once). See [Dev environment bring-up — Test lane
(`--reuse-db`)](setup.md#test-lane---reuse-db) for the full workflow and
[ATW-357](/ATW/issues/ATW-357) / [ATW-351](/ATW/issues/ATW-351) for the
rationale. The model/view/API tests use `pytest.importorskip("netbox")` and
skip cleanly outside a NetBox environment.

### Test-conventions invariant (`--reuse-db` safety)

`--reuse-db` keeps the `test_netbox` **schema** across runs; per-test data
isolation comes from Django's `TestCase` transaction rollback (every
NetBox-gated test subclasses `utilities.testing.TestCase` / `APITestCase`).
For that to stay safe, **integration tests must scope assertions to rows
they create, not table-wide `count() == N` on a clean table.** A kept schema
does not reset auto-increment sequences or clear pre-existing rows, so a
table-wide count that assumes an empty table is a latent bug under
`--reuse-db`. Scope counts to rows the test itself created in `setUpTestData`
/ `setUp` (e.g. `PyatsSnapshot.objects.filter(pk=snap.pk).count()`). This is
an enforced going-forward invariant; the existing tree was audited and
conforms ([ATW-353](/ATW/issues/ATW-353)).

## Lint and format

```bash
pip install -e ".[dev]"
black --check netbox_pyats
isort --check-only netbox_pyats
flake8 netbox_pyats
```

## Secret / PII leakage gate (pre-commit + gitleaks)

A `pre-commit` hook running [gitleaks](https://github.com/gitleaks/gitleaks) is
committed as defense-in-depth against the secret/PII leakage class (see
[ATW-116](/ATW/issues/ATW-116)). It catches Tailscale CGNAT IPs
(`100.64.0.0/10`), Tailscale DNS (`*.ts.net` / `*.tscale.net` /
`*.tailscale.com`), Paperclip agent/server identifiers, private keys, and the
upstream gitleaks defaults (GitHub tokens, cloud provider secrets, etc.)
**before a secret reaches the public repo**.

Install once per clone:

```bash
pip install pre-commit
pre-commit install
```

Run manually across the whole tree (e.g. after pulling new rules):

```bash
pre-commit run gitleaks --all-files
```

The rules live in [`.gitleaks.toml`](../../.gitleaks.toml). The repo uses a
`<...>` placeholder convention for infra values in docs
(`<TAILSCALE_IP>`, `<TAILNET_FQDN>`); the allowlist whitelists those forms so
the documented redacted runbook does not false-positive. When you add a new
infra placeholder, add the matching allowlist entry.

The pure-Python regression test for the rules is
`netbox_pyats/tests/test_secret_detection.py` (fast lane, no NetBox needed).

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

## Test conventions

- **Scope assertions to rows the test creates, never table-wide `count() == N`.** See [Test-conventions invariant (`--reuse-db` safety)](#test-conventions-invariant---reuse-db--safety) above for the rationale and a concrete example. The existing tree was audited and conforms ([ATW-353](/ATW/issues/ATW-353)); keep new tests conformant.
- **Prefer `pytest.importorskip` over `try/except ImportError`.** It produces a clean skip in the lane that lacks the dependency rather than a silent pass or a collection error.
- **Lane discipline.** Pure-Python unit tests belong in the five
  logic-core modules (`test_diff`, `test_testbed`, `test_capture`,
  `test_compliance`, `test_crypto`) and must not carry
  `@pytest.mark.django_db` — that mark is the integration-lane contract (it
  tells pytest-django to stand up a test database). A `django_db`-marked test
  in the unit set would fail outside NetBox or silently drag the unit lane
  into needing a database. If a test needs the DB, it belongs in the
  integration lane, not the unit set. See [setup.md — Test lane
  split](setup.md#test-lane-split).
- **Sync the split.** If you add a pure-Python logic test module, add it to
  both `scripts/test-unit.sh` and the CI `unit` lane in
  `.github/workflows/ci.yml` so the two stay in sync.

## Architectural decisions (ADRs)

Structural changes (package layout, background-work patterns, new model storage strategies, release process) are recorded as short ADRs in `docs/adr/`. See [docs/adr/README.md](../adr/README.md) for when an ADR is required and the format. The current locked ADRs are:

- [ADR-0001 — Plugin package layout](../adr/0001-plugin-layout.md)
- [ADR-0002 — Multi-vendor graceful degradation pattern](../adr/0002-graceful-degradation.md)
- [ADR-0003 — NetBox 4.6 migration dependencies and worker build toolchain](../adr/0003-netbox46-migration-and-worker-toolchain.md)
- [ADR-0004 — Compliance golden-config comparison shape](../adr/0004-compliance-golden-parse-shape.md)
- [ADR-0005 — PyatsJob unified job-tracking model + status vocabulary extension](../adr/0005-pyatsjob-model.md)
- [ADR-0006 — PR-body hygiene](../adr/0006-pr-body-hygiene.md)
- [ADR-0007 — Device-page tab via `register_model_view` + `ObjectView` + `ViewTab`](../adr/0007-device-page-tab.md)
- [ADR-0008 — Scheduling surface for recurring snapshot capture](../adr/0008-scheduling-surface.md)
- [ADR-0005 — PyatsJob unified job-tracking model](../adr/0005-pyatsjob-model.md)
- [ADR-0006 — PR-body hygiene](../adr/0006-pr-body-hygiene.md)
- [ADR-0007 — Device-page tab via `register_model_view` + `ObjectView`](../adr/0007-device-page-tab.md)

The architectural baseline is the [architecture overview](https://github.com/openjarv/netbox-pyats) tracked on [ATW-23](/ATW/issues/ATW-23). Non-trivial PRs must fit the locked structure; if a PR would change it, open an ADR first and get CTO sign-off.

## Branch / PR conventions

- Branch off `main`; name branches `<type>/<issue-id>-<slug>` (e.g. `docs/atw-82-docs-update`). The `scripts/dev-worktree.sh add` helper does this for you.
- One PR per issue; reference the issue in the PR description.
- Do not commit directly to `main`; use branches and PRs.
- Do not publish to PyPI without CEO sign-off on the first release.

## PR body hygiene (ATW-159)

The PR *body* is a public artifact — anyone reading the repo can see it. Do
not paste Paperclip control-plane metadata into it. The CI lane
`pr-body-scrub-guard` (scripts/pr-body-scrub-guard.sh) fails the PR if any of
the following are present in the body:

- `agent://<uuid>` URIs (full Paperclip agent links)
- bare agent UUIDs (RFC-4122 8-4-4-4-12 hex)
- 8-char agent-ID prefixes in an `(agent <prefix>)` / `agent <prefix>` context

This is a repeat finding across PRs #44–#47, escalated as
[ATW-159](/ATW/issues/ATW-159). The realistic harm is org-structure
disclosure + confirming Atw runs Paperclip agents (aids targeted social
engineering); no direct code-exec or data-access path from this leak
alone. It is enforced structurally because review alone did not catch it.

**Role-only labels are fine.** `reviewer: CTO` and `merger: CEO` (role
title, no IDs) are the *allowed* form — the leak is the agent ID/URI, not
the role title. Role words in normal prose ("The QA Engineer will run
regression") are also fine. Omit the reviewer/merger lines entirely if in
doubt — GitHub's reviewer-request UI is the real assignment path.

The `.github/PULL_REQUEST_TEMPLATE.md` carries the convention with an HTML
comment that does not render in the body. The pure-Python regression test
is `netbox_pyats/tests/test_pr_body_scrub_guard.py` (fast lane, no NetBox
needed). Sibling guard: `scripts/graphify-scrub-guard.sh` for
graphify-out/ artifacts (ATW-125).

## CI

See [CI](ci.md) for the three lanes and what each one enforces. Keep `lint` and `unit` green on every PR. Do not merge if either is red.