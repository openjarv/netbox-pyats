"""Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).

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

ATW-434 adds the v2 ordered (sequence-aware) diff as the default mode, with
the v1 set diff retained as an explicit ``mode="set"`` opt-in. The ordered
diff flags re-ordered lines (ACL entry order, route-map sequence, interface
definition order) as drift — the documented v1 gap. Both modes are exercised
here.
"""

import json

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.choices import ComplianceModeChoices, ComplianceResultChoices
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

# A small ACL-bearing config used to exercise order-sensitive drift (ATW-434).
# Two ACL entries whose order is semantically significant: permit 10.0.0.1
# before deny 10.0.0.0/24 is *not* the same policy as the reverse.
ACL_GOLDEN = """!
hostname rtr01
!
ip access-list extended ACL_IN
 permit ip host 10.0.0.1 any
 deny ip 10.0.0.0 0.0.0.255 any
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
        # v2 ordered is the default mode.
        assert r.mode == ComplianceModeChoices.MODE_ORDERED
        assert r.diff["mode"] == ComplianceModeChoices.MODE_ORDERED

    def test_compliant_ignores_bang_delimiters_and_blank_lines(self):
        # Extra "!" delimiter lines and blank lines are noise; two configs
        # that differ only in delimiter/blank-line placement classify as
        # compliant in both modes (delimiters are dropped by normalization).
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


class TestOrderedModeReorderDrift:
    """ATW-434: the v2 ordered (default) diff flags re-ordered lines as drift.

    This is the order-sensitive drift the v1 set diff missed (ACL entry order,
    route-map sequence, interface definition order). Each test pins the
    default mode explicitly to guard against a future default flip.
    """

    def test_reordered_acl_entries_yield_drift_ordered(self):
        # The golden requires permit-then-deny; the snapshot has the reverse
        # order. The set diff would call this compliant (same lines); the
        # ordered diff must flag it as drift.
        snapshot = ACL_GOLDEN.replace(
            " permit ip host 10.0.0.1 any\n deny ip 10.0.0.0 0.0.0.255 any",
            " deny ip 10.0.0.0 0.0.0.255 any\n permit ip host 10.0.0.1 any",
        )
        r = run_compliance(ACL_GOLDEN, snapshot)
        assert r.mode == ComplianceModeChoices.MODE_ORDERED
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        # The two ACL lines show up as added+removed (moved), not unchanged.
        assert r.summary["added"] >= 1
        assert r.summary["removed"] >= 1

    def test_reversed_config_yields_drift_ordered(self):
        # A fully reversed config has the same lines in reverse order — set
        # diff calls it compliant, ordered diff calls it drift.
        golden_lines = [ln for ln in BASE_CONFIG.splitlines() if ln.strip() and ln.strip() != "!"]
        snapshot_lines = list(reversed(golden_lines))
        snapshot_text = "\n".join(snapshot_lines)
        r = run_compliance(BASE_CONFIG, snapshot_text)
        assert r.mode == ComplianceModeChoices.MODE_ORDERED
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True

    def test_reordered_interfaces_yield_drift_ordered(self):
        # Two interfaces swapped in definition order — set diff misses this,
        # ordered diff flags it.
        golden = (
            "hostname rtr01\n"
            "interface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
            "interface Gig1\n ip address 10.0.0.2 255.255.255.0\n"
        )
        snapshot = (
            "hostname rtr01\n"
            "interface Gig1\n ip address 10.0.0.2 255.255.255.0\n"
            "interface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        )
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True

    def test_ordered_mode_records_mode_on_result(self):
        r = run_compliance(BASE_CONFIG, BASE_CONFIG)
        assert r.mode == ComplianceModeChoices.MODE_ORDERED
        assert r.diff["mode"] == ComplianceModeChoices.MODE_ORDERED

    def test_ordered_mode_compliant_when_lines_in_same_order(self):
        # Same lines in the same order → compliant even in ordered mode.
        r = run_compliance(ACL_GOLDEN, ACL_GOLDEN)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False


class TestSetMode:
    """v1 set (order-independent) diff, retained as an explicit opt-in.

    A re-ordered config with the same lines classifies as compliant — the
    documented v1 limitation. Kept so operators whose configs legitimately
    vary in section order can opt out of order-sensitive drift.
    """

    def test_reordered_acl_entries_yield_compliant_set(self):
        snapshot = ACL_GOLDEN.replace(
            " permit ip host 10.0.0.1 any\n deny ip 10.0.0.0 0.0.0.255 any",
            " deny ip 10.0.0.0 0.0.0.255 any\n permit ip host 10.0.0.1 any",
        )
        r = run_compliance(ACL_GOLDEN, snapshot, mode=ComplianceModeChoices.MODE_SET)
        assert r.mode == ComplianceModeChoices.MODE_SET
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_reversed_config_still_compliant_set(self):
        golden_lines = BASE_CONFIG.splitlines()
        snapshot_lines = list(reversed(golden_lines))
        snapshot_text = "\n".join(snapshot_lines)
        r = run_compliance(BASE_CONFIG, snapshot_text, mode=ComplianceModeChoices.MODE_SET)
        assert r.mode == ComplianceModeChoices.MODE_SET
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert r.has_drift is False

    def test_set_mode_records_mode_on_result(self):
        r = run_compliance(BASE_CONFIG, BASE_CONFIG, mode=ComplianceModeChoices.MODE_SET)
        assert r.mode == ComplianceModeChoices.MODE_SET
        assert r.diff["mode"] == ComplianceModeChoices.MODE_SET


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
        # A "changed" line is a remove + an add (the line text differs), so
        # both counts are non-zero.
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

    def test_drift_in_both_modes(self):
        # Genuine content drift (not just re-ordering) is drift in both modes.
        golden = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
        snapshot = "hostname rtr01\ninterface Gig0\n ip address 10.0.0.99 255.255.255.0\n"
        for mode in (ComplianceModeChoices.MODE_ORDERED, ComplianceModeChoices.MODE_SET):
            r = run_compliance(golden, snapshot, mode=mode)
            assert r.result == ComplianceResultChoices.RESULT_DRIFT, mode
            assert r.has_drift is True, mode
            assert r.summary["added"] == 1, mode
            assert r.summary["removed"] == 1, mode


class TestDuplicateLines:
    """The ordered diff can emit the same line text at multiple positions
    (e.g. two `` ip address`` leaves from two interfaces). The children dict
    must disambiguate them so each leaf has a unique key — otherwise the
    viewer would collapse them. (ATW-434.)
    """

    def test_ordered_diff_disambiguates_duplicate_lines(self):
        # Two interfaces with the same subnet line text — the ordered diff
        # emits the line twice; the children dict keys must not collide.
        golden = (
            "interface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
            "interface Gig1\n ip address 10.0.0.1 255.255.255.0\n"
        )
        snapshot = (
            "interface Gig0\n ip address 10.0.0.1 255.255.255.0\n"
            "interface Gig1\n ip address 10.0.0.1 255.255.255.0\n"
        )
        r = run_compliance(golden, snapshot)
        assert r.result == ComplianceResultChoices.RESULT_COMPLIANT
        # The two duplicate " ip address ..." lines both surface in the tree.
        keys = list(r.diff["children"].keys())
        assert sum(1 for k in keys if k.startswith(" ip address 10.0.0.1")) == 2


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

    def test_error_records_mode(self):
        # The mode is echoed back on error results so the row records which
        # mode the operator requested even when inputs are bad.
        r = run_compliance("", BASE_CONFIG, mode=ComplianceModeChoices.MODE_SET)
        assert r.result == ComplianceResultChoices.RESULT_ERROR
        assert r.mode == ComplianceModeChoices.MODE_SET


class TestUnknownModeDegradesToOrdered:
    def test_unknown_mode_falls_back_to_ordered(self):
        # An unknown mode string degrades to ordered (the more informative
        # comparison) rather than raising — the job passes the user-selected
        # mode straight through and must not crash on a bad value.
        golden = "hostname rtr01\n"
        snapshot = "hostname rtr02\n"
        r = run_compliance(golden, snapshot, mode="nonsense")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        # The effective mode recorded is ordered (the fallback), not the
        # bogus value.
        assert r.mode == ComplianceModeChoices.MODE_ORDERED


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

    def test_realistic_ordered_drift_acl_reordered(self):
        # ATW-434: the real-world scenario the ordered diff unlocks — an ACL
        # whose entry order drifted between the golden and the snapshot. The
        # v1 set diff would call this compliant; the v2 ordered default flags
        # it as drift.
        golden_text = ACL_GOLDEN
        snapshot_raw = ACL_GOLDEN.replace(
            " permit ip host 10.0.0.1 any\n deny ip 10.0.0.0 0.0.0.255 any",
            " deny ip 10.0.0.0 0.0.0.255 any\n permit ip host 10.0.0.1 any",
        )
        r = run_compliance(golden_text, snapshot_raw, name="rtr01")
        assert r.result == ComplianceResultChoices.RESULT_DRIFT
        assert r.has_drift is True
        assert r.summary["added"] >= 1
        assert r.summary["removed"] >= 1
