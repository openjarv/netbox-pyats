"""Tests for the PyatsJob model + job-callable side effects + batch summary (Phase 5, ATW-16).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- PyatsJob model persistence + status color map + ``related_result`` accessor.
- The ADR-0005 §3 plumbing contract: ``capture_snapshot_job`` /
  ``run_diff_job`` / ``run_compliance_job`` set the PyatsJob row to
  ``running`` at entry, ``success`` (with the result-row FK) on a clean run,
  and ``error`` (with the exception text) when the job raised and the result
  row could not be written. The error path re-raises so RQ/``core.Job`` is
  also marked failed.
- ``batch_capture_job`` iterates devices, counts supported/unsupported/errored,
  and sets the PyatsJob row to ``success`` (all clean) or ``partial`` (any
  per-device failure or unsupported platform), with the batch ``summary``.
"""

import types
from unittest import mock

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from utilities.testing import TestCase

from netbox_pyats import jobs
from netbox_pyats.capture import CaptureResult
from netbox_pyats.choices import (
    DiffStatusChoices,
    PyatsJobStatusChoices,
    PyatsJobTypeChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
)
from netbox_pyats.models import PyatsJob, PyatsSnapshot


class PyatsJobModelTest(TestCase):
    """Persistence + helpers for PyatsJob (Phase 5, ATW-16)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="PJM01", slug="pjm01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-P", slug="cisco-p")
        cls.device_type = DeviceType.objects.create(model="C9300-P", slug="c9300-p", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-P", slug="router-p")
        cls.device = Device.objects.create(name="jobrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _make_snapshot(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            data={"config": {"hostname": "rtr01"}},
        )
        snap.full_clean()
        snap.save()
        return snap

    def test_pending_job_round_trips(self):
        job_row = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        job_row.full_clean()
        job_row.save()
        reloaded = PyatsJob.objects.get(pk=job_row.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_PENDING
        assert reloaded.job_type == PyatsJobTypeChoices.JOB_CAPTURE
        assert reloaded.device_id == self.device.pk
        assert reloaded.error == ""
        assert reloaded.summary == {}

    def test_batch_job_has_null_device(self):
        job_row = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        job_row.full_clean()
        job_row.save()
        reloaded = PyatsJob.objects.get(pk=job_row.pk)
        assert reloaded.device_id is None
        s = str(reloaded)
        assert "batch" in s

    def test_get_status_color_maps_each_status(self):
        assert PyatsJob(status=PyatsJobStatusChoices.STATUS_PENDING).get_status_color() == "secondary"
        assert PyatsJob(status=PyatsJobStatusChoices.STATUS_RUNNING).get_status_color() == "info"
        assert PyatsJob(status=PyatsJobStatusChoices.STATUS_SUCCESS).get_status_color() == "success"
        assert PyatsJob(status=PyatsJobStatusChoices.STATUS_ERROR).get_status_color() == "danger"
        assert PyatsJob(status=PyatsJobStatusChoices.STATUS_PARTIAL).get_status_color() == "warning"

    def test_related_result_returns_snapshot_when_set(self):
        snap = self._make_snapshot()
        job_row = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_SUCCESS,
            device=self.device,
            related_snapshot=snap,
        )
        job_row.full_clean()
        job_row.save()
        reloaded = PyatsJob.objects.get(pk=job_row.pk)
        assert reloaded.related_result is not None
        assert reloaded.related_result.pk == snap.pk

    def test_related_result_returns_none_when_no_fk_set(self):
        job_row = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PARTIAL,
            device=None,
            summary={"supported": 1, "unsupported": 1, "errored": 0, "total": 2},
        )
        job_row.full_clean()
        job_row.save()
        reloaded = PyatsJob.objects.get(pk=job_row.pk)
        assert reloaded.related_result is None
        assert reloaded.summary == {"supported": 1, "unsupported": 1, "errored": 0, "total": 2}


class CaptureJobPyatsJobPlumbingTest(TestCase):
    """ADR-0005 §3 plumbing for ``capture_snapshot_job`` (Phase 5, ATW-16)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="CJP01", slug="cjp01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-CJ", slug="cisco-cj")
        cls.device_type = DeviceType.objects.create(model="C9300-CJ", slug="c9300-cj", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-CJ", slug="router-cj")
        cls.device = Device.objects.create(name="cjrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _fake_job(self):
        return types.SimpleNamespace(object=self.device)

    def test_success_sets_running_then_success_with_snapshot_fk(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        pyats_job.full_clean()
        pyats_job.save()

        success_result = CaptureResult(
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            data={"config": {"hostname": "rtr01"}, "config_raw": "hostname rtr01\n"},
        )

        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            return_value=success_result,
        ):
            jobs.capture_snapshot_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.related_snapshot_id is not None
        assert reloaded.started_at is not None
        assert reloaded.finished_at is not None
        assert reloaded.error == ""
        # The snapshot row itself was written.
        assert PyatsSnapshot.objects.filter(pk=reloaded.related_snapshot_id).exists()

    def test_unsupported_snapshot_is_still_job_success(self):
        # ADR-0002: an unsupported *snapshot row* is a successful *job*
        # (the job ran fine; the device's platform was unsupported).
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        pyats_job.full_clean()
        pyats_job.save()

        unsupported_result = CaptureResult(
            status=SnapshotStatusChoices.STATUS_UNSUPPORTED,
            data={},
            warnings=["platform os='unsupported - no parser' has no Genie parser; skipped"],
        )

        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            return_value=unsupported_result,
        ):
            jobs.capture_snapshot_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.related_snapshot_id is not None
        # The unsupported snapshot row itself was still written.
        snap = PyatsSnapshot.objects.get(pk=reloaded.related_snapshot_id)
        assert snap.status == SnapshotStatusChoices.STATUS_UNSUPPORTED

    def test_error_when_result_row_write_fails_records_error_text(self):
        # ADR-0005 §3 step 4: when the job raised and the result row could not
        # be written, PyatsJob.error is populated and the job re-raises so
        # RQ/core.Job is also marked failed.
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        pyats_job.full_clean()
        pyats_job.save()

        with (
            mock.patch(
                "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
                side_effect=RuntimeError("connection refused"),
            ),
            mock.patch(
                "netbox_pyats.models.PyatsSnapshot.full_clean",
                side_effect=RuntimeError("full_clean failed"),
            ),
        ):
            with pytest.raises(RuntimeError):
                jobs.capture_snapshot_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_ERROR
        assert "connection refused" in reloaded.error
        assert reloaded.related_snapshot_id is None
        assert reloaded.finished_at is not None

    def test_capture_raises_but_error_row_written_sets_fk(self):
        # ADR-0005 §3 step 3: when capture raises but the error-row snapshot
        # is written successfully, the PyatsJob is a plumbing-success with an
        # error *result row* — status=error, the snapshot FK is set, and
        # ``error`` stays empty (the row carries the failure detail). Mirrors
        # run_diff_job / run_compliance_job. The job still re-raises so RQ /
        # core.Job is marked failed.
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        pyats_job.full_clean()
        pyats_job.save()

        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            side_effect=RuntimeError("connection refused"),
        ):
            with pytest.raises(RuntimeError):
                jobs.capture_snapshot_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.related_snapshot_id is not None
        assert reloaded.error == ""
        assert reloaded.finished_at is not None
        # The error-row snapshot itself was written.
        snap = PyatsSnapshot.objects.get(pk=reloaded.related_snapshot_id)
        assert snap.status == SnapshotStatusChoices.STATUS_ERROR


class DiffJobPyatsJobPlumbingTest(TestCase):
    """ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="DJP01", slug="djp01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-DJ", slug="cisco-dj")
        cls.device_type = DeviceType.objects.create(model="C9300-DJ", slug="c9300-dj", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-DJ", slug="router-dj")
        cls.device = Device.objects.create(name="djrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _make_snapshot(self, data):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            data=data,
        )
        snap.full_clean()
        snap.save()
        return snap

    def _fake_job(self):
        return types.SimpleNamespace(object=self.device)

    def test_doesnotexist_writes_error_row_and_job_success(self):
        # ADR-0002: the DoesNotExist error row is a successful *job*
        # (the result row exists), even though the job re-raises so
        # core.Job is marked failed.
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_DIFF,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=self.device,
        )
        pyats_job.full_clean()
        pyats_job.save()

        from netbox_pyats.models import PyatsSnapshotDiff

        with pytest.raises(PyatsSnapshot.DoesNotExist):
            jobs.run_diff_job(
                self._fake_job(),
                before_id=999_001,
                after_id=999_002,
                pyats_job_id=pyats_job.pk,
            )

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.related_diff_id is not None
        diff_row = PyatsSnapshotDiff.objects.get(pk=reloaded.related_diff_id)
        assert diff_row.status == DiffStatusChoices.STATUS_ERROR
        assert diff_row.before_id is None
        assert diff_row.after_id is None


class BatchCaptureJobTest(TestCase):
    """``batch_capture_job`` summary + status transitions (Phase 5, ATW-16)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="BCJ01", slug="bcj01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-BC", slug="cisco-bc")
        cls.device_type = DeviceType.objects.create(model="C9300-BC", slug="c9300-bc", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-BC", slug="router-bc")
        cls.device_a = Device.objects.create(name="bcrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)
        cls.device_b = Device.objects.create(name="bcrtr02", site=cls.site, device_type=cls.device_type, role=cls.role)
        cls.device_c = Device.objects.create(name="bcrtr03", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _fake_job(self):
        return types.SimpleNamespace(object=None)

    def test_all_success_sets_success_with_supported_count(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        success_result = CaptureResult(
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            data={"config": {"hostname": "rtr"}, "config_raw": "hostname rtr\n"},
        )

        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            return_value=success_result,
        ):
            counts = jobs.batch_capture_job(
                self._fake_job(),
                device_ids=[self.device_a.pk, self.device_b.pk, self.device_c.pk],
                pyats_job_id=pyats_job.pk,
            )

        assert counts == {"supported": 3, "unsupported": 0, "errored": 0, "total": 3}
        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.summary == counts
        # Three snapshot rows were written.
        assert PyatsSnapshot.objects.filter(device__in=[self.device_a, self.device_b, self.device_c]).count() == 3

    def test_mixed_outcomes_sets_partial_with_counts(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        # Per-device results: A=success, B=unsupported, C=error (raised).
        results = {
            self.device_a.pk: CaptureResult(
                status=SnapshotStatusChoices.STATUS_SUCCESS,
                data={"config": {"hostname": "a"}, "config_raw": "hostname a\n"},
            ),
            self.device_b.pk: CaptureResult(
                status=SnapshotStatusChoices.STATUS_UNSUPPORTED,
                data={},
                warnings=["unsupported"],
            ),
        }

        def fake_capture(device, *, kind=SnapshotKindChoices.KIND_FULL):
            r = results.get(device.pk)
            if r is None:
                raise RuntimeError("device C exploded")
            return r

        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            side_effect=fake_capture,
        ):
            counts = jobs.batch_capture_job(
                self._fake_job(),
                device_ids=[self.device_a.pk, self.device_b.pk, self.device_c.pk],
                pyats_job_id=pyats_job.pk,
            )

        assert counts == {"supported": 1, "unsupported": 1, "errored": 1, "total": 3}
        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_PARTIAL
        assert reloaded.summary == counts

    def test_deleted_device_between_enqueue_and_run_is_skipped(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        success_result = CaptureResult(
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            data={"config": {"hostname": "x"}, "config_raw": "hostname x\n"},
        )

        # device_c is deleted between enqueue and run → silently skipped,
        # total reflects only the devices actually iterated.
        with mock.patch(
            "netbox_pyats.jobs.capture_snapshot_for_netbox_device",
            return_value=success_result,
        ):
            counts = jobs.batch_capture_job(
                self._fake_job(),
                device_ids=[self.device_a.pk, self.device_b.pk, 999_999],
                pyats_job_id=pyats_job.pk,
            )

        assert counts == {"supported": 2, "unsupported": 0, "errored": 0, "total": 2}
        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS


class DeviceBulkCaptureViewTest(TestCase):
    """The device-list bulk "PyATS capture" view renders its confirmation
    form (Phase 5, ATW-16). Guards against the regression where
    ``DeviceBulkCaptureView.template_name`` pointed at a template file that
    did not exist under ``netbox_pyats/templates/netbox_pyats/`` (PR #29
    review: changes_requested #1).
    """

    user_permissions = (
        "netbox_pyats.add_pyatsjob",
        "netbox_pyats.view_pyatsjob",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="BCV01", slug="bcv01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-BCV", slug="cisco-bcv")
        cls.device_type = DeviceType.objects.create(model="C9300-BCV", slug="c9300-bcv", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-BCV", slug="router-bcv")
        cls.device = Device.objects.create(name="bcvrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def test_get_confirmation_renders(self):
        from django.urls import reverse

        url = reverse("plugins:netbox_pyats:device_bulk_capture")
        response = self.client.get(url, {"pk": self.device.pk})
        self.assertEqual(response.status_code, 200)
        # The confirmation form renders the capture-kind select and echoes
        # the selected device pks as hidden inputs.
        self.assertContains(response, "PyATS Batch Capture")
        self.assertContains(response, f'value="{self.device.pk}"')
