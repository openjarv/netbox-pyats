"""REST API tests for the PyatsCredential model.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.test import TestCase
from rest_framework import status

from netbox_pyats import crypto
from netbox_pyats.choices import CredentialScopeChoices
from netbox_pyats.models import PyatsCredential
from users.models import User


class PyatsCredentialAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AMS01", slug="ams01")
        cls.mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        cls.device_type = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router", slug="router")
        cls.device = Device.objects.create(name="rtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def setUp(self):
        # NetBox 4.6 rejects anonymous API requests (403). Authenticate the
        # client as a superuser so the credential endpoints are reachable,
        # matching the pattern NetBox's own plugin tests use.
        self.user = User.objects.create_user(username="api-test", is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

    def test_list_credentials(self):
        url = "/api/plugins/pyats/pyats-credentials/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_credential_encrypts_password(self):
        url = "/api/plugins/pyats/pyats-credentials/"
        data = {
            "name": "rtr01-ssh",
            "scope": CredentialScopeChoices.SCOPE_DEVICE,
            "device": self.device.pk,
            "username": "admin",
            "protocol": "ssh",
            "ssh_port": 22,
            "plaintext_password": "hunter2",
            "plaintext_enable_secret": "enablepass",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cred = PyatsCredential.objects.get(name="rtr01-ssh")
        self.assertTrue(crypto.is_encrypted_token(cred.password))
        self.assertEqual(cred.get_password(), "hunter2")
        self.assertEqual(cred.get_enable_secret(), "enablepass")
        # Ciphertext must not appear in the API response.
        self.assertNotIn("password", response.data)
        self.assertNotIn("enable_secret", response.data)
        self.assertNotIn("hunter2", str(response.data))

    def test_retrieve_credential_omits_secrets(self):
        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", device=self.device, scope=CredentialScopeChoices.SCOPE_DEVICE, username="admin"
        )
        cred.set_password("hunter2")
        cred.save()
        url = f"/api/plugins/pyats/pyats-credentials/{cred.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ciphertext and plaintext must never appear.
        self.assertNotIn("password", response.data)
        self.assertNotIn("enable_secret", response.data)
        self.assertNotIn("hunter2", str(response.data))

    def test_update_credential_keeps_existing_secret_when_blank(self):
        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", device=self.device, scope=CredentialScopeChoices.SCOPE_DEVICE, username="admin"
        )
        cred.set_password("hunter2")
        cred.set_enable_secret("enablepass")
        cred.save()
        # PUT without plaintext_password: keep the existing ciphertext.
        url = f"/api/plugins/pyats/pyats-credentials/{cred.pk}/"
        response = self.client.patch(
            url,
            {"username": "admin2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cred.refresh_from_db()
        self.assertEqual(cred.username, "admin2")
        self.assertEqual(cred.get_password(), "hunter2")
        self.assertEqual(cred.get_enable_secret(), "enablepass")

    def test_delete_credential(self):
        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", device=self.device, scope=CredentialScopeChoices.SCOPE_DEVICE, username="admin"
        )
        pk = cred.pk
        url = f"/api/plugins/pyats/pyats-credentials/{pk}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PyatsCredential.objects.filter(pk=pk).exists())
