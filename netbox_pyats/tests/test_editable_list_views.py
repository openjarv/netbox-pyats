"""Regression tests for the four editable plugin list views (ATW-817).

The list views for ``PyatsCredential``, ``PyatsGoldenConfig``,
``PyatsCaptureSchedule``, and ``PyatsParserCatalogRefreshSchedule`` must
render HTTP 200 and expose working edit/clone action links — the symmetric
gap to the ATW-183 append-only guard.

Before a hypothetical regression, any of these tables that reuses
``_APPEND_ONLY_ACTIONS`` (or any ActionsColumn that omits ``'edit'``) would
cause a ``NoReverseMatch`` at render time because the plugin registers
``*_edit`` and ``*_add`` URL names for all four models.

These tests render each list view inside a real request context (logged-in
admin user, at least one row in the queryset) so the actions column is
exercised in CI, not just the model helpers.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import (
    GoldenConfigSourceChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from netbox_pyats.models import (
    PyatsCaptureSchedule,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsParserCatalogRefreshSchedule,
    PyatsSnapshot,
)


class _EditableListViewsBase(TestCase):
    """Shared fixture: one device + rows for each editable model list view.

    Subclasses set ``user_permissions`` to cover the ``view`` and ``change``
    permissions for each model exercised plus ``dcim.view_device`` (FK link
    rendering in the table column).
    """

    user_permissions = (
        "netbox_pyats.view_pyatscredential",
        "netbox_pyats.change_pyatscredential",
        "netbox_pyats.view_pyatsgoldenconfig",
        "netbox_pyats.change_pyatsgoldenconfig",
        "netbox_pyats.view_pyatscaptureschedule",
        "netbox_pyats.change_pyatscaptureschedule",
        "netbox_pyats.view_pyatsparsercatalogrefreshschedule",
        "netbox_pyats.change_pyatsparsercatalogrefreshschedule",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="EDIT01", slug="edit01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-EDIT", slug="cisco-edit")
        cls.device_type = DeviceType.objects.create(model="C9300-EDIT", slug="c9300-edit", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-EDIT", slug="router-edit")
        cls.device = Device.objects.create(name="editrt01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _make_snapshot(self, *, data=None):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data=data or {"config": {"hostname": "rtr01"}},
            size_bytes=1,
        )
        snap.full_clean()
        snap.save()
        return snap


class PyatsCredentialListViewRenderTest(_EditableListViewsBase):
    """``/plugins/pyats/credentials/`` must render 200 (ATW-817 regression)."""

    def test_list_view_renders_200_with_row(self):
        cred = PyatsCredential(
            device=self.device,
            name="edit-test-cred",
            scope="enable",
            username="admin",
            protocol="ssh",
            ssh_port=22,
        )
        cred.full_clean()
        cred.save()
        url = reverse("plugins:netbox_pyats:pyatscredential_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"credential list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatscredential_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsGoldenConfigListViewRenderTest(_EditableListViewsBase):
    """``/plugins/pyats/golden-configs/`` must render 200 (ATW-817 regression)."""

    def test_list_view_renders_200_with_row(self):
        golden = PyatsGoldenConfig(
            device=self.device,
            name="edit-test-golden",
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
            config_text="hostname rtr01",
        )
        golden.full_clean()
        golden.save()
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"golden-config list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatsgoldenconfig_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsCaptureScheduleListViewRenderTest(_EditableListViewsBase):
    """``/plugins/pyats/capture-schedules/`` must render 200 (ATW-817 regression)."""

    def test_list_view_renders_200_with_row(self):
        schedule = PyatsCaptureSchedule(
            name="edit-test-schedule",
            device_filter={"id__in": [self.device.pk]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        schedule.full_clean()
        schedule.save()
        url = reverse("plugins:netbox_pyats:pyatscaptureschedule_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"capture-schedule list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatscaptureschedule_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsParserCatalogRefreshScheduleListViewRenderTest(_EditableListViewsBase):
    """``/plugins/pyats/parser-catalog-refresh-schedules/`` must render 200.

    ATW-817 regression guard: this model is singleton-like (single-row intent
    gate) but still registers standard edit URLs; the table must not use
    ``_APPEND_ONLY_ACTIONS``.
    """

    def test_list_view_renders_200_with_row(self):
        schedule = PyatsParserCatalogRefreshSchedule(enabled=True)
        schedule.full_clean()
        schedule.save()
        url = reverse("plugins:netbox_pyats:pyatsparsercatalogrefreshschedule_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"parser-catalog-refresh-schedule list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatsparsercatalogrefreshschedule_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
