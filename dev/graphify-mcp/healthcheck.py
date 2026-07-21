#!/usr/bin/env python3
"""Liveness probe for the graphify-mcp HTTP container.

Posts an unauthenticated MCP `initialize` to the local server and treats
HTTP 401 (api-key enforced) as healthy. Any other outcome — connection
refused, 5xx, 200 with no auth — is unhealthy.

We deliberately do NOT send the api-key here so the secret never appears in
`docker inspect` healthcheck output or container logs. The server itself
enforces the key on real requests.
"""
import os
import sys
import json
import urllib.request
import urllib.error

host = os.environ.get("GRAPHIFY_HC_HOST", "127.0.0.1")
port = os.environ.get("GRAPHIFY_HC_PORT", "8080")
path = os.environ.get("GRAPHIFY_HC_PATH", "/mcp")
url = f"http://{host}:{port}{path}"

body = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "healthcheck", "version": "1"},
    },
}).encode()

req = urllib.request.Request(
    url,
    data=body,
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=2) as r:
        # 200/202 without auth means the server is NOT enforcing the api-key,
        # which is a misconfiguration we want to surface as unhealthy.
        sys.stderr.write(f"healthcheck: unexpected {r.status} without auth\n")
        sys.exit(1)
except urllib.error.HTTPError as e:
    # 401 is the healthy case: server is up and rejecting unauthenticated
    # requests. 404/405/406 mean the server is up but the mount path is
    # wrong — also unhealthy so the operator notices.
    if e.code == 401:
        sys.exit(0)
    sys.stderr.write(f"healthcheck: HTTP {e.code}\n")
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"healthcheck: {type(e).__name__}: {e}\n")
    sys.exit(1)