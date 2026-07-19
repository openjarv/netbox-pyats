"""REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable.

- :class:`PyatsGoldenConfig` is fully editable via the API in v1.
- :class:`PyatsComplianceRun` is read-only in v1 (produced by the
  ``run_compliance`` RQ job, not by direct API writes).
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from rest_framework import status
from utilities.testing.api import APITestCase

from netbox_pyats.choices import (
    ComplianceResultChoices,
    GoldenConfigSourceChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from netbox_pyats.models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot


class PyatsGoldenConfigAPITest(APITestCase):
    user_permissions = (
        "netbox_pyats.view_pyatsgoldenconfig",
        "netbox_pyats.add_pyatsgoldenconfig",
        "netbox_pyats.change_pyatsgoldenconfig",
        "netbox_pyats.delete_pyatsgoldenconfig",
        # NetBox 4.6 restricts the device ModelChoiceField queryset to
        # devices the user can view (same pattern as PyatsCredential).
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="APIG01", slug="apig01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-AG", slug="cisco-ag")
        cls.device_type = DeviceType.objects.create(model="C9300-AG", slug="c9300-ag", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-AG", slug="router-ag")
        cls.device = Device.objects.create(
            name="apigoldrtr01", site=cls.site, device_type=cls.device_type, role=cls.role
        )

    def test_list_golden_configs(self):
        url = "/api/plugins/pyats/pyats-golden-configs/"
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_golden_config(self):
        url = "/api/plugins/pyats/pyats-golden-configs/"
        data = {
            "name": "baseline",
            "device": self.device.pk,
            "config_text": "hostname rtr01\n",
            "source": GoldenConfigSourceChoices.SOURCE_MANUAL,
        }
        response = self.client.post(url, data, format="json", **self.header)
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"response: {response.data}",
        )
        golden = PyatsGoldenConfig.objects.get(name="baseline")
        self.assertEqual(golden.config_text, "hostname rtr01\n")
        self.assertEqual(golden.source, GoldenConfigSourceChoices.SOURCE_MANUAL)
        self.assertIsNone(golden.source_snapshot)

    def test_retrieve_golden_config_returns_config_text(self):
        golden = PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        url = f"/api/plugins/pyats/pyats-golden-configs/{golden.pk}/"
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config_text"], "hostname rtr01\n")

    def test_update_golden_config(self):
        golden = PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        url = f"/api/plugins/pyats/pyats-golden-configs/{golden.pk}/"
        response = self.client.patch(
            url,
            {"config_text": "hostname rtr02\n"},
            format="json",
            **self.header,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        golden.refresh_from_db()
        self.assertEqual(golden.config_text, "hostname rtr02\n")

    def test_delete_golden_config(self):
        golden = PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="",
        )
        pk = golden.pk
        url = f"/api/plugins/pyats/pyats-golden-configs/{pk}/"
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PyatsGoldenConfig.objects.filter(pk=pk).exists())


class PyatsComplianceRunAPITest(APITestCase):
    user_permissions = (
        "netbox_pyats.view_pyatscompliancerun",
        "netbox_pyats.add_pyatscompliancerun",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="APIC01", slug="apic01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-AC", slug="cisco-ac")
        cls.device_type = DeviceType.objects.create(model="C9300-AC", slug="c9300-ac", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-AC", slug="router-ac")
        cls.device = Device.objects.create(
            name="apicmprtr01", site=cls.site, device_type=cls.device_type, role=cls.role
        )
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

    def test_list_compliance_runs(self):
        url = "/api/plugins/pyats/pyats-compliance-runs/"
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_compliance_run_returns_diff_and_summary(self):
        run = PyatsComplianceRun.objects.create(
            device=self.device,
            golden=self.golden,
            snapshot=self.snapshot,
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff={"name": "root", "type": "dict", "status": "unchanged", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            size_bytes=42,
        )
        url = f"/api/plugins/pyats/pyats-compliance-runs/{run.pk}/"
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], ComplianceResultChoices.RESULT_COMPLIANT)
        self.assertEqual(response.data["summary"]["unchanged"], 1)
        self.assertEqual(response.data["size_bytes"], 42)

    def test_create_compliance_run_rejected_read_only(self):
        # Compliance runs are read-only in v1 (produced by the RQ job, not by
        # direct API writes). POST must be rejected.
        url = "/api/plugins/pyats/pyats-compliance-runs/"
        data = {
            "device": self.device.pk,
            "golden": self.golden.pk,
            "snapshot": self.snapshot.pk,
            "result": ComplianceResultChoices.RESULT_COMPLIANT,
            "diff": {},
            "summary": {},
        }
        response = self.client.post(url, data, format="json", **self.header)
        # http_method_names = ["get", "head", "options"] → 405 Method Not Allowed.
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
