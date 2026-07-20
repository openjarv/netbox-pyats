"""View tests for the Phase 4 compliance views (ATW-15).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Exercises the list and detail pages for :class:`PyatsGoldenConfig`
and :class:`PyatsComplianceRun`, plus the device-page compliance POST endpoint.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import (
    ComplianceResultChoices,
    GoldenConfigSourceChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from netbox_pyats.models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot


class PyatsGoldenConfigViewTest(TestCase):
    user_permissions = (
        "netbox_pyats.view_pyatsgoldenconfig",
        "netbox_pyats.add_pyatsgoldenconfig",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="VWG01", slug="vwg01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-VG", slug="cisco-vg")
        cls.device_type = DeviceType.objects.create(model="C9300-VG", slug="c9300-vg", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-VG", slug="router-vg")
        cls.device = Device.objects.create(
            name="vwgoldrtr01", site=cls.site, device_type=cls.device_type, role=cls.role
        )

    def test_list_view(self):
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_with_data(self):
        golden = PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, golden.name)

    def test_detail_view(self):
        golden = PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig", kwargs={"pk": golden.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "baseline")
        # The config text body is rendered in the detail page.
        self.assertContains(response, "hostname rtr01")

    def test_add_view_creates_golden_config(self):
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig_add")
        response = self.client.post(
            url,
            {
                "name": "baseline",
                "device": self.device.pk,
                "config_text": "hostname rtr01\n",
                "source": GoldenConfigSourceChoices.SOURCE_MANUAL,
                "tags": [],
            },
        )
        # NetBox's ObjectEditView redirects on success (302).
        self.assertEqual(
            response.status_code,
            302,
            msg=f"form errors: {response.context['form'].errors if response.context else 'no context'}",
        )
        golden = PyatsGoldenConfig.objects.get(name="baseline")
        self.assertEqual(golden.config_text, "hostname rtr01\n")
        self.assertEqual(golden.source, GoldenConfigSourceChoices.SOURCE_MANUAL)


class PyatsComplianceRunViewTest(TestCase):
    user_permissions = (
        "netbox_pyats.view_pyatscompliancerun",
        "netbox_pyats.add_pyatscompliancerun",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="VWC01", slug="vwc01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-VC", slug="cisco-vc")
        cls.device_type = DeviceType.objects.create(model="C9300-VC", slug="c9300-vc", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-VC", slug="router-vc")
        cls.device = Device.objects.create(name="vwcmprtr01", site=cls.site, device_type=cls.device_type, role=cls.role)
        cls.golden = PyatsGoldenConfig.objects.create(
            device=cls.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        cls.snapshot = PyatsSnapshot.objects.create(
            device=cls.device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {"hostname": "rtr01"}},
        )

    def test_list_view(self):
        url = reverse("plugins:netbox_pyats:pyatscompliancerun_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_with_data(self):
        PyatsComplianceRun.objects.create(
            device=self.device,
            golden=self.golden,
            snapshot=self.snapshot,
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff={"name": "root", "type": "dict", "status": "unchanged", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            size_bytes=42,
        )
        url = reverse("plugins:netbox_pyats:pyatscompliancerun_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compliant")

    def test_detail_view(self):
        run = PyatsComplianceRun.objects.create(
            device=self.device,
            golden=self.golden,
            snapshot=self.snapshot,
            result=ComplianceResultChoices.RESULT_DRIFT,
            diff={"name": "root", "type": "dict", "status": "changed", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
        )
        url = reverse("plugins:netbox_pyats:pyatscompliancerun", kwargs={"pk": run.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Drift")
        # The detail page links back to the golden and the snapshot.
        self.assertContains(response, self.golden.name)

    def test_device_compliance_post_validates_device_membership(self):
        # POSTing a golden_id that belongs to a different device must be
        # rejected with an error message and a redirect (no job enqueued).
        other_site = Site.objects.create(name="VWC02", slug="vwc02")
        other_mfr = Manufacturer.objects.create(name="Cisco-VC2", slug="cisco-vc2")
        other_dt = DeviceType.objects.create(model="C9300-VC2", slug="c9300-vc2", manufacturer=other_mfr)
        other_role = DeviceRole.objects.create(name="Router-VC2", slug="router-vc2")
        other_device = Device.objects.create(name="vwcmprtr02", site=other_site, device_type=other_dt, role=other_role)
        other_golden = PyatsGoldenConfig.objects.create(
            device=other_device,
            name="other-baseline",
            config_text="hostname rtr02\n",
        )
        url = reverse(
            "plugins:netbox_pyats:device_compliance",
            kwargs={"device_id": self.device.pk},
        )
        response = self.client.post(
            url,
            {"golden_id": other_golden.pk, "snapshot_id": self.snapshot.pk},
        )
        self.assertEqual(response.status_code, 302)
        # No compliance run row should have been created.
        self.assertEqual(PyatsComplianceRun.objects.filter(device=self.device).count(), 0)
