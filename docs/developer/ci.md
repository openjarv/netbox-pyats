# CI

CI runs on every push to `main` and every PR via [.github/workflows/ci.yml](../../.github/workflows/ci.yml). Three lanes, mirroring the dual-mode test setup in `conftest.py` and the compatibility matrix (NetBox 4.6.x × Python 3.10 / 3.11 / 3.12 × pyATS 26.x worker-only).

## Lanes

### `lint`

`black --check`, `isort --check-only`, `flake8`. Fast; single Python (3.12).

```bash
black --check netbox_pyats
isort --check-only netbox_pyats
flake8 netbox_pyats
```

### `unit`

Pure-Python tests on the compatibility-matrix Python versions (3.10 / 3.11 / 3.12) with `pyats[full]` installed so the testbed suite runs instead of skipping. No NetBox / PostgreSQL / Redis required.

```bash
pip install -e ".[dev]" "pyats[full]>=26.0"
pytest netbox_pyats/tests/test_crypto.py netbox_pyats/tests/test_testbed.py \
       netbox_pyats/tests/test_diff.py netbox_pyats/tests/test_capture.py \
       netbox_pyats/tests/test_compliance.py netbox_pyats/tests/test_supported_platforms.py \
       netbox_pyats/tests/test_graphify_scrub_guard.py \
       netbox_pyats/tests/test_pr_body_scrub_guard.py \
       netbox_pyats/tests/test_secret_detection.py
```

The CI `unit` lane runs the five logic-core modules (`test_diff`,
`test_testbed`, `test_capture`, `test_compliance`, `test_crypto`) plus the
repo-hygiene pure-Python guards (`test_supported_platforms`,
`test_graphify_scrub_guard`, `test_pr_body_scrub_guard`,
`test_secret_detection`). Locally, `scripts/test-unit.sh` (or
`make test-unit`) runs just the five logic-core modules — see
[setup.md — Test lane split](setup.md#test-lane-split) for the decision
rule and how to keep the split clean.

This is the lane that enforces the Python-version matrix on every PR.

### `integration`

Full NetBox-dependent suite inside a dedicated `netbox-test` container (`docker-compose.dev.yml` + `docker-compose.test.yml`, [ATW-357](/ATW/issues/ATW-357)) with the default backend versions (NetBox 4.6.5 × PostgreSQL 18 × Valkey 9.1). Gating (`continue-on-error: false`); the NetBox 4.6 dev-image compatibility work ([ATW-25](/ATW/issues/ATW-25)) and the gating flip ([ATW-49](/ATW/issues/ATW-49)) have landed.

The `netbox-test` service runs pytest **without granian**, removing the granian-connection race (ATW-85 / ATW-188) that previously made re-runs unreliable. CI and local dev use the same container shape; CI uses `--create-db` for a clean, authoritative pre-merge regression pass (migration-order + data-leakage coverage), while local dev uses `--reuse-db` for velocity (the migrated `test_netbox` schema persists across runs). See [ATW-351](/ATW/issues/ATW-351) ADR-1 for the rationale.

The integration lane runs a **single cell**, not a PostgreSQL × Redis matrix. An audit for [ATW-96](/ATW/issues/ATW-96) found the plugin has no direct PostgreSQL or Redis surface (Django ORM + `JSONField` only; RQ queue declared by name and enqueued via `netbox.core.Job.enqueue`), so sweeping backend versions tests NetBox's infrastructure rather than the plugin. The board accepted collapsing the matrix on 2026-07-22.

The integration lane is a **required** check: no merge is green without it passing. Python is not swept here because the NetBox community image pins Python internally; the `unit` lane above exercises Python 3.10/3.11/3.12.

Bring-up is **scoped** to `postgres redis` — the `netbox-test` service depends on them only (NOT `netbox`), so the web server, workers, and `netbox-pyats-worker` are not started. The plugin's test suite is designed to run without workers: `conftest.py` dual-mode skips cleanly when the RQ backend is absent, test files gate themselves with `pytest.importorskip`, and job-callable tests invoke `run_*_job` directly rather than through the queue. The workers are only needed for live device capture from the UI. Refs: [ATW-244](/ATW/issues/ATW-244), [ATW-245](/ATW/issues/ATW-245).

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.test.yml up -d --wait postgres redis
docker compose -f docker-compose.dev.yml -f docker-compose.test.yml run --rm -T netbox-test --create-db netbox_pyats/tests -v
```

To run against different backend versions locally, pass the image overrides the compose file reads (see [Image overrides](setup.md#image-overrides-compatibility-sweeps) in the setup guide):

```bash
NETBOX_IMAGE=docker.io/netboxcommunity/netbox:v4.6-5.0.2 \
PG_VERSION=16-alpine \
REDIS_IMAGE=redis:7-alpine \
REDIS_SERVER=redis-server \
  docker compose -f docker-compose.dev.yml up -d --wait
```

## What to keep green

Keep `lint`, `unit`, and `integration` green on every PR. Do not merge if any lane is red.

The integration lane runs inside the dev container; if it fails locally but passes in CI (or vice versa), check that your local dev stack is up to date with `docker-compose.dev.yml`.

## References

- Architecture decision D-7 ([ATW-23](/ATW/issues/ATW-23) architecture document, §4 / §5).
- [ATW-38](/ATW/issues/ATW-38): NetBox 4.6.5 compatibility fixes (PR #15).
- [ATW-96](/ATW/issues/ATW-96): compatibility-matrix CI (collapsed to single cell per audit + board decision).
- [ATW-101](/ATW/issues/ATW-101): apt-retry + backoff in the pyats-worker Dockerfile (PR #35).
- [Contributing](contributing.md) — local dev setup, tests, and lint commands.
- [Dev environment bring-up](setup.md) — the dev stack that the integration lane uses.