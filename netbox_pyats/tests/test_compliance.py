"""Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15 / ADR-0004 Option 3).

Pure-Python: exercises the compliance engine against raw text strings (no
NetBox, no RQ, no Genie). The v1 compliance engine is a line-set diff over
raw ``show running-config`` text on both sides — see ADR-0004 Option 3 and
the ``compliance.py`` module docstring for the rationale and the documented
v1 limitation (order-independent comparison).

Covers:

- Golden text matches snapshot text → ``compliant`` (no drift), even when
  lines are re-ordered (order-independent — the v1 contract).
- Golden text differs from snapshot text → ``drift`` with a structured diff
  tree keyed by line, non-zero ``added``/``removed`` counts, and the same
  ``{name, type, status, children}`` shape as
  :func:`netbox_pyats.diff.diff_snapshots` so the Phase 3
  ``inc/diff_tree.html`` partial renders it unchanged.
- Empty golden text → ``error`` with a "golden config text is empty" warning.
- Empty snapshot text → ``error`` with a "snapshot config text is empty"
  warning.
- Normalization: blank lines and lone ``!`` delimiters are dropped; trailing
  whitespace is stripped; leading whitespace is preserved (indented sub-mode
  lines are semantically distinct).
- ``ComplianceResult.size_bytes`` derives from the JSON-serialized ``diff``.
- ``has_drift`` is False for compliant and True for drift.
- The e2e acceptance gate (``test_compliance_job_e2e``) feeds a golden text
  and a matching ``config_raw`` text and asserts ``compliant`` — this is the
  regression test for the ATW-64 shape-mismatch bug. No Genie required; runs
  in the CI unit lane.
"""

import json

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.choices import ComplianceResultChoices
from netbox_pyats.compliance import run_compliance

# A realistic IOS-XE running-config text. Used as both the golden and (with
# edits) the snapshot's ``config_raw`` in the tests below. Matches the shape
# that ``execute("show running-config")`` returns on a real device.
IOS_XE_CONFIG = """\
!
hostname rtr01
!
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.2 255.255.255.0
 shutdown
!
end
"""


class TestCompliant:
    def test_matching_golden_and_snapshot_yields_compliant(self):
        r = run_compliance(IOS_XE_CONFIG, IOS_XE_CONFIG, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False
        # No drift: all lines unchanged. ``changed`` is always 0 for a
        # line-set diff.
        assert r.summary["added"] == 0
        assert r.summary["removed"] == 0
        assert r.summary["changed"] == 0
        assert r.summary["unchanged"] > 0
        # Compliant runs still carry a diff tree (all-unchanged) so the viewer
        # can render "nothing changed" explicitly.
        assert r.diff["status"] == "unchanged"
        assert r.diff["name"] == "rtr01"

    def test_compliant_reordered_lines_still_compliant(self):
        """Order-independent comparison — the documented v1 contract.

        A re-ordered config classifies as ``compliant`` because the line-set
        diff only asks "does the device carry the golden lines?". This is
        correct for the common compliance question but misses order-sensitive
        drift (e.g. ACL entry order); ordered/structured compliance is v2
        (ADR-0004 "Documented v1 limitation").
        """
        golden_lines = IOS_XE_CONFIG.splitlines()
        # Reverse the non-empty, non-`!` lines to produce a re-ordered config
        # with the same line set.
        reordered = "\n".join(reversed(golden_lines)) + "\n"
        r = run_compliance(IOS_XE_CONFIG, reordered, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_compliant_normalizes_blank_lines_and_bang_delimiters(self):
        """Blank lines and lone ``!`` are dropped before diffing.

        A golden with extra blank lines / ``!`` delimiters vs. a snapshot
        without them (or vice versa) is still ``compliant`` — those tokens
        carry no config semantics.
        """
        golden = "hostname rtr01\n!\n!\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_compliant_strips_trailing_whitespace(self):
        """Trailing whitespace is stripped per line before diffing."""
        golden = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr01   \ninterface Gig0\t\n ip address 10.0.0.1 255.255.255.0  \n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False


class TestDrift:
    def test_changed_line_yields_drift(self):
        # One line differs (hostname) → the golden's "hostname rtr01" is
        # removed, the snapshot's "hostname rtr02" is added.
        snapshot = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        r = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] == 1
        assert r.summary["removed"] == 1
        assert r.summary["changed"] == 0
        # The diff tree records the added and removed lines keyed by line.
        children = r.diff["children"]
        added_lines = [k for k, v in children.items() if v["status"] == "added"]
        removed_lines = [k for k, v in children.items() if v["status"] == "removed"]
        assert "hostname rtr02" in added_lines
        assert "hostname rtr01" in removed_lines

    def test_added_line_in_snapshot_yields_drift(self):
        snapshot = IOS_XE_CONFIG + "snmp-server community public RO\n"
        r = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] == 1
        assert r.summary["removed"] == 0

    def test_removed_line_in_snapshot_yields_drift(self):
        # Remove the "no shutdown" line from the snapshot → it's present in
        # the golden but missing on the device → removed.
        snapshot = IOS_XE_CONFIG.replace(" no shutdown\n", "")
        r = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] == 0
        assert r.summary["removed"] == 1

    def test_drift_diff_tree_shape_matches_phase3(self):
        """The diff tree has the same shape as PyatsSnapshotDiff.diff.

        The Phase 3 ``inc/diff_tree.html`` partial renders this tree
        unchanged — root node with ``name``, ``type``, ``status``, ``children``,
        and leaf children keyed by line with ``type=leaf`` and a
        ``status`` of ``added``/``removed``/``unchanged``.
        """
        snapshot = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        r = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.diff["name"] == "rtr01"
        assert r.diff["type"] == "dict"
        assert r.diff["status"] == "changed"
        assert isinstance(r.diff["children"], dict)
        # Every child is a leaf node with the expected keys.
        for line, node in r.diff["children"].items():
            assert node["type"] == "leaf"
            assert node["status"] in ("added", "removed", "unchanged")


class TestErrorInputs:
    def test_empty_golden_yields_error(self):
        r = run_compliance("", IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert r.diff == {}
        assert r.summary == {}
        assert any("golden config text is empty" in w for w in r.warnings)

    def test_none_golden_yields_error(self):
        r = run_compliance(None, IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config text is empty" in w for w in r.warnings)

    def test_whitespace_only_golden_yields_error(self):
        r = run_compliance("   \n\n  \n", IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config text is empty" in w for w in r.warnings)

    def test_bang_only_golden_yields_error(self):
        # Lone ``!`` lines are dropped by normalization → empty golden.
        r = run_compliance("!\n!\n!\n", IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config text is empty" in w for w in r.warnings)

    def test_empty_snapshot_yields_error(self):
        r = run_compliance(IOS_XE_CONFIG, "")
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("snapshot config text is empty" in w for w in r.warnings)

    def test_none_snapshot_yields_error(self):
        r = run_compliance(IOS_XE_CONFIG, None)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("snapshot config text is empty" in w for w in r.warnings)

    def test_both_empty_yields_error(self):
        # Both empty: golden-empty check fires first (deterministic order).
        r = run_compliance("", "")
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config text is empty" in w for w in r.warnings)


class TestComplianceResultSizeBytes:
    def test_error_result_is_zero_bytes(self):
        r = run_compliance("", IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert r.size_bytes == 0

    def test_compliant_result_has_nonzero_bytes(self):
        # Compliant runs carry an all-unchanged diff tree, so size_bytes > 0.
        r = run_compliance(IOS_XE_CONFIG, IOS_XE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.size_bytes > 0

    def test_drift_result_has_nonzero_bytes(self):
        snapshot = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        r = run_compliance(IOS_XE_CONFIG, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.size_bytes > 0

    def test_size_bytes_matches_json_length(self):
        snapshot = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        r = run_compliance(IOS_XE_CONFIG, snapshot)
        expected = len(json.dumps(r.diff, default=str).encode("utf-8"))
        assert r.size_bytes == expected


class TestJsonSerializable:
    def test_compliance_result_round_trips_through_json(self):
        snapshot = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        r = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        blob = json.dumps(r.diff, default=str)
        reloaded = json.loads(blob)
        assert reloaded["status"] == "changed"
        assert reloaded["name"] == "rtr01"
        json.dumps(r.summary)


class TestComplianceJobE2E:
    """End-to-end compliance tests: golden text + snapshot raw text → classification.

    These are the acceptance-gate tests for ATW-64. The original bug was that
    the golden was parsed into a dict-of-lists shape that was never comparable
    to the Genie-structured snapshot config, so a matching golden always
    classified as ``drift``. The v1 fix (ADR-0004 Option 3: line-set raw-text
    diff on both sides) makes a matching golden classify as ``compliant``.

    No Genie required — these run in the CI unit lane. This is the regression
    gate that the old ``test_golden_parse.py`` e2e gate claimed to be but
    wasn't (it skipped in every environment because ``device.parse`` requires
    a connection, not just installation).
    """

    def test_compliance_job_e2e_matching_golden_yields_compliant(self):
        """The acceptance gate: matching golden → compliant, not drift.

        Feed the same raw config text as both the golden and the snapshot's
        ``config_raw``; assert ``compliant``. With the old line-oriented
        golden parser + Genie-structured snapshot this was always ``drift``
        because the shapes were incomparable.
        """
        result = run_compliance(IOS_XE_CONFIG, IOS_XE_CONFIG, name="rtr01")
        assert result.result == "compliant", (
            f"Expected compliant but got {result.result} with "
            f"summary={result.summary}. This is the ATW-64 shape-mismatch "
            f"regression — the v1 raw-text line-set diff must classify a "
            f"matching golden as compliant."
        )
        assert result.has_drift is False

    def test_compliance_job_e2e_drifted_snapshot_yields_drift(self):
        """One drifted line → drift with a non-empty diff tree."""
        drifted = IOS_XE_CONFIG.replace("hostname rtr01", "hostname rtr02")
        result = run_compliance(IOS_XE_CONFIG, drifted, name="rtr01")
        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["added"] > 0
        assert result.summary["removed"] > 0

    def test_compliance_job_e2e_added_line_yields_drift(self):
        """A line present only in the snapshot → drift (added)."""
        snapshot = IOS_XE_CONFIG + "snmp-server community public RO\n"
        result = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["added"] > 0

    def test_compliance_job_e2e_removed_line_yields_drift(self):
        """A line present only in the golden → drift (removed)."""
        snapshot = IOS_XE_CONFIG.replace(" no shutdown\n", "")
        result = run_compliance(IOS_XE_CONFIG, snapshot, name="rtr01")
        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["removed"] > 0
