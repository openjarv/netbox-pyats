"""Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.jobs` (Phase 4).

Pure-Python: exercises the snapshot-raw-config-text extraction path that
:func:`netbox_pyats.jobs.run_compliance_job` uses — the ``data["config_raw"]``
field with a fallback to the legacy ``data["config"]["raw"]`` for snapshots
captured before ``config_raw`` was added.

The golden-text parser (``_golden_text_to_config_dict``) was removed in the
v1 rework (ATW-62 blocker 1): v1 compliance is now a line-oriented text diff
between the golden config text and the snapshot's raw running-config text
(see :mod:`netbox_pyats.compliance`). The compliance job's job is to extract
those two strings; this test covers the extraction.
"""

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files


def _extract_snapshot_raw(snapshot_data: dict) -> str:
    """Replicate the extraction logic in :func:`run_compliance_job` for unit testing.

    Kept in sync with ``jobs.run_compliance_job`` — if the job's extraction
    changes, update this helper (or refactor the job to expose a tested helper).
    """
    snapshot_data = snapshot_data or {}
    snapshot_raw = snapshot_data.get("config_raw") or ""
    if not snapshot_raw:
        legacy_config = snapshot_data.get("config") or {}
        if isinstance(legacy_config, dict):
            snapshot_raw = legacy_config.get("raw") or ""
    return snapshot_raw


class TestSnapshotRawExtraction:
    def test_config_raw_present_is_used_directly(self):
        # The normal path: a config/full snapshot captured with the v1 rework
        # carries data["config_raw"].
        data = {
            "config": {"hostname": "rtr01"},
            "config_raw": "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n",
        }
        assert _extract_snapshot_raw(data) == ("hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n")

    def test_legacy_snapshot_falls_back_to_config_raw_key(self):
        # A snapshot captured before config_raw was added (migration 0006
        # onward populates it) and whose Genie parser had failed at capture
        # time has data["config"]["raw"] instead. The job falls back to it so
        # compliance can still run against legacy snapshots.
        data = {
            "config": {
                "raw": "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n",
                "_parser_error": "ParserNotFound",
            },
        }
        assert _extract_snapshot_raw(data) == ("hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n")

    def test_config_raw_takes_precedence_over_legacy_raw(self):
        # When both are present (shouldn't happen in practice, but the
        # extraction is deterministic), config_raw wins.
        data = {
            "config": {"raw": "legacy text"},
            "config_raw": "current text",
        }
        assert _extract_snapshot_raw(data) == "current text"

    def test_empty_config_raw_falls_back_to_legacy(self):
        # An empty string config_raw is treated as missing — fall back to the
        # legacy path. (Captures with config_raw="" are the unsupported/error
        # case; compliance then classifies as error, which is the right
        # outcome — but if a legacy raw exists, use it.)
        data = {
            "config": {"raw": "legacy text"},
            "config_raw": "",
        }
        assert _extract_snapshot_raw(data) == "legacy text"

    def test_state_only_snapshot_has_no_raw(self):
        # A state-only snapshot has no config payload; compliance classifies
        # as error. The extraction returns empty.
        data = {"state": {"show version": {}}}
        assert _extract_snapshot_raw(data) == ""

    def test_unsupported_snapshot_has_no_raw(self):
        # An unsupported-platform snapshot has empty data; extraction returns
        # empty (compliance → error with "snapshot raw config is empty").
        assert _extract_snapshot_raw({}) == ""
        assert _extract_snapshot_raw(None) == ""

    def test_legacy_config_not_a_dict_returns_empty(self):
        # Defensive: if data["config"] is somehow not a dict (corrupt JSONB),
        # don't crash — return empty (compliance → error).
        data = {"config": "not a dict"}
        assert _extract_snapshot_raw(data) == ""
