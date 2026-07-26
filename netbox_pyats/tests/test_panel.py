"""Tests for the device-page panel platform-support decision (ATW-184).

Pure-Python: exercises :func:`netbox_pyats.panel_support.resolve_panel_platform_support`
against fake device/snapshot objects. No NetBox or Genie installation required;
this guards the panel-level consistency guard that suppresses the green
supported badge when the most recent snapshot contradicts the static map.
"""

from netbox_pyats.choices import SnapshotStatusChoices
from netbox_pyats.panel_support import resolve_panel_platform_support
from netbox_pyats.testbed import UNSUPPORTED_OS


class FakePlatform:
    def __init__(self, slug):
        self.slug = slug
        self.name = slug.replace("-", " ").title() if slug else ""


class FakeDevice:
    def __init__(self, platform=None):
        self.platform = platform


class FakeSnapshot:
    def __init__(self, status):
        self.status = status


class TestResolvePanelPlatformSupport:
    def test_supported_slug_no_snapshots_claims_support(self):
        device = FakeDevice(platform=FakePlatform("cisco-iosxe"))
        supported, os_value = resolve_panel_platform_support(device, None)
        assert supported is True
        assert os_value == "iosxe"

    def test_unknown_slug_no_snapshots_is_unsupported(self):
        device = FakeDevice(platform=FakePlatform("mystery-os"))
        supported, os_value = resolve_panel_platform_support(device, None)
        assert supported is False
        assert os_value == UNSUPPORTED_OS

    def test_cisco_manufacturer_unknown_slug_is_unsupported(self):
        # ATW-184 regression: the manufacturer fallback was removed, so a
        # Cisco-manufacturer device with an unknown slug must surface as
        # unsupported even though the vendor is known.
        device = FakeDevice(platform=FakePlatform("mystery-os"))
        supported, os_value = resolve_panel_platform_support(device, None)
        assert supported is False
        assert os_value == UNSUPPORTED_OS

    def test_supported_slug_but_latest_snapshot_unsupported_is_unsupported(self):
        # ATW-184 consistency guard: the static map claims iosxe, but the most
        # recent capture reported 'unsupported'. The panel must reflect
        # observed reality, not the optimistic map.
        device = FakeDevice(platform=FakePlatform("cisco-iosxe"))
        snap = FakeSnapshot(status=SnapshotStatusChoices.STATUS_UNSUPPORTED)
        supported, os_value = resolve_panel_platform_support(device, snap)
        assert supported is False
        assert os_value == UNSUPPORTED_OS

    def test_supported_slug_and_latest_snapshot_success_claims_support(self):
        device = FakeDevice(platform=FakePlatform("cisco-iosxe"))
        snap = FakeSnapshot(status=SnapshotStatusChoices.STATUS_SUCCESS)
        supported, os_value = resolve_panel_platform_support(device, snap)
        assert supported is True
        assert os_value == "iosxe"

    def test_unknown_slug_and_latest_snapshot_unsupported_is_unsupported(self):
        # Both signals agree: the map says unsupported and the snapshot agrees.
        device = FakeDevice(platform=FakePlatform("mystery-os"))
        snap = FakeSnapshot(status=SnapshotStatusChoices.STATUS_UNSUPPORTED)
        supported, os_value = resolve_panel_platform_support(device, snap)
        assert supported is False
        assert os_value == UNSUPPORTED_OS

    def test_no_platform_is_unsupported_regardless_of_snapshot(self):
        device = FakeDevice(platform=None)
        snap = FakeSnapshot(status=SnapshotStatusChoices.STATUS_SUCCESS)
        supported, os_value = resolve_panel_platform_support(device, snap)
        assert supported is False
        assert os_value == UNSUPPORTED_OS

    def test_supported_slug_with_latest_snapshot_error_does_not_override(self):
        # An errored capture is not the same as an unsupported platform; the
        # static map still applies. Only an explicit 'unsupported' snapshot
        # overrides the map (the panel-level guard's defined scope).
        device = FakeDevice(platform=FakePlatform("cisco-iosxe"))
        snap = FakeSnapshot(status=SnapshotStatusChoices.STATUS_ERROR)
        supported, os_value = resolve_panel_platform_support(device, snap)
        assert supported is True
        assert os_value == "iosxe"
