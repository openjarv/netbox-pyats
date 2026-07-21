"""Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15).

Pure-Python: exercises the compliance engine against plain config-text strings
(no NetBox, no RQ, no Genie). Covers the shipped end-to-end compliance path:

- Golden text matches snapshot raw text → ``compliant`` (no drift). This is
  the Phase 4 intent test that was missing in the original v1 (the
  dict-of-lists golden parser produced a shape not comparable to the Genie
  structured dict, so a matching golden always classified as ``drift``).
- Golden text differs from snapshot raw text → ``drift`` with a structured
  diff tree and non-zero added/removed counts.
- Empty golden → ``error`` with a "golden config is empty" warning.
- Empty snapshot raw config → ``error`` with a "snapshot raw config is empty"
  warning.
- ``ComplianceResult.size_bytes`` derives from the JSON-serialized ``diff``.
- ``has_drift`` is False for compliant and True for drift.
- The diff tree shape matches :func:`netbox_pyats.diff.diff_snapshots` so the
  Phase 3 ``inc/diff_tree.html`` partial renders it unchanged.
- Realistic Cisco IOS running-config golden vs. snapshot raw text (the
  scenario the worker actually runs).
"""

import json

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.choices import ComplianceResultChoices
from netbox_pyats.compliance import run_compliance

# A realistic Cisco IOS/XE running-config fragment, used for both the golden
# (expected) and the snapshot's raw text (actual) in the compliant case, then
# mutated for the drift case. This mirrors the shape of a real
# `show running-config` output the worker captures into `data["config_raw"]`.
BASE_CONFIG = """!
version 16.12
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
        r = run_compliance(BASE_CONFIG, BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        # No drift: every line is unchanged.
        assert r.summary["added"] == 0
        assert r.summary["removed"] == 0
        assert r.summary["changed"] == 0
        assert r.summary["unchanged"] > 0
        assert r.has_drift is False
        # Compliant runs carry an all-unchanged diff tree so the viewer can
        # render "nothing changed" explicitly.
        assert r.diff["status"] == "unchanged"

    def test_compliant_with_reordered_lines_still_compliant(self):
        # v1 is a set diff (order-independent): a re-ordered config with the
        # same lines classifies as compliant. Documented v1 limitation —
        # order-sensitive compliance is v2.
        golden_lines = BASE_CONFIG.splitlines()
        snapshot_lines = list(reversed(golden_lines))
        snapshot_text = "\n".join(snapshot_lines)
        r = run_compliance(BASE_CONFIG, snapshot_text)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_compliant_ignores_bang_delimiters_and_blank_lines(self):
        # Extra "!" delimiter lines and blank lines are noise; two configs
        # that differ only in delimiter/blank-line placement classify as
        # compliant.
        golden = "hostname rtr01\n!\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr01\n\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n!\n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_compliant_trailing_whitespace_normalized(self):
        # Trailing whitespace is stripped before comparison so "hostname rtr01   "
        # and "hostname rtr01" compare equal.
        golden = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr01   \ninterface Gig0\n ip address 10.0.0.1 255.255.255.0   \n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False


class TestDrift:
    def test_added_line_in_snapshot_yields_drift(self):
        # Snapshot has an extra interface line the golden does not.
        golden = BASE_CONFIG
        snapshot = BASE_CONFIG + "interface Loopback0\n ip address 192.168.0.1 255.255.255.255\n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.summary["added"] >= 2  # the two new lines
        assert r.summary["removed"] == 0
        assert r.has_drift is True
        assert r.diff["status"] == "changed"

    def test_removed_line_in_snapshot_yields_drift(self):
        # Snapshot is missing an interface the golden requires.
        golden = BASE_CONFIG
        snapshot = BASE_CONFIG.replace(
            "interface GigabitEthernet0/1\n ip address 10.0.0.2 255.255.255.0\n shutdown\n",
            "",
        )
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.summary["removed"] >= 3  # the three removed lines
        assert r.has_drift is True

    def test_changed_line_yields_drift(self):
        # A "changed" line is a remove + an add in the set diff (the line text
        # differs), so both counts are non-zero.
        golden = "hostname rtr01\n"
        snapshot = "hostname rtr02\n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.summary["added"] == 1
        assert r.summary["removed"] == 1
        assert r.has_drift is True
        # The diff tree records both leaves.
        children = r.diff["children"]
        assert children["hostname rtr01"]["status"] == "removed"
        assert children["hostname rtr02"]["status"] == "added"

    def test_ip_address_drift_realistic(self):
        # The common real-world drift: an interface's IP address changed.
        golden = BASE_CONFIG
        snapshot = BASE_CONFIG.replace(" ip address 10.0.0.1 255.255.255.0", " ip address 10.0.0.99 255.255.255.0")
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] == 1
        assert r.summary["removed"] == 1


class TestErrorInputs:
    def test_empty_golden_yields_error(self):
        r = run_compliance("", BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert r.diff == {}
        assert r.summary == {}
        assert any("golden config is empty" in w for w in r.warnings)

    def test_none_golden_yields_error(self):
        r = run_compliance(None, BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config is empty" in w for w in r.warnings)

    def test_golden_with_only_bangs_and_blanks_yields_error(self):
        # A golden with only noise lines (no comparable lines after
        # normalization) is treated as empty.
        r = run_compliance("!\n\n!\n", BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config is empty" in w for w in r.warnings)

    def test_empty_snapshot_raw_yields_error(self):
        r = run_compliance(BASE_CONFIG, "")
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("snapshot raw config is empty" in w for w in r.warnings)

    def test_none_snapshot_raw_yields_error(self):
        r = run_compliance(BASE_CONFIG, None)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("snapshot raw config is empty" in w for w in r.warnings)

    def test_snapshot_with_only_bangs_yields_error(self):
        r = run_compliance(BASE_CONFIG, "!\n!\n")
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("snapshot raw config is empty" in w for w in r.warnings)

    def test_both_empty_yields_error(self):
        # Both empty: golden-empty check fires first (deterministic order).
        r = run_compliance("", "")
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert any("golden config is empty" in w for w in r.warnings)


class TestComplianceResultSizeBytes:
    def test_error_result_is_zero_bytes(self):
        r = run_compliance("", BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert r.size_bytes == 0

    def test_compliant_result_has_nonzero_bytes(self):
        # Compliant runs carry an all-unchanged diff tree, so size_bytes > 0.
        r = run_compliance(BASE_CONFIG, BASE_CONFIG)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.size_bytes > 0

    def test_size_bytes_matches_json_length(self):
        golden = "hostname rtr01\n"
        snapshot = "hostname rtr02\n"
        r = run_compliance(golden, snapshot)
        expected = len(json.dumps(r.diff, default=str).encode("utf-8"))
        assert r.size_bytes == expected
        assert r.size_bytes > 0


class TestJsonSerializable:
    def test_compliance_result_round_trips_through_json(self):
        golden = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr02\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        blob = json.dumps(r.diff, default=str)
        reloaded = json.loads(blob)
        assert reloaded["status"] == "changed"
        json.dumps(r.summary)


class TestEndToEndCompliancePath:
    """Exercise the exact path the RQ job runs: golden text → snapshot raw text.

    This is the test the original v1 was missing (CI green masked the bug
    because no test fed ``_golden_text_to_config_dict(...)`` output into
    ``run_compliance`` against a realistic Genie-shaped snapshot). v1 now
    compares raw texts directly, so this test feeds the same raw text shapes
    the job extracts from ``PyatsGoldenConfig.config_text`` and
    ``PyatsSnapshot.data["config_raw"]``.
    """

    def test_realistic_compliant_run(self):
        # The golden matches a snapshot captured from the same device (the
        # happy path — a device in compliance with its golden).
        golden_text = BASE_CONFIG
        snapshot_raw = BASE_CONFIG
        r = run_compliance(golden_text, snapshot_raw, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False
        assert r.diff["name"] == "rtr01"
        # Every line is in the unchanged set.
        assert r.summary["added"] == 0
        assert r.summary["removed"] == 0

    def test_realistic_drift_run_ip_changed(self):
        # The golden expects 10.0.0.1 but the device drifted to 10.0.0.99.
        golden_text = BASE_CONFIG
        snapshot_raw = BASE_CONFIG.replace(
            " ip address 10.0.0.1 255.255.255.0",
            " ip address 10.0.0.99 255.255.255.0",
        )
        r = run_compliance(golden_text, snapshot_raw, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        # One line removed (the golden's IP), one line added (the snapshot's IP).
        assert r.summary["added"] == 1
        assert r.summary["removed"] == 1
        assert r.diff["name"] == "rtr01"
        # The diff tree carries both leaves with the right status.
        children = r.diff["children"]
        assert children[" ip address 10.0.0.1 255.255.255.0"]["status"] == "removed"
        assert children[" ip address 10.0.0.99 255.255.255.0"]["status"] == "added"

    def test_realistic_drift_run_interface_added_on_device(self):
        # The device added an extra interface not in the golden.
        golden_text = BASE_CONFIG
        snapshot_raw = BASE_CONFIG + "interface Loopback0\n ip address 192.168.0.1 255.255.255.255\n!\n"
        r = run_compliance(golden_text, snapshot_raw, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] == 2  # interface + ip lines
        assert r.summary["removed"] == 0

    def test_realistic_drift_run_interface_missing_on_device(self):
        # The device is missing an interface the golden requires.
        golden_text = BASE_CONFIG
        snapshot_raw = BASE_CONFIG.replace(
            "interface GigabitEthernet0/1\n ip address 10.0.0.2 255.255.255.0\n shutdown\n",
            "",
        )
        r = run_compliance(golden_text, snapshot_raw, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["removed"] == 3  # the three removed lines
        assert r.summary["added"] == 0
