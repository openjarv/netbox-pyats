"""Regression test for the compliance job's legacy ``config[raw]`` fallback (ATW-437).

:func:`netbox_pyats.jobs.run_compliance_job` extracts the snapshot's raw
running-config text from the snapshot ``data`` JSONB before running the
line-oriented compliance diff. The extraction has two paths:

1. **Current path** — ``data["config_raw"]`` (populated since migration 0006).
2. **Legacy fallback** — ``data["config"]["raw"]`` for snapshots captured
   *before* ``config_raw`` was added and whose Genie parser had failed at
   capture time. Documented at ``jobs.py`` §``run_compliance_job`` but
   previously *untested*: a regression in the fallback would silently
   classify every legacy-shape snapshot as ``error`` ("snapshot raw config is
   empty") instead of running compliance against the preserved raw text.

ATW-437 extracted the inline block into the pure helper
:func:`netbox_pyats.jobs.extract_snapshot_raw_config` so the fallback is
exercised against the *real* job code (not a replicated stub). This module
pins the helper's contract: current-path precedence, legacy fallback,
empty/missing handling, and defensive guards against corrupt JSONB shapes.

Pure-Python: imports the helper from :mod:`netbox_pyats.jobs` only; no
NetBox, no DB, no RQ. Runs in the fast pytest lane.
"""

from netbox_pyats.jobs import extract_snapshot_raw_config


class TestExtractSnapshotRawConfig:
    """Pin the contract of :func:`extract_snapshot_raw_config` (ATW-437)."""

    def test_config_raw_present_is_used_directly(self):
        # The normal path: a config/full snapshot captured with the v1 rework
        # carries data["config_raw"].
        data = {
            "config": {"hostname": "rtr01"},
            "config_raw": "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n",
        }
        assert extract_snapshot_raw_config(data) == (
            "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        )

    def test_legacy_snapshot_falls_back_to_config_raw_key(self):
        # The ATW-437 regression target: a snapshot captured before config_raw
        # was added (migration 0006 onward populates it) and whose Genie
        # parser had failed at capture time has data["config"]["raw"] instead.
        # The job falls back to it so compliance can still run against legacy
        # snapshots. A regression here silently classifies legacy snapshots as
        # error ("snapshot raw config is empty") instead of running compliance.
        data = {
            "config": {
                "raw": "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n",
                "_parser_error": "ParserNotFound",
            },
        }
        assert extract_snapshot_raw_config(data) == (
            "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        )

    def test_config_raw_takes_precedence_over_legacy_raw(self):
        # When both are present (shouldn't happen in practice, but the
        # extraction is deterministic), config_raw wins. This pins the
        # precedence so a refactor that flips the order is caught.
        data = {
            "config": {"raw": "legacy text"},
            "config_raw": "current text",
        }
        assert extract_snapshot_raw_config(data) == "current text"

    def test_empty_config_raw_falls_back_to_legacy(self):
        # An empty string config_raw is treated as missing — fall back to the
        # legacy path. (Captures with config_raw="" are the unsupported/error
        # case; compliance then classifies as error, which is the right
        # outcome — but if a legacy raw exists, use it.)
        data = {
            "config": {"raw": "legacy text"},
            "config_raw": "",
        }
        assert extract_snapshot_raw_config(data) == "legacy text"

    def test_state_only_snapshot_has_no_raw(self):
        # A state-only snapshot has no config payload; compliance classifies
        # as error. The extraction returns empty.
        data = {"state": {"show version": {}}}
        assert extract_snapshot_raw_config(data) == ""

    def test_unsupported_snapshot_has_no_raw(self):
        # An unsupported-platform snapshot has empty data; extraction returns
        # empty (compliance → error with "snapshot raw config is empty").
        assert extract_snapshot_raw_config({}) == ""
        assert extract_snapshot_raw_config(None) == ""

    def test_legacy_config_not_a_dict_returns_empty(self):
        # Defensive: if data["config"] is somehow not a dict (corrupt JSONB),
        # don't crash — return empty (compliance → error). This guards the
        # isinstance check in the fallback.
        data = {"config": "not a dict"}
        assert extract_snapshot_raw_config(data) == ""

    def test_legacy_config_raw_not_a_string_returns_empty(self):
        # Defensive: if data["config"]["raw"] is not a string (corrupt JSONB),
        # the `or ""` guard returns empty rather than returning a non-string
        # that the compliance engine's line-split would choke on.
        data = {"config": {"raw": None}}
        assert extract_snapshot_raw_config(data) == ""

    def test_legacy_config_raw_empty_string_returns_empty(self):
        # An empty-string legacy raw is treated as missing — extraction
        # returns empty (compliance → error). Pins the `or ""` truthiness
        # guard so a refactor that drops it is caught.
        data = {"config": {"raw": ""}}
        assert extract_snapshot_raw_config(data) == ""

    def test_legacy_config_raw_present_but_config_raw_missing_key(self):
        # The config key exists, raw is present, and config_raw key is absent
        # entirely (not just empty). The fallback path must still fire.
        data = {"config": {"raw": "hostname rtr01\nend\n"}}
        assert extract_snapshot_raw_config(data) == "hostname rtr01\nend\n"
