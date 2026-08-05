"""Tests for the PyatsCaptureSchedule model + run_capture_schedules_job dispatcher (ATW-433).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- PyatsCaptureSchedule model persistence + resolve_devices re-resolution.
- run_capture_schedules_job dispatches one enqueue_batch_capture per enabled
  schedule, skips disabled schedules, updates last_run_at, and handles the
  "device_filter matches zero devices" case.
- next_run_at is populated from the NetBox Job row's interval for recurring
  runs and left blank for one-shot runs (ATW-610).
"""

from datetime import timedelta
from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from utilities.testing import TestCase

from netbox_pyats.choices import SnapshotKindChoices
from netbox_pyats.models import PyatsCaptureSchedule


class PyatsCaptureScheduleFormTest(TestCase):
    """Form validation for device_filter allowlist (ATW-578)."""

    def test_clean_device_filter_valid_keys(self):
        from netbox_pyats.forms import PyatsCaptureScheduleForm

        form = PyatsCaptureScheduleForm(
            data={
                "name": "Valid filter test",
                "device_filter": '{"id__in": [1, 2], "site__slug__in": ["nyc", "lax"]}',
                "kind": SnapshotKindChoices.KIND_FULL,
                "enabled": True,
            }
        )
        assert form.is_valid(), form.errors

    def test_clean_device_filter_disallowed_key_rejected(self):
        from netbox_pyats.forms import PyatsCaptureScheduleForm

        form = PyatsCaptureScheduleForm(
            data={
                "name": "Invalid filter test",
                "device_filter": '{"secret__icontains": "sensitive-region"}',
                "kind": SnapshotKindChoices.KIND_FULL,
                "enabled": True,
            }
        )
        assert not form.is_valid()
        assert "disallowed keys" in str(form.errors["device_filter"])

    def test_clean_device_filter_empty_is_valid(self):
        from netbox_pyats.forms import PyatsCaptureScheduleForm

        form = PyatsCaptureScheduleForm(
            data={
                "name": "Empty filter test",
                "device_filter": "",
                "kind": SnapshotKindChoices.KIND_FULL,
                "enabled": True,
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["device_filter"] == {}

    def test_clean_device_filter_invalid_json_rejected(self):
        from netbox_pyats.forms import PyatsCaptureScheduleForm

        form = PyatsCaptureScheduleForm(
            data={
                "name": "Bad JSON test",
                "device_filter": "not json at all",
                "kind": SnapshotKindChoices.KIND_FULL,
                "enabled": True,
            }
        )
        assert not form.is_valid()
        assert "valid JSON" in str(form.errors["device_filter"])


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
        # The model field is NOT NULL with default=dict, so the DB-legal
        # "no filter" value is the empty dict {} (handled by _resolve_device_filter
        # as "match no devices"). A non-dict value like None is handled by the
        # _resolve_device_filter helper (defensive), but cannot be persisted
        # on the NOT NULL field — test the helper directly for that case.
        from netbox_pyats.models import _resolve_device_filter

        assert _resolve_device_filter(None).count() == 0
        assert _resolve_device_filter("not-a-dict").count() == 0
        # The persisted "no filter" case uses {} (the field's default).
        sched = PyatsCaptureSchedule(
            name="Empty dict",
            device_filter={},
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
        # mock.Mock() has no interval attr → one-shot run, next_run_at stays blank.
        assert reloaded.next_run_at is None
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
        # mock.Mock() has no interval attr → one-shot run, next_run_at stays blank.
        assert reloaded.next_run_at is None
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

    def test_next_run_at_set_from_job_interval(self):
        """Recurring run (Job.interval set) → next_run_at = last_run_at + interval (ATW-610)."""
        sched = self._make_schedule("Recurring", {"id__in": [self.device.pk]})
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:
            mock_enqueue.return_value = mock.Mock(pk=42)
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock(interval=30))
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert reloaded.next_run_at is not None
        # next_run_at == last_run_at + 30 minutes (interval is in minutes).
        assert reloaded.next_run_at == reloaded.last_run_at + timedelta(minutes=30)
        assert result["dispatched"] == 1

    def test_next_run_at_blank_for_zero_device_skip_with_interval(self):
        """Zero-device skip still sets next_run_at when Job.interval is set (ATW-610)."""
        sched = self._make_schedule("Zero recurring", {"id__in": [999999]})
        with mock.patch("netbox_pyats.jobs.enqueue_batch_capture") as mock_enqueue:
            from netbox_pyats.jobs import run_capture_schedules_job

            result = run_capture_schedules_job(job=mock.Mock(interval=60))
        mock_enqueue.assert_not_called()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert reloaded.next_run_at == reloaded.last_run_at + timedelta(minutes=60)
        assert result["skipped"] == 1
