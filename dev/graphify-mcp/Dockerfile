# Graphify MCP HTTP server image.
#
# Containerizes the `graphify-mcp` Streamable HTTP transport so Atw agents on
# other hosts can reach a shared code-graph server over the network with a
# Bearer api-key. This is the multi-host / shared-service upgrade path from
# the stdio MCP server wired in ATW-40 (see GRAPHIFY_MCP.md). On a single
# dev host the stdio server is simpler and safer; this image only needs to be
# built when Atw agents span more than one host (or the board asks for a
# centralized graph service — see ATW-42).
#
# Runtime contract (verified during ATW-40 / ATW-42):
#   - Listens on 127.0.0.1:8080 inside the container by default; the compose
#     service overrides --host to 0.0.0.0 so it is reachable across the
#     devnet bridge. The compose `ports:` binding is loopback-only on the
#     host (127.0.0.1:), so the server is never exposed on the host's public
#     IP. Remote hosts reach it over SSH port forwarding or a private
#     network, never by widening the publish binding.
#   - Requires --api-key on the HTTP transport. The key is read from the
#     GRAPHIFY_API_KEY env var or the --api-key flag; we use the env var so
#     the secret is injected via the compose `secrets:` mechanism and never
#     baked into the image or written into the process argv.
#   - --stateless: no per-session state, safe behind a load balancer / for
#     parallel CI runs.
#   - The graph file is bind-mounted read-only at runtime from
#     graphify-out/graph.json (per repo) or a shared volume. The image
#     itself ships no graph data.
#
# Build (dev):
#   docker compose -f docker-compose.dev.yml build graphify-mcp
# Or standalone:
#   docker build -t atw/graphify-mcp:dev -f dev/graphify-mcp/Dockerfile .

FROM docker.io/python:3.12-slim

# uv installs graphify-mcp and its mcp/uvicorn/starlette deps into an
# isolated tool venv and exposes the `graphify-mcp` binary on PATH. We use
# uv (not pip) because the repo's other dev containers already standardize
# on uv and the mcp extra pulls tree-sitter wheels that uv resolves faster.
# We fetch the uv static binary directly (no install script — python:3.12-slim
# has no curl/wget, and the official ghcr image is smaller than a curl+script
# install). Pinned version keeps the build reproducible.
ARG UV_VERSION=0.11.30
ADD "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" /tmp/uv.tar.gz
RUN tar -xzf /tmp/uv.tar.gz -C /tmp --strip-components=1 \
    && mv /tmp/uv /usr/local/bin/uv \
    && mv /tmp/uvx /usr/local/bin/uvx \
    && rm -rf /tmp/uv.tar.gz /tmp/uv /tmp/uvx \
    && chmod 0555 /usr/local/bin/uv /usr/local/bin/uvx

# graphifyy[mcp] pulls graphify + the `mcp` SDK + uvicorn + starlette. Pin
# to the same version installed on the dev host (ATW-37 Phase 1) so the
# container serves the same graph format the on-host `graphify update`
# produces. Override GRAPHIFY_VERSION to upgrade after a graphifyy release.
#
# Install into /opt/uv (not /root/.local) so the non-root runtime user can
# both execute the binary and read the tool venv. uv tool install creates
# bin + lib under UV_TOOL_DIR; we symlink the binary into /usr/local/bin.
ARG GRAPHIFY_VERSION=0.9.20
ENV UV_TOOL_DIR=/opt/uv/tools
ENV UV_TOOL_BIN_DIR=/opt/uv/bin
RUN uv tool install "graphifyy[mcp]==${GRAPHIFY_VERSION}" --python 3.12 \
    && ln -s /opt/uv/bin/graphify-mcp /usr/local/bin/graphify-mcp \
    && chmod -R a+rX /opt/uv

# Non-root runtime user. The entrypoint runs as root just long enough to
# read the compose-mounted secret (compose preserves the host file's owner
# and mode, which on the dev host is 0600 owned by the operator's uid, so
# the non-root user cannot read it directly), then drops to this user via
# `runuser` before exec'ing graphify-mcp. The graph file is bind-mounted
# read-only at /graph and world-readable, so this user only needs read
# access to it.
RUN useradd --system --uid 1001 --no-create-home graphify

# Liveness probe script. An unauthenticated POST to /mcp returns HTTP 401
# when the server is up and enforcing --api-key (verified during ATW-42).
# Any other outcome (connection refused, 5xx, 200 with no auth) is unhealthy.
# We deliberately do NOT send the api-key in the healthcheck so the secret
# never appears in `docker inspect` / healthcheck logs. python3 is already in
# the base image (python:3.12-slim), so no curl/busybox extra dep is needed.
COPY --chown=root:root dev/graphify-mcp/healthcheck.py /usr/local/bin/graphify-mcp-healthcheck

# Entrypoint shim: reads /run/secrets/graphify_api_key as root, exports
# GRAPHIFY_API_KEY, then drops to the `graphify` user via runuser and execs
# graphify-mcp. Fails fast if the secret is missing/empty so the container
# never starts an unauthenticated 0.0.0.0 server by accident.
COPY --chown=root:root dev/graphify-mcp/entrypoint.sh /usr/local/bin/graphify-mcp-entrypoint
RUN chmod 0555 /usr/local/bin/graphify-mcp-healthcheck /usr/local/bin/graphify-mcp-entrypoint

# NOTE: no USER directive here — the entrypoint starts as root (to read the
# secret) and drops to `graphify` itself. The healthcheck also runs as root
# but only posts an unauthenticated HTTP request (no secret access needed).

# Default in-container graph path. Compose overrides via the command below.
ENV GRAPHIFY_GRAPH=/graph/graph.json
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["graphify-mcp-healthcheck"]

# The shim adds `--transport http --stateless` and the GRAPHIFY_API_KEY env
# var; the CMD passes only the bind/listen args, which compose overrides.
ENTRYPOINT ["graphify-mcp-entrypoint"]
CMD ["--host", "127.0.0.1", "--port", "8080", "--graph", "/graph/graph.json"]