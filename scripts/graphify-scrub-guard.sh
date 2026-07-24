#!/usr/bin/env bash
# scripts/graphify-scrub-guard.sh
#
# Build-time scrub guard for committed graphify-out/ artifacts.
#
# The Graphify generator writes the absolute working-directory path into some
# tracked artifacts (graphify-out/GRAPH_REPORT.md line 1, graphify-out/graph.html
# <title>). When the nightly refresh runs from a developer home directory that
# leaks the OS username and absolute home layout into the public repo — the
# regression caught by Security on PR #41 (ATW-112 gate, fixed in 90435be).
#
# This guard enforces the "." / workspace-relative convention structurally
# instead of relying on manual review. It runs after `graphify update` /
# `graphify cluster-only` and either:
#
#   - fails the job (default): exits non-zero so the nightly routine surfaces
#     the leak instead of committing it, or
#   - auto-scrubs (--scrub): rewrites every leaked absolute home path to the
#     canonical relative form ("." for GRAPH_REPORT.md, "graphify-out/<file>"
#     for graph.html) and exits 0.
#
# Matched patterns (the absolute home path classes that must not be public):
#   /home/<user>   /Users/<user>   /root   ~ (literal, when expanded by a shell)
#
# Only committed graphify-out/ text artifacts are scanned: GRAPH_REPORT.md,
# graph.html, manifest.json, graph.json, and any *.md/*.html/*.json under
# graphify-out/. Binary/ignored files are skipped.
#
# Usage:
#   scripts/graphify-scrub-guard.sh                # check; exit 1 on leak
#   scripts/graphify-scrub-guard.sh --scrub        # auto-scrub; exit 0
#   scripts/graphify-scrub-guard.sh --scrub --check  # scrub then re-verify
#   scripts/graphify-scrub-guard.sh <repo-root>    # explicit repo root
#
# Exit codes:
#   0  no leak found (or scrub succeeded and re-verified clean)
#   1  leak found in check mode (or scrub left a residual leak)
#   2  mis-use / bad path
#
# References: ATW-125, ATW-112 (Security gate), ATW-121 (nightly routine),
# ATW-55 (PR review model). Regression source: PR #41 / commit 90435be.

set -euo pipefail

# --- paths -----------------------------------------------------------------

# Allow --scrub / --check flags to appear before/after the path argument.
REPO_ROOT=""
SCRUB=0
RECHECK=0
for arg in "$@"; do
  case "$arg" in
    --scrub)  SCRUB=1 ;;
    --check)  RECHECK=1 ;;
    -h|--help)
      sed -n '2,40p' "$0"; exit 0 ;;
    -*) echo "graphify-scrub-guard: unknown flag $arg" >&2; exit 2 ;;
    *) REPO_ROOT="$arg" ;;
  esac
done
[ -n "$REPO_ROOT" ] || REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# --- validation ------------------------------------------------------------

if [ ! -d "$REPO_ROOT/graphify-out" ]; then
  echo "graphify-scrub-guard: no graphify-out/ under $REPO_ROOT — nothing to scan." >&2
  exit 0
fi

# Anchored home-path patterns. Anchored to a leading slash so legitimate
# substrings like "homepage" or "userhome" do not false-positive. ~ is only
# matched when it appears as a path-tilde at a token boundary (start of a
# quoted path), not mid-string.
#
# We deliberately keep this an allowlist of "things that must not be public"
# rather than a denylist: a new OS/home layout is caught by the broad
# /home/ + /Users/ + /root classes, not by enumerating specific usernames.
PATTERN='(/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+|/root\b)'

# Files we scan: the known tracked artifacts plus any md/html/json that
# graphify may emit. Skips the dated snapshot dirs (graphify-out/2026-07-24/
# etc.) — those are not committed and not part of the public surface.
SCAN_GLOB=(
  graphify-out/GRAPH_REPORT.md
  graphify-out/graph.html
  graphify-out/manifest.json
  graphify-out/graph.json
)

# Collect only files that exist.
FILES=()
for f in "${SCAN_GLOB[@]}"; do
  [ -f "$REPO_ROOT/$f" ] && FILES+=("$REPO_ROOT/$f")
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "graphify-scrub-guard: no tracked graphify-out artifacts present in $REPO_ROOT." >&2
  exit 0
fi

# --- scan ------------------------------------------------------------------

# Returns the matching files (one per line) for the leak pattern.
leaked_files() {
  grep -El "$PATTERN" "${FILES[@]}" 2>/dev/null || true
}

LEAKED=$(leaked_files)

if [ -z "$LEAKED" ]; then
  echo "graphify-scrub-guard: clean — no absolute home paths in graphify-out/ artifacts."
  exit 0
fi

# --- report ----------------------------------------------------------------

echo "graphify-scrub-guard: FOUND absolute home-path leak in graphify-out/:" >&2
echo "$LEAKED" | while IFS= read -r f; do
  echo "  $f:" >&2
  grep -En "$PATTERN" "$f" 2>/dev/null | sed 's/^/    /' >&2 || true
done

if [ "$SCRUB" -ne 1 ]; then
  cat >&2 <<EOF
graphify-scrub-guard: refusing to commit leaked artifacts.
  Fix: re-run with --scrub to auto-rewrite to workspace-relative paths,
  or fix the generator's working directory (cd to repo root before
  running graphify update / cluster-only).
  Refs: ATW-125, ATW-112, PR #41, commit 90435be.
EOF
  exit 1
fi

# --- scrub -----------------------------------------------------------------

# Rewrites each leaked file: replace absolute home paths with the canonical
# relative form. GRAPH_REPORT.md line 1 wants "." (the corpus root); graph.html
# <title> wants the path relative to repo root ("graphify-out/graph.html").
# For all other occurrences we collapse to "." which is safe for any
# workspace-relative consumer.
for f in $LEAKED; do
  rel="${f#"$REPO_ROOT"/}"
  # Graphify emits the absolute path then /graphify-out/<file>; normalise the
  # graph.html <title> form specifically (".../graphify-out/graph.html").
  sed -i -E \
    -e "s|/home/[A-Za-z0-9._-]+[^ \"'<>]*/graphify-out/graph\.html|graphify-out/graph.html|g" \
    -e "s|/Users/[A-Za-z0-9._-]+[^ \"'<>]*/graphify-out/graph\.html|graphify-out/graph.html|g" \
    -e "s|/root([^ \"'<>]*)/graphify-out/graph\.html|graphify-out/graph.html|g" \
    -e "s|/home/[A-Za-z0-9._-]+[^ \"'<>]*|.|g" \
    -e "s|/Users/[A-Za-z0-9._-]+[^ \"'<>]*|.|g" \
    -e "s|/root(/[A-Za-z0-9._-]+)?|.|g" \
    "$f"
  echo "graphify-scrub-guard: scrubbed $rel"
done

if [ "$RECHECK" -eq 1 ]; then
  LEAKED=$(leaked_files)
  if [ -n "$LEAKED" ]; then
    echo "graphify-scrub-guard: RESIDUAL leak after scrub — manual fix required:" >&2
    echo "$LEAKED" >&2
    exit 1
  fi
  echo "graphify-scrub-guard: scrubbed and re-verified clean."
fi

exit 0