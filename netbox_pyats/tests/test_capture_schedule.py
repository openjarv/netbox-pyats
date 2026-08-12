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


class PyatsCaptureScheduleCleanTest(TestCase):
    """Model-level ``device_filter`` validation (ATW-814 CR-1).

    ``PyatsCaptureSchedule.clean()`` dry-run-compiles the ORM spec against
    ``dcim.Device`` and raises ``ValidationError`` on unknown fields, bad
    lookup suffixes, or wrong value types — shared by the form (calls
    ``full_clean``) and the API serializer (NetBoxModelSerializer.validate
    calls ``instance.full_clean()``).
    """

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="CL01", slug="cl01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-CL", slug="cisco-cl")
        cls.device_type = DeviceType.objects.create(model="C9200-CL", slug="c9200-cl", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-CL", slug="router-cl")
        cls.device = Device.objects.create(
            name="cl-rtr01",
            site=cls.site,
            device_type=cls.device_type,
            role=cls.role,
        )

    def _make(self, device_filter):
        return PyatsCaptureSchedule(
            name="Clean-test",
            device_filter=device_filter,
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )

    def test_clean_accepts_valid_lookup(self):
        sched = self._make({"id__in": [self.device.pk]})
        sched.full_clean()  # no raise

    def test_clean_accepts_empty_dict(self):
        sched = self._make({})
        sched.full_clean()  # no raise

    def test_clean_rejects_unknown_field(self):
        from django.core.exceptions import ValidationError

        sched = self._make({"not_a_real_field__in": [1, 2]})
        with pytest.raises(ValidationError) as exc:
            sched.full_clean()
        assert "device_filter" in exc.value.message_dict

    def test_clean_rejects_bad_lookup_suffix(self):
        from django.core.exceptions import ValidationError

        sched = self._make({"name__not_a_lookup": "foo"})
        with pytest.raises(ValidationError) as exc:
            sched.full_clean()
        assert "device_filter" in exc.value.message_dict

    def test_clean_rejects_wrong_value_type(self):
        from django.core.exceptions import ValidationError

        # ``id__in`` expects an iterable; a non-iterable (int) raises a
        # TypeError when the SQL compiler builds the IN clause.
        sched = self._make({"id__in": 42})
        with pytest.raises(ValidationError) as exc:
            sched.full_clean()
        assert "device_filter" in exc.value.message_dict


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


# --- HD-2 (ATW-818): invalid ORM key regression tests ------------------ #
#
# Companion to CR-1 (ATW-814): the model gains a model-level ``clean()``
# that dry-run resolves the ORM spec against ``dcim.Device`` and rejects
# invalid lookup keys at save time (``ValidationError``, not
# ``django.core.exceptions.FieldError`` at dispatch time).
#
# These tests self-skip until CR-1 lands on ``main`` (feature-detected via
# ``hasattr(PyatsCaptureSchedule, "clean")``). NetBoxModel (the base) does
# not define a model-level ``clean``, so the attribute only appears after
# CR-1 adds it to the subclass. When CR-1 lands, remove the skip guard
# (or delete the ``_CR1_LANDED`` sentinel and the ``skipUnless``).
#
# Expected CR-1 behavior:
#   - ``full_clean()`` raises ``django.core.exceptions.ValidationError``
#     whose error dict includes the ``device_filter`` key.
#   - The bad key never reaches ``Device.objects.filter(**spec)`` (which
#     would raise ``FieldError`` at dispatch time, not save time).
#
# See: ATW-814, ATW-818 (HD-2).


class _PyatsCaptureScheduleModelTestHD2(TestCase):
    """HD-2 regression guards for device_filter ORM-key validation (ATW-818)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="HD01", slug="hd01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-HD", slug="cisco-hd")
        cls.device_type = DeviceType.objects.create(
            model="C9200-HD", slug="c9200-hd", manufacturer=cls.mfr
        )
        cls.role = DeviceRole.objects.create(name="Switch-HD", slug="switch-hd")
        cls.device = Device.objects.create(
            name="hd-sw01",
            site=cls.site,
            device_type=cls.device_type,
            role=cls.role,
        )

    @staticmethod
    def _cr1_landed():
        """Feature-detect CR-1 (ATW-814): model-level clean() on the subclass.

        NetBoxModel itself has no ``clean`` method, so ``PyatsCaptureSchedule.clean``
        only exists once CR-1 defines it on the subclass. ``hasattr`` on the
        class (not an instance) avoids triggering the descriptor protocol that
        would resolve to the base class's inherited ``full_clean`` wrapper.
        """
        return "clean" in PyatsCaptureSchedule.__dict__

    def test_invalid_orm_key_rejected_at_save_time(self):
        """HD-2: a bad ORM key raises ValidationError at save, not FieldError at dispatch.

        Guards the hardening framing (ATW-818): operator-supplied keys must not
        reach ``Device.objects.filter(**spec)`` unvalidated. The typo
        ``region_idd__in`` is not a valid ``dcim.Device`` lookup and would raise
        ``django.core.exceptions.FieldError`` inside ``_resolve_device_filter``
        at dispatch time without CR-1's save-time validator.
        """
        import unittest

        from django.core.exceptions import ValidationError

        if not self._cr1_landed():
            raise unittest.SkipTest(
                "CR-1 (ATW-814) not landed: model-level device_filter "
                "validator absent — skipping HD-2 regression guard"
            )

        sched = PyatsCaptureSchedule(
            name="Bad-key save",
            device_filter={"region_idd__in": [1, 2]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        with pytest.raises(ValidationError) as exc_info:
            sched.full_clean()
        assert "device_filter" in exc_info.value.message_dict
        assert sched.pk is None

        sched2 = PyatsCaptureSchedule(
            name="Bad-key dispatch",
            device_filter={"region_idd__in": [1, 2]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        with pytest.raises(ValidationError):
            sched2.full_clean()
        assert sched2.pk is None

    def test_valid_orm_key_still_accepted_at_save_time(self):
        """HD-2: a valid ORM key still saves cleanly after CR-1 lands.

        Guards against CR-1 over-validating (rejecting specs that
        ``Device.objects.filter(**spec)`` accepts). ``id__in`` is a valid
        ``dcim.Device`` lookup that the existing tests already use.
        """
        import unittest

        if not self._cr1_landed():
            raise unittest.SkipTest(
                "CR-1 (ATW-814) not landed: model-level device_filter "
                "validator absent — skipping HD-2 regression guard"
            )

        sched = PyatsCaptureSchedule(
            name="Valid-key save",
            device_filter={"id__in": [self.device.pk]},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.device_filter == {"id__in": [self.device.pk]}

    def test_empty_filter_still_accepted_at_save_time(self):
        """HD-2: the empty-dict default (no filter) still saves cleanly after CR-1.

        Guards against CR-1 rejecting the documented "match no devices"
        sentinel (``device_filter={}``).
        """
        import unittest

        if not self._cr1_landed():
            raise unittest.SkipTest(
                "CR-1 (ATW-814) not landed: model-level device_filter "
                "validator absent — skipping HD-2 regression guard"
            )

        sched = PyatsCaptureSchedule(
            name="Empty-filter save",
            device_filter={},
            kind=SnapshotKindChoices.KIND_FULL,
            enabled=True,
        )
        sched.full_clean()
        sched.save()
        reloaded = PyatsCaptureSchedule.objects.get(pk=sched.pk)
        assert reloaded.device_filter == {}
