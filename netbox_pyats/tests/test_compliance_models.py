"""Tests for :class:`netbox_pyats.models.PyatsGoldenConfig` and
:class:`netbox_pyats.models.PyatsComplianceRun` (Phase 4, ATW-15).

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (compliance engine +
golden-text parser) in matrix jobs that don't stand up NetBox.
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
from netbox_pyats.models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot


class PyatsGoldenConfigModelTest(TestCase):
    """Persistence and helper behavior of PyatsGoldenConfig."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="GLD01", slug="gld01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-G", slug="cisco-g")
        cls.device_type = DeviceType.objects.create(model="C9300-G", slug="c9300-g", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-G", slug="router-g")
        cls.device = Device.objects.create(name="goldrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def test_manual_golden_round_trips_config_text(self):
        golden = PyatsGoldenConfig(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n!\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0\n",
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
        )
        golden.full_clean()
        golden.save()
        reloaded = PyatsGoldenConfig.objects.get(pk=golden.pk)
        assert reloaded.config_text.startswith("hostname rtr01")
        assert reloaded.source == GoldenConfigSourceChoices.SOURCE_MANUAL
        assert reloaded.is_from_snapshot is False
        assert reloaded.source_snapshot is None

    def test_snapshot_sourced_golden_records_provenance(self):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {"hostname": "rtr01"}},
        )
        snap.full_clean()
        snap.save()
        golden = PyatsGoldenConfig(
            device=self.device,
            name="known-good",
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_SNAPSHOT,
            source_snapshot=snap,
        )
        golden.full_clean()
        golden.save()
        reloaded = PyatsGoldenConfig.objects.get(pk=golden.pk)
        assert reloaded.source == GoldenConfigSourceChoices.SOURCE_SNAPSHOT
        assert reloaded.is_from_snapshot is True
        assert reloaded.source_snapshot_id == snap.pk

    def test_str_includes_device_and_name(self):
        golden = PyatsGoldenConfig(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
        )
        golden.full_clean()
        golden.save()
        s = str(golden)
        assert "baseline" in s
        assert "goldrtr01" in s

    def test_unique_per_device_name_constraint(self):
        from django.db import IntegrityError

        PyatsGoldenConfig.objects.create(
            device=self.device,
            name="baseline",
            config_text="",
        )
        with pytest.raises(IntegrityError):
            PyatsGoldenConfig.objects.create(
                device=self.device,
                name="baseline",
                config_text="",
            )

    def test_two_goldens_same_device_different_names_allowed(self):
        PyatsGoldenConfig.objects.create(device=self.device, name="baseline", config_text="")
        PyatsGoldenConfig.objects.create(device=self.device, name="post-maint", config_text="")
        assert PyatsGoldenConfig.objects.filter(device=self.device).count() == 2


class PyatsComplianceRunModelTest(TestCase):
    """Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)."""

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="CMP01", slug="cmp01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-C", slug="cisco-c")
        cls.device_type = DeviceType.objects.create(model="C9300-C", slug="c9300-c", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-C", slug="router-c")
        cls.device = Device.objects.create(name="cmprtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

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

    def _make_golden(self, name="baseline", config_text="hostname rtr01\n"):
        golden = PyatsGoldenConfig(
            device=self.device,
            name=name,
            config_text=config_text,
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
        )
        golden.full_clean()
        golden.save()
        return golden

    def test_compliant_run_round_trips_jsonb(self):
        golden = self._make_golden()
        snap = self._make_snapshot({"config": {"hostname": "rtr01"}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff={"name": "root", "type": "dict", "status": "unchanged", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 1},
            parser_warnings=[],
            size_bytes=42,
        )
        run.full_clean()
        run.save()
        reloaded = PyatsComplianceRun.objects.get(pk=run.pk)
        assert reloaded.result == ComplianceResultChoices.RESULT_COMPLIANT
        assert reloaded.has_drift is False
        assert reloaded.summary == {"added": 0, "removed": 0, "changed": 0, "unchanged": 1}
        assert reloaded.size_bytes == 42
        assert reloaded.golden_id == golden.pk
        assert reloaded.snapshot_id == snap.pk
        assert reloaded.device_id == self.device.pk

    def test_drift_run_round_trips_jsonb(self):
        golden = self._make_golden()
        snap = self._make_snapshot({"config": {"hostname": "rtr02"}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_DRIFT,
            diff={"name": "root", "type": "dict", "status": "changed", "children": {}},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
        )
        run.full_clean()
        run.save()
        reloaded = PyatsComplianceRun.objects.get(pk=run.pk)
        assert reloaded.result == ComplianceResultChoices.RESULT_DRIFT
        assert reloaded.has_drift is True

    def test_error_run_records_warnings(self):
        golden = self._make_golden(config_text="")
        snap = self._make_snapshot({"config": {}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            parser_warnings=["golden config is empty; cannot run compliance"],
        )
        run.full_clean()
        run.save()
        reloaded = PyatsComplianceRun.objects.get(pk=run.pk)
        assert reloaded.result == ComplianceResultChoices.RESULT_ERROR
        assert reloaded.has_warnings is True
        assert "golden config is empty" in reloaded.parser_warnings[0]

    def test_str_includes_device_and_result(self):
        golden = self._make_golden()
        snap = self._make_snapshot({"config": {}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_DRIFT,
            diff={},
            summary={"added": 0, "removed": 0, "changed": 1, "unchanged": 0},
        )
        run.full_clean()
        run.save()
        s = str(run)
        assert "cmprtr01" in s
        assert "Drift" in s

    def test_get_result_color_maps_each_result(self):
        assert PyatsComplianceRun(result=ComplianceResultChoices.RESULT_COMPLIANT).get_result_color() == "success"
        assert PyatsComplianceRun(result=ComplianceResultChoices.RESULT_DRIFT).get_result_color() == "warning"
        assert PyatsComplianceRun(result=ComplianceResultChoices.RESULT_ERROR).get_result_color() == "danger"

    def test_has_drift_reflects_summary(self):
        golden = self._make_golden()
        snap = self._make_snapshot({"config": {}})
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 3},
        )
        assert run.has_drift is False
        run.summary = {"added": 1, "removed": 0, "changed": 0, "unchanged": 2}
        assert run.has_drift is True

    def test_recent_compliance_runs_ordered_newest_first(self):
        import time

        golden = self._make_golden()
        snap = self._make_snapshot({"config": {}})
        for _ in range(3):
            run = PyatsComplianceRun(
                device=self.device,
                golden=golden,
                snapshot=snap,
                result=ComplianceResultChoices.RESULT_COMPLIANT,
                diff={},
                summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 0},
            )
            run.full_clean()
            run.save()
            time.sleep(0.01)  # ensure created differs
        qs = list(PyatsComplianceRun.objects.filter(device=self.device).order_by("-created"))
        assert len(qs) == 3
        assert qs[0].created >= qs[1].created >= qs[2].created
