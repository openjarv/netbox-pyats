"""Regression tests for the four append-only plugin list views (ATW-183).

The list views for ``PyatsSnapshot``, ``PyatsSnapshotDiff``,
``PyatsComplianceRun``, and ``PyatsJob`` must render HTTP 200 even though
those models are append-only and register no ``*_edit`` URL.

Before the fix in this commit, each list view returned 500 with
``NoReverseMatch: 'pyats<model>_edit' is not a valid view function or pattern
name.``: ``PyatsSnapshotTable`` / ``PyatsSnapshotDiffTable`` /
``PyatsComplianceRunTable`` / ``PyatsJobTable`` all inherited
``NetBoxTable.Meta`` without overriding ``actions``, so the default
``ActionsColumn(actions=('edit', 'delete', 'changelog'))`` reversed the
non-existent ``plugins:netbox_pyats:<model>_edit`` URL at render time.

These tests render each list view inside a real request context (logged-in
admin user, at least one row in the queryset) so the actions column is
exercised in CI, not just the model helpers. This is the test gap that let
the bug ship.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import (
    DiffStatusChoices,
    PyatsJobStatusChoices,
    PyatsJobTypeChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from netbox_pyats.models import PyatsComplianceRun, PyatsGoldenConfig, PyatsJob, PyatsSnapshot, PyatsSnapshotDiff


class _AppendOnlyListViewsBase(TestCase):
    """Shared fixture: one device + the four model rows a list view needs.

    Subclasses set ``user_permissions`` to cover the ``view`` permission for
    each model exercised plus ``dcim.view_device`` (FK link rendering in the
    table column).
    """

    user_permissions = (
        "netbox_pyats.view_pyatssnapshot",
        "netbox_pyats.view_pyatssnapshotdiff",
        "netbox_pyats.view_pyatscompliancerun",
        "netbox_pyats.view_pyatsjob",
        "netbox_pyats.view_pyatsgoldenconfig",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AOL01", slug="aol01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-AOL", slug="cisco-aol")
        cls.device_type = DeviceType.objects.create(model="C9300-AOL", slug="c9300-aol", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-AOL", slug="router-aol")
        cls.device = Device.objects.create(name="aolrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

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


class PyatsSnapshotListViewRenderTest(_AppendOnlyListViewsBase):
    """``/plugins/pyats/snapshots/`` must render 200 (ATW-183 regression)."""

    def test_list_view_renders_200_with_row(self):
        self._make_snapshot()
        url = reverse("plugins:netbox_pyats:pyatssnapshot_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"snapshot list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatssnapshot_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsSnapshotDiffListViewRenderTest(_AppendOnlyListViewsBase):
    """``/plugins/pyats/diffs/`` must render 200 (ATW-183 regression)."""

    def test_list_view_renders_200_with_row(self):
        before = self._make_snapshot(data={"config": {"hostname": "rtr01"}})
        after = self._make_snapshot(data={"config": {"hostname": "rtr02"}})
        diff_row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_SUCCESS,
            diff={"name": "root", "type": "dict", "status": "changed", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
            size_bytes=1,
        )
        diff_row.full_clean()
        diff_row.save()

        url = reverse("plugins:netbox_pyats:pyatssnapshotdiff_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"diff list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatssnapshotdiff_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsComplianceRunListViewRenderTest(_AppendOnlyListViewsBase):
    """``/plugins/pyats/compliance-runs/`` must render 200 (ATW-183 regression)."""

    def test_list_view_renders_200_with_row(self):
        snap = self._make_snapshot()
        golden = PyatsGoldenConfig(
            device=self.device,
            name="baseline",
            source="manual",
            config_text="hostname rtr01",
        )
        golden.full_clean()
        golden.save()
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result="drift",
            diff={"name": "root", "type": "dict", "status": "changed", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
            size_bytes=1,
        )
        run.full_clean()
        run.save()

        url = reverse("plugins:netbox_pyats:pyatscompliancerun_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"compliance-run list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatscompliancerun_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PyatsJobListViewRenderTest(_AppendOnlyListViewsBase):
    """``/plugins/pyats/jobs/`` must render 200 (ATW-183 regression)."""

    def test_list_view_renders_200_with_row(self):
        job_row = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_SUCCESS,
            device=self.device,
        )
        job_row.full_clean()
        job_row.save()

        url = reverse("plugins:netbox_pyats:pyatsjob_list")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"job list view 500'd; body: {response.content[:500]!r}",
        )

    def test_list_view_renders_200_empty(self):
        url = reverse("plugins:netbox_pyats:pyatsjob_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
