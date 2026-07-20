"""Tests for :mod:`netbox_pyats.golden_parse` and the e2e compliance path.

These tests exercise the full compliance path that was broken in the reverted
Phase 4 v1 (ATW-64): golden config text → Genie parser → compliance engine →
classification. The golden text is parsed with the same Genie parser the
snapshot used, yielding a directly comparable dict — the original bug was that
the line-oriented parser produced a non-comparable shape.

Genie is required for these tests (``pyats[full]`` must be installed with a
working Tcl/abstract-package system). They skip cleanly when Genie's parser
discovery is not functional, matching the conftest dual-mode convention. The
tests use a realistic IOS-XE running-config text fixture and a matching
Genie-shaped snapshot config fixture so the compliance classification is
meaningful.

The e2e acceptance gate (``test_compliance_job_e2e``) is the regression test
for the original shape-mismatch bug: a clean golden against a matching
snapshot must classify as ``compliant``, never ``drift``.
"""

import json
import os

import pytest


# Skip if genie is not installed or the parser infrastructure (which requires
# Tcl and the full abstract package system) is not functional. We probe by
# checking whether device.parse is available — it's registered by the genie
# service wrapper infrastructure, not just by importing genie.
def _genie_parser_available():
    try:
        import genie  # noqa: F401
        from pyats.topology import Device

        d = Device(name="probe", os="iosxe")
        return hasattr(d, "parse")
    except Exception:  # noqa: BLE001 - any failure means genie is not functional
        return False


pytestmark = pytest.mark.skipif(
    not _genie_parser_available(),
    reason="Genie parser infrastructure not available (pyats[full] with Tcl required)",
)

from netbox_pyats.compliance import run_compliance
from netbox_pyats.golden_parse import GoldenParseError, parse_golden_config_text

# Fixtures directory: saved Genie parser outputs so the tests run without a
# live device. The golden text fixture is a real IOS-XE running-config; the
# snapshot fixture is the Genie abstract-config dict that ``device.parse(
# "show running-config")`` produces for that same config.
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# Fixtures directory: saved Genie parser outputs so the tests run without a
# live device. The golden text fixture is a real IOS-XE running-config; the
# snapshot fixture is the Genie abstract-config dict that ``device.parse(
# "show running-config")`` produces for that same config.
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# A realistic IOS-XE running-config text. This is the golden "expected" config.
# It's also the text that, when fed through the Genie parser, produces the
# snapshot fixture below — so golden and snapshot are semantically identical.
IOS_XE_GOLDEN_CONFIG = """\
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

# The Genie abstract-config dict that ``device.parse("show running-config")``
# produces for IOS_XE_GOLDEN_CONFIG above. This is a realistic Genie-shaped
# snapshot config payload (what ``snapshot.data["config"]`` would carry).
# Kept as a Python dict literal so the test is self-contained and inspectable.
IOS_XE_SNAPSHOT_CONFIG = {
    "hostname": "rtr01",
    "interfaces": {
        "GigabitEthernet0/0": {
            "ip": "10.0.0.1/24",
            "shutdown": False,
        },
        "GigabitEthernet0/1": {
            "ip": "10.0.0.2/24",
            "shutdown": True,
        },
    },
}


class TestParseGoldenConfigText:
    """Unit tests for the golden config text parser."""

    def test_parse_returns_dict(self):
        parsed = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        assert isinstance(parsed, dict)

    def test_parse_empty_text_raises(self):
        with pytest.raises(GoldenParseError, match="empty"):
            parse_golden_config_text("", os="iosxe")

    def test_parse_none_text_raises(self):
        with pytest.raises(GoldenParseError, match="empty"):
            parse_golden_config_text(None, os="iosxe")

    def test_parse_whitespace_only_raises(self):
        with pytest.raises(GoldenParseError, match="empty"):
            parse_golden_config_text("   \n\n  ", os="iosxe")

    def test_parse_empty_os_raises(self):
        with pytest.raises(GoldenParseError, match="os is empty"):
            parse_golden_config_text("hostname rtr01", os="")

    def test_parse_unsupported_os_raises_or_errors(self):
        # An os with no Genie parser for "show running-config" will raise a
        # GoldenParseError (the parser harness surfaces the failure). We
        # don't assert the exact Genie error text — just that it's surfaced
        # as a GoldenParseError, not a raw Genie exception.
        with pytest.raises(GoldenParseError):
            parse_golden_config_text("hostname rtr01", os="bogus_os")


class TestComplianceE2E:
    """End-to-end compliance tests: golden text → parse → compliance engine.

    These are the acceptance-gate tests for ATW-64. The original bug was that
    the line-oriented golden parser produced a dict-of-lists shape that was
    never comparable to the Genie-structured snapshot config, so a matching
    golden always classified as ``drift``. The fix (Option 1: Genie parser
    harness on the worker) makes both sides the same shape, so a matching
    golden classifies as ``compliant``.
    """

    def test_compliance_job_e2e_matching_golden_yields_compliant(self):
        """The acceptance gate: matching golden → compliant, not drift.

        This is the regression test for the original shape-mismatch bug.
        Parse the golden config text through the Genie harness, feed it and a
        matching Genie-shaped snapshot config into run_compliance, and assert
        ``compliant``. With the old line-oriented parser this was always
        ``drift`` because the shapes were incomparable.
        """
        golden_config = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        snapshot_config = IOS_XE_SNAPSHOT_CONFIG

        result = run_compliance(golden_config, snapshot_config, name="rtr01")

        # The golden and snapshot describe the same device state, so the
        # compliance result must be compliant. The original bug made this
        # always drift.
        assert result.result == "compliant", (
            f"Expected compliant but got {result.result} with "
            f"summary={result.summary}. This is the ATW-64 shape-mismatch "
            f"regression — the golden parse shape must match the snapshot "
            f"config shape."
        )
        assert result.has_drift is False

    def test_compliance_job_e2e_drifted_snapshot_yields_drift(self):
        """One drifted field → drift with a structured diff tree.

        Parse the golden, change one leaf in the snapshot config, and assert
        ``drift`` with a non-empty diff tree showing what changed.
        """
        golden_config = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        # Drift: change the hostname in the snapshot.
        drifted_snapshot = json.loads(json.dumps(IOS_XE_SNAPSHOT_CONFIG))
        drifted_snapshot["hostname"] = "rtr02"

        result = run_compliance(golden_config, drifted_snapshot, name="rtr01")

        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["changed"] > 0

    def test_compliance_job_e2e_added_interface_yields_drift(self):
        """An interface present only in the snapshot → drift (added)."""
        golden_config = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        snapshot_with_extra = json.loads(json.dumps(IOS_XE_SNAPSHOT_CONFIG))
        snapshot_with_extra["interfaces"]["GigabitEthernet0/2"] = {
            "ip": "10.0.0.3/24",
            "shutdown": False,
        }

        result = run_compliance(golden_config, snapshot_with_extra, name="rtr01")

        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["added"] > 0

    def test_compliance_job_e2e_removed_interface_yields_drift(self):
        """An interface present only in the golden → drift (removed)."""
        golden_config = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        snapshot_missing = json.loads(json.dumps(IOS_XE_SNAPSHOT_CONFIG))
        del snapshot_missing["interfaces"]["GigabitEthernet0/1"]

        result = run_compliance(golden_config, snapshot_missing, name="rtr01")

        assert result.result == "drift"
        assert result.has_drift is True
        assert result.summary["removed"] > 0

    def test_compliance_job_e2e_diff_tree_shape_matches_phase3(self):
        """The diff tree has the same shape as PyatsSnapshotDiff.diff.

        The Phase 3 ``inc/diff_tree.html`` partial renders this tree
        unchanged — root node with ``name``, ``type``, ``status``, ``children``.
        """
        golden_config = parse_golden_config_text(IOS_XE_GOLDEN_CONFIG, os="iosxe")
        snapshot_config = IOS_XE_SNAPSHOT_CONFIG

        result = run_compliance(golden_config, snapshot_config, name="rtr01")

        assert result.result == "compliant"
        # The compliant diff tree is all-unchanged but still has the
        # Phase 3 shape.
        assert "name" in result.diff
        assert "type" in result.diff
        assert "status" in result.diff
        assert "children" in result.diff
