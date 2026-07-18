# Contributing to netbox-pyats

Thanks for helping make netbox-pyats better. This is the Atw PyATS/Genie
plugin for NetBox.

## Setup

```bash
git clone https://github.com/openjarv/netbox-pyats.git
cd netbox-pyats
python -m venv .venv && . .venv/bin/activate
pip install -e .[dev]
pytest
```

Tests run in two modes (handled by `conftest.py`):

- **Pure-Python** (default, no NetBox installed): runs the credential
  encryption and testbed-builder unit tests against fixture devices with
  mocked Unicon.
- **Inside NetBox** (integration): NetBox-dependent tests skip cleanly via
  `pytest.importorskip("netbox")` when NetBox isn't importable.

## Conventions

- Black, line length 120. isort (black profile).
- flake8 clean.
- Every model change ships a migration.
- Don't cut the NetBox compatibility matrix without CEO sign-off.
- Don't commit directly to `main`; branches and PRs only.

## Releases

First PyPI release requires CEO sign-off. After that, follow the existing
versioning and release pipeline.