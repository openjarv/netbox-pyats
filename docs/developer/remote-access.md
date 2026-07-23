# Remote access to the dev NetBox UI over Tailscale

This runbook gets a developer onto the netbox-pyats dev UI from their own laptop,
over the dev host's **Tailscale** IP — never the public IP — and makes it
repeatable. It works against the plugin's `main` branch and the existing
per-worktree compose stack from [ATW-35](/ATW/issues/ATW-35).

The dev UI stays bound to `127.0.0.1:<port>` on the dev host (the ATW-35
loopback-only rule). Nothing in this runbook widens that binding to `0.0.0.0`
or the public eth0 IP. We reach the loopback port **through** the tailnet
without ever publishing it on eth0.

## Host facts (fill in your own)

| What                       | Value                                    |
| -------------------------- | ---------------------------------------- |
| Tailscale IP (tailscale0)  | `<TAILSCALE_IP>` (e.g. `100.x.y.z`)      |
| Tailnet FQDN               | `<TAILNET_FQDN>` (e.g. `your-host.tailnet-name.ts.net`) |
| Public eth0 IP             | `<ETH0_IP>` (only used to verify it is **not** published) |
| SSH                        | `0.0.0.0:22` (reachable via both IPs)    |
| Compose UI binding          | `127.0.0.1:<NETBOX_PORT>:8080` (loopback only) |
| Tailscale `serve`/`funnel`  | available, currently no config           |

The dev host is on your tailnet as `<TAILNET_HOSTNAME>`, with tailnet name
`<TAILNET_NAME>`. Your laptop must already be on the same tailnet
(`tailscale up` on the laptop, same account). Find your dev host's values with:

```bash
# on the dev host:
tailscale ip -4          # -> <TAILSCALE_IP>
tailscale status         # -> Self line shows <TAILNET_FQDN> and <TAILNET_NAME>
```

If your tailnet name differs, substitute your dev host's Tailscale
IP or FQDN throughout.

## Prerequisites

- You are on the **same tailnet** as the dev host. Verify from your laptop:
  ```bash
  tailscale status | grep <TAILNET_HOSTNAME>    # should show the dev host as reachable
  ```
- A worktree for the branch you want to test has been created with
  `scripts/dev-worktree.sh add` (see [Dev environment bring-up](setup.md)).
  The worktree's `.env` records its `NETBOX_PORT` (drawn from the 8001..8010
  pool). For the `main` branch, use a dedicated worktree, e.g.:
  ```bash
  # on the dev host:
  cd /home/hermes/netbox-pyats
  scripts/dev-worktree.sh add atw-106 test main-ui-test
  cd /home/hermes/netbox-pyats-wt/atw-106
  scripts/dev-worktree.sh up
  ```
  Note the `NETBOX_PORT` it prints (e.g. `8002`).

## Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS)

`tailscale serve` reverse-proxies the loopback port out to the tailnet only.
It does **not** open anything on the public eth0 IP, needs no compose change,
and gives you HTTPS with a Tailscale-issued cert automatically. This is the
recommended path because it is a one-liner, is encrypted end-to-end within
the tailnet, and never touches the public internet.

> Do **not** use `tailscale funnel` — that publishes the port to the public
> internet, which the user explicitly does not want. `serve` is tailnet-only.

On the **dev host**, after the worktree's stack is up (with
`NETBOX_PORT=<port>`), run in the foreground:

```bash
# foreground (Ctrl-C to stop). Replace <port> with the worktree's NETBOX_PORT.
tailscale serve --bg=false http://127.0.0.1:<port>
```

Or leave it running in the background:

```bash
# background; it keeps running after you log out. Stop with `tailscale serve reset`.
tailscale serve --bg http://127.0.0.1:<port>
```

Then from your **laptop**, open:

```
https://<TAILNET_FQDN>/
```

(Tailscale `serve` terminates TLS on the dev host using a tailnet CA cert,
so the URL is `https://`, and your laptop's Tailscale client validates it
automatically — no browser cert warning once Tailscale is running on the
laptop.)

Log in with `admin` / `admin`.

### Stopping it

```bash
# on the dev host:
tailscale serve reset
```

This removes the serve config. The compose stack keeps running; the UI is
back to loopback-only (`127.0.0.1:<port>`), reachable only from the dev host
itself.

### Repeatable one-liner (recommended alias)

Add this to the dev host shell so the user does not need to remember the
port each time:

```bash
# ~/.bashrc or ~/.zshrc on the dev host
ts-nb() {
  local port="${1:-$(grep -E '^NETBOX_PORT=' .env 2>/dev/null | cut -d= -f2-)}"
  [ -n "$port" ] || { echo "usage: ts-nb <port>  (or run from a worktree with .env)"; return 1; }
  tailscale serve --bg http://127.0.0.1:"$port" && \
  echo "UI: https://$(tailscale status --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')/"
}
```

Then from inside any worktree:

```bash
ts-nb          # uses the worktree's NETBOX_PORT
ts-nb 8002     # or pass a port explicitly
```

Stop with `tailscale serve reset`.

## Fallback path: SSH tunnel over Tailscale

If `tailscale serve` is unavailable (e.g. an older Tailscale client without
`serve`) or you prefer not to run a long-lived proxy on the dev host, use
an SSH tunnel. The SSH connection goes over the Tailscale IP (`<TAILSCALE_IP>`
or the FQDN), so it never touches the public internet. The compose binding
stays `127.0.0.1:<port>`; the tunnel just forwards that loopback port to
your laptop.

From your **laptop**:

```bash
# one-shot tunnel. Replace <port> with the worktree's NETBOX_PORT and
# <user> with your dev-host shell user.
ssh -N -L 8000:127.0.0.1:<port> <user>@<TAILSCALE_IP>
# then open http://localhost:8000 on the laptop (admin / admin)
```

Or using the Tailscale FQDN (preferred — survives IP changes):

```bash
ssh -N -L 8000:127.0.0.1:<port> <user>@<TAILNET_FQDN>
```

`-N` keeps the tunnel open without spawning a shell. `Ctrl-C` closes it
and the laptop-side `8000` stops forwarding. Pick a free local port on
the laptop (8000 is conventional; use another if something is already on
it).

### Repeatable alias

```bash
# ~/.bashrc or ~/.zshrc on the LAPTOP
nb-tunnel() {
  local port="${1:?usage: nb-tunnel <dev-host-NETBOX_PORT> [local-port]}"
  local lport="${2:-8000}"
  ssh -N -L "$lport:127.0.0.1:$port" "$@" <TAILSCALE_IP>
  # e.g. nb-tunnel 8002         -> http://localhost:8000
  #     nb-tunnel 8002 8080     -> http://localhost:8080
}
```

## Why not bind the compose port to `<TAILSCALE_IP>`?

The issue lists a third option: publish the port as
`<TAILSCALE_IP>:<port>:8080` via a per-worktree `.env` override (e.g. a
`NETBOX_BIND_IP` hook). It is **not recommended** because:

- It requires a compose change (a `NETBOX_BIND_IP` env hook in
  `docker-compose.dev.yml`), which is a PR + review + merge for something
  `tailscale serve` and SSH tunnels already solve with zero compose
  change.
- Docker publishes the port on that interface to anyone who can route to
  `<TAILSCALE_IP>`, which on a tailnet is every node in the tailnet. `serve`
  is tailnet-only too, but `serve` is explicitly Tailscale-audited and
  HTTPS-terminated; a raw Docker publish is not.
- It is easy to misconfigure into `0.0.0.0` (which violates ATW-35 and
  exposes the dev UI with `admin/admin` + the dev `SECRET_KEY` to the
  public internet). Keeping the binding hardcoded to `127.0.0.1` and
  proxying through `serve`/SSH avoids that footgun entirely.

The loopback-only binding from [ATW-35](/ATW/issues/ATW-35) is the
security boundary. Both recommended paths above preserve it; option 3
weaken it.

## What does NOT change

- `docker-compose.dev.yml` keeps `127.0.0.1:${NETBOX_PORT:-8000}:8080`.
  No `NETBOX_BIND_IP` hook, no `0.0.0.0` publish.
- `scripts/dev-worktree.sh` port pool (8001..8010) is unchanged.
- The plugin `main` branch is unchanged.
- No `tailscale funnel` (public exposure) is used anywhere.

## Quick decision table

| Want…                                | Use                                |
| ------------------------------------ | ---------------------------------- |
| One-liner, auto-HTTPS, no SSH session | `tailscale serve` (recommended)    |
| No long-lived proxy on the dev host  | SSH tunnel over Tailscale IP       |
| Public access (NOT recommended)      | `tailscale funnel` — do not use    |

## Verification checklist (after bringing the stack up)

On the dev host, from inside the worktree:

```bash
# 1. Stack is healthy and bound to loopback only.
docker compose -f docker-compose.dev.yml ps
# every service should read (healthy). netbox ports should read
# 127.0.0.1:<NETBOX_PORT>->8080/tcp — never 0.0.0.0:<port>.

# 2. Nothing is published on the public eth0 IP for the netbox port.
ss -tlnp | grep ":$NETBOX_PORT "
# expected: 127.0.0.1:<port> ... and nothing on <ETH0_IP>:<port>

# 3. (serve path) UI is reachable over the tailnet.
curl -kI https://<TAILNET_FQDN>/login/
# expected: 200/302 from NetBox

# 4. (SSH-tunnel path) from the laptop, after opening the tunnel:
curl -I http://localhost:8000/login/
# expected: 200/302 from NetBox
```

If step 2 shows the port on `0.0.0.0` or `<ETH0_IP>`, **stop and file an
infra issue** — something has widened the binding past ATW-35.