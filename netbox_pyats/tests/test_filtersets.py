"""Tests for the ``has_changes`` / ``has_warnings`` / ``has_drift``
BooleanFilter method filters on ``PyatsSnapshotDiffFilterSet`` and
``PyatsComplianceRunFilterSet`` (ATW-917).

The ``has_*`` attributes are model **properties** (not model fields), so the
FilterForm checkboxes rendered but did nothing until these method filters were
declared. These tests verify the SQL-level filter matches the Python property
semantics exactly.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python unit lane without NetBox.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from utilities.testing import TestCase

from netbox_pyats.choices import (
    ComplianceResultChoices,
    GoldenConfigSourceChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from netbox_pyats.filtersets import PyatsComplianceRunFilterSet, PyatsSnapshotDiffFilterSet
from netbox_pyats.models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot, PyatsSnapshotDiff


class _SharedFixtures:
    """Shared setUpTestData for both FilterSet test classes."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="FLT01", slug="flt01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-FLT", slug="cisco-flt")
        cls.dt = DeviceType.objects.create(model="C9300-FLT", slug="c9300-flt", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-FLT", slug="router-flt")
        cls.device = Device.objects.create(
            name="flt_rtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
        )

    def _make_snapshot(self, data=None):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data=data or {},
        )
        snap.full_clean()
        snap.save()
        return snap


class PyatsSnapshotDiffFilterSetTest(_SharedFixtures, TestCase):
    """``has_changes`` / ``has_warnings`` method filters on
    :class:`PyatsSnapshotDiffFilterSet` (ATW-917)."""

    def _make_diff(self, summary, parser_warnings=None):
        before = self._make_snapshot({"config": {"hostname": "before"}})
        after = self._make_snapshot({"config": {"hostname": "after"}})
        diff = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status="success",
            diff={},
            summary=summary,
            parser_warnings=parser_warnings if parser_warnings is not None else [],
            size_bytes=1,
        )
        diff.full_clean()
        diff.save()
        return diff

    def test_has_changes_true_filters_only_changed_rows(self):
        changed = self._make_diff(summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0})
        unchanged = self._make_diff(summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 2})
        qs = PyatsSnapshotDiffFilterSet({"has_changes": True}, queryset=PyatsSnapshotDiff.objects.all()).qs
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(changed.id, ids)
        self.assertNotIn(unchanged.id, ids)

    def test_has_changes_added_count_also_matches(self):
        added = self._make_diff(summary={"added": 1, "removed": 0, "changed": 0, "unchanged": 1})
        qs = PyatsSnapshotDiffFilterSet({"has_changes": True}, queryset=PyatsSnapshotDiff.objects.all()).qs
        self.assertIn(added.id, set(qs.values_list("id", flat=True)))

    def test_has_changes_removed_count_also_matches(self):
        removed = self._make_diff(summary={"added": 0, "removed": 2, "changed": 0, "unchanged": 0})
        qs = PyatsSnapshotDiffFilterSet({"has_changes": True}, queryset=PyatsSnapshotDiff.objects.all()).qs
        self.assertIn(removed.id, set(qs.values_list("id", flat=True)))

    def test_has_changes_false_returns_all_rows(self):
        self._make_diff(summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0})
        self._make_diff(summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 2})
        qs = PyatsSnapshotDiffFilterSet({"has_changes": False}, queryset=PyatsSnapshotDiff.objects.all()).qs
        self.assertEqual(qs.count(), 2)

    def test_has_warnings_true_filters_only_rows_with_warnings(self):
        with_warns = self._make_diff(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            parser_warnings=["parse error on line 3"],
        )
        without_warns = self._make_diff(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            parser_warnings=[],
        )
        qs = PyatsSnapshotDiffFilterSet({"has_warnings": True}, queryset=PyatsSnapshotDiff.objects.all()).qs
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(with_warns.id, ids)
        self.assertNotIn(without_warns.id, ids)

    def test_has_warnings_false_returns_all_rows(self):
        self._make_diff(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            parser_warnings=["warn"],
        )
        self._make_diff(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            parser_warnings=[],
        )
        qs = PyatsSnapshotDiffFilterSet({"has_warnings": False}, queryset=PyatsSnapshotDiff.objects.all()).qs
        self.assertEqual(qs.count(), 2)


class PyatsComplianceRunFilterSetTest(_SharedFixtures, TestCase):
    """``has_drift`` / ``has_warnings`` method filters on
    :class:`PyatsComplianceRunFilterSet` (ATW-917)."""

    _golden_counter = 0

    def _make_golden(self):
        self._golden_counter += 1
        golden = PyatsGoldenConfig(
            device=self.device,
            name=f"baseline-{self._golden_counter}",
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
        )
        golden.full_clean()
        golden.save()
        return golden

    def _make_run(self, summary, parser_warnings=None, result=None):
        golden = self._make_golden()
        snap = self._make_snapshot({"config": {"hostname": "rtr01"}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=result or ComplianceResultChoices.RESULT_COMPLIANT,
            diff={},
            summary=summary,
            parser_warnings=parser_warnings if parser_warnings is not None else [],
            size_bytes=1,
        )
        run.full_clean()
        run.save()
        return run

    def test_has_drift_true_filters_only_drift_rows(self):
        drift = self._make_run(
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
            result=ComplianceResultChoices.RESULT_DRIFT,
        )
        compliant = self._make_run(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
        )
        qs = PyatsComplianceRunFilterSet({"has_drift": True}, queryset=PyatsComplianceRun.objects.all()).qs
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(drift.id, ids)
        self.assertNotIn(compliant.id, ids)

    def test_has_drift_added_count_also_matches(self):
        added = self._make_run(
            summary={"added": 2, "removed": 0, "changed": 0, "unchanged": 1},
            result=ComplianceResultChoices.RESULT_DRIFT,
        )
        qs = PyatsComplianceRunFilterSet({"has_drift": True}, queryset=PyatsComplianceRun.objects.all()).qs
        self.assertIn(added.id, set(qs.values_list("id", flat=True)))

    def test_has_drift_false_returns_all_rows(self):
        self._make_run(
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
            result=ComplianceResultChoices.RESULT_DRIFT,
        )
        self._make_run(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
        )
        qs = PyatsComplianceRunFilterSet({"has_drift": False}, queryset=PyatsComplianceRun.objects.all()).qs
        self.assertEqual(qs.count(), 2)

    def test_has_warnings_true_filters_only_rows_with_warnings(self):
        with_warns = self._make_run(
            summary={},
            parser_warnings=["golden config is empty"],
            result=ComplianceResultChoices.RESULT_ERROR,
        )
        without_warns = self._make_run(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
        )
        qs = PyatsComplianceRunFilterSet({"has_warnings": True}, queryset=PyatsComplianceRun.objects.all()).qs
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(with_warns.id, ids)
        self.assertNotIn(without_warns.id, ids)

    def test_has_warnings_false_returns_all_rows(self):
        self._make_run(
            summary={},
            parser_warnings=["warn"],
            result=ComplianceResultChoices.RESULT_ERROR,
        )
        self._make_run(
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
        )
        qs = PyatsComplianceRunFilterSet({"has_warnings": False}, queryset=PyatsComplianceRun.objects.all()).qs
        self.assertEqual(qs.count(), 2)
