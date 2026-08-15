"""Tests for :class:`netbox_pyats.models.PyatsCredential`.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (crypto + testbed) in
matrix jobs that don't stand up NetBox.
"""

import pytest

pytest.importorskip("netbox")

from django.test import override_settings
from utilities.testing import TestCase

from netbox_pyats import crypto
from netbox_pyats.choices import CredentialProtocolChoices, CredentialScopeChoices
from netbox_pyats.models import PyatsCredential, PyatsSnapshot


class PyatsCredentialModelTest(TestCase):
    """Field-level encryption and validation behavior of PyatsCredential."""

    def test_password_round_trip_via_setters(self):
        cred = PyatsCredential(name="rtr01-ssh", username="admin")
        cred.set_password("hunter2")
        cred.set_enable_secret("enablepass")
        cred.save()
        # Stored value is ciphertext, not plaintext.
        self.assertNotEqual(cred.password, "hunter2")
        self.assertNotEqual(cred.enable_secret, "enablepass")
        self.assertTrue(crypto.is_encrypted_token(cred.password))
        self.assertTrue(crypto.is_encrypted_token(cred.enable_secret))
        # Decrypts back to plaintext.
        self.assertEqual(cred.get_password(), "hunter2")
        self.assertEqual(cred.get_enable_secret(), "enablepass")

    def test_empty_secrets_round_trip(self):
        cred = PyatsCredential(name="rtr01-ssh", username="admin")
        cred.set_password("")
        cred.set_enable_secret("")
        self.assertEqual(cred.password, "")
        self.assertEqual(cred.enable_secret, "")
        self.assertEqual(cred.get_password(), "")
        self.assertEqual(cred.get_enable_secret(), "")

    def test_str_representation_includes_device_name(self):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site

        site = Site.objects.create(name="AMS01", slug="ams01")
        mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        dt = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=mfr)
        role = DeviceRole.objects.create(name="Router", slug="router")
        dev = Device.objects.create(name="rtr01", site=site, device_type=dt, role=role)

        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", scope=CredentialScopeChoices.SCOPE_DEVICE, device=dev, username="admin"
        )
        self.assertIn("rtr01-ssh", str(cred))
        self.assertIn("rtr01", str(cred))

    def test_global_scope_str_representation(self):
        cred = PyatsCredential.objects.create(
            name="lab-shared", scope=CredentialScopeChoices.SCOPE_GLOBAL, device=None, username="lab"
        )
        self.assertIn("global", str(cred))

    def test_device_scope_requires_device(self):
        from django.core.exceptions import ValidationError

        cred = PyatsCredential(
            name="no-device", scope=CredentialScopeChoices.SCOPE_DEVICE, device=None, username="admin"
        )
        with self.assertRaises(ValidationError):
            cred.full_clean()

    def test_global_scope_rejects_device(self):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
        from django.core.exceptions import ValidationError

        site = Site.objects.create(name="AMS02", slug="ams02")
        mfr = Manufacturer.objects.create(name="Cisco2", slug="cisco2")
        dt = DeviceType.objects.create(model="Catalyst 9300-2", slug="catalyst-9300-2", manufacturer=mfr)
        role = DeviceRole.objects.create(name="Router2", slug="router2")
        dev = Device.objects.create(name="rtr02", site=site, device_type=dt, role=role)

        cred = PyatsCredential(
            name="bad-global", scope=CredentialScopeChoices.SCOPE_GLOBAL, device=dev, username="admin"
        )
        with self.assertRaises(ValidationError):
            cred.full_clean()

    def test_unique_per_device_name_constraint(self):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
        from django.db import IntegrityError

        site = Site.objects.create(name="AMS03", slug="ams03")
        mfr = Manufacturer.objects.create(name="Cisco3", slug="cisco3")
        dt = DeviceType.objects.create(model="Catalyst 9300-3", slug="catalyst-9300-3", manufacturer=mfr)
        role = DeviceRole.objects.create(name="Router3", slug="router3")
        dev = Device.objects.create(name="rtr03", site=site, device_type=dt, role=role)

        PyatsCredential.objects.create(
            name="rtr03-ssh", scope=CredentialScopeChoices.SCOPE_DEVICE, device=dev, username="admin"
        )
        with self.assertRaises(IntegrityError):
            PyatsCredential.objects.create(
                name="rtr03-ssh", scope=CredentialScopeChoices.SCOPE_DEVICE, device=dev, username="admin"
            )

    def test_default_protocol_is_ssh_and_port_22(self):
        cred = PyatsCredential(name="rtr-default", username="admin")
        cred.save()
        self.assertEqual(cred.protocol, CredentialProtocolChoices.PROTOCOL_SSH)
        self.assertEqual(cred.ssh_port, 22)

    def test_get_password_raises_invalid_token_on_wrong_key(self):
        # CR-2 (ATW-815): a credential encrypted under one key cannot be
        # decrypted under another. The model accessors (get_password /
        # get_enable_secret) must surface the underlying InvalidToken so
        # the testbed builder can catch it and raise CredentialDecryptError
        # with provenance (currently untested before this change).
        from cryptography.fernet import Fernet, InvalidToken

        from netbox_pyats import crypto

        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        cred = PyatsCredential(name="rtr-wrong-key", username="admin")
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"credential_key": key1.decode()}}):
            cred.set_password("hunter2")
            cred.set_enable_secret("enablepass")
        # Rotate the key without re-keying the credential: decrypt must fail.
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"credential_key": key2.decode()}}):
            with self.assertRaises(InvalidToken):
                cred.get_password()
            with self.assertRaises(InvalidToken):
                cred.get_enable_secret()
        # Sanity: decrypts fine under the original key.
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"credential_key": key1.decode()}}):
            self.assertEqual(cred.get_password(), "hunter2")
            self.assertEqual(cred.get_enable_secret(), "enablepass")
        # The domain error class is importable from crypto for the call site.
        self.assertTrue(issubclass(crypto.CredentialDecryptError, Exception))


class PyatsCredentialFernetCleanTest(TestCase):
    """ATW-907 H1: ``PyatsCredential.clean()`` rejects plaintext ciphertext fields."""

    def test_clean_rejects_plaintext_password(self):
        from django.core.exceptions import ValidationError

        cred = PyatsCredential(name="plain-pw", username="admin", scope=CredentialScopeChoices.SCOPE_GLOBAL)
        cred.password = "hunter2"  # direct assignment, not via set_password
        with self.assertRaises(ValidationError) as cm:
            cred.full_clean()
        self.assertIn("password", cm.exception.message_dict)

    def test_clean_rejects_plaintext_enable_secret(self):
        from django.core.exceptions import ValidationError

        cred = PyatsCredential(name="plain-enable", username="admin", scope=CredentialScopeChoices.SCOPE_GLOBAL)
        cred.enable_secret = "enablepass"  # direct assignment
        with self.assertRaises(ValidationError) as cm:
            cred.full_clean()
        self.assertIn("enable_secret", cm.exception.message_dict)

    def test_clean_accepts_fernet_ciphertext_password(self):
        cred = PyatsCredential(name="cipher-pw", username="admin", scope=CredentialScopeChoices.SCOPE_GLOBAL)
        cred.set_password("hunter2")
        cred.set_enable_secret("enablepass")
        cred.full_clean()  # no raise — ciphertext is valid

    def test_clean_accepts_empty_secrets(self):
        cred = PyatsCredential(name="empty-secrets", username="admin", scope=CredentialScopeChoices.SCOPE_GLOBAL)
        cred.password = ""
        cred.enable_secret = ""
        cred.full_clean()  # no raise — blank=True round-trips to ""


class PyatsSnapshotDiffCleanTest(TestCase):
    """ATW-907 L1: ``PyatsSnapshotDiff.clean()`` cross-field device invariant."""

    @classmethod
    def setUpTestData(cls):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site

        cls.site = Site.objects.create(name="DC01", slug="dc01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-D", slug="cisco-d")
        cls.dt = DeviceType.objects.create(model="C9300-D", slug="c9300-d", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-D", slug="router-d")
        cls.device = Device.objects.create(name="diffrtr01", site=cls.site, device_type=cls.dt, role=cls.role)
        cls.other_device = Device.objects.create(name="diffrtr02", site=cls.site, device_type=cls.dt, role=cls.role)

    def _make_snapshot(self, device, data=None):
        from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices

        snap = PyatsSnapshot(
            device=device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data=data or {"config": {"hostname": str(device)}},
        )
        snap.full_clean()
        snap.save()
        return snap

    def test_clean_accepts_same_device_before(self):
        from netbox_pyats.models import PyatsSnapshotDiff

        snap = self._make_snapshot(self.device)
        diff = PyatsSnapshotDiff(
            device=self.device,
            before=snap,
            after=snap,
            status="success",
            diff={},
            summary={},
        )
        diff.full_clean()  # no raise

    def test_clean_rejects_cross_device_before(self):
        from django.core.exceptions import ValidationError

        from netbox_pyats.models import PyatsSnapshotDiff

        # A before snapshot from a different device than the diff row's device.
        other_snap = self._make_snapshot(self.other_device)
        diff = PyatsSnapshotDiff(
            device=self.device,
            before=other_snap,
            after=None,
            status="success",
            diff={},
            summary={},
        )
        with self.assertRaises(ValidationError) as cm:
            diff.full_clean()
        self.assertIn("before", cm.exception.message_dict)

    def test_clean_skips_check_for_error_status(self):
        # ATW-68: the job's device-mismatch error-row path persists the
        # mismatched row as status="error" via full_clean(). clean() must not
        # reject it.
        from netbox_pyats.models import PyatsSnapshotDiff

        other_snap = self._make_snapshot(self.other_device)
        diff = PyatsSnapshotDiff(
            device=self.device,
            before=other_snap,
            after=None,
            status="error",
            diff={},
            summary={},
            parser_warnings=["device mismatch"],
        )
        diff.full_clean()  # no raise — error rows are exempt

    def test_clean_skips_check_for_null_before(self):
        # ATW-68: a diff whose before snapshot was deleted writes before=None.
        from netbox_pyats.models import PyatsSnapshotDiff

        diff = PyatsSnapshotDiff(
            device=self.device,
            before=None,
            after=None,
            status="error",
            diff={},
            summary={},
            parser_warnings=["before snapshot missing"],
        )
        diff.full_clean()  # no raise


class PyatsGoldenConfigCleanTest(TestCase):
    """ATW-907 L1: ``PyatsGoldenConfig.clean()`` source_snapshot device invariant."""

    @classmethod
    def setUpTestData(cls):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site

        cls.site = Site.objects.create(name="GC01", slug="gc01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-GC", slug="cisco-gc")
        cls.dt = DeviceType.objects.create(model="C9300-GC", slug="c9300-gc", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-GC", slug="router-gc")
        cls.device = Device.objects.create(name="goldrtr01", site=cls.site, device_type=cls.dt, role=cls.role)
        cls.other_device = Device.objects.create(name="goldrtr02", site=cls.site, device_type=cls.dt, role=cls.role)

    def _make_snapshot(self, device):
        from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices

        snap = PyatsSnapshot(
            device=device,
            kind=SnapshotKindChoices.KIND_CONFIG,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {"hostname": str(device)}},
        )
        snap.full_clean()
        snap.save()
        return snap

    def test_clean_accepts_same_device_source_snapshot(self):
        from netbox_pyats.choices import GoldenConfigSourceChoices
        from netbox_pyats.models import PyatsGoldenConfig

        snap = self._make_snapshot(self.device)
        golden = PyatsGoldenConfig(
            device=self.device,
            name="baseline",
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_SNAPSHOT,
            source_snapshot=snap,
        )
        golden.full_clean()  # no raise

    def test_clean_rejects_cross_device_source_snapshot(self):
        from django.core.exceptions import ValidationError

        from netbox_pyats.choices import GoldenConfigSourceChoices
        from netbox_pyats.models import PyatsGoldenConfig

        other_snap = self._make_snapshot(self.other_device)
        golden = PyatsGoldenConfig(
            device=self.device,
            name="bad-snapshot",
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_SNAPSHOT,
            source_snapshot=other_snap,
        )
        with self.assertRaises(ValidationError) as cm:
            golden.full_clean()
        self.assertIn("source_snapshot", cm.exception.message_dict)

    def test_clean_accepts_null_source_snapshot(self):
        from netbox_pyats.choices import GoldenConfigSourceChoices
        from netbox_pyats.models import PyatsGoldenConfig

        golden = PyatsGoldenConfig(
            device=self.device,
            name="manual",
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
            source_snapshot=None,
        )
        golden.full_clean()  # no raise


class PyatsComplianceRunCleanTest(TestCase):
    """ATW-907 L1: ``PyatsComplianceRun.clean()`` cross-field device invariant."""

    @classmethod
    def setUpTestData(cls):
        from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site

        cls.site = Site.objects.create(name="CR01", slug="cr01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-CR", slug="cisco-cr")
        cls.dt = DeviceType.objects.create(model="C9300-CR", slug="c9300-cr", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-CR", slug="router-cr")
        cls.device = Device.objects.create(name="cmprtr01", site=cls.site, device_type=cls.dt, role=cls.role)
        cls.other_device = Device.objects.create(name="cmprtr02", site=cls.site, device_type=cls.dt, role=cls.role)

    def _make_snapshot(self, device):
        from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices

        snap = PyatsSnapshot(
            device=device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data={"config": {"hostname": str(device)}},
        )
        snap.full_clean()
        snap.save()
        return snap

    def _make_golden(self, device, name="baseline"):
        from netbox_pyats.choices import GoldenConfigSourceChoices
        from netbox_pyats.models import PyatsGoldenConfig

        golden = PyatsGoldenConfig(
            device=device,
            name=name,
            config_text="hostname rtr01\n",
            source=GoldenConfigSourceChoices.SOURCE_MANUAL,
        )
        golden.full_clean()
        golden.save()
        return golden

    def test_clean_accepts_same_device_golden_and_snapshot(self):
        from netbox_pyats.choices import ComplianceResultChoices
        from netbox_pyats.models import PyatsComplianceRun

        golden = self._make_golden(self.device)
        snap = self._make_snapshot(self.device)
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff={},
            summary={},
        )
        run.full_clean()  # no raise

    def test_clean_rejects_cross_device_golden(self):
        from django.core.exceptions import ValidationError

        from netbox_pyats.choices import ComplianceResultChoices
        from netbox_pyats.models import PyatsComplianceRun

        other_golden = self._make_golden(self.other_device, name="other-baseline")
        snap = self._make_snapshot(self.device)
        run = PyatsComplianceRun(
            device=self.device,
            golden=other_golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_DRIFT,
            diff={},
            summary={},
        )
        with self.assertRaises(ValidationError) as cm:
            run.full_clean()
        self.assertIn("golden", cm.exception.message_dict)

    def test_clean_rejects_cross_device_snapshot(self):
        from django.core.exceptions import ValidationError

        from netbox_pyats.choices import ComplianceResultChoices
        from netbox_pyats.models import PyatsComplianceRun

        golden = self._make_golden(self.device)
        other_snap = self._make_snapshot(self.other_device)
        run = PyatsComplianceRun(
            device=self.device,
            golden=golden,
            snapshot=other_snap,
            result=ComplianceResultChoices.RESULT_DRIFT,
            diff={},
            summary={},
        )
        with self.assertRaises(ValidationError) as cm:
            run.full_clean()
        self.assertIn("snapshot", cm.exception.message_dict)

    def test_clean_skips_check_for_error_result(self):
        # ATW-68: the job's device-mismatch error-row path persists the
        # mismatched row as result="error" via full_clean(). clean() must not
        # reject it.
        from netbox_pyats.choices import ComplianceResultChoices
        from netbox_pyats.models import PyatsComplianceRun

        other_golden = self._make_golden(self.other_device, name="err-baseline")
        snap = self._make_snapshot(self.device)
        run = PyatsComplianceRun(
            device=self.device,
            golden=other_golden,
            snapshot=snap,
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            parser_warnings=["device mismatch"],
        )
        run.full_clean()  # no raise — error rows are exempt

    def test_clean_skips_check_for_null_fks(self):
        # ATW-68: a compliance run whose golden/snapshot was deleted writes
        # golden=None / snapshot=None.
        from netbox_pyats.choices import ComplianceResultChoices
        from netbox_pyats.models import PyatsComplianceRun

        run = PyatsComplianceRun(
            device=self.device,
            golden=None,
            snapshot=None,
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            parser_warnings=["golden or snapshot missing"],
        )
        run.full_clean()  # no raise
