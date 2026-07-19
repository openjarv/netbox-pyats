"""Tests for :class:`netbox_pyats.models.PyatsSnapshot`.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (crypto + testbed +
capture) in matrix jobs that don't stand up NetBox.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.test import TestCase

from netbox_pyats.choices import DiffStatusChoices, SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices
from netbox_pyats.models import PyatsSnapshot, PyatsSnapshotDiff


class PyatsSnapshotModelTest(TestCase):
    """Persistence and helper behavior of PyatsSnapshot."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AMS01", slug="ams01")
        cls.mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        cls.device_type = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router", slug="router")
        cls.device = Device.objects.create(name="rtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def test_success_snapshot_round_trips_jsonb(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {"hostname": "rtr01"}, "state": {"interfaces": {}}},
            parser_warnings=[],
            genie_version="26.6",
            pyats_version="26.6",
            size_bytes=42,
        )
        snap.full_clean()
        snap.save()
        reloaded = PyatsSnapshot.objects.get(pk=snap.pk)
        assert reloaded.data == {"config": {"hostname": "rtr01"}, "state": {"interfaces": {}}}
        assert reloaded.kind == SnapshotKindChoices.KIND_FULL
        assert reloaded.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert reloaded.size_bytes == 42
        assert reloaded.genie_version == "26.6"

    def test_unsupported_snapshot_has_empty_data_and_warning(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_UNSUPPORTED,
            triggered_by=SnapshotTriggerChoices.TRIGGER_JOB,
            data={},
            parser_warnings=["platform os='unsupported - no parser' has no Genie parser; skipped"],
        )
        snap.full_clean()
        snap.save()
        reloaded = PyatsSnapshot.objects.get(pk=snap.pk)
        assert reloaded.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert reloaded.data == {}
        assert reloaded.has_warnings is True

    def test_error_snapshot_records_exception(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_STATE,
            status=SnapshotStatusChoices.STATUS_ERROR,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={},
            parser_warnings=["capture error: connection refused"],
        )
        snap.full_clean()
        snap.save()
        reloaded = PyatsSnapshot.objects.get(pk=snap.pk)
        assert reloaded.status == SnapshotStatusChoices.STATUS_ERROR
        assert "connection refused" in reloaded.parser_warnings[0]

    def test_str_includes_device_kind_and_timestamp(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {}},
        )
        snap.full_clean()
        snap.save()
        s = str(snap)
        assert "rtr01" in s
        assert "Full" in s

    def test_get_status_color_maps_each_status(self):
        assert PyatsSnapshot(status=SnapshotStatusChoices.STATUS_SUCCESS).get_status_color() == "success"
        assert PyatsSnapshot(status=SnapshotStatusChoices.STATUS_UNSUPPORTED).get_status_color() == "warning"
        assert PyatsSnapshot(status=SnapshotStatusChoices.STATUS_ERROR).get_status_color() == "danger"

    def test_has_warnings_false_for_empty_list(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {}},
            parser_warnings=[],
        )
        snap.full_clean()
        snap.save()
        assert PyatsSnapshot.objects.get(pk=snap.pk).has_warnings is False

    def test_recent_snapshots_ordered_newest_first(self):
        import time

        for i in range(3):
            snap = PyatsSnapshot(
                device=self.device,
                kind=SnapshotKindChoices.KIND_CONFIG,
                status=SnapshotStatusChoices.STATUS_SUCCESS,
                triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
                data={"config": {"i": i}},
            )
            snap.full_clean()
            snap.save()
            time.sleep(0.01)  # ensure captured_at differs
        qs = list(PyatsSnapshot.objects.filter(device=self.device).order_by("-captured_at"))
        assert len(qs) == 3
        assert qs[0].captured_at >= qs[1].captured_at >= qs[2].captured_at


class PyatsSnapshotDiffModelTest(TestCase):
    """Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="DLS01", slug="dls01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-D", slug="cisco-d")
        cls.device_type = DeviceType.objects.create(model="C9300-D", slug="c9300-d", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-D", slug="router-d")
        cls.device = Device.objects.create(name="diffrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _make_snapshot(self, data):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data=data,
        )
        snap.full_clean()
        snap.save()
        return snap

    def test_success_diff_round_trips_jsonb(self):
        before = self._make_snapshot({"config": {"hostname": "rtr01"}})
        after = self._make_snapshot({"config": {"hostname": "rtr02"}})
        diff_row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_SUCCESS,
            diff={"name": "root", "type": "dict", "status": "changed", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
            parser_warnings=[],
            size_bytes=42,
        )
        diff_row.full_clean()
        diff_row.save()
        reloaded = PyatsSnapshotDiff.objects.get(pk=diff_row.pk)
        assert reloaded.status == DiffStatusChoices.STATUS_SUCCESS
        assert reloaded.summary == {"added": 0, "removed": 0, "changed": 1, "unchanged": 0}
        assert reloaded.size_bytes == 42
        assert reloaded.before_id == before.pk
        assert reloaded.after_id == after.pk
        assert reloaded.device_id == self.device.pk

    def test_empty_diff_status_round_trips(self):
        before = self._make_snapshot({})
        after = self._make_snapshot({})
        diff_row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_EMPTY,
            diff={"name": "root", "type": "dict", "status": "unchanged", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 0},
        )
        diff_row.full_clean()
        diff_row.save()
        reloaded = PyatsSnapshotDiff.objects.get(pk=diff_row.pk)
        assert reloaded.status == DiffStatusChoices.STATUS_EMPTY
        assert reloaded.has_changes is False

    def test_error_diff_records_warnings(self):
        before = self._make_snapshot({"config": {}})
        after = self._make_snapshot({"config": {}})
        diff_row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_ERROR,
            diff={},
            summary={},
            parser_warnings=["diff error: malformed payload"],
        )
        diff_row.full_clean()
        diff_row.save()
        reloaded = PyatsSnapshotDiff.objects.get(pk=diff_row.pk)
        assert reloaded.status == DiffStatusChoices.STATUS_ERROR
        assert reloaded.has_warnings is True
        assert "malformed payload" in reloaded.parser_warnings[0]

    def test_str_includes_device_and_snapshot_ids(self):
        before = self._make_snapshot({"config": {}})
        after = self._make_snapshot({"config": {}})
        diff_row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_SUCCESS,
            diff={},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 0},
        )
        diff_row.full_clean()
        diff_row.save()
        s = str(diff_row)
        assert "diffrtr01" in s
        assert f"{before.id}→{after.id}" in s

    def test_get_status_color_maps_each_status(self):
        assert PyatsSnapshotDiff(status=DiffStatusChoices.STATUS_SUCCESS).get_status_color() == "success"
        assert PyatsSnapshotDiff(status=DiffStatusChoices.STATUS_EMPTY).get_status_color() == "secondary"
        assert PyatsSnapshotDiff(status=DiffStatusChoices.STATUS_ERROR).get_status_color() == "danger"

    def test_has_changes_reflects_summary(self):
        d = PyatsSnapshotDiff(
            device=self.device,
            before=PyatsSnapshot(),
            after=PyatsSnapshot(),
            status=DiffStatusChoices.STATUS_SUCCESS,
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 3},
        )
        assert d.has_changes is False
        d.summary = {"added": 1, "removed": 0, "changed": 0, "unchanged": 2}
        assert d.has_changes is True

    def test_recent_diffs_ordered_newest_first(self):
        import time

        before = self._make_snapshot({"config": {}})
        after = self._make_snapshot({"config": {}})
        for _ in range(3):
            diff_row = PyatsSnapshotDiff(
                device=self.device,
                before=before,
                after=after,
                status=DiffStatusChoices.STATUS_SUCCESS,
                diff={},
                summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 0},
            )
            diff_row.full_clean()
            diff_row.save()
            time.sleep(0.01)  # ensure created differs
        qs = list(PyatsSnapshotDiff.objects.filter(device=self.device).order_by("-created"))
        assert len(qs) == 3
        assert qs[0].created >= qs[1].created >= qs[2].created
