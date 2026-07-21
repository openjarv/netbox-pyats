#!/bin/sh
# Container entrypoint shim for graphify-mcp HTTP server.
#
# Runs as root (the Dockerfile sets no USER directive) just long enough to
# read the compose file-based secret at /run/secrets/graphify_api_key —
# compose preserves the host file's owner and mode, and on the dev host
# the key is mode 0600 owned by the operator, so the non-root runtime user
# cannot read it directly. After loading the key into GRAPHIFY_API_KEY, we
# drop to the `graphify` user (uid 1001) via runuser and exec graphify-mcp,
# so the server process itself never runs as root.
#
# The key is read from the env var (GRAPHIFY_API_KEY) by graphify-mcp, not
# passed via --api-key, so it never appears in the process argv or
# `docker inspect` process args. We also do NOT export the key into the
# runuser child's environment in a way that leaks it beyond the final
# exec'd process — runuser preserves the exported env, which is what we
# want (graphify-mcp reads it from its own env).
#
# If the secret file is missing or empty, we exit 1 before exec'ing
# graphify-mcp so the container fails fast and loudly (and the healthcheck
# stays unhealthy) rather than starting an unauthenticated server — the
# server explicitly warns and would bind 0.0.0.0 unauthenticated otherwise.
set -eu

SECRET_FILE="${GRAPHIFY_API_KEY_FILE:-/run/secrets/graphify_api_key}"
RUNTIME_USER="${GRAPHIFY_RUNTIME_USER:-graphify}"

if [ ! -s "$SECRET_FILE" ]; then
  echo "graphify-mcp-entrypoint: FATAL: api-key secret missing or empty at $SECRET_FILE" >&2
  echo "  Generate it with scripts/graphify-mcp-key.sh generate (see docs/developer/graphify-mcp-http.md)." >&2
  exit 1
fi

# Read the key, trim trailing whitespace/newlines so a file written by
# `echo` or printf is accepted. The key itself must be a single opaque
# token. Export so runuser's child inherits it.
export GRAPHIFY_API_KEY="$(tr -d '\r\n' < "$SECRET_FILE")"

# Drop the _FILE var so the path doesn't leak into the runtime env
# (cosmetic; the path is not sensitive, but keeping env clean is nicer).
unset GRAPHIFY_API_KEY_FILE

# Drop to the non-root runtime user and exec graphify-mcp. runuser replaces
# its shell with the exec'd process, so this is the final process tree.
# `--` separates runuser options from the command. We use `env -i`-style
# preservation (runuser keeps the environment by default) so
# GRAPHIFY_API_KEY survives the drop.
exec runuser -u "$RUNTIME_USER" -- /usr/local/bin/graphify-mcp --transport http --stateless "$@"