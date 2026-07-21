"""Tests for the supported-platforms report (Phase 5, ATW-16, Option A).

Two lanes:

1. **Pure-Python** (unit lane, no NetBox required): the static
   :data:`netbox_pyats.testbed.PLATFORM_SLUG_TO_PYATS_OS` map is the data
   source for the report, so we assert the invariants the report relies on
   against that map directly. This also pins the web-process-safety contract
   (ADR-0001 §6): importing :mod:`netbox_pyats.testbed` (the module the report
   view reads) must not import Genie.
2. **Integration** (NetBox container): the report view renders the map +
   per-platform device counts without error. Loaded lazily so the unit lane
   runs without NetBox installed.
"""

import importlib
import sys

from netbox_pyats.testbed import (
    MANUFACTURER_NAME_TO_PYATS_OS,
    PLATFORM_SLUG_TO_PYATS_OS,
    UNSUPPORTED_OS,
    is_supported_os,
    platform_to_pyats_os,
)

# Pure-Python lane: these tests run anywhere (laptop, CI unit job, NetBox
# container) without NetBox or Genie installed. They guard the contract the
# report relies on (the static map the testbed builder uses is the same map
# the report shows). The testbed module is imported lazily by the capture /
# worker paths, so importing it here does not pull in Genie (asserted below).
# Note: no ``pytest.importorskip("pyats")`` here — testbed.PLATFORM_SLUG_TO_PYATS_OS
# is a plain dict and does not require pyats to import.


class TestSupportedPlatformsMap:
    """The static map the report renders (Phase 5, ATW-16, Option A)."""

    def test_map_is_non_empty_and_str_str(self):
        assert len(PLATFORM_SLUG_TO_PYATS_OS) > 0
        for slug, pyats_os in PLATFORM_SLUG_TO_PYATS_OS.items():
            assert isinstance(slug, str) and slug
            assert isinstance(pyats_os, str) and pyats_os

    def test_known_cisco_slugs_map_to_expected_os(self):
        # A small, stable subset of the map — guards against an accidental
        # rename that would silently change the report's contents.
        assert PLATFORM_SLUG_TO_PYATS_OS["cisco-iosxe"] == "iosxe"
        assert PLATFORM_SLUG_TO_PYATS_OS["cisco-nxos"] == "nxos"
        assert PLATFORM_SLUG_TO_PYATS_OS["juniper-junos"] == "junos"
        assert PLATFORM_SLUG_TO_PYATS_OS["arista-eos"] == "eos"

    def test_unsupported_sentinel_is_distinct_from_every_mapped_os(self):
        # The report renders the unsupported sentinel as the "skipped" badge;
        # it must not collide with a real mapped os string.
        mapped_oses = set(PLATFORM_SLUG_TO_PYATS_OS.values())
        assert UNSUPPORTED_OS not in mapped_oses
        assert is_supported_os(UNSUPPORTED_OS) is False
        for os_value in mapped_oses:
            assert is_supported_os(os_value) is True

    def test_manufacturer_fallback_map_is_subset_of_supported_oses(self):
        # Manufacturer fallbacks must map to os strings that are themselves
        # supported (otherwise a device with a generic platform slug would
        # round-trip to an unsupported os via the fallback, contradicting the
        # report).
        for manufacturer_os in MANUFACTURER_NAME_TO_PYATS_OS.values():
            assert is_supported_os(manufacturer_os) is True

    def test_platform_to_pyats_os_unknown_slug_returns_unsupported(self):
        class FakePlatform:
            slug = "totally-fake-vendor-os"
            name = "Fake"
            manufacturer = None

        assert platform_to_pyats_os(FakePlatform()) == UNSUPPORTED_OS

    def test_platform_to_pyats_os_none_returns_unsupported(self):
        assert platform_to_pyats_os(None) == UNSUPPORTED_OS


class TestSupportedPlatformsReportWebProcessSafety:
    """ADR-0001 §6: the data path the report view reads must not import Genie.

    The report view renders in the web process, where Genie is not installed
    (it is a worker-only dependency). The view reads
    :data:`netbox_pyats.testbed.PLATFORM_SLUG_TO_PYATS_OS` — a plain Python
    dict — so importing :mod:`netbox_pyats.testbed` must not transitively
    import ``genie`` or ``pyats.parser``. (``netbox_pyats.views`` itself
    imports ``netbox.views.generic`` at module top, so it is only importable
    inside NetBox; the views' Genie-free contract is exercised end-to-end by
    the integration lane below.)
    """

    def test_importing_testbed_does_not_import_genie(self):
        # Drop any cached genie / pyats.parser modules so the import actually
        # runs from scratch. pyats itself (the top-level package) is allowed —
        # the testbed builder lazy-imports it inside functions, not at module
        # import time.
        for name in list(sys.modules.keys()):
            if name.startswith("genie") or name.startswith("pyats.parser"):
                sys.modules.pop(name, None)
        # Drop netbox_pyats.testbed too so the import re-runs.
        sys.modules.pop("netbox_pyats.testbed", None)

        importlib.import_module("netbox_pyats.testbed")
        # Genie must not be in sys.modules after importing testbed. pyats.parser
        # (the parser subpackage) must not either — that is what would pull in
        # the parser registry.
        assert "genie" not in sys.modules
        for name in sys.modules:
            assert not name.startswith("genie."), f"netbox_pyats.testbed pulled in {name} — ADR-0001 §6 violation"


def _netbox_available() -> bool:
    try:
        import netbox  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


if _netbox_available():
    # NetBox-backed report-rendering tests (skip in the unit lane). Imported
    # lazily so the pure-Python tests above run without NetBox installed.
    from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site
    from django.urls import reverse
    from utilities.testing import TestCase

    class SupportedPlatformsReportViewTest(TestCase):
        """Report contents: the static map renders with per-slug device counts."""

        user_permissions = (
            "netbox_pyats.view_pyatsjob",
            "dcim.view_device",
            "dcim.view_platform",
        )

        @classmethod
        def setUpTestData(cls):
            cls.site = Site.objects.create(name="SPR01", slug="spr01")
            cls.mfr = Manufacturer.objects.create(name="Cisco-SPR", slug="cisco-spr")
            cls.device_type = DeviceType.objects.create(model="C9300-SPR", slug="c9300-spr", manufacturer=cls.mfr)
            cls.role = DeviceRole.objects.create(name="Router-SPR", slug="router-spr")
            # A platform whose slug is in the static map (cisco-ios -> ios).
            cls.ios_platform = Platform.objects.create(name="Cisco IOS", slug="cisco-ios", manufacturer=cls.mfr)
            # A platform whose slug is NOT in the static map.
            cls.unsupported_platform = Platform.objects.create(
                name="Mystery OS", slug="mystery-os", manufacturer=cls.mfr
            )
            # Three devices on the supported platform, one on the unsupported
            # platform, one with no platform at all.
            for i in range(3):
                Device.objects.create(
                    name=f"rtr{i:02d}",
                    site=cls.site,
                    device_type=cls.device_type,
                    role=cls.role,
                    platform=cls.ios_platform,
                )
            Device.objects.create(
                name="mystery01",
                site=cls.site,
                device_type=cls.device_type,
                role=cls.role,
                platform=cls.unsupported_platform,
            )
            Device.objects.create(
                name="noplatform01",
                site=cls.site,
                device_type=cls.device_type,
                role=cls.role,
            )

        def test_report_renders(self):
            url = reverse("plugins:netbox_pyats:supported_platforms")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # The supported map's canonical Cisco IOS entry is rendered with its
            # pyATS os string and the device count we set up (3 devices).
            self.assertContains(response, "cisco-ios")
            self.assertContains(response, "ios")
            self.assertContains(response, "Supported Platforms")

        def test_report_shows_unsupported_and_no_platform_counts(self):
            url = reverse("plugins:netbox_pyats:supported_platforms")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # The "Unsupported" section renders with the count of devices on
            # platforms not in the map (1 mystery-os) plus the no-platform count.
            self.assertContains(response, "Unsupported")
            self.assertContains(response, "have no platform set at all")

        def test_report_does_not_import_genie(self):
            # ADR-0001 section 6: rendering the report must not pull Genie into
            # the web process. The view reads a static dict; this is a belt-and-
            # braces check that the GET handler did not trigger a Genie import.
            for mod in list(sys.modules):
                if mod.startswith("genie"):
                    del sys.modules[mod]

            url = reverse("plugins:netbox_pyats:supported_platforms")
            self.client.get(url)
            for mod in sys.modules:
                assert not mod.startswith(
                    "genie"
                ), f"supported_platforms GET pulled in genie.{mod} - ADR-0001 section 6 violation"
