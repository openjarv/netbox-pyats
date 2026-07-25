#!/usr/bin/env bash
# scripts/pr-body-scrub-guard.sh
#
# CI guard against Paperclip control-plane metadata leaking into public
# GitHub PR bodies (ATW-159). The graphify-scrub-guard.sh sibling protects
# committed graphify-out/ artifacts from absolute home-path leaks; this
# guard protects the PR *description* — a public artifact the Author edits
# by hand — from carrying agent UUIDs, `agent://` URIs, and internal
# org-role titles.
#
# The leak class: across PRs #44–#47 the closing-checklist block (ATW-55)
# emitted `reviewer: [@CTO](agent://<uuid>)` and `merger: [@Chief of
# staff](agent://<uuid>)` into the PR body, disclosing Atw's Paperclip agent
# fleet, agent UUIDs, and internal org-role titles to anyone reading the
# public repo. Severity is low/exploitability is low, but it is a *repeat*
# pattern, which is why it is enforced structurally rather than by review.
#
# This guard reads the PR body via the GitHub Actions `pull_request` event
# payload (GITHUB_EVENT_PATH) and fails the lane if any forbidden pattern is
# present. It does NOT scan the diff — the diff is Security's gate
# (ATW-112 / gitleaks). It scans only the PR description.
#
# Matched patterns (the control-plane metadata classes that must not be
# public):
#   agent://<uuid>            — full Paperclip agent URI
#   bare UUID (8-4-4-4-12)    — any RFC-4122-style UUID; agent UUIDs are
#                               the realistic source, but matching the
#                               shape catches all of them
#   8-char hex prefix in a
#     "(agent <prefix>)" or
#     "agent <prefix>" context — the redacted-prefix form that leaked on
#                               PR #47 (`reviewer: @CTO (agent 1c41beee)`)
#   internal org-role titles  — "Chief of staff", "CTO", "QA Engineer",
#     in a reviewer/merger line   "Security Engineer", "Community Manager",
#                               "Senior Dev Engineer" when paired with a
#                               reviewer/merger label. Role-only prose
#                               elsewhere in the body is fine.
#
# Usage (CI lane):
#   bash scripts/pr-body-scrub-guard.sh
#
# Local dry-run:
#   PR_BODY="..." bash scripts/pr-body-scrub-guard.sh
#
# Exit codes:
#   0  no leak found (or not a PR event — pushes pass through)
#   1  leak found in the PR body
#   2  mis-use / missing GITHUB_EVENT_PATH
#
# References: ATW-159, ATW-112 (Security gate), ATW-55 (PR review model).
# Sibling: scripts/graphify-scrub-guard.sh (graphify-out/ artifacts).

set -euo pipefail

# --- source the PR body ----------------------------------------------------

# CI: read from the actions event payload. Local dry-run: PR_BODY env var.
BODY=""
if [ -n "${PR_BODY+x}" ]; then
  # PR_BODY is set (even if empty) — treat it as the body to scan.
  BODY="$PR_BODY"
elif [ -n "${GITHUB_EVENT_PATH:-}" ] && [ -f "$GITHUB_EVENT_PATH" ]; then
  if ! command -v jq >/dev/null 2>&1; then
    echo "pr-body-scrub-guard: jq is required to read the PR event payload." >&2
    exit 2
  fi
  # Only pull_request events carry a body. On push events there is no PR
  # body to scan — pass through cleanly.
  EV_TYPE="$(jq -r '.pull_request // empty | .head.ref' "$GITHUB_EVENT_PATH" 2>/dev/null || true)"
  if [ -z "$EV_TYPE" ]; then
    echo "pr-body-scrub-guard: not a pull_request event — nothing to scan."
    exit 0
  fi
  BODY="$(jq -r '.pull_request.body // ""' "$GITHUB_EVENT_PATH")"
else
  echo "pr-body-scrub-guard: no GITHUB_EVENT_PATH and no PR_BODY env var." >&2
  echo "  Set PR_BODY for a local dry-run, or run inside GitHub Actions." >&2
  exit 2
fi

if [ -z "$BODY" ]; then
  echo "pr-body-scrub-guard: PR body is empty — nothing to scan."
  exit 0
fi

# --- patterns --------------------------------------------------------------

# 1. agent://<uuid> URIs (the highest-value leak — full agent link).
PAT_AGENT_URI='agent://[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

# 2. Bare RFC-4122 UUIDs. Catches the #44/#45 `[@CTO](agent://...)` form and
#    any stray UUID. The gitleaks paperclip-identifier rule keys on the
#    PAPERCLIP_ keyword; this catches the bare shape regardless of keyword.
PAT_UUID='[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

# 3. 8-char hex prefix in an "(agent <prefix>)" / "agent <prefix>" context.
#    This is the PR #47 form: `reviewer: @CTO (agent 1c41beee)`. We require
#    the "agent" keyword nearby to avoid flagging incidental 8-char hex
#    strings (commit short-SHAs, etc.).
PAT_AGENT_PREFIX='agent[: ]+[0-9a-fA-F]{8}\b'

# Note: role-only reviewer/merger lines ("reviewer: CTO", "merger: CEO") are
# the *allowed* form per the ATW-159 finding itself — the leak is the agent
# ID/URI, not the role title. Patterns 1-3 catch every actual ID leak that
# occurred across PRs #44-#47; role titles alone are acceptable and are not
# flagged.

# --- scan ------------------------------------------------------------------

leaks=""
add_leak() {
  local label="$1" pattern="$2" flags="${3:-}"
  local hit
  hit="$(printf '%s' "$BODY" | grep -En $flags "$pattern" 2>/dev/null || true)"
  if [ -n "$hit" ]; then
    leaks+="$(printf '\n  [%s]:' "$label")"$'\n'"$(printf '%s\n' "$hit" | sed 's/^/    /')"
  fi
}

add_leak "agent:// URI" "$PAT_AGENT_URI"
add_leak "bare UUID" "$PAT_UUID"
add_leak "agent <prefix>" "$PAT_AGENT_PREFIX"

if [ -z "$leaks" ]; then
  echo "pr-body-scrub-guard: clean — no Paperclip control-plane metadata in PR body."
  exit 0
fi

# --- report ----------------------------------------------------------------

cat >&2 <<EOF
pr-body-scrub-guard: FOUND Paperclip control-plane metadata in PR body:$leaks

  These patterns disclose Atw's Paperclip agent fleet, agent UUIDs, and
  internal org-role titles to anyone reading the public repo (ATW-159).

  Fix: edit the PR body to remove:
    - any \`agent://<uuid>\` URIs
    - any bare or prefixed agent UUIDs
    - internal role titles on reviewer/merger lines (use role-only labels
      like "reviewer: CTO" with no IDs, or omit the lines entirely —
      GitHub's reviewer-request UI is the real assignment path)

  The PR template (.github/PULL_REQUEST_TEMPLATE.md) carries the convention.
  See docs/developer/contributing.md § "PR body hygiene".
  Refs: ATW-159, ATW-112, ATW-55.
EOF
exit 1