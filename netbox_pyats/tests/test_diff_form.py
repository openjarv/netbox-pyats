"""Tests for the ``DeviceDiffForm`` kind filter (ATW-241 child 4 / ATW-252).

NetBox-gated: requires a running NetBox/Django test database (the form looks
up :class:`PyatsSnapshot` rows by pk in ``clean()``). Skipped when NetBox is
not importable.

Coverage (per the issue's deliverables):

- parse-vs-parse diff: ``clean()`` passes (same kind).
- parse-vs-state diff: ``clean()`` raises ``ValidationError`` (kind mismatch).
- state-vs-full diff: ``clean()`` raises ``ValidationError`` (kind mismatch).
- config-vs-config diff: ``clean()`` passes (same kind).
- A diff against a non-existent snapshot pk: ``clean()`` raises
  ``ValidationError`` (the form owns existence, not just kind).
- The device-page diff view rejects a kind-mismatched POST (returns a redirect
  with an error flash, no diff enqueued), and accepts a same-kind POST
  (enqueues a diff job).
"""

import pytest

pytest.importorskip("netbox")

from unittest import mock

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices
from netbox_pyats.forms import DeviceDiffForm
from netbox_pyats.models import PyatsSnapshot


def _make_snapshot(device, kind, *, pk_offset=0):
    """Create a minimal PyatsSnapshot row of the given kind for ``device``."""
    return PyatsSnapshot.objects.create(
        device=device,
        kind=kind,
        status=SnapshotStatusChoices.STATUS_SUCCESS,
        data={"state": {"show version": {"version": "1.0"}}},
        parser_warnings=[],
    )


class DeviceDiffFormKindFilterTest(TestCase):
    """Form-level kind-filter enforcement (ATW-241 child 4)."""

    user_permissions = (
        "netbox_pyats.view_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AMS01", slug="ams01")
        cls.mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        cls.device_type = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router", slug="router")
        cls.device = Device.objects.create(name="rtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _form(self, before_id, after_id):
        return DeviceDiffForm(data={"before_id": before_id, "after_id": after_id})

    def test_parse_vs_parse_diff_is_allowed(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        form = self._form(before.pk, after.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_parse_vs_state_diff_is_rejected(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_STATE)
        form = self._form(before.pk, after.pk)
        self.assertFalse(form.is_valid())
        # The kind-mismatch error is a non-field error (raised in clean()).
        self.assertIn("__all__", form.errors)
        self.assertIn("kind", " ".join(form.errors["__all__"]).lower())

    def test_state_vs_full_diff_is_rejected(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_STATE)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_FULL)
        form = self._form(before.pk, after.pk)
        self.assertFalse(form.is_valid())

    def test_config_vs_config_diff_is_allowed(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_CONFIG)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_CONFIG)
        form = self._form(before.pk, after.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_full_vs_full_diff_is_allowed(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_FULL)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_FULL)
        form = self._form(before.pk, after.pk)
        self.assertTrue(form.is_valid(), form.errors)

    def test_diff_against_nonexistent_snapshot_is_rejected(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_STATE)
        form = self._form(before.pk, before.pk + 999999)
        self.assertFalse(form.is_valid())


class DeviceDiffViewKindFilterTest(TestCase):
    """The ``device_diff`` view surfaces the kind filter as a redirect+flash."""

    user_permissions = (
        "netbox_pyats.add_pyatssnapshotdiff",
        "netbox_pyats.view_pyatssnapshot",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AMS01", slug="ams01")
        cls.mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        cls.device_type = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router", slug="router")
        cls.device = Device.objects.create(name="rtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _url(self):
        return reverse("plugins:netbox_pyats:device_diff", kwargs={"device_id": self.device.pk})

    def test_kind_mismatch_post_redirects_and_does_not_enqueue(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_STATE)
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff") as enqueue:
            response = self.client.post(
                self._url(),
                {"before_id": before.pk, "after_id": after.pk},
            )
        self.assertEqual(response.status_code, 302)
        enqueue.assert_not_called()

    def test_same_kind_post_enqueues_diff(self):
        before = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        after = _make_snapshot(self.device, SnapshotKindChoices.KIND_PARSE)
        with mock.patch("netbox_pyats.views.jobs.enqueue_diff") as enqueue:
            response = self.client.post(
                self._url(),
                {"before_id": before.pk, "after_id": after.pk},
            )
        self.assertEqual(response.status_code, 302)
        enqueue.assert_called_once()
        _, kwargs = enqueue.call_args
        self.assertEqual(kwargs["before_id"], before.pk)
        self.assertEqual(kwargs["after_id"], after.pk)
