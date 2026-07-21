#!/usr/bin/env bash
# scripts/graphify-mcp-key.sh — manage the graphify-mcp HTTP api-key.
#
# The api-key is the Bearer token that Atw agents present to the shared
# graphify-mcp HTTP server (Authorization: Bearer <key>). It is delivered
# to the container via the compose `secrets:` mechanism from a file on the
# host, and never baked into the image or committed to the repo.
#
# Commands:
#   generate [opts]   Write a fresh opaque key to dev/graphify-mcp/api-key
#                     (mode 0600). Prints the key to stdout unless --quiet.
#   rotate [opts]     Generate a new key, then print the rotation steps
#                     (update the compose service, roll agent configs,
#                     restart heartbeats). Does NOT restart anything itself
#                     — the operator/agent performs the rolling restart so
#                     the order is controlled.
#   show              Print the current key (mode 0600 read). For verifying
#                     what's on disk; do NOT paste this into comments.
#   fingerprint       Print a short sha256 fingerprint of the current key,
#                     safe to post in issue threads / audit logs for
#                     at-a-glance key identification without leaking the key.
#
# Options:
#   --bits N          Key length in bytes (default 32 → 43 base64url chars).
#   --out PATH        Override the default key file path.
#   --quiet           Suppress stdout on generate/rotate (file still written).
#
# The key file is .gitignored (see .gitignore). If you ever commit it by
# accident, rotate immediately and treat the old key as compromised.
#
# See docs/developer/graphify-mcp-http.md for the full secret lifecycle and rotation
# runbook. Owned by Infrastructure Engineer (ATW-42).

set -euo pipefail

BITS=32
QUIET=0
KEY_FILE_DEFAULT="dev/graphify-mcp/api-key"
KEY_FILE="$KEY_FILE_DEFAULT"

usage() {
  sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --bits) BITS="$2"; shift 2 ;;
    --out)  KEY_FILE="$2"; shift 2 ;;
    --quiet) QUIET=1; shift ;;
    -h|--help) usage 0 ;;
    *) break ;;
  esac
done

cmd="${1:-}"; [ -n "$cmd" ] || usage 1 >&2; shift || true

generate_key() {
  # openssl rand -base64 produces 4/3 * BITS chars with trailing = padding.
  # We strip padding and any +/ to get a URL-safe opaque token. 32 bytes →
  # 43 chars, well above the "long enough not to guess" bar for a dev-time
  # shared secret on a loopback-only service.
  openssl rand -base64 "$BITS" 2>/dev/null | tr -d '\n=+/' | tr -d '=' | head -c "$((BITS * 4 / 3 + 2))"
}

fingerprint_key() {
  # Read the key from stdin and print a short sha256 fingerprint (first 16
  # hex chars). Safe to post in issue threads / audit logs for at-a-glance
  # key identification without leaking the key itself.
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | cut -c1-16
  else
    shasum -a 256 | cut -c1-16
  fi
}

ensure_gitignored() {
  local rel="$1"
  local gi=".gitignore"
  touch "$gi"
  if ! grep -qxF "$rel" "$gi" 2>/dev/null; then
    {
      echo ""
      echo "# graphify-mcp HTTP api-key (ATW-42) — never commit."
      echo "$rel"
    } >> "$gi"
    echo "graphify-mcp-key.sh: added $rel to $gi" >&2
  fi
}

case "$cmd" in
  generate)
    key="$(generate_key)"
    mkdir -p "$(dirname "$KEY_FILE")"
    printf '%s\n' "$key" > "$KEY_FILE"
    chmod 0600 "$KEY_FILE"
    # Make sure the key file is gitignored relative to the repo root. We
    # assume the script is run from a worktree root (the conventional
    # invocation). If run from elsewhere the grep/append is a no-op or
    # writes to a .gitignore that isn't tracked — either way the key file
    # itself is never committed.
    if [ -w ".gitignore" ] || [ ! -e ".gitignore" ]; then
      ensure_gitignored "$KEY_FILE"
    fi
    if [ "$QUIET" -eq 0 ]; then
      printf '%s\n' "$key"
    else
      echo "graphify-mcp-key.sh: wrote $KEY_FILE (mode 0600, gitignored)" >&2
    fi
    ;;

  rotate)
    old_fp="(none)"
    if [ -s "$KEY_FILE" ]; then
      old_fp="$(fingerprint_key < "$KEY_FILE")"
    fi
    key="$(generate_key)"
    mkdir -p "$(dirname "$KEY_FILE")"
    printf '%s\n' "$key" > "$KEY_FILE"
    chmod 0600 "$KEY_FILE"
    new_fp="$(printf '%s' "$key" | fingerprint_key)"
    if [ "$QUIET" -eq 0 ]; then
      printf 'new key: %s\n' "$key"
    else
      echo "graphify-mcp-key.sh: rotated $KEY_FILE" >&2
    fi
    cat >&2 <<EOF

rotation steps (operator/agent performs, in order):
  1. Old key fingerprint: $old_fp
  2. New key fingerprint: $new_fp
  3. Restart the graphify-mcp container so it picks up the new secret:
       docker compose -f docker-compose.dev.yml \\
         -f docker-compose.graphify-mcp.yml up -d --force-recreate graphify-mcp
  4. Update each remote agent's OpenCode MCP config (headers.Authorization
     or environment.GRAPHIFY_API_KEY) to the new key.
  5. Restart those agents' heartbeats.
  6. Once all agents are on the new key, the old key is revoked (it no
     longer exists on the server, so it cannot authenticate).
  7. Post the new fingerprint to the issue thread for audit — NOT the key.
EOF
    ;;

  show)
    [ -s "$KEY_FILE" ] || { echo "no key at $KEY_FILE" >&2; exit 1; }
    cat "$KEY_FILE"
    ;;

  fingerprint)
    [ -s "$KEY_FILE" ] || { echo "no key at $KEY_FILE" >&2; exit 1; }
    fingerprint_key < "$KEY_FILE"
    ;;

  *)
    usage 1 >&2
    ;;
esac