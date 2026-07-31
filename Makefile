# Makefile — convenience targets for the netbox-pyats dev workflow.
#
# Targets here are thin wrappers around the scripts/ helpers so the single
# source of truth stays in scripts/. Run `make <target>` from the repo root
# (or from a worktree).

.PHONY: test test-unit test-integration lint format

# Pure-Python unit lane: 103 tests, no Docker, no NetBox, ~3s.
# Use this for logic changes (diff, testbed, capture, compliance, crypto).
# Extra pytest flags pass through:  make test-unit ARGS="-k crypto -v"
test-unit:
	scripts/test-unit.sh $(ARGS)

# Full integration suite inside the dev container (requires Docker).
# See docs/developer/setup.md for the one-run-per-fresh-stack workflow.
test-integration:
	docker compose -f docker-compose.dev.yml exec -w /opt/netbox/netbox/netbox_pyats_src \
		netbox pytest netbox_pyats/tests $(ARGS)

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