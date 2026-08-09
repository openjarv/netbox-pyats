"""Tests for the dedicated Genie Learn page (ATW-730).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- :class:`netbox_pyats.views.GenieLearnView`:
  - GET with no device: renders the parser catalog, device picker, and
    recent learn results table (empty when no learn snapshots exist).
  - GET with ``?device=<pk>``: renders the picker with the device selected
    and the platform support badge.
  - GET with an unsupported platform: renders the unsupported banner.
  - POST with a selected device: enqueues a learn job via
    ``jobs.enqueue_learn`` and redirects back to the page with
    ``?device=<pk>``.
  - POST with no device: redirects to the page with an error message.
  - Recent learn results show ``kind='learn'`` snapshots.

``enqueue_learn`` is monkeypatched so the view tests do not need a live RQ
worker (same pattern as ``test_genie_parse.py``).
"""

from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.models import PyatsParserCatalog, PyatsSnapshot


class GenieLearnViewTest(TestCase):
    """View tests for :class:`views.GenieLearnView` (ATW-730)."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshot",
        "netbox_pyats.view_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="GL01", slug="gl01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-GL", slug="cisco-gl")
        cls.platform_iosxe = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.unknown_mfr = Manufacturer.objects.create(name="Mystery-GL", slug="mystery-gl")
        cls.platform_unknown = Platform.objects.create(
            name="Mystery OS", slug="mystery-os", manufacturer=cls.unknown_mfr
        )
        cls.dt = DeviceType.objects.create(model="C9300-GL", slug="c9300-gl", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-GL", slug="router-gl")
        cls.device = Device.objects.create(
            name="glrtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        cls.device_unknown = Device.objects.create(
            name="glmystery",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_unknown,
        )

    def test_get_no_device_renders_catalog_picker_and_recent_results(self):
        PyatsParserCatalog.objects.create(
            pyats_os="iosxe",
            commands=["show version", "show interfaces"],
            genie_version="26.6",
            pyats_version="26.6",
        )
        url = reverse("plugins:netbox_pyats:genie_learn")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Genie Learn")
        self.assertContains(response, "Select a device")
        # Parser catalog renders (summary table: os + command count).
        self.assertContains(response, "Parser Catalog")
        self.assertContains(response, "iosxe")
        self.assertContains(response, "Parseable commands")
        # The catalog row shows the command count (2), not the command names.
        self.assertContains(response, ">2<")
        # Recent results section renders even when empty.
        self.assertContains(response, "Recent Learn Results")
        # No device selected → the Run Learn submit button is not rendered.
        # (The phrase "Run Learn" appears in the intro copy, so assert on the
        # button's unique mdi-school icon instead.)
        self.assertNotContains(response, "mdi-school")

    def test_get_with_device_renders_run_learn_form(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        response = self.client.get(url, {"device": self.device.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Run Learn")
        # The Run Learn submit button (mdi-school icon) renders with a device.
        self.assertContains(response, "mdi-school")
        self.assertContains(response, "iosxe")

    def test_get_with_unsupported_platform_renders_banner(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        response = self.client.get(url, {"device": self.device_unknown.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unsupported platform")

    def test_post_with_device_enqueues_learn_and_redirects(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        fake_core_job = mock.Mock()
        fake_core_job.pk = 5151
        with mock.patch("netbox_pyats.views.jobs.enqueue_learn", return_value=fake_core_job) as mocked:
            response = self.client.post(url, {"device": str(self.device.pk)})
        self.assertEqual(response.status_code, 302)
        # Redirects back to the same page with ?device=<pk>.
        self.assertIn(f"device={self.device.pk}", response["Location"])
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        self.assertEqual(args[0].pk, self.device.pk)

    def test_post_with_no_device_redirects_with_error(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        with mock.patch("netbox_pyats.views.jobs.enqueue_learn") as mocked:
            response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        mocked.assert_not_called()

    def test_recent_results_show_learn_snapshots(self):
        # Create a learn snapshot so the recent results table has a row.
        PyatsSnapshot.objects.create(
            device=self.device,
            kind="learn",
            status="success",
            triggered_by="user",
            data={"learn": {"interface": {"interfaces": {}}}},
        )
        url = reverse("plugins:netbox_pyats:genie_learn")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent Learn Results")
        # The snapshot's device name appears in the rendered table.
        self.assertContains(response, str(self.device))
