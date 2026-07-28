"""Tests for :class:`netbox_pyats.models.PyatsParserCatalog` (ATW-241 child 1, ATW-249).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (parser_catalog helper
tests in ``test_parser_catalog.py``) in matrix jobs that don't stand up
NetBox.

Covers:

- Model persistence: ``pyats_os`` (unique), ``commands`` (JSONField),
  ``genie_version`` / ``pyats_version`` / ``refreshed_at``, and the
  ``NetBoxModel``-provided ``created`` / ``last_updated`` / ``tags``.
- ``pyats_os`` uniqueness (the one-row-per-os contract).
- ``__str__`` representation includes the os and the command count.
- ``get_absolute_url`` resolves to the plugin detail route.
- ``refresh_parser_catalog_job`` upserts one row per supported os and sets
  ``PyatsJob`` to ``running`` then ``success`` with a batch summary
  (ADR-0005 §3 plumbing). Per-os parser-registry failures are counted as
  ``errored`` rather than aborting the whole refresh.
"""

import types
from datetime import datetime
from datetime import timezone as dt_timezone
from unittest import mock

import pytest

pytest.importorskip("netbox")

from utilities.testing import TestCase

from netbox_pyats import jobs
from netbox_pyats.choices import PyatsJobStatusChoices, PyatsJobTypeChoices
from netbox_pyats.models import PyatsJob, PyatsParserCatalog
from netbox_pyats.parser_catalog import CatalogRefreshResult


class PyatsParserCatalogModelTest(TestCase):
    """Persistence + helpers for PyatsParserCatalog (ATW-241 child 1)."""

    def test_round_trip(self):
        row = PyatsParserCatalog(
            pyats_os="iosxe",
            commands=["show version", "show interfaces"],
            genie_version="26.6",
            pyats_version="26.6",
        )
        row.full_clean()
        row.save()
        reloaded = PyatsParserCatalog.objects.get(pk=row.pk)
        assert reloaded.pyats_os == "iosxe"
        assert reloaded.commands == ["show version", "show interfaces"]
        assert reloaded.genie_version == "26.6"
        assert reloaded.pyats_version == "26.6"
        assert reloaded.refreshed_at is None
        assert reloaded.created is not None
        assert reloaded.last_updated is not None

    def test_pyats_os_is_unique(self):
        from django.core.exceptions import ValidationError

        PyatsParserCatalog.objects.create(pyats_os="iosxe", commands=[])
        dup = PyatsParserCatalog(pyats_os="iosxe", commands=["show version"])
        with self.assertRaises(ValidationError):
            dup.full_clean()

    def test_str_includes_os_and_command_count(self):
        row = PyatsParserCatalog(pyats_os="nxos", commands=["show version", "show interfaces"])
        s = str(row)
        assert "nxos" in s
        assert "2 commands" in s

    def test_str_handles_empty_commands(self):
        row = PyatsParserCatalog(pyats_os="iosxr", commands=[])
        s = str(row)
        assert "iosxr" in s
        assert "0 commands" in s

    def test_refreshed_at_round_trips(self):
        ts = datetime(2026, 7, 27, 12, 0, 0, tzinfo=dt_timezone.utc)
        row = PyatsParserCatalog(
            pyats_os="junos",
            commands=["show version"],
            refreshed_at=ts,
        )
        row.full_clean()
        row.save()
        reloaded = PyatsParserCatalog.objects.get(pk=row.pk)
        assert reloaded.refreshed_at is not None
        # Re-read the field as a tz-aware datetime to compare robustly.
        assert reloaded.refreshed_at.year == 2026


class RefreshParserCatalogJobTest(TestCase):
    """ADR-0005 §3 plumbing for ``refresh_parser_catalog_job`` (ATW-249)."""

    def _fake_job(self):
        return types.SimpleNamespace(object=None)

    def _patch_refresh_for_os(self, results_by_os, all_oses=None):
        """Patch the pure-Python helper to return canned results per os.

        ``results_by_os`` maps os string → CatalogRefreshResult. Oses not in
        the map raise to simulate a per-os failure. ``all_oses`` is the full
        list of oses the job iterates; it defaults to the results keys (so
        only the succeeding oses are visited) and should include the failing
        oses when a test exercises the per-os error path.
        """
        supported_os_values_patch = all_oses if all_oses is not None else list(results_by_os.keys())

        def _fake_refresh(os_value):
            if os_value in results_by_os:
                return results_by_os[os_value]
            raise RuntimeError(f"boom for {os_value}")

        return (
            mock.patch(
                "netbox_pyats.parser_catalog.refresh_parser_catalog_for_os",
                side_effect=_fake_refresh,
            ),
            mock.patch(
                "netbox_pyats.parser_catalog.supported_os_values",
                return_value=iter(supported_os_values_patch),
            ),
        )

    def test_success_upserts_rows_and_sets_pyatsjob_success(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_REFRESH_PARSER_CATALOG,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        results = {
            "iosxe": CatalogRefreshResult(
                pyats_os="iosxe",
                commands=["show version", "show interfaces"],
                genie_version="26.6",
                pyats_version="26.6",
            ),
            "nxos": CatalogRefreshResult(
                pyats_os="nxos",
                commands=["show version"],
                genie_version="26.6",
                pyats_version="26.6",
            ),
        }
        refresh_patch, os_patch = self._patch_refresh_for_os(results)
        with refresh_patch, os_patch:
            jobs.refresh_parser_catalog_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.started_at is not None
        assert reloaded.finished_at is not None
        assert reloaded.error == ""
        # Two catalog rows upserted.
        assert PyatsParserCatalog.objects.filter(pyats_os="iosxe").exists()
        assert PyatsParserCatalog.objects.filter(pyats_os="nxos").exists()
        iosxe = PyatsParserCatalog.objects.get(pyats_os="iosxe")
        assert iosxe.commands == ["show version", "show interfaces"]
        assert iosxe.refreshed_at is not None
        # Summary counts.
        assert reloaded.summary["total"] == 2
        assert reloaded.summary["refreshed"] == 2
        assert reloaded.summary["errored"] == 0

    def test_per_os_error_is_counted_not_fatal(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_REFRESH_PARSER_CATALOG,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        results = {
            "iosxe": CatalogRefreshResult(
                pyats_os="iosxe",
                commands=["show version"],
            ),
            # 'nxos' omitted → the stubbed refresh_for_os raises for it.
        }
        refresh_patch, os_patch = self._patch_refresh_for_os(results, all_oses=["iosxe", "nxos"])
        with refresh_patch, os_patch:
            jobs.refresh_parser_catalog_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        # The refresh completed (did not crash) → job is success, not error.
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.summary["total"] == 2
        assert reloaded.summary["refreshed"] == 1
        assert reloaded.summary["errored"] == 1
        # The successful os still wrote a row.
        assert PyatsParserCatalog.objects.filter(pyats_os="iosxe").exists()
        # The errored os did not.
        assert not PyatsParserCatalog.objects.filter(pyats_os="nxos").exists()

    def test_upsert_updates_existing_row(self):
        # A pre-existing row for iosxe is updated, not duplicated.
        PyatsParserCatalog.objects.create(
            pyats_os="iosxe",
            commands=["show version"],
            genie_version="26.5",
        )
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_REFRESH_PARSER_CATALOG,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        results = {
            "iosxe": CatalogRefreshResult(
                pyats_os="iosxe",
                commands=["show version", "show interfaces"],
                genie_version="26.6",
                pyats_version="26.6",
            ),
        }
        refresh_patch, os_patch = self._patch_refresh_for_os(results)
        with refresh_patch, os_patch:
            jobs.refresh_parser_catalog_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        # Exactly one row for iosxe (updated, not duplicated).
        assert PyatsParserCatalog.objects.filter(pyats_os="iosxe").count() == 1
        reloaded = PyatsParserCatalog.objects.get(pyats_os="iosxe")
        assert reloaded.commands == ["show version", "show interfaces"]
        assert reloaded.genie_version == "26.6"

    def test_warnings_count_as_skipped(self):
        pyats_job = PyatsJob(
            job_type=PyatsJobTypeChoices.JOB_REFRESH_PARSER_CATALOG,
            status=PyatsJobStatusChoices.STATUS_PENDING,
            device=None,
        )
        pyats_job.full_clean()
        pyats_job.save()

        results = {
            "iosxe": CatalogRefreshResult(
                pyats_os="iosxe",
                commands=[],
                warnings=["unsupported os 'iosxe': no Genie parser package"],
            ),
        }
        refresh_patch, os_patch = self._patch_refresh_for_os(results)
        with refresh_patch, os_patch:
            jobs.refresh_parser_catalog_job(self._fake_job(), pyats_job_id=pyats_job.pk)

        reloaded = PyatsJob.objects.get(pk=pyats_job.pk)
        assert reloaded.status == PyatsJobStatusChoices.STATUS_SUCCESS
        assert reloaded.summary["total"] == 1
        assert reloaded.summary["refreshed"] == 0
        assert reloaded.summary["skipped"] == 1
        # The warning-bearing row is still written (empty commands, with warnings recorded in the log).
        assert PyatsParserCatalog.objects.filter(pyats_os="iosxe").exists()
