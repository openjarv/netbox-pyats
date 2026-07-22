# CI

CI runs on every push to `main` and every PR via [.github/workflows/ci.yml](../../.github/workflows/ci.yml). Four lanes, mirroring the dual-mode test setup in `conftest.py` and the compatibility matrix (NetBox 4.6.x × Python 3.10 / 3.11 / 3.12 × pyATS 26.x worker-only), plus a backend-version sweep across PostgreSQL × Redis.

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
       netbox_pyats/tests/test_diff.py netbox_pyats/tests/test_compliance.py
```

This is the lane that enforces the Python-version matrix on every PR.

### `integration`

Full NetBox-dependent suite inside the dev container (`docker-compose.dev.yml`) with the default backend versions (PostgreSQL 18 + Valkey 9.1). Gating (`continue-on-error: false`); the NetBox 4.6 dev-image compatibility work ([ATW-25](/ATW/issues/ATW-25)) and the gating flip ([ATW-49](/ATW/issues/ATW-49)) have landed.

```bash
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

### `integration-matrix`

Same full NetBox-dependent suite, sweeping PostgreSQL × Redis/Valkey backend versions from the supported matrix ([ATW-96](/ATW/issues/ATW-96)). Gating; every PR must pass on all supported backend combinations — no merge is green without matrix coverage.

The matrix covers:

| PostgreSQL | Redis / Valkey |
|------------|----------------|
| 15-alpine  | Redis 6        |
| 16-alpine  | Redis 7        |
| 17-alpine  |                |

PostgreSQL 18 + Valkey 9.1 (the defaults) are covered by the `integration` lane above and are not repeated here. PostgreSQL 14 and Redis 5 are excluded because NetBox 4.7 drops them.

The lane overrides the `PG_VERSION`, `REDIS_IMAGE`, and `REDIS_SERVER` env vars that `docker-compose.dev.yml` reads (see [Image overrides](setup.md#image-overrides-compatibility-sweeps) in the setup guide).

## What to keep green

Keep `lint`, `unit`, `integration`, and `integration-matrix` green on every PR. Do not merge if any lane is red.

The integration lanes run inside the dev container; if a lane fails locally but passes in CI (or vice versa), check that your local dev stack is up to date with `docker-compose.dev.yml`.

## References

- Architecture decision D-7 ([ATW-23](/ATW/issues/ATW-23) architecture document, §4 / §5).
- [ATW-38](/ATW/issues/ATW-38): NetBox 4.6.5 compatibility fixes (PR #15).
- [ATW-96](/ATW/issues/ATW-96): compatibility-matrix CI (PG × Redis sweep).
- [Contributing](contributing.md) — local dev setup, tests, and lint commands.
- [Dev environment bring-up](setup.md) — the dev stack that the integration lanes use.