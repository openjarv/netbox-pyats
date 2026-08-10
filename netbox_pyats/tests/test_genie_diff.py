"""Tests for the dedicated Genie Diff page (ATW-731).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- :class:`netbox_pyats.views.GenieDiffView`:
  - GET with no device: renders the mode picker + device pickers, no snapshot
    pickers, recent diffs table (empty when no diffs exist).
  - GET with ``?before_device=<pk>`` (same-device mode): renders the snapshot
    pickers populated for the selected device.
  - GET with ``?mode=cross&before_device=<pk>&after_device=<pk>``: renders
    both snapshot pickers populated for their respective devices.
  - POST same-device with two snapshots of the same device: enqueues a diff
    via ``jobs.enqueue_diff`` with ``cross_device=False``.
  - POST cross-device with snapshots of different devices: enqueues a diff
    with ``cross_device=True``.
  - POST same-device with snapshots of different devices: redirects with an
    error (mode mismatch).
  - POST with a missing snapshot: redirects with an error.
  - POST diffing a snapshot against itself: redirects with an error.
  - Recent diffs table renders existing :class:`PyatsSnapshotDiff` rows.

``enqueue_diff`` is monkeypatched so the view tests do not need a live RQ
worker (same pattern as ``test_device_parse.py`` / ``test_genie_parse.py``).
"""

from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.models import PyatsSnapshot, PyatsSnapshotDiff


class GenieDiffViewTest(TestCase):
    """View tests for :class:`views.GenieDiffView` (ATW-731)."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshotdiff",
        "netbox_pyats.view_pyatssnapshotdiff",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="GD01", slug="gd01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-GD", slug="cisco-gd")
        cls.platform_iosxe = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.dt = DeviceType.objects.create(model="C9300-GD", slug="c9300-gd", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-GD", slug="router-gd")
        cls.device_a = Device.objects.create(
            name="gd_rtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        cls.device_b = Device.objects.create(
            name="gd_rtr02",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        # Two snapshots on device_a (same-device diff input)
        cls.snap_a1 = PyatsSnapshot.objects.create(
            device=cls.device_a,
            kind="config",
            status="success",
            triggered_by="user",
            data={"hostname": "rtr01", "version": "1.0"},
        )
        cls.snap_a2 = PyatsSnapshot.objects.create(
            device=cls.device_a,
            kind="config",
            status="success",
            triggered_by="user",
            data={"hostname": "rtr01", "version": "2.0"},
        )
        # One snapshot on device_b (cross-device diff input)
        cls.snap_b1 = PyatsSnapshot.objects.create(
            device=cls.device_b,
            kind="config",
            status="success",
            triggered_by="user",
            data={"hostname": "rtr02", "version": "1.0"},
        )

    def test_get_no_device_renders_mode_and_device_pickers(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Genie Diff")
        self.assertContains(response, "Select a device")
        # No device selected → snapshot pickers are not rendered.
        self.assertNotContains(response, "Before snapshot")
        # Recent diffs section renders even when empty.
        self.assertContains(response, "Recent Diffs")

    def test_get_same_device_renders_snapshot_pickers(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        response = self.client.get(url, {"before_device": self.device_a.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Before snapshot")
        self.assertContains(response, "After snapshot")
        # Both snapshots of device_a appear in the pickers.
        self.assertContains(response, f"#{self.snap_a1.pk}")
        self.assertContains(response, f"#{self.snap_a2.pk}")

    def test_get_cross_device_renders_both_device_snapshots(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        response = self.client.get(
            url,
            {
                "mode": "cross",
                "before_device": self.device_a.pk,
                "after_device": self.device_b.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.device_a))
        self.assertContains(response, str(self.device_b))
        self.assertContains(response, f"#{self.snap_a1.pk}")
        self.assertContains(response, f"#{self.snap_b1.pk}")

    def test_post_same_device_enqueues_diff_without_cross_device(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        fake_core_job = mock.Mock()
        fake_core_job.pk = 7701
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff", return_value=fake_core_job) as mocked:
            response = self.client.post(
                url,
                {
                    "mode": "same",
                    "before_id": str(self.snap_a1.pk),
                    "after_id": str(self.snap_a2.pk),
                },
            )
        self.assertEqual(response.status_code, 302)
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        self.assertEqual(args[0].pk, self.device_a.pk)
        self.assertEqual(kwargs["before_id"], self.snap_a1.pk)
        self.assertEqual(kwargs["after_id"], self.snap_a2.pk)
        self.assertFalse(kwargs["cross_device"])

    def test_post_cross_device_enqueues_diff_with_cross_device(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        fake_core_job = mock.Mock()
        fake_core_job.pk = 7702
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff", return_value=fake_core_job) as mocked:
            response = self.client.post(
                url,
                {
                    "mode": "cross",
                    "before_id": str(self.snap_a1.pk),
                    "after_id": str(self.snap_b1.pk),
                },
            )
        self.assertEqual(response.status_code, 302)
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        # Before snapshot's device owns the diff row.
        self.assertEqual(args[0].pk, self.device_a.pk)
        self.assertEqual(kwargs["before_id"], self.snap_a1.pk)
        self.assertEqual(kwargs["after_id"], self.snap_b1.pk)
        self.assertTrue(kwargs["cross_device"])

    def test_post_same_device_with_cross_device_snapshots_redirects_with_error(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff") as mocked:
            response = self.client.post(
                url,
                {
                    "mode": "same",
                    "before_id": str(self.snap_a1.pk),
                    "after_id": str(self.snap_b1.pk),
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        mocked.assert_not_called()

    def test_post_missing_snapshot_redirects_with_error(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff") as mocked:
            response = self.client.post(
                url,
                {
                    "mode": "same",
                    "before_id": "999999",
                    "after_id": str(self.snap_a2.pk),
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        mocked.assert_not_called()

    def test_post_diffing_snapshot_against_itself_redirects_with_error(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff") as mocked:
            response = self.client.post(
                url,
                {
                    "mode": "same",
                    "before_id": str(self.snap_a1.pk),
                    "after_id": str(self.snap_a1.pk),
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], url)
        mocked.assert_not_called()

    def test_recent_diffs_show_existing_diff_rows(self):
        PyatsSnapshotDiff.objects.create(
            device=self.device_a,
            before=self.snap_a1,
            after=self.snap_a2,
            status="success",
            diff={},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 1},
            parser_warnings=[],
            size_bytes=42,
        )
        url = reverse("plugins:netbox_pyats:genie_diff")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent Diffs")
        self.assertContains(response, str(self.device_a))
