"""Tests for the PyatsCaptureSchedule model + run_capture_schedules_job dispatcher (ATW-433).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- PyatsCaptureSchedule model persistence + resolve_devices re-resolution.
- run_capture_schedules_job dispatches one enqueue_batch_capture per enabled
  schedule, skips disabled schedules, updates last_run_at, and handles the
  "device_filter matches zero devices" case.
"""

from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from utilities.testing import TestCase

from netbox_pyats.choices import SnapshotKindChoices
from netbox_pyats.models import PyatsCaptureSchedule


class PyatsCaptureScheduleModelTest(TestCase):
    """Persistence + resolve_devices for PyatsCaptureSchedule (ATW-433)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="CS01", slug="cs01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-CS", slug="cisco-cs")
        cls.device_type = DeviceType.objects.create(model="C9200-CS", slug="c9200-cs", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Switch-CS", slug="switch-cs")
        cls.device = Device.objects.create(
            name="cs-rtr01",
            site=cls.site,
            device_type=cls.device_type,
            role=cls.role,
        )

    def test_schedule_round_trips(self):
        sched = PyatsCaptureSchedule(
            name="Edge nightly",
            device_filter={"id__in": [self.device.pk]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.name == "Edge nightly"
        assert reloaded.kind == SnapshotKindChoices.KIND_FULL
        assert reloaded.enabled is True
        assert reloaded.device_filter == {"id__in": [self.device.pk]}
        assert reloaded.last_run_at is None
        assert reloaded.next_run_at is None

    def test_resolve_devices_matches_filter(self):
        sched = PyatsCaptureSchedule(
            name="Filter match",
            device_filter={"id__in": [self.device.pk]},
            kind=SnapshotKindChoices.KIND_CONFIG,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        qs = sched.resolve_devices()
        assert list(qs.values_list("pk", flat=True)) == [self.device.pk]

    def test_resolve_devices_empty_filter(self):
        sched = PyatsCaptureSchedule(
            name="Empty filter",
            device_filter={},
            kind=SnapshotKindChoices.KIND_STATE,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        assert sched.resolve_devices().count() == 0

    def test_resolve_devices_non_dict_filter(self):
        sched = PyatsCaptureSchedule(
            name="Non-dict",
            device_filter=None,
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        assert sched.resolve_devices().count() == 0

    def test_disabled_schedule_persists(self):
        sched = PyatsCaptureSchedule(
            name="Paused",
            device_filter={"id__in": [self.device.pk]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=False,
        )
        sched.full_clean()
        sched.save()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.enabled is False


class RunCaptureSchedulesJobTest(TestCase):
    """run_capture_schedules_job dispatch logic (ATW-433)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="RS01", slug="rs01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-RS", slug="cisco-rs")
        cls.device_type = DeviceType.objects.create(model="C9300-RS", slug="c9300-rs", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-RS", slug="router-rs")
        cls.device = Device.objects.create(
            name="rs-rtr01",
            site=cls.site,
            device_type=cls.device_type,
            role=cls.role,
        )

    def _make_schedule(self, name, device_filter, enabled=True, kind=SnapshotKindChoices.KIND_FULL):
        sched = PyatsCaptureSchedule(
            name=name,
            device_filter=device_filter,
            kind=kind,
            enabled=enabled,
        )
        sched.full_clean()
        sched.save()
        return sched

    def test_dispatches_enabled_schedule(self):
        sched = self._make_schedule("Active", {"id__in": [self.device.pk]})
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:

            class FakeJob:
                pk = 42

            mock_enqueue.return_value = FakeJob()
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock())
        mock_enqueue.assert_called_once()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert result["dispatched"] == 1
        assert result["skipped"] == 0

    def test_skips_disabled_schedule(self):
        self._make_schedule("Disabled", {"id__in": [self.device.pk]}, enabled=False)
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock())
        mock_enqueue.assert_not_called()
        assert result["dispatched"] == 0
        assert result["skipped"] == 0

    def test_skips_schedule_with_zero_devices(self):
        sched = self._make_schedule("Zero match", {"id__in": [999999]})
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock())
        mock_enqueue.assert_not_called()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert result["dispatched"] == 0
        assert result["skipped"] == 1

    def test_dispatches_multiple_enabled_schedules(self):
        self._make_schedule("S1", {"id__in": [self.device.pk]})
        self._make_schedule("S2", {"id__in": [self.device.pk]})
        self._make_schedule("S3", {"id__in": [self.device.pk]}, enabled=False)
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:

            class FakeJob:
                pk = 1

            mock_enqueue.return_value = FakeJob()
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock())
        assert mock_enqueue.call_count == 2
        assert result["dispatched"] == 2
        assert result["skipped"] == 0
