# Makefile — convenience targets for the netbox-pyats dev workflow.
#
# Targets here are thin wrappers around the scripts/ helpers so the single
# source of truth stays in scripts/. Run `make <target>` from the repo root
# (or from a worktree).

.PHONY: test test-unit test-integration lint format seed

# Pure-Python unit lane: 204 tests, no Docker, no NetBox, ~3s.
# Use this for logic changes (diff, testbed, capture, compliance, crypto).
# Extra pytest flags pass through:  make test-unit ARGS="-k crypto -v"
test-unit:
	scripts/test-unit.sh $(ARGS)

# Full integration suite via the dedicated `netbox-test` compose service
# (ATW-357 / ATW-354). This is the SAFE path: pytest runs without granian,
# so the granian-connection race (ATW-85 / ATW-188) cannot occur, and
# --reuse-db keeps the migrated test_netbox across runs. The stale-schema
# guard (ATW-534 #2) auto-falls-back to --create-db if migrations drifted
# since the last seed/--create-db. Extra pytest flags pass through.
#
# Historical note: this target previously routed to
#   docker compose exec netbox pytest
# which runs pytest INSIDE the granian web container and re-hits the
# ATW-85/188 race (granian's idle connections hold test_netbox between
# DROP and CREATE). That path is RETIRED (ATW-534 #3) — one integration
# entrypoint, not two. If you need the old behavior for debugging, run
# the docker compose exec command by hand, but prefer this target.
test-integration:
	scripts/dev-worktree.sh test $(ARGS)

# Build the shared migrated-postgres seed volume (ATW-534 #1). Run from a
# worktree at the latest origin/main. Once built, new worktrees auto-detect
# the seed and skip the ~8 min migration cold start on first test run.
seed:
	scripts/dev-seed.sh build $(ARGS)

# Lint + format checks (fast lane, no Docker).
lint:
	black --check netbox_pyats
	isort --check-only netbox_pyats
	flake8 netbox_pyats

format:
	black netbox_pyats
	isort netbox_pyats

# Default: run the cheap lanes that need no Docker.
test: test-unit lint