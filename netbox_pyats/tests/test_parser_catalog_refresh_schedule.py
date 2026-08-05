"""Tests for the PyatsParserCatalogRefreshSchedule model + dispatcher (ATW-581).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable. Covers:

- PyatsParserCatalogRefreshSchedule model persistence (singleton row).
- run_parser_catalog_refresh_schedules_job dispatches a refresh when the
  schedule is enabled, skips when disabled, and updates last_run_at in both
  cases (the dispatcher touches last_run_at even on a skip so the operator
  can see the dispatcher is alive).
- next_run_at is populated from the NetBox Job row's interval for recurring
  runs and left blank for one-shot runs (ATW-610).
"""

from datetime import timedelta
from unittest import mock

import pytest

pytest.importorskip("netbox")

from utilities.testing import TestCase

from netbox_pyats.models import PyatsParserCatalogRefreshSchedule


class PyatsParserCatalogRefreshScheduleModelTest(TestCase):
    """Persistence for the singleton refresh-schedule model (ATW-581)."""

    def test_round_trips_disabled(self):
        sched = PyatsParserCatalogRefreshSchedule(pk=1, enabled=False)
        sched.full_clean()
        sched.save()
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.enabled is False
        assert reloaded.last_run_at is None
        assert reloaded.next_run_at is None

    def test_round_trips_enabled(self):
        sched = PyatsParserCatalogRefreshSchedule(pk=1, enabled=True)
        sched.full_clean()
        sched.save()
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.enabled is True


class RunParserCatalogRefreshSchedulesJobTest(TestCase):
    """run_parser_catalog_refresh_schedules_job dispatch logic (ATW-581)."""

    def _make_schedule(self, enabled):
        sched = PyatsParserCatalogRefreshSchedule(pk=1, enabled=enabled)
        sched.full_clean()
        sched.save()
        return sched

    def test_dispatches_when_enabled(self):
        sched = self._make_schedule(enabled=True)
        with mock.patch("netbox_pyats.jobs.enqueue_refresh_parser_catalog") as mock_enqueue:

            class FakeJob:
                pk = 42

            mock_enqueue.return_value = FakeJob()
            from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job

            result = run_parser_catalog_refresh_schedules_job(job=mock.Mock())
        mock_enqueue.assert_called_once_with(user=None)
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        # mock.Mock() has no interval attr → one-shot run, next_run_at stays blank.
        assert reloaded.next_run_at is None
        assert result["dispatched"] == 1
        assert result["skipped"] == 0

    def test_skips_when_disabled(self):
        sched = self._make_schedule(enabled=False)
        with mock.patch("netbox_pyats.jobs.enqueue_refresh_parser_catalog") as mock_enqueue:
            from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job

            result = run_parser_catalog_refresh_schedules_job(job=mock.Mock())
        mock_enqueue.assert_not_called()
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert result["dispatched"] == 0
        assert result["skipped"] == 1

    def test_creates_row_lazily_when_missing(self):
        # No schedule row exists. The dispatcher's get_or_create(pk=1) path
        # creates one with enabled=False, so a missing row is a skip (not a
        # crash) and the row exists after the run.
        assert not PyatsParserCatalogRefreshSchedule.objects.exists()
        with mock.patch("netbox_pyats.jobs.enqueue_refresh_parser_catalog") as mock_enqueue:
            from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job

            result = run_parser_catalog_refresh_schedules_job(job=mock.Mock())
        mock_enqueue.assert_not_called()
        assert result["dispatched"] == 0
        assert result["skipped"] == 1
        assert PyatsParserCatalogRefreshSchedule.objects.count() == 1

    def test_next_run_at_set_from_job_interval_when_enabled(self):
        """Recurring enabled run → next_run_at = last_run_at + interval (ATW-610)."""
        sched = self._make_schedule(enabled=True)
        with mock.patch("netbox_pyats.jobs.enqueue_refresh_parser_catalog") as mock_enqueue:
            mock_enqueue.return_value = mock.Mock(pk=42)
            from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job

            result = run_parser_catalog_refresh_schedules_job(job=mock.Mock(interval=1440))
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert reloaded.next_run_at is not None
        assert reloaded.next_run_at == reloaded.last_run_at + timedelta(minutes=1440)
        assert result["dispatched"] == 1

    def test_next_run_at_set_from_job_interval_when_disabled(self):
        """Recurring disabled-skip → next_run_at still set from interval (ATW-610)."""
        sched = self._make_schedule(enabled=False)
        with mock.patch("netbox_pyats.jobs.enqueue_refresh_parser_catalog") as mock_enqueue:
            from netbox_pyats.jobs import run_parser_catalog_refresh_schedules_job

            result = run_parser_catalog_refresh_schedules_job(job=mock.Mock(interval=15))
        mock_enqueue.assert_not_called()
        reloaded = PyatsParserCatalogRefreshSchedule.objects.get(pk=sched.pk)
        assert reloaded.last_run_at is not None
        assert reloaded.next_run_at == reloaded.last_run_at + timedelta(minutes=15)
        assert result["skipped"] == 1
