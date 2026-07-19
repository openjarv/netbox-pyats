"""View tests for the PyatsCredential list/detail/edit pages.

Requires a running NetBox/Django test database. Skipped when NetBox is not
importable.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import CredentialScopeChoices
from netbox_pyats.models import PyatsCredential


class PyatsCredentialViewTest(TestCase):
    # NetBox's TestCase.setUp force_logins a user and grants the listed
    # permissions (format: "<app>.<action>_<model>"). The view tests exercise
    # list/detail/add, so the user needs view + add on PyatsCredential.
    user_permissions = (
        "netbox_pyats.view_pyatscredential",
        "netbox_pyats.add_pyatscredential",
        # NetBox 4.6 restricts the device ModelChoiceField queryset to
        # devices the user can view. Without dcim.view_device the add
        # form's device field has no valid choices and the POST fails
        # validation ("Select a valid choice").
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="AMS01", slug="ams01")
        cls.mfr = Manufacturer.objects.create(name="Cisco", slug="cisco")
        cls.device_type = DeviceType.objects.create(model="Catalyst 9300", slug="catalyst-9300", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router", slug="router")
        cls.device = Device.objects.create(name="rtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def test_list_view(self):
        url = reverse("plugins:netbox_pyats:pyatscredential_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_with_data(self):
        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", device=self.device, scope=CredentialScopeChoices.SCOPE_DEVICE, username="admin"
        )
        url = reverse("plugins:netbox_pyats:pyatscredential_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The list table's Name column links to the detail page using the
        # credential's name (not the full __str__, which includes the device).
        self.assertContains(response, cred.name)

    def test_detail_view(self):
        cred = PyatsCredential.objects.create(
            name="rtr01-ssh", device=self.device, scope=CredentialScopeChoices.SCOPE_DEVICE, username="admin"
        )
        cred.set_password("hunter2")
        cred.set_enable_secret("enablepass")
        cred.save()
        url = reverse("plugins:netbox_pyats:pyatscredential", kwargs={"pk": cred.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rtr01-ssh")
        # The ciphertext must never be rendered in the detail page. Assert
        # against the actual stored ciphertext (not an empty string, which
        # trivially matches any response).
        self.assertNotContains(response, cred.password)
        self.assertNotContains(response, cred.enable_secret)
        self.assertNotContains(response, "hunter2")

    def test_add_view_creates_encrypted_credential(self):
        from netbox_pyats import crypto

        url = reverse("plugins:netbox_pyats:pyatscredential_add")
        response = self.client.post(
            url,
            {
                "name": "rtr01-ssh",
                "scope": CredentialScopeChoices.SCOPE_DEVICE,
                "device": self.device.pk,
                "username": "admin",
                "protocol": "ssh",
                "ssh_port": 22,
                "plaintext_password": "hunter2",
                "plaintext_enable_secret": "enablepass",
                "tags": [],
            },
        )
        # NetBox's ObjectEditView redirects on success (302).
        self.assertEqual(
            response.status_code,
            302,
            msg=f"form errors: {response.context['form'].errors if response.context else 'no context'}",
        )
        cred = PyatsCredential.objects.get(name="rtr01-ssh")
        self.assertNotEqual(cred.password, "hunter2")
        self.assertTrue(crypto.is_encrypted_token(cred.password))
        self.assertEqual(cred.get_password(), "hunter2")
        self.assertEqual(cred.get_enable_secret(), "enablepass")
