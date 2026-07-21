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
       netbox_pyats/tests/test_diff.py netbox_pyats/tests/test_compliance.py
```

This is the lane that enforces the compatibility matrix on every PR.

### `integration`

Full NetBox-dependent suite inside the dev container (`docker-compose.dev.yml`). Gating (`continue-on-error: false`); the NetBox 4.6 dev-image compatibility work ([ATW-25](/ATW/issues/ATW-25)) and the gating flip ([ATW-49](/ATW/issues/ATW-49)) have landed.

```bash
docker compose -f docker-compose.dev.yml exec netbox pytest netbox_pyats/tests
```

## What to keep green

Keep `lint` and `unit` green on every PR. Do not merge if either is red.

The integration lane runs inside the dev container; if it fails locally but passes in CI (or vice versa), check that your local dev stack is up to date with `docker-compose.dev.yml`.

## References

- Architecture decision D-7 ([ATW-23](/ATW/issues/ATW-23) architecture document, §4 / §5).
- [ATW-38](/ATW/issues/ATW-38): NetBox 4.6.5 compatibility fixes (PR #15).
- [Contributing](contributing.md) — local dev setup, tests, and lint commands.
- [Dev environment bring-up](setup.md) — the dev stack that the integration lane uses.