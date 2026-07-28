#!/usr/bin/env bash
# dev-worktree.sh — manage per-issue git worktrees + isolated compose stacks.
#
# Conventions (see docs/developer/setup.md):
#   - Trunk worktree at /home/hermes/netbox-pyats stays on main; no feature work
#     happens there. Each issue gets its own worktree under ../netbox-pyats-wt/.
#   - One issue = one branch = one worktree. Branch name: <type>/<issue-id>-<slug>.
#   - Each worktree runs its own docker compose project (COMPOSE_PROJECT_NAME)
#     on a unique loopback port drawn from a small pool.
#
# Commands:
#   dev-worktree.sh add <issue-id> <type> <slug>
#       Create ../netbox-pyats-wt/<issue-id> on branch <type>/<issue-id>-<slug>
#       based on the latest origin/main (fetch first; offline fallback to local
#       main), write .env with a unique port, and print path + port + base SHA.
#       Refuses to run when the trunk worktree is not on main (or a branch
#       tracking origin/main) so worktrees never branch from a stale feature
#       branch. (ATW-208)
#
#   dev-worktree.sh up
#       Run `docker compose -f docker-compose.dev.yml up -d` in the current
#       worktree (uses the worktree's .env for project name + port).
#
#   dev-worktree.sh remove <issue-id>
#       Run `docker compose down -v` in the worktree, then `git worktree remove`.
#       Use when the issue reaches a terminal state (done/cancelled).
#
#   dev-worktree.sh cleanup
#       Find and tear down orphaned compose projects (netbox dev stacks whose
#       worktree directory no longer exists or has no running containers).
#       Removes their containers, volumes, and networks. Safe to run on a
#       schedule — skips stacks with running containers. (ATW-201)
#
#   dev-worktree.sh audit
#       Print a report of running/stopped compose stacks, orphaned volumes,
#       images, networks, and host port-exposure check. Post the output back
#       to the originating issue. (ATW-201)
#
# Port pool: 8001..8010 (10 ports). Scans ../netbox-pyats-wt/*/.dev-port for
# claimed ports. Fails loud if the pool is exhausted.
#
# Base branch policy (ATW-208): every new worktree branch is based on the
# latest origin/main, unless a documented reason on the originating issue
# names an alternate base. The script fetches origin/main before branching,
# bases on origin/main (falling back to local main only when offline and
# local main exists), refreshes local main from origin/main when present,
# refuses to add when the trunk is off main, and prints the base SHA used.
# See docs/developer/setup.md "Base branch policy".
#
# OOM guardrail (ATW-201): The dev host has 7.8 GiB RAM + 2 GiB swap. One netbox
# dev stack (netbox 2g + worker 1g + pyats-worker 2g + postgres 512m + redis
# 256m ≈ 5.7 GiB of mem_limit) consumes ~58% of RAM. Two concurrent stacks
# (11.4 GiB) exceed total RAM+swap (9.8 GiB) and guarantee OOM. `cmd_up` refuses
# to start a new stack if another netbox dev stack is already running unless
# MAX_CONCURRENT_STACKS is set >1 (not recommended on this host).

set -euo pipefail

# Resolve the trunk repo root (the worktree this script lives alongside, or the
# common dir for linked worktrees). We anchor everything to the trunk so the
# script works no matter which worktree it is invoked from.
TRUNK="$(git rev-parse --git-common-dir 2>/dev/null)"
if [ -z "$TRUNK" ]; then
  echo "error: not inside a git repo" >&2
  exit 1
fi
# git-common-dir is relative to cwd for main worktree, absolute for linked ones.
case "$TRUNK" in
  /*) TRUNK="$(cd "$TRUNK" && pwd)" ;;
  *)  TRUNK="$(cd "$(pwd)/$TRUNK" && pwd)" ;;
esac
# The trunk working tree is the parent of the .git dir for the main worktree.
TRUNK_ROOT="$(dirname "$TRUNK")"
# Worktrees live in a sibling directory of the trunk repo (not nested inside
# it), so e.g. /home/hermes/netbox-pyats -> /home/hermes/netbox-pyats-wt.
WT_ROOT="$(dirname "$TRUNK_ROOT")/$(basename "$TRUNK_ROOT")-wt"

PORT_MIN=8001
PORT_MAX=8010

# Maximum concurrent netbox dev stacks allowed on the host (ATW-201 OOM
# guardrail). The host has 7.8 GiB RAM + 2 GiB swap; one stack is ~5.7 GiB of
# mem_limit, so 2 concurrent stacks guarantee OOM. Override to 2+ only on a
# host with more RAM. The guardrail counts running containers labelled as
# netbox dev compose projects — it does not count stopped stacks.
MAX_CONCURRENT_STACKS="${MAX_CONCURRENT_STACKS:-1}"

die() { echo "error: $*" >&2; exit 1; }

# Regex matching compose project names that look like netbox dev stacks.
# Matches the `COMPOSE_PROJECT_NAME` convention used by dev-worktree.sh add
# (issue-id like `atw-44`, `ATW-201`) plus the trunk `netbox-pyats` project.
# Deliberately does NOT include a bare-numeric `[0-9]+` alternative: that
# would match any pure-numeric compose project on the dev host, and
# NETBOX_PROJECT_RE feeds container_netbox_projects() which feeds the
# destructive cmd_cleanup() path (docker rm -f). Bare-numeric projects are
# instead discovered via NETBOX_VOLUME_RE (volume-name prefix), which is
# netbox-specific. (ATW-271 Security finding, ATW-272)
NETBOX_PROJECT_RE='^(netbox-pyats|[Aa][Tt][Ww]-?[0-9]+)$'

# Same regex anchored for volume-name prefix matching:
# `<project>_netbox-*`. Compose names volumes `<project>_<svc>_<n>`, so the
# project segment is everything before the first `_netbox`. Includes the
# bare-numeric `[0-9]+` alternative because the `_netbox` suffix is a strong
# netbox-specific signal — an unrelated numeric project will not have
# `<proj>_netbox-*` volumes unless it is running a netbox stack.
# (ATW-204/ATW-271)
NETBOX_VOLUME_RE='^(netbox-pyats|[Aa][Tt][Ww]-?[0-9]+|[0-9]+)_netbox'

# Non-anchored alternation (no `^`/`$`) for embedding inside larger regexes
# such as the audit report's tab-delimited project filter. Includes the
# bare-numeric alternative because the audit's running-stacks and
# stopped-containers sections are display-only (non-destructive) — a looser
# match is safe there and ensures bare-numeric stacks are reported.
# (ATW-271)
NETBOX_PROJECT_ALT='netbox-pyats|[Aa][Tt][Ww]-?[0-9]+|[0-9]+'

# List running compose project names that look like netbox dev stacks.
running_netbox_projects() {
  docker ps --format '{{.Label "com.docker.compose.project"}}' 2>/dev/null \
    | grep -E "$NETBOX_PROJECT_RE" \
    | sort -u || true
}

next_free_port() {
  local claimed=""
  if [ -d "$WT_ROOT" ]; then
    claimed="$(find "$WT_ROOT" -maxdepth 2 -name '.dev-port' -exec cat {} \; 2>/dev/null || true)"
  fi
  local port="$PORT_MIN"
  while [ "$port" -le "$PORT_MAX" ]; do
    if ! printf '%s\n' "$claimed" | grep -qx "$port"; then
      echo "$port"
      return 0
    fi
    port=$((port + 1))
  done
  die "port pool exhausted ($PORT_MIN..$PORT_MAX). Remove stale worktrees with: $0 remove <issue-id>"
}

usage() {
  cat >&2 <<EOF
usage: dev-worktree.sh <command> [args]

  add <issue-id> <type> <slug>     create a worktree for an issue
  up                               bring up the compose stack in the current worktree
  remove <issue-id>                tear down the worktree + its compose stack
  cleanup                          tear down orphaned/stopped compose stacks (ATW-201)
  audit                            print exposure + cleanup report (ATW-201)

examples:
  dev-worktree.sh add atw-44 chore dev-worktree-helper
  dev-worktree.sh up
  dev-worktree.sh remove atw-44
  dev-worktree.sh cleanup
  dev-worktree.sh audit
EOF
  exit 2
}

cmd_add() {
  local issue_id="${1:-}" type="${2:-}" slug="${3:-}"
  [ -n "$issue_id" ] && [ -n "$type" ] && [ -n "$slug" ] || usage

  # Accept both short (feat) and long (feature) forms; normalise to short.
  case "$type" in
    feat|feature)   type=feat ;;
    fix)            type=fix ;;
    chore)          type=chore ;;
    docs)           type=docs ;;
    infra)          type=infra ;;
    refactor)       type=refactor ;;
    test)           type=test ;;
    *) die "type must be one of: feat fix chore docs infra refactor test (got '$type')" ;;
  esac

  local branch="$type/$issue_id-$slug"
  local wt="$WT_ROOT/$issue_id"

  [ -e "$wt" ] && die "worktree already exists: $wt"

  # Ensure the worktree directory exists.
  mkdir -p "$WT_ROOT"

  # Refuse to clobber an existing branch.
  if git show-ref --verify --quiet "refs/heads/$branch" 2>/dev/null; then
    die "branch already exists: $branch (delete it or pick a new slug)"
  fi

  # --- Base branch policy (ATW-208) ---------------------------------------
  # Every new worktree branches from the latest origin/main. We:
  #   1. Refuse to add when the trunk working tree is not on main (or a
  #      branch tracking origin/main), so worktrees never silently branch
  #      from a stale feature branch.
  #   2. Fetch origin/main (non-fatal on network failure with a warning).
  #   3. Refresh local main from origin/main when present, or create it
  #      from origin/main when missing, so the trunk worktree can return
  #      to it.
  #   4. Base the new branch on origin/main; fall back to local main only
  #      when offline and local main exists. Never fall back to the current
  #      HEAD or another feature branch.
  #   5. Print the base SHA used so the worktree's origin is auditable.

  local trunk_branch
  trunk_branch="$(git -C "$TRUNK_ROOT" branch --show-current 2>/dev/null || true)"

  # A branch is an acceptable trunk base iff it is `main` or tracks
  # origin/main. Anything else (a feature branch, detached HEAD) is refused.
  local trunk_tracks_main=0
  if [ "$trunk_branch" = "main" ]; then
    trunk_tracks_main=1
  elif [ -n "$trunk_branch" ]; then
    local upstream
    upstream="$(git -C "$TRUNK_ROOT" rev-parse --abbrev-ref --symbolic-full-name "$trunk_branch@{upstream}" 2>/dev/null || true)"
    if [ "$upstream" = "refs/remotes/origin/main" ]; then
      trunk_tracks_main=1
    fi
  fi

  if [ "$trunk_tracks_main" -ne 1 ]; then
    cat >&2 <<EOF
error: trunk worktree is not on main (or a branch tracking origin/main).
  trunk branch: ${trunk_branch:-<detached HEAD>}
  trunk root:   $TRUNK_ROOT

Worktrees must branch from the latest origin/main, not from the current
checkout. Restore the trunk to main first:

  git -C "$TRUNK_ROOT" fetch origin main
  git -C "$TRUNK_ROOT" branch -f main origin/main
  git -C "$TRUNK_ROOT" checkout main

Then re-run: $0 add $issue_id $type $slug

If you genuinely need to base this work on a different branch, record the
alternate base and the reason on the originating issue, then run git
worktree add by hand.
EOF
    exit 1
  fi

  # Fetch origin/main so the base is current. Non-fatal on network failure:
  # we fall back to local main below. (ATW-208)
  local online=1
  if ! git -C "$TRUNK_ROOT" fetch --quiet origin main 2>/dev/null; then
    online=0
    echo "warning: 'git fetch origin main' failed — continuing offline from local main if present" >&2
  fi

  # Resolve the base SHA. Prefer origin/main; fall back to local main only
  # when offline and local main exists. Never fall back to HEAD.
  local base_ref="" base_sha=""
  if [ "$online" -eq 1 ] && git -C "$TRUNK_ROOT" rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    base_ref="origin/main"
    base_sha="$(git -C "$TRUNK_ROOT" rev-parse origin/main)"
  elif git -C "$TRUNK_ROOT" rev-parse --verify --quiet main >/dev/null 2>&1; then
    if [ "$online" -eq 1 ]; then
      base_ref="origin/main"
      base_sha="$(git -C "$TRUNK_ROOT" rev-parse origin/main)"
    else
      base_ref="main (offline — may be stale; fetch when network returns)"
      base_sha="$(git -C "$TRUNK_ROOT" rev-parse main)"
    fi
  else
    die "no origin/main and no local main to base on. Run: git -C \"$TRUNK_ROOT\" fetch origin main && git -C \"$TRUNK_ROOT\" branch -f main origin/main"
  fi

  # Refresh / create local main from origin/main so the trunk worktree can
  # return to it. Only when online and origin/main moved ahead of local main
  # (or local main is missing). (ATW-208)
  if [ "$online" -eq 1 ]; then
    if ! git -C "$TRUNK_ROOT" rev-parse --verify --quiet main >/dev/null 2>&1; then
      echo "local main missing — creating from origin/main" >&2
      git -C "$TRUNK_ROOT" branch main origin/main
    else
      local local_main_sha
      local_main_sha="$(git -C "$TRUNK_ROOT" rev-parse main)"
      if [ "$local_main_sha" != "$base_sha" ]; then
        # Fast-forward local main to origin/main. Use -f only as a safety net;
        # origin/main is an ancestor-fast-forward of main in normal flow, but
        # if local main diverged we refuse rather than rewrite history.
        if git -C "$TRUNK_ROOT" merge-base --is-ancestor "$local_main_sha" "$base_sha"; then
          git -C "$TRUNK_ROOT" branch -f main "$base_sha" >/dev/null 2>&1 || true
        else
          echo "warning: local main ($local_main_sha) has diverged from origin/main ($base_sha) — not rewriting local main. Trunk checkout unchanged." >&2
        fi
      fi
    fi
  fi

  local port
  port="$(next_free_port)"

  # Create the worktree branched from the resolved base. Use origin/main
  # directly when online so the new branch starts at the fetched tip; use
  # local main only when offline.
  local create_from="$base_sha"
  if [ "$online" -eq 1 ]; then
    create_from="origin/main"
  fi
  git -C "$TRUNK_ROOT" worktree add "$wt" -b "$branch" "$create_from"
  base_sha="$(git -C "$wt" rev-parse HEAD)"

  # Record the claimed port and write the worktree .env so docker compose picks
  # up the project name + published port. COMPOSE_PROJECT_NAME namespaces
  # containers, volumes, and networks per issue. Docker Compose v2 requires the
  # project name to be lowercase alphanumeric/hyphens/underscores, so lowercase
  # the issue id (e.g. ATW-193 -> atw-193) — an uppercase project name is
  # rejected with "invalid project name" at `up` time.
  printf '%s\n' "$port" > "$wt/.dev-port"
  cat > "$wt/.env" <<EOF
# Per-worktree dev environment. Generated by scripts/dev-worktree.sh.
# Edit by hand if you need different resource caps; do not commit this file.
COMPOSE_PROJECT_NAME=$(printf '%s' "$issue_id" | tr '[:upper:]' '[:lower:]')
NETBOX_PORT=$port
EOF

  cat <<EOF
created worktree: $wt
branch:          $branch
base:            $base_ref
base SHA:        $base_sha
compose project: $issue_id
netbox port:     127.0.0.1:$port

Next:
  cd $wt
  scripts/dev-worktree.sh up
EOF
}

cmd_up() {
  # Run from the current worktree. Requires .env next to docker-compose.dev.yml.
  [ -f "./.env" ]           || die "no ./.env found — run this from a worktree created by 'dev-worktree.sh add'"
  [ -f "./docker-compose.dev.yml" ] || die "no ./docker-compose.dev.yml — run this from a worktree root"

  local port
  port="$(grep -E '^NETBOX_PORT=' .env | cut -d= -f2-)"

  # OOM guardrail (ATW-201): refuse to start a new stack if another netbox dev
  # stack is already running and we're at the concurrency cap. Each stack is
  # ~5.7 GiB of mem_limit; the host has 7.8 GiB RAM + 2 GiB swap, so 2
  # concurrent stacks guarantee OOM.
  local current_proj
  current_proj="$(grep -E '^COMPOSE_PROJECT_NAME=' .env | cut -d= -f2-)"
  local running
  running="$(running_netbox_projects | grep -vxF "$current_proj" || true)"
  if [ -n "$running" ]; then
    local count
    count="$(printf '%s\n' "$running" | wc -l)"
    if [ "$count" -ge "$MAX_CONCURRENT_STACKS" ]; then
      echo "error: $count other netbox dev stack(s) already running:" >&2
      printf '  - %s\n' $running >&2
      cat >&2 <<EOF
  Host has 7.8 GiB RAM + 2 GiB swap; one stack ≈ 5.7 GiB mem_limit.
  $((count + 1)) concurrent stacks would exceed total memory and OOM.

  Tear down the other stack(s) first:
    scripts/dev-worktree.sh remove <issue-id>
  Or override (dangerous on this host):
    MAX_CONCURRENT_STACKS=$((count + 1)) scripts/dev-worktree.sh up
EOF
      exit 1
    fi
  fi

  echo "bringing up compose stack on 127.0.0.1:$port ..."
  docker compose -f docker-compose.dev.yml --env-file .env up -d
  echo
  echo "netbox: http://localhost:$port  (admin / admin)"
}

cmd_remove() {
  local issue_id="${1:-}"
  [ -n "$issue_id" ] || usage
  local wt="$WT_ROOT/$issue_id"

  [ -d "$wt" ] || die "no worktree for $issue_id at $wt"

  # Tear down the compose stack + volumes if the .env is still present.
  if [ -f "$wt/.env" ] && [ -f "$wt/docker-compose.dev.yml" ]; then
    echo "bringing down compose stack for $issue_id ..."
    docker compose -f "$wt/docker-compose.dev.yml" --env-file "$wt/.env" down -v \
      || echo "warning: compose down failed (continuing with worktree removal)" >&2
  else
    echo "no .env/compose file in $wt — skipping compose down"
  fi

  git -C "$TRUNK_ROOT" worktree remove --force "$wt"

  # Clean up the worktree directory if git left it behind.
  rmdir "$wt" 2>/dev/null || true

  # Delete the branch too. Refuse if it has unmerged commits; print the SHA so
  # the operator can recover it if they really meant to keep it.
  local branch
  branch="$(git -C "$TRUNK_ROOT" worktree list --porcelain 2>/dev/null \
            | awk -v wt="$wt/" 'BEGIN{found=0} /^worktree /{g=substr($2,1,length(wt)); if(g==wt) found=1; else found=0} found && /^branch /{print $2; exit}')"
  # The branch lookup above ran after removal, so it won't find anything. Track
  # branches by convention instead: <type>/<issue-id>-<slug>.
  echo "removed worktree: $wt"
  echo "note: matching branches (<type>/$issue_id-*) were not auto-deleted; remove with:"
  echo "  git -C \"$TRUNK_ROOT\" branch -D <branch>"
}

# List compose project names that own at least one container (running or
# stopped) and look like a netbox dev stack. Does NOT match bare-numeric
# projects — those are discovered via volume_netbox_projects() which is
# netbox-specific (requires `<proj>_netbox-*` prefix). This prevents
# cmd_cleanup() from force-removing stopped containers of unrelated
# numeric-named compose projects on the dev host. (ATW-201/ATW-271/ATW-272)
container_netbox_projects() {
  docker ps -a --format '{{.Label "com.docker.compose.project"}}' 2>/dev/null \
    | grep -E "$NETBOX_PROJECT_RE" \
    | sort -u || true
}

# List compose project names derived from orphaned netbox volumes — volumes
# whose names match the `${project}_netbox-*` compose convention but whose
# project has no containers at all. This is the common accumulation case:
# volumes outlive their containers unless `docker compose down -v` ran, so the
# project is invisible to container-label discovery. (ATW-204)
volume_netbox_projects() {
  # Compose names volumes `<project>_<service>_<instance>` or
  # `<project>_<volume_name>`. Netbox dev stacks always create at least one
  # volume starting with `<project>_netbox`, so prefix-match on that.
  # Uses the shared NETBOX_VOLUME_RE so bare-numeric projects (e.g. `251`)
  # are discovered alongside `atw-*`. (ATW-204/ATW-271)
  docker volume ls --format '{{.Name}}' 2>/dev/null \
    | grep -iE "$NETBOX_VOLUME_RE" \
    | sed -E 's/^(.*)_netbox-.*/\1/' \
    | sort -u || true
}

cmd_cleanup() {
  # Find and tear down orphaned compose projects — netbox dev stacks whose
  # worktree directory is gone or whose containers are all stopped. Skips
  # stacks that have at least one running container (so it won't kill a live
  # dev session or a QA testbed). Safe to run on a schedule. (ATW-201)
  #
  # Project discovery is the union of:
  #   - container-label discovery (projects with any container), and
  #   - volume-name discovery (projects whose containers are gone but whose
  #     `<project>_netbox-*` volumes remain — the orphaned-volume case that
  #     container-only discovery silently misses). (ATW-204)
  echo "=== dev-worktree cleanup: scanning for orphaned stacks ==="

  local container_projects volume_projects all_projects
  container_projects="$(container_netbox_projects)"
  volume_projects="$(volume_netbox_projects)"
  # Union the two project sets (both already sorted-u, awk dedups again).
  all_projects="$(printf '%s\n%s\n' "$container_projects" "$volume_projects" \
    | awk 'NF' | sort -u)"

  if [ -z "$all_projects" ]; then
    echo "no netbox dev compose projects found — nothing to clean."
    return 0
  fi

  local cleaned=0
  local skipped=0
  for proj in $all_projects; do
    local has_running
    has_running="$(docker ps --filter "label=com.docker.compose.project=$proj" -q 2>/dev/null | head -1)"
    if [ -n "$has_running" ]; then
      echo "  $proj: running containers found — skipping (live dev session or QA testbed)"
      skipped=$((skipped + 1))
      continue
    fi

    # All containers stopped. Find the compose config file to run `down -v`.
    # Try worktree paths first, then /tmp fallback.
    local config_file="" env_file=""
    local norm_proj
    norm_proj="$(printf '%s' "$proj" | tr '[:upper:]' '[:lower:]')"
    for wt_dir in "$WT_ROOT/$proj" "$WT_ROOT/$norm_proj" "/tmp/netbox-pyats-wt/$proj" "/tmp/netbox-pyats-wt/$norm_proj"; do
      if [ -f "$wt_dir/docker-compose.dev.yml" ]; then
        config_file="$wt_dir/docker-compose.dev.yml"
        if [ -f "$wt_dir/.env" ]; then
          env_file="$wt_dir/.env"
        fi
        break
      fi
    done

    if [ -z "$config_file" ]; then
      # No compose file found. Two sub-cases:
      #   - stopped containers with no recoverable compose file, or
      #   - pure orphaned volumes (no containers at all — discovered via
      #     volume-name prefix). (ATW-204)
      local stopped_ids
      stopped_ids="$(docker ps -aq --filter "label=com.docker.compose.project=$proj" 2>/dev/null)"
      if [ -n "$stopped_ids" ]; then
        echo "  $proj: stopped, no compose file — removing containers by label"
        docker rm -f $stopped_ids 2>/dev/null || true
      else
        echo "  $proj: no containers, no compose file — removing orphaned volumes"
      fi
    else
      echo "  $proj: stopped — running 'docker compose down -v' from $config_file"
      if [ -n "$env_file" ]; then
        docker compose -f "$config_file" --env-file "$env_file" down -v 2>&1 | sed 's/^/    /' || true
      else
        docker compose -f "$config_file" down -v 2>&1 | sed 's/^/    /' || true
      fi
    fi

    # Remove orphaned volumes for this project (compose down -v should handle
    # it, but catch stragglers).
    local dangling_volumes
    dangling_volumes="$(docker volume ls --format '{{.Name}}' 2>/dev/null \
      | grep -iE "^${proj}_netbox-" || true)"
    for v in $dangling_volumes; do
      if docker volume rm "$v" >/dev/null 2>&1; then
        echo "    removed volume: $v"
      else
        echo "    warning: could not remove volume: $v" >&2
      fi
    done

    cleaned=$((cleaned + 1))
  done

  echo
  echo "cleanup complete: $cleaned stack(s) torn down, $skipped active stack(s) skipped."
}

cmd_audit() {
  # Print a report of running/stopped compose stacks, orphaned volumes,
  # images, networks, and host port-exposure. Post the output back to the
  # originating issue. (ATW-201)
  echo "=== dev-worktree audit: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo

  echo "--- running netbox dev stacks ---"
  # Match the same project-name alternation as running_netbox_projects so
  # running atw-* and bare-numeric stacks show up here too, not just the
  # trunk netbox-pyats project. (ATW-204/ATW-271)
  local running
  running="$(docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Image}}\t{{.Ports}}' 2>/dev/null \
    | grep -E "$(printf '\t(%s)\t' "$NETBOX_PROJECT_ALT")" || true)"
  if [ -z "$running" ]; then
    echo "  (none)"
  else
    printf '%s\n' "$running" | sed 's/^/  /'
  fi
  echo

  echo "--- stopped netbox dev containers (orphaned) ---"
  # Match the project alternation on the tab-delimited project label so
  # bare-numeric stacks (e.g. `251-postgres-1`) are not missed. The `netbox`
  # fallback catches containers whose project label is absent but whose name
  # contains `netbox`. The tab-delimited project filter must use real tab
  # characters (built via printf) because grep -E does not interpret `\t`.
  # (ATW-271)
  local stopped_tab_re
  stopped_tab_re="$(printf '\t(%s)\t' "$NETBOX_PROJECT_ALT")"
  local stopped
  stopped="$(docker ps -a --filter 'status=exited' \
    --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Status}}' \
    | grep -iE "(netbox|$stopped_tab_re)" || true)"
  if [ -z "$stopped" ]; then
    echo "  (none)"
  else
    echo "$stopped" | sed 's/^/  /'
  fi
  echo

  echo "--- host memory ---"
  free -h | sed 's/^/  /'
  echo

  echo "--- docker disk usage ---"
  docker system df | sed 's/^/  /'
  echo

  echo "--- netbox-related volumes ---"
  # Use the shared volume regex so bare-numeric project volumes (e.g.
  # `251_netbox-postgres`) are listed alongside `atw-*` and `netbox-pyats`.
  # (ATW-271)
  docker volume ls --format '{{.Name}}' 2>/dev/null \
    | grep -iE "$NETBOX_VOLUME_RE" | sed 's/^/  /' || echo "  (none)"
  echo

  echo "--- images (dev stack) ---"
  docker images --format '  {{.Repository}}:{{.Tag}}\t{{.Size}}' 2>/dev/null \
    | grep -iE '(netbox|atw-|pyats|valkey|postgres|redis)' || echo "  (none)"
  echo

  echo "--- networks ---"
  docker network ls --format '{{.Name}}' 2>/dev/null \
    | grep -iE '(netbox|atw|devnet)' | sed 's/^/  /' || echo "  (none)"
  echo

  echo "--- host port exposure check (public IP) ---"
  # Any listening port bound to a non-loopback address is a potential exposure.
  ss -tlnp 2>/dev/null | grep -vE '127\.0\.0|::1|\[::1\]|\*' \
    | grep -E ':[0-9]+' | sed 's/^/  /' || echo "  (no non-loopback bindings)"
  echo
  echo "--- wildcard (*) bindings (review for public exposure) ---"
  ss -tlnp 2>/dev/null | grep -E '\*:[0-9]+' | sed 's/^/  /' || echo "  (none)"
  echo

  echo "--- worktree inventory ---"
  git -C "$TRUNK_ROOT" worktree list 2>/dev/null | sed 's/^/  /' || echo "  (no worktrees)"
  echo

  echo "--- orphaned /tmp worktree dirs (no matching git worktree) ---"
  if [ -d /tmp/netbox-pyats-wt ]; then
    local git_wts
    git_wts="$(git -C "$TRUNK_ROOT" worktree list --porcelain 2>/dev/null \
      | awk '/^worktree /{print $2}' || true)"
    for d in /tmp/netbox-pyats-wt/*/; do
      if ! printf '%s\n' "$git_wts" | grep -qxF "${d%/}"; then
        echo "  $d"
      fi
    done
  else
    echo "  (none)"
  fi
}

[ $# -ge 1 ] || usage
sub="$1"; shift
case "$sub" in
  add)     cmd_add "$@" ;;
  up)      cmd_up "$@" ;;
  remove)  cmd_remove "$@" ;;
  cleanup) cmd_cleanup "$@" ;;
  audit)   cmd_audit "$@" ;;
  -h|--help|help) usage ;;
  *)       usage ;;
esac
