"""Tests for the device-page Parse sub-tab (ATW-241 child 2, ATW-250).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- :class:`netbox_pyats.forms.DeviceParseForm` validation: at least one of
  ``commands`` / ``manual_command`` is required; choices are populated from
  the catalog row; unsupported-os path yields empty choices.
- :class:`netbox_pyats.views.DeviceParseView`: GET renders the form; POST
  with a selected command enqueues a parse job and redirects to the device
  page; POST with no input re-renders with an error; unsupported-os GET
  renders the banner.
- :class:`netbox_pyats.views.DeviceRefreshCatalogView`: POST enqueues the
  refresh job and redirects back to the parse page.

``enqueue_parse`` and ``enqueue_refresh_parser_catalog`` are monkeypatched
so the view tests do not need a live RQ worker (same pattern as the existing
``test_pyatsjob.py`` mock-patch approach).
"""

from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats import forms
from netbox_pyats.models import PyatsParserCatalog

# --------------------------------------------------------------------------- #
# DeviceParseForm
# --------------------------------------------------------------------------- #


class DeviceParseFormTest(TestCase):
    """Pure-form validation for :class:`forms.DeviceParseForm`."""

    def test_clean_requires_at_least_one_input(self):
        form = forms.DeviceParseForm(
            {"commands": [], "manual_command": ""},
            command_choices=[("show version", "show version")],
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Select at least one parser command or type a manual command.", form.non_field_errors())

    def test_clean_accepts_only_commands(self):
        form = forms.DeviceParseForm(
            {"commands": ["show version"], "manual_command": ""},
            command_choices=[("show version", "show version")],
        )
        self.assertTrue(form.is_valid())

    def test_clean_accepts_only_manual_command(self):
        form = forms.DeviceParseForm({"commands": [], "manual_command": "show platform"})
        self.assertTrue(form.is_valid())

    def test_clean_accepts_both(self):
        form = forms.DeviceParseForm(
            {"commands": ["show version"], "manual_command": "show platform"},
            command_choices=[("show version", "show version")],
        )
        self.assertTrue(form.is_valid())

    def test_empty_command_choices_is_valid_with_manual_command(self):
        # No catalog row -> no choices; the manual text box still works.
        form = forms.DeviceParseForm(
            {"commands": [], "manual_command": "show version"},
            command_choices=[],
        )
        self.assertTrue(form.is_valid())


# --------------------------------------------------------------------------- #
# DeviceParseView
# --------------------------------------------------------------------------- #


class DeviceParseViewTest(TestCase):
    """View tests for :class:`views.DeviceParseView` (ATW-250)."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="DPV01", slug="dpv01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-DPV", slug="cisco-dpv")
        cls.platform_iosxe = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.unknown_mfr = Manufacturer.objects.create(name="Mystery-DPV", slug="mystery-dpv")
        cls.platform_unknown = Platform.objects.create(
            name="Mystery OS", slug="mystery-os", manufacturer=cls.unknown_mfr
        )
        cls.dt = DeviceType.objects.create(model="C9300-DPV", slug="c9300-dpv", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-DPV", slug="router-dpv")
        cls.device = Device.objects.create(
            name="dpvrtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        cls.device_unknown = Device.objects.create(
            name="dpvmystery",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_unknown,
        )

    def test_get_renders_form_with_catalog_choices(self):
        PyatsParserCatalog.objects.create(
            pyats_os="iosxe",
            commands=["show version", "show interfaces"],
            genie_version="26.6",
            pyats_version="26.6",
        )
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "show version")
        self.assertContains(response, "show interfaces")
        self.assertContains(response, "iosxe")

    def test_get_with_no_catalog_row_renders_refresh_banner(self):
        # Supported os but no catalog row yet -> the "refresh to populate"
        # banner renders, and the manual text box still works.
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No parser catalog row exists yet")

    def test_get_with_unsupported_platform_renders_banner(self):
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device_unknown.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unsupported platform")

    def test_post_with_command_enqueues_parse_and_redirects(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        fake_core_job = mock.Mock()
        fake_core_job.pk = 4242
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse", return_value=fake_core_job) as mocked:
            response = self.client.post(url, {"commands": ["show version"], "manual_command": ""})
        self.assertEqual(response.status_code, 302)
        # The view redirects back to the device page.
        self.assertEqual(response["Location"], self.device.get_absolute_url())
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        self.assertEqual(args[0].pk, self.device.pk)
        self.assertEqual(kwargs["commands"], ["show version"])

    def test_post_with_manual_command_enqueues_parse(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        fake_core_job = mock.Mock()
        fake_core_job.pk = 9090
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse", return_value=fake_core_job) as mocked:
            response = self.client.post(url, {"commands": [], "manual_command": "show platform"})
        self.assertEqual(response.status_code, 302)
        _, kwargs = mocked.call_args
        self.assertEqual(kwargs["commands"], ["show platform"])

    def test_post_with_both_dedupes_overlapping_command(self):
        # A manual command that matches a checked box should not run twice.
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        fake_core_job = mock.Mock()
        fake_core_job.pk = 1
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse", return_value=fake_core_job) as mocked:
            response = self.client.post(
                url,
                {"commands": ["show version"], "manual_command": "show version"},
            )
        self.assertEqual(response.status_code, 302)
        _, kwargs = mocked.call_args
        self.assertEqual(kwargs["commands"], ["show version"])

    def test_post_with_no_input_rerenders_with_error(self):
        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=["show version"])
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        with mock.patch("netbox_pyats.views.jobs.enqueue_parse") as mocked:
            response = self.client.post(url, {"commands": [], "manual_command": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select at least one parser command or type a manual command.")
        mocked.assert_not_called()


# --------------------------------------------------------------------------- #
# DeviceRefreshCatalogView
# --------------------------------------------------------------------------- #


class DeviceRefreshCatalogViewTest(TestCase):
    """View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="DRC01", slug="drc01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-DRC", slug="cisco-drc")
        cls.platform = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.dt = DeviceType.objects.create(model="C9300-DRC", slug="c9300-drc", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-DRC", slug="router-drc")
        cls.device = Device.objects.create(
            name="drcrtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform,
        )

    def test_post_enqueues_refresh_and_redirects_to_parse_page(self):
        url = reverse(
            "plugins:netbox_pyats:device_refresh_parser_catalog",
            kwargs={"device_id": self.device.pk},
        )
        fake_core_job = mock.Mock()
        fake_core_job.pk = 7
        with mock.patch("netbox_pyats.views.jobs.enqueue_refresh_parser_catalog", return_value=fake_core_job) as mocked:
            response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk}),
        )
        mocked.assert_called_once()
