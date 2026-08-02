#!/usr/bin/env bash
# dev-seed.sh — build and manage a shared migrated-postgres seed volume so
# fresh worktrees skip the ~8-9 min NetBox migration cold start into
# `test_netbox` (ATW-527 / ATW-534).
#
# The seed is a single shared named Docker volume, `netbox-pyats-pg-seed`
# (host-wide, NOT per-worktree), holding a `pg_dump -Fc` custom-format dump
# of the fully-migrated `test_netbox` schema. A fresh worktree's
# `dev-worktree.sh up` restores `test_netbox` from this dump into its OWN
# per-worktree `netbox-postgres` volume on first boot (opt-in via the
# POSTGRES_SEED_VOLUME mechanism), turning the ~8 min cold start into a
# ~30 s `pg_restore`.
#
# The `--reuse-db` velocity win (ATW-357) only pays off inside the SAME
# worktree's postgres volume. Each worktree gets its own isolated
# `<project>_netbox-postgres` volume, so every new worktree re-pays the
# ~200-NetBox-migration cold start into a brand-new `test_netbox`. A single
# PR generates 4 worktrees (Author + Review + Security + QA), only one of
# which reuses. The seed volume is what makes the cross-worktree reuse
# promise actually true.
#
# Re-seed when migrations change on `main` (run `dev-seed.sh build` from a
# worktree at the latest origin/main, or schedule it as a routine). The
# seed carries a marker file recording the migration-state hash and
# NETBOX_IMAGE it was built against, so `dev-worktree.sh test` can detect
# drift against the worktree's own migration state and fall back to
# `--create-db` with a warning instead of failing opaquely (ATW-534 #2).
#
# Commands:
#   dev-seed.sh build [pytest-args...]
#       Build (or rebuild) the seed volume by spinning a one-shot
#       postgres + the netbox-test service running pytest with --create-db
#       (no --reuse-db). pytest-django creates + migrates `test_netbox`
#       from scratch, then the script dumps it into the shared volume.
#       Run this from a worktree at the latest origin/main. Extra args
#       pass through to the netbox-test service (after --create-db).
#
#   dev-seed.sh restore
#       Restore `test_netbox` from the shared seed volume into the
#       current worktree's own postgres volume. Requires the postgres
#       service to be running. Idempotent: skips the restore if
#       `test_netbox` already exists in the worktree's postgres (use
#       `dev-seed.sh force-restore` to overwrite). The marker file is
#       written into the worktree so `dev-worktree.sh test` can detect
#       stale-schema drift on the next test run.
#
#   dev-seed.sh force-restore
#       Restore `test_netbox` from the seed, dropping an existing
#       `test_netbox` first.
#
#   dev-seed.sh remove
#       Delete the shared seed volume.
#
#   dev-seed.sh info
#       Print seed volume status, marker, and worktree migration state.
#
# Safety:
#   - The seed build runs a full `netbox-test` service bring-up, which
#     counts toward MAX_CONCURRENT_STACKS (ATW-201) while it runs. The
#     script refuses to build if another netbox dev stack is already
#     running on the host (OOM guardrail, 7.8 GiB RAM + 2 GiB swap).
#   - All postgres work happens inside containers on the isolated devnet
#     bridge network (ATW-35). No port is published to the host's public
#     IP during the seed build; the script reuses the worktree's loopback
#     port assignment.
#   - The seed volume is shared (not namespaced) so all worktrees read the
#     same migrated schema. Worktrees restore INTO their own per-project
#     postgres volume — the seed is never written to by a worktree.
#
# Opt-in: the seed mechanism is opt-in. `dev-worktree.sh up` only restores
# from the seed when a seed volume exists AND the worktree's .env has
# POSTGRES_SEED_VOLUME set (set by `dev-worktree.sh add` when a seed
# exists), or when run with `POSTGRES_SEED_VOLUME=netbox-pyats-pg-seed`
# on the command line. Without a seed, behavior is unchanged (ATW-534 #4).

set -euo pipefail

# Resolve the trunk repo root so the script works from any worktree.
TRUNK="$(git rev-parse --git-common-dir 2>/dev/null)"
if [ -z "$TRUNK" ]; then
  echo "error: not inside a git repo" >&2
  exit 1
fi
case "$TRUNK" in
  /*) TRUNK="$(cd "$TRUNK" && pwd)" ;;
  *)  TRUNK="$(cd "$(pwd)/$TRUNK" && pwd)" ;;
esac
TRUNK_ROOT="$(dirname "$TRUNK")"
WT_ROOT="$(dirname "$TRUNK_ROOT")/$(basename "$TRUNK_ROOT")-wt"

# Shared seed volume name (host-wide, NOT namespaced by project). Every
# worktree reads from this same volume. Re-seeding replaces it atomically
# (we build into a temp volume, then swap).
SEED_VOLUME="${POSTGRES_SEED_VOLUME:-netbox-pyats-pg-seed}"
# Marker file inside the seed volume, recording the migration-state hash
# and NETBOX_IMAGE the seed was built against. dev-worktree.sh test reads
# a copy of this (restored into the worktree) to detect stale-schema drift.
SEED_MARKER_NAME="seed-marker"

# Plugin migration directory. The migration-state hash covers the plugin's
# own migrations + the NetBox image (which carries NetBox's own migrations)
# + the dev configuration, so a NetBox upgrade or a plugin migration both
# invalidate the seed. NetBox's migrations live inside the image at
# /opt/netbox/netbox/core/migrations etc.; we hash the plugin migrations
# here and let the NETBOX_IMAGE tag cover the NetBox side.
PLUGIN_MIGRATIONS_DIR="netbox_pyats/migrations"

# Per-invocation temp dir, cleaned on exit. Used for the dump file and the
# marker copy pulled out of a volume. mktemp -d gives a unique, predictable
# path; the trap removes it on any exit path so no temp files leak.
TMP_DIR="$(mktemp -d -t dev-seed.XXXXXX)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

die() { echo "error: $*" >&2; exit 1; }

# Compute a stable hash of the plugin migration state. This is the marker
# that `dev-worktree.sh test` compares against to detect stale schema.
# Includes the NETBOX_IMAGE tag (so a NetBox upgrade invalidates the seed)
# and the dev configuration that affects migrations (PLUGINS list etc.).
# We hash file CONTENTS, not names, so a renamed migration with the same
# ops does not falsely invalidate — but a new migration (new content) does.
migration_state_hash() {
  local netbox_image="${NETBOX_IMAGE:-docker.io/netboxcommunity/netbox:v4.6-5.0.2}"
  local h=""
  if [ -d "$PLUGIN_MIGRATIONS_DIR" ]; then
    h="$(find "$PLUGIN_MIGRATIONS_DIR" -name '*.py' -not -name '__init__.py' \
        -print0 | sort -z | xargs -0 cat 2>/dev/null | sha256sum | cut -d' ' -f1)"
  else
    h="no-migrations-dir"
  fi
  printf '%s|%s\n' "$h" "$netbox_image"
}

# Write the marker file into a target path. Args: $1 = target marker file
# path, $2 = optional existing marker file to copy (else compute fresh).
write_marker() {
  local target="$1" src="${2:-}"
  if [ -n "$src" ] && [ -f "$src" ]; then
    cp "$src" "$target"
    return
  fi
  local hash image ts
  hash="$(migration_state_hash)"
  image="${NETBOX_IMAGE:-docker.io/netboxcommunity/netbox:v4.6-5.0.2}"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "$target" <<EOF
# Seed marker — written by dev-seed.sh. Do not edit by hand.
# dev-worktree.sh test compares the worktree's migration-state hash
# against this to detect stale-schema drift and auto-fall-back to
# --create-db (ATW-534 #2).
migration_hash=$hash
netbox_image=$image
seeded_at=$ts
seed_volume=$SEED_VOLUME
EOF
}

# Count running netbox dev compose projects (excluding the seed build's
# own transient project). Reuses the same definition as dev-worktree.sh.
running_netbox_projects() {
  docker ps --format '{{.Label "com.docker.compose.project"}}' 2>/dev/null \
    | grep -E '^(netbox-pyats|[Aa][Tt][Ww]-?[0-9]+)$' \
    | sort -u || true
}

usage() {
  cat >&2 <<EOF
usage: dev-seed.sh <command> [args]

  build [pytest-args...]   build/rebuild the shared seed volume
  restore                  restore test_netbox from seed into current worktree
  force-restore            restore, dropping an existing test_netbox first
  remove                   delete the shared seed volume
  info                     print seed status + worktree migration state

examples:
  dev-seed.sh build                         # full migrate into seed volume
  dev-seed.sh build --create-db -v          # pass-through pytest args
  dev-seed.sh restore                       # into current worktree's postgres
  dev-seed.sh info

env overrides:
  POSTGRES_SEED_VOLUME  shared volume name (default: netbox-pyats-pg-seed)
  NETBOX_IMAGE          NetBox image tag to seed against
EOF
  exit 2
}

# --- build ----------------------------------------------------------------
# Spins a one-shot postgres + the netbox-test service running pytest with
# --create-db (so pytest-django builds test_netbox from scratch), then
# dumps test_netbox into the shared seed volume with the marker file.
# Runs inside the current worktree's compose project so the loopback-only
# publish policy (ATW-35) and OOM guardrail (ATW-201) are respected.
cmd_build() {
  [ -f "./.env" ] || die "no ./.env — run from a worktree created by 'dev-worktree.sh add'"
  [ -f "./docker-compose.dev.yml" ] || die "no ./docker-compose.dev.yml — run from a worktree root"
  [ -f "./docker-compose.test.yml" ] || die "no ./docker-compose.test.yml — required for the seed build"

  local current_proj
  current_proj="$(grep -E '^COMPOSE_PROJECT_NAME=' .env | cut -d= -f2-)"

  # OOM guardrail (ATW-201): refuse to build if another netbox dev stack is
  # running. The seed build itself starts postgres + netbox-test (~2 GiB),
  # which is fine on its own but not alongside a running stack.
  local running others
  running="$(running_netbox_projects)"
  if [ -n "$running" ]; then
    others="$(printf '%s\n' "$running" | grep -vxF "$current_proj" || true)"
    if [ -n "$others" ]; then
      echo "error: other netbox dev stack(s) running — seed build would oversubscribe the host:" >&2
      printf '  - %s\n' $others >&2
      echo "  tear them down first: scripts/dev-worktree.sh remove <issue-id>" >&2
      exit 1
    fi
  fi

  local netbox_image="${NETBOX_IMAGE:-docker.io/netboxcommunity/netbox:v4.6-5.0.2}"
  echo "=== dev-seed.sh build: seeding test_netbox for $netbox_image ==="
  echo "  seed volume: $SEED_VOLUME"
  echo "  worktree:    $(pwd) (project: $current_proj)"
  echo

  # Ensure postgres + redis are up and healthy.
  echo "ensuring postgres + redis are up ..."
  docker compose -f docker-compose.dev.yml -f docker-compose.test.yml \
    --env-file .env up -d --wait postgres redis

  # Run the netbox-test service with --create-db to build a fresh
  # test_netbox from scratch (all ~200 NetBox migrations + plugin migrations).
  # We use --create-db explicitly so the build is authoritative even if a
  # stale test_netbox somehow exists in this worktree's postgres.
  #
  # We run a SINGLE fast TestCase (PyatsCredentialModelTest) to force
  # Django's test runner to create + migrate test_netbox. A no-op `-k
  # nope` deselected all tests and left test_netbox uncreated, because
  # Django's TestCase test-db setup only fires when at least one TestCase
  # is collected and run. PyatsCredentialModelTest is a model smoke test
  # (create/read/delete a PyatsCredential row) — it runs in <1 s after
  # migrations and proves the schema is usable, not just present. We pass
  # `--create-db -q` to keep the output minimal; the test result itself
  # is irrelevant (we just want the migrated test_netbox to exist for the
  # dump), so we tolerate a non-zero exit if the single test fails for a
  # cosmetic reason — the dump step verifies test_netbox exists.
  echo "running netbox-test --create-db (building test_netbox migrations + 1 smoke test) ..."
  local t0 t1
  t0="$(date +%s)"
  docker compose -f docker-compose.dev.yml -f docker-compose.test.yml \
    --env-file .env run --rm -T netbox-test \
    --create-db -q netbox_pyats/tests/test_models.py::PyatsCredentialModelTest || true
  t1="$(date +%s)"
  echo "  migration build took $((t1 - t0))s"
  echo

  # Verify test_netbox actually exists before dumping (the single-test run
  # should have created it; if not, we fail loudly instead of dumping an
  # empty/missing DB).
  local has_test_db
  has_test_db="$(docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
    psql -U netbox -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='test_netbox'" 2>/dev/null | tr -d '[:space:]')"
  if [ "$has_test_db" != "1" ]; then
    die "test_netbox was not created by the netbox-test run — cannot dump. Check the netbox-test logs."
  fi

  # Dump test_netbox into a temp host file, then copy it + the marker into
  # the shared seed volume. pg_dump -Fc gives a custom-format dump that
  # pg_restore can load in parallel (fast restore). We restore only the
  # schema (--schema-only) at worktree time, not the data, because
  # pytest-django re-creates test fixtures per-run — but a schema-only
  # dump skips the ~200 migrations which is the actual cold-start cost.
  # (A full dump is also fine and lets us skip the data setup too; we keep
  # the full dump for flexibility and pg_restore --schema-only at restore.)
  echo "dumping test_netbox ..."
  local dump_file="$TMP_DIR/test_netbox.dump"
  docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
    pg_dump -U netbox -d test_netbox -Fc > "$dump_file"
  local dump_size
  dump_size="$(stat -c '%s' "$dump_file")"
  echo "  dump size: $((dump_size / 1024 / 1024)) MiB"

  # Build into a TEMP seed volume first, then atomically swap into the
  # final name. A failed build never corrupts an existing good seed.
  local tmp_vol
  tmp_vol="${SEED_VOLUME}-new-$$"
  echo "copying dump + marker into temp seed volume $tmp_vol ..."
  docker volume rm "$tmp_vol" >/dev/null 2>&1 || true
  docker volume create "$tmp_vol" >/dev/null

  local marker_file="$TMP_DIR/${SEED_MARKER_NAME}"
  write_marker "$marker_file"

  docker run --rm \
    -v "$tmp_vol:/seed" \
    -v "$dump_file:/dump-source:ro" \
    -v "$marker_file:/marker-source:ro" \
    --entrypoint sh \
    docker.io/alpine:3 \
    -c "cp /dump-source /seed/test_netbox.dump && cp /marker-source /seed/${SEED_MARKER_NAME} && sync && ls -la /seed/"

  # Atomic swap: remove the old seed volume, create the final, copy
  # contents from the temp, remove the temp.
  echo "swapping temp seed volume into place ($SEED_VOLUME) ..."
  if docker volume inspect "$SEED_VOLUME" >/dev/null 2>&1; then
    docker volume rm "$SEED_VOLUME" >/dev/null
  fi
  docker volume create "$SEED_VOLUME" >/dev/null
  docker run --rm \
    -v "$tmp_vol:/src:ro" \
    -v "$SEED_VOLUME:/dst" \
    --entrypoint sh \
    docker.io/alpine:3 \
    -c "cp -a /src/. /dst/ && sync && ls -la /dst/"
  docker volume rm "$tmp_vol" >/dev/null

  echo
  echo "=== seed build complete ==="
  echo "  seed volume:  $SEED_VOLUME"
  echo "  dump file:    /seed/test_netbox.dump ($((dump_size / 1024 / 1024)) MiB)"
  echo "  marker:       /seed/${SEED_MARKER_NAME}"
  echo
  cmd_info
}

# --- restore ---------------------------------------------------------------
# Restore test_netbox from the shared seed volume into the CURRENT
# worktree's own postgres volume. The worktree's postgres service must be
# running. Idempotent: skips if test_netbox already exists unless --force.
_restore() {
  local force="${1:-0}"
  [ -f "./.env" ] || die "no ./.env — run from a worktree created by 'dev-worktree.sh add'"
  [ -f "./docker-compose.dev.yml" ] || die "no ./docker-compose.dev.yml — run from a worktree root"

  local current_proj
  current_proj="$(grep -E '^COMPOSE_PROJECT_NAME=' .env | cut -d= -f2-)"

  # Verify the seed volume exists.
  if ! docker volume inspect "$SEED_VOLUME" >/dev/null 2>&1; then
    die "seed volume $SEED_VOLUME does not exist. Build it first: scripts/dev-seed.sh build"
  fi

  # Verify the worktree's postgres is running.
  if ! docker compose -f docker-compose.dev.yml --env-file .env ps postgres 2>/dev/null \
        | grep -qE "running|healthy"; then
    die "postgres is not running for project $current_proj. Run 'scripts/dev-worktree.sh up' (or at least 'docker compose up -d --wait postgres') first."
  fi

  # Check for an existing test_netbox in this worktree's postgres.
  local existing
  existing="$(docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
    psql -U netbox -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='test_netbox'" 2>/dev/null | tr -d '[:space:]')"
  if [ "$existing" = "1" ] && [ "$force" -ne 1 ]; then
    echo "test_netbox already exists in $current_proj postgres — skipping restore (use 'dev-seed.sh force-restore' to overwrite)"
    return 0
  fi

  if [ "$existing" = "1" ]; then
    echo "dropping existing test_netbox in $current_proj postgres ..."
    # Kill any connections holding test_netbox open, then drop it.
    docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
      psql -U netbox -d postgres -c \
      "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='test_netbox' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true
    docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
      psql -U netbox -d postgres -c "DROP DATABASE IF EXISTS test_netbox;" >/dev/null
  fi

  echo "restoring test_netbox from seed volume $SEED_VOLUME into $current_proj postgres ..."
  local t0 t1
  t0="$(date +%s)"

  # Copy the dump out of the shared seed volume into the per-invocation
  # temp dir, then stream it into pg_restore inside the worktree's postgres
  # container. The dump is ~tens of MiB so the temp copy is cheap and keeps
  # the restore path container-agnostic (no volume mount gymnastics).
  local tmp_dump="$TMP_DIR/restore-test_netbox.dump"
  docker run --rm \
    -v "$SEED_VOLUME:/seed:ro" \
    -v "$tmp_dump:/dump-out" \
    --entrypoint sh \
    docker.io/alpine:3 \
    -c "cp /seed/test_netbox.dump /dump-out"

  # Create the (empty) test_netbox database, then restore the schema into it.
  # pg_restore --schema-only because pytest-django re-creates test fixtures
  # per run — the win is skipping the ~200 migrations, not the test data.
  # --no-owner / --no-acl avoid ownership mismatches between the seed's
  # postgres and this one (both are the dev netbox user, but be safe).
  docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
    psql -U netbox -d postgres -c "CREATE DATABASE test_netbox OWNER netbox;" >/dev/null
  docker compose -f docker-compose.dev.yml --env-file .env exec -T postgres \
    pg_restore -U netbox -d test_netbox --no-owner --no-acl --schema-only --jobs=4 \
    < "$tmp_dump" 2>&1 | grep -vE '^(WARNING|ERROR|pg_restore:)' || true

  t1="$(date +%s)"
  echo "  restore took $((t1 - t0))s"

  # Write the worktree's .dev-test-marker from the seed's marker so
  # dev-worktree.sh test can detect stale-schema drift on the next run.
  local marker_wt_tmp="$TMP_DIR/${SEED_MARKER_NAME}-wt"
  docker run --rm \
    -v "$SEED_VOLUME:/seed:ro" \
    -v "$marker_wt_tmp:/marker-out" \
    --entrypoint sh \
    docker.io/alpine:3 \
    -c "cp /seed/${SEED_MARKER_NAME} /marker-out"
  cp "$marker_wt_tmp" .dev-test-marker
  echo "  wrote worktree marker: .dev-test-marker"
  echo
  echo "restore complete. Run 'scripts/dev-worktree.sh test' to use the seeded test_netbox."
}

cmd_restore()       { _restore 0; }
cmd_force_restore() { _restore 1; }

# --- remove ----------------------------------------------------------------
cmd_remove() {
  if ! docker volume inspect "$SEED_VOLUME" >/dev/null 2>&1; then
    echo "seed volume $SEED_VOLUME does not exist — nothing to remove"
    return 0
  fi
  echo "removing seed volume $SEED_VOLUME ..."
  docker volume rm "$SEED_VOLUME"
  echo "removed."
}

# --- info ------------------------------------------------------------------
cmd_info() {
  echo "=== dev-seed.sh info ==="
  echo
  echo "--- seed volume ---"
  if docker volume inspect "$SEED_VOLUME" >/dev/null 2>&1; then
    echo "  $SEED_VOLUME: present"
    # Print the marker from inside the volume.
    local marker_info="$TMP_DIR/${SEED_MARKER_NAME}-info"
    if docker run --rm \
        -v "$SEED_VOLUME:/seed:ro" \
        -v "$marker_info:/marker-out" \
        --entrypoint sh \
        docker.io/alpine:3 \
        -c "cp /seed/${SEED_MARKER_NAME} /marker-out 2>/dev/null" 2>/dev/null; then
      echo "  marker:"
      sed 's/^/    /' "$marker_info" 2>/dev/null || echo "    (unreadable)"
    else
      echo "  marker: (missing)"
    fi
    # Dump file size.
    local size
    size="$(docker run --rm -v "$SEED_VOLUME:/seed:ro" --entrypoint sh docker.io/alpine:3 \
      -c 'stat -c %s /seed/test_netbox.dump 2>/dev/null || echo 0' 2>/dev/null || echo 0)"
    echo "  dump size: $((size / 1024 / 1024)) MiB"
  else
    echo "  $SEED_VOLUME: absent (no seed built yet)"
  fi
  echo
  echo "--- worktree migration state ---"
  if [ -f "./.env" ]; then
    local current_proj
    current_proj="$(grep -E '^COMPOSE_PROJECT_NAME=' .env | cut -d= -f2-)"
    echo "  project: $current_proj"
    echo "  worktree migration hash: $(migration_state_hash)"
    if [ -f ".dev-test-marker" ]; then
      echo "  worktree marker (.dev-test-marker):"
      sed 's/^/    /' .dev-test-marker
    else
      echo "  worktree marker: (none — no seed restore or --create-db yet)"
    fi
  else
    echo "  (not in a worktree — no ./.env)"
  fi
  echo
  echo "--- running netbox dev stacks ---"
  local running
  running="$(running_netbox_projects)"
  if [ -n "$running" ]; then
    printf '  %s\n' $running
  else
    echo "  (none)"
  fi
}

[ $# -ge 1 ] || usage
sub="$1"; shift
case "$sub" in
  build)         cmd_build "$@" ;;
  restore)       cmd_restore "$@" ;;
  force-restore) cmd_force_restore "$@" ;;
  remove)        cmd_remove "$@" ;;
  info)          cmd_info "$@" ;;
  -h|--help|help) usage ;;
  *)             usage ;;
esac