#!/usr/bin/env bash
# scripts/test-unit.sh
#
# Run the pure-Python unit lane: the five test modules that exercise logic
# with no NetBox, no PostgreSQL, no Redis, and no Docker. They configure a
# minimal in-memory Django settings via conftest.py and skip cleanly when
# pyats is absent (pytest.importorskip). Use this lane for iterating on the
# diff engine, testbed builder, capture parser, compliance comparison, and
# credential crypto — seconds, not minutes.
#
# The lane split (see docs/developer/setup.md "Test lane split"):
#   - logic change      -> unit lane   (this script; seconds, no Docker)
#   - view/model/       -> integration lane (Docker + --reuse-db)
#     migration change
#
# This is the same set the CI `unit` lane runs
# (.github/workflows/ci.yml). If you add a pure-Python test module, add it
# to BOTH this script and the CI `unit` lane so the split stays in sync.
#
# Usage:
#   scripts/test-unit.sh           # run all 103 unit tests
#   scripts/test-unit.sh -v        # verbose
#   scripts/test-unit.sh -k crypto # pass-through extra pytest flags
#
# Exit code is pytest's. No network, no containers.
set -euo pipefail

# Resolve the repo root from this script's location so it works from any CWD.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The pure-Python unit set (keep in sync with CI .github/workflows/ci.yml).
# test_navmenu_uniqueness_guard (ATW-183) and test_panel (ATW-184) are AST /
# fake-object suites with no NetBox/Genie import; they belong in the fast
# lane alongside test_supported_platforms / test_template_extension. (ATW-435.)
unit_tests=(
  "${repo_root}/netbox_pyats/tests/test_diff.py"
  "${repo_root}/netbox_pyats/tests/test_testbed.py"
  "${repo_root}/netbox_pyats/tests/test_capture.py"
  "${repo_root}/netbox_pyats/tests/test_capture_learn.py"
  "${repo_root}/netbox_pyats/tests/test_compliance.py"
  "${repo_root}/netbox_pyats/tests/test_compliance_job_legacy.py"
  "${repo_root}/netbox_pyats/tests/test_state_commands_invariant.py"
  "${repo_root}/netbox_pyats/tests/test_crypto.py"
  "${repo_root}/netbox_pyats/tests/test_template_extension.py"
  "${repo_root}/netbox_pyats/tests/test_navmenu_uniqueness_guard.py"
  "${repo_root}/netbox_pyats/tests/test_panel.py"
)

exec python3 -m pytest "${unit_tests[@]}" "$@"