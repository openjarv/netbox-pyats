"""Tests for :class:`netbox_pyats.models.PyatsCredential`.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable so CI can still run the pure-Python tests (crypto + testbed) in
matrix jobs that don't stand up NetBox.
"""

import pytest

pytest.importorskip("netbox")

from django.test import TestCase

from netbox_pyats import crypto
from netbox_pyats.choices import CredentialProtocolChoices, CredentialScopeChoices
from netbox_pyats.models import PyatsCredential


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
