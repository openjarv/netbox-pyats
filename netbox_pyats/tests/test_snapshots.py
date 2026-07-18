"""Tests for :class:`netbox_pyats.models.PyatsSnapshot`.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (crypto + testbed +
capture) in matrix jobs that don't stand up NetBox.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.test import TestCase

from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices
from netbox_pyats.models import PyatsSnapshot


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
