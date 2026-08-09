"""Tests for the dedicated Genie Parse page (ATW-729).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- :class:`netbox_pyats.views.GenieParseView`:
  - GET with no device: renders the device picker, no parse form, recent
    results table (empty when no parse snapshots exist).
  - GET with ``?device=<pk>``: renders the picker + parse form populated
    from the selected device's parser catalog row.
  - GET with an unsupported platform: renders the unsupported banner.
  - POST with a selected device + command: enqueues a parse job via
    ``jobs.enqueue_parse`` and redirects back to the page with
    ``?device=<pk>``.
  - POST with no device: redirects to the page with an error message.
  - POST with a device but no commands: re-renders with a form error.

``enqueue_parse`` is monkeypatched so the view tests do not need a live RQ
worker (same pattern as ``test_device_parse.py``).
"""

from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.models import PyatsParserCatalog, PyatsSnapshot


class GenieParseViewTest(TestCase):
    """View tests for :class:`views.GenieParseView` (ATW-729)."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshot",
        "netbox_pyats.view_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="GP01", slug="gp01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-GP", slug="cisco-gp")
        cls.platform_iosxe = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.unknown_mfr = Manufacturer.objects.create(name="Mystery-GP", slug="mystery-gp")
        cls.platform_unknown = Platform.objects.create(
            name="Mystery OS", slug="mystery-os", manufacturer=cls.unknown_mfr
        )
        cls.dt = DeviceType.objects.create(model="C9300-GP", slug="c9300-gp", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-GP", slug="router-gp")
        cls.device = Device.objects.create(
            name="gprtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        cls.device_unknown = Device.objects.create(
            name="gpmystery",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_unknown,
        )

    def test_get_no_device_renders_picker_and_recent_results(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Genie Parse")
        self.assertContains(response, "Select a device")
        # No device selected → the parse form is not rendered.
        self.assertNotContains(response, "Parser commands")
        # Recent results section renders even when empty.
        self.assertContains(response, "Recent Parse Results")

    def test_get_with_device_renders_parse_form_with_catalog(self):
        PyatsParserCatalog.objects.create(
            pyats_os="iosxe",
            commands=["show version", "show interfaces"],
            genie_version="26.6",
            pyats_version="26.6",
        )
        url = reverse("plugins:netbox_pyats:genie_parse")
        response = self.client.get(url, {"device": self.device.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "show version")
        self.assertContains(response, "show interfaces")
        self.assertContains(response, "iosxe")

    def test_get_with_unsupported_platform_renders_banner(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        response = self.client.get(url, {"device": self.device_unknown.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unsupported platform")

    def test_get_with_no_catalog_row_renders_refresh_banner(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        response = self.client.get(url, {"device": self.device.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No parser catalog row exists yet")

    def test_post_with_command_enqueues_parse_and_redirects(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:genie_parse")
        fake_core_job = mock.Mock()
        fake_core_job.pk = 4242
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse", return_value=fake_core_job) as mocked:
            response = self.client.post(
                url,
                {"device": str(self.device.pk), "commands": ["show version"], "manual_command": ""},
            )
        self.assertEqual(response.status_code, 302)
        # Redirects back to the same page with ?device=<pk>.
        self.assertIn(f"device={self.device.pk}", response["Location"])
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        self.assertEqual(args[0].pk, self.device.pk)
        self.assertEqual(kwargs["commands"], ["show version"])

    def test_post_with_manual_command_enqueues_parse(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:genie_parse")
        fake_core_job = mock.Mock()
        fake_core_job.pk = 9090
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse", return_value=fake_core_job) as mocked:
            response = self.client.post(
                url,
                {"device": str(self.device.pk), "commands": [], "manual_command": "show platform"},
            )
        self.assertEqual(response.status_code, 302)
        _, kwargs = mocked.call_args
        self.assertEqual(kwargs["commands"], ["show platform"])

    def test_post_with_no_device_redirects_with_error(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse") as mocked:
            response = self.client.post(url, {"commands": ["show version"], "manual_command": ""})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        mocked.assert_not_called()

    def test_post_with_device_but_no_commands_rerenders_with_error(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:genie_parse")
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse") as mocked:
            response = self.client.post(
                url,
                {"device": str(self.device.pk), "commands": [], "manual_command": ""},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select at least one parser command or type a manual command.")
        mocked.assert_not_called()

    def test_recent_results_show_parse_snapshots(self):
        # Create a parse snapshot so the recent results table has a row.
        PyatsSnapshot.objects.create(
            device=self.device,
            kind="parse",
            status="success",
            triggered_by="user",
            data={"state": {"show version": {"version": "1.0"}}},
        )
        url = reverse("plugins:netbox_pyats:genie_parse")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent Parse Results")
        # The snapshot's device name appears in the rendered table.
        self.assertContains(response, str(self.device))
