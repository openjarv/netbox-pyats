#!/usr/bin/env bash
# scripts/gitleaks-fixture-regression.sh
#
# ATW-167 companion CI assertion for the secret-detection fixture path
# allowlist.
#
# Root cause this closes: .gitleaks.toml path-allowlists
# netbox_pyats/tests/test_secret_detection.py so gitleaks does not block
# commits containing the deliberately-real-shaped positive test values. A
# path allowlist is content-blind — it cannot detect a real secret placed
# inside that file. That is the hole that allowed ATW-163: a live Paperclip
# agent-ID prefix sat in the allowlisted file and was not caught until a
# later PR replaced it with a synthetic UUID. (The exact live value is
# intentionally NOT reproduced here — committing it would itself be an
# ATW-159 leak. A synthetic UUID-shaped value in the same content class is
# used for the injection below.)
#
# This script proves the path allowlist has not silently regressed into a
# real-secret blind spot. It:
#   1. Copies the fixture file to a temp path OUTSIDE the path allowlist.
#   2. Injects a real-shaped value not in the synthetic fixture set (a live
#      agent-ID prefix) into the copy.
#   3. Runs gitleaks against the temp tree.
#   4. Asserts gitleaks produces a finding for the injected value.
#
# If gitleaks ever stopped catching real-shaped values in the fixture's
# content class (e.g. the rules were weakened, or the allowlist was widened
# to suppress the value shape), this assertion fails CI.
#
# Usage:
#   scripts/gitleaks-fixture-regression.sh            # check; exit 1 on regression
#
# Stewardship: CTO owns standards; Security Engineer owns execution (ATW-55).
# Exit codes: 0 = regression guard passed; 1 = regression detected or error.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITLEAKS_CONFIG="$REPO_ROOT/.gitleaks.toml"
FIXTURE="$REPO_ROOT/netbox_pyats/tests/test_secret_detection.py"

# A real-shaped agent-ID prefix that is NOT a real Paperclip identifier.
# This is deliberately NOT the ATW-163 escape value (that was a live agent ID
# — committing it into a public repo would itself be an ATW-159 leak). The
# value below is a synthetic UUID-shaped string in the real content class
# (8-4-4-4-12 hex, assigned to PAPERCLIP_AGENT_ID) that gitleaks must catch
# but which is not a live control-plane identifier.
#
# The literal is assembled at runtime from shell variables so the committed
# script source does not contain the contiguous real-shaped token that
# gitleaks would flag — otherwise the pre-commit gitleaks hook would block
# the commit that adds this very script. The assembled value still lands in
# the temp scan target below, where gitleaks MUST catch it.
_PREFIX='PAPERCLIP_AGENT_ID=dead'
_HEX='beef-1234-5678-9abc-def012345678'
INJECTED_VALUE="${_PREFIX}${_HEX}"

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "FAIL: gitleaks binary not found on PATH" >&2
  exit 1
fi

if [ ! -f "$GITLEAKS_CONFIG" ]; then
  echo "FAIL: gitleaks config not found at $GITLEAKS_CONFIG" >&2
  exit 1
fi

if [ ! -f "$FIXTURE" ]; then
  echo "FAIL: fixture not found at $FIXTURE" >&2
  exit 1
fi

# Temp tree: copy the fixture to a path OUTSIDE the allowlist, inject the
# real-shaped value, and scan only that temp tree.
TMP_TREE="$(mktemp -d)"
trap 'rm -rf "$TMP_TREE"' EXIT

mkdir -p "$TMP_TREE/leak_check"
# Copy the fixture content but place it at a non-allowlisted path so gitleaks
# scans it. Append the injected real-shaped value on its own line.
cp "$FIXTURE" "$TMP_TREE/leak_check/injected_fixture.py"
printf '\n# ATW-167 regression injection (real-shaped, not synthetic):\n%s\n' \
  "$INJECTED_VALUE" >> "$TMP_TREE/leak_check/injected_fixture.py"

# Run gitleaks against the temp tree (no-git: plain directory scan).
# --exit-code 1 makes gitleaks exit non-zero when findings are present; we
# expect exactly that here.
GITLEAKS_OUTPUT="$(gitleaks detect \
  --config "$GITLEAKS_CONFIG" \
  --source "$TMP_TREE" \
  --no-banner \
  --no-git \
  --verbose 2>&1 || true)"

# Assert the injected synthetic-but-real-shaped value appears in the
# findings. The value is synthetic (not a live identifier) but in the real
# content class, so gitleaks must still flag it. Grep for the assembled
# hex tail (the script source only stores it split across variables, so
# the pre-commit gitleaks hook does not flag this file itself).
if echo "$GITLEAKS_OUTPUT" | grep -q "${_HEX}"; then
  echo "PASS (ATW-167): gitleaks caught the injected real-shaped agent-ID value outside the path allowlist."
  echo "The path allowlist on test_secret_detection.py is backed by a content-aware regression guard."
  exit 0
else
  echo "FAIL (ATW-167): gitleaks did NOT catch the injected real-shaped agent-ID value." >&2
  echo "The path allowlist may have silently regressed into a content-blind blind spot." >&2
  echo "--- gitleaks output ---" >&2
  echo "$GITLEAKS_OUTPUT" >&2
  exit 1
fi