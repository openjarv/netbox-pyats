"""Tests for :mod:`netbox_pyats.testbed`.

Pure-Python: exercises the NetBox→pyATS testbed bridge against fake NetBox
Device-like objects (no NetBox installation required). pyATS must be
importable (the plugin worker environment) for these tests to run; if pyATS is
absent we skip, because build_testbed is only ever exercised on the worker.

Covers:
- Platform slug → pyATS os mapping (supported + unsupported).
- Management IP resolution from primary_ip4 / primary_ip6.
- Credential attachment (plaintext appears only on the in-memory Device).
- on_unsupported="flag" vs "skip" semantics.
- TestbedBuildReport summary correctness.
"""

import pytest

pytest.importorskip("pyats")

import unittest

from netbox_pyats.choices import CredentialProtocolChoices
from netbox_pyats.testbed import UNSUPPORTED_OS, build_testbed, is_supported_os, platform_to_pyats_os

# --------------------------------------------------------------------------- #
# Fake NetBox objects (duck-typed; we only need the attributes the bridge reads).
# --------------------------------------------------------------------------- #


class FakePlatform:
    def __init__(self, slug, manufacturer_name=None):
        self.slug = slug
        self.name = slug.replace("-", " ").title() if slug else ""
        self.manufacturer = FakeManufacturer(manufacturer_name) if manufacturer_name else None


class FakeManufacturer:
    def __init__(self, name):
        self.name = name


class FakeIPAddress:
    def __init__(self, address):
        # NetBox IPAddress.address str() yields '10.0.0.1/24'
        self.address = address


class FakeDeviceType:
    def __init__(self, model="cisco-router"):
        self.model = model


class FakeDevice:
    def __init__(
        self, pk, name, platform_slug=None, manufacturer_name=None, mgmt_ip="10.0.0.1/24", device_type_model="router"
    ):
        self.pk = pk
        self.name = name
        self.platform = FakePlatform(platform_slug, manufacturer_name) if platform_slug else None
        self.primary_ip4 = FakeIPAddress(mgmt_ip) if mgmt_ip else None
        self.primary_ip6 = None
        self.device_type = FakeDeviceType(device_type_model)
        # Mirrors the NetBox Device interface the bridge reads.
        self.id = pk


class FakeCredential:
    """Duck-typed PyatsCredential (avoids DB/NetBox in unit tests)."""

    def __init__(self, pk, username="admin", password="hunter2", enable_secret="", ssh_port=22, protocol="ssh"):
        self.pk = pk
        self.username = username
        self._password = password
        self._enable_secret = enable_secret
        self.ssh_port = ssh_port
        self.protocol = protocol

    def get_password(self):
        return self._password

    def get_enable_secret(self):
        return self._enable_secret


# --------------------------------------------------------------------------- #
# platform_to_pyats_os
# --------------------------------------------------------------------------- #


class TestPlatformToOs(unittest.TestCase):
    def test_cisco_ios_slug(self):
        p = FakePlatform("cisco-ios")
        self.assertEqual(platform_to_pyats_os(p), "ios")

    def test_ios_slug(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("ios")), "ios")

    def test_iosxe(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("iosxe")), "iosxe")

    def test_junos(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("junos")), "junos")

    def test_arista_eos(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("arista-eos")), "eos")

    def test_nokia_sros(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("nokia-sros")), "sros")

    def test_unknown_slug_returns_unsupported_sentinel(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform("acme-switchos")), UNSUPPORTED_OS)

    def test_none_platform_returns_unsupported(self):
        self.assertEqual(platform_to_pyats_os(None), UNSUPPORTED_OS)

    def test_platform_with_no_slug_returns_unsupported(self):
        self.assertEqual(platform_to_pyats_os(FakePlatform(None)), UNSUPPORTED_OS)

    def test_manufacturer_fallback(self):
        # A platform with a non-matching slug but a known manufacturer should
        # fall back to the manufacturer's default os.
        p = FakePlatform("some-custom-slug", manufacturer_name="Juniper")
        self.assertEqual(platform_to_pyats_os(p), "junos")


# --------------------------------------------------------------------------- #
# is_supported_os
# --------------------------------------------------------------------------- #


class TestIsSupportedOs(unittest.TestCase):
    def test_supported(self):
        self.assertTrue(is_supported_os("iosxe"))
        self.assertTrue(is_supported_os("junos"))

    def test_unsupported_sentinel(self):
        self.assertFalse(is_supported_os(UNSUPPORTED_OS))

    def test_empty(self):
        self.assertFalse(is_supported_os(""))


# --------------------------------------------------------------------------- #
# build_testbed
# --------------------------------------------------------------------------- #


def _cred_resolver_factory(cred):
    """Return a credential_resolver that always returns ``cred`` (or None)."""

    def _resolver(device):
        return cred

    return _resolver


class TestBuildTestbed(unittest.TestCase):
    def test_supported_device_attached_with_os_and_mgmt_ip(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe", mgmt_ip="10.0.0.1/24")
        cred = FakeCredential(pk=1, username="admin", password="hunter2")
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(cred))
        self.assertIn("rtr01", tb.devices)
        pyats_d = tb.devices["rtr01"]
        self.assertEqual(pyats_d.os, "iosxe")
        self.assertEqual(pyats_d.connections["a"]["ip"], "10.0.0.1")
        self.assertEqual(pyats_d.connections["a"]["port"], 22)
        # Credentials attached (plaintext in-memory only)
        self.assertEqual(pyats_d.credentials["default"]["username"], "admin")
        self.assertEqual(pyats_d.credentials["default"]["password"], "hunter2")
        # NetBox metadata stashed for the UI
        self.assertEqual(pyats_d.custom["netbox_pyats"]["netbox_device_id"], 1)
        self.assertTrue(pyats_d.custom["netbox_pyats"]["supported"])

    def test_unsupported_device_flagged_by_default(self):
        dev = FakeDevice(pk=2, name="weird-switch", platform_slug="acme-switchos")
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(None))
        self.assertIn("weird-switch", tb.devices)
        pyats_d = tb.devices["weird-switch"]
        self.assertEqual(pyats_d.os, UNSUPPORTED_OS)
        self.assertFalse(pyats_d.custom["netbox_pyats"]["supported"])
        self.assertEqual(len(report.supported), 0)
        self.assertEqual(len(report.unsupported), 1)
        self.assertEqual(report.unsupported[0]["name"], "weird-switch")
        self.assertIn("unsupported", report.unsupported[0]["reason"])

    def test_unsupported_device_skipped_when_on_unsupported_skip(self):
        dev = FakeDevice(pk=3, name="skipped-switch", platform_slug="acme-switchos")
        tb, report = build_testbed([dev], on_unsupported="skip", credential_resolver=_cred_resolver_factory(None))
        self.assertEqual(len(tb.devices), 0)
        self.assertEqual(len(report.unsupported), 1)
        self.assertEqual(report.unsupported[0]["name"], "skipped-switch")

    def test_mixed_queryset_report_summary(self):
        devices = [
            FakeDevice(pk=1, name="rtr01", platform_slug="iosxe"),
            FakeDevice(pk=2, name="rtr02", platform_slug="junos"),
            FakeDevice(pk=3, name="weird", platform_slug="acme"),
        ]
        tb, report = build_testbed(devices, credential_resolver=_cred_resolver_factory(None))
        self.assertEqual(len(report.supported), 2)
        self.assertEqual(len(report.unsupported), 1)
        self.assertTrue(report.ok)
        self.assertIn("2 supported, 1 unsupported (3 total)", report.summary())

    def test_no_supported_devices_report_not_ok(self):
        devices = [FakeDevice(pk=1, name="weird1", platform_slug="acme")]
        tb, report = build_testbed(devices, credential_resolver=_cred_resolver_factory(None))
        self.assertFalse(report.ok)
        self.assertEqual(report.summary(), "0 supported, 1 unsupported (1 total)")

    def test_missing_mgmt_ip_leaves_ip_none(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe", mgmt_ip=None)
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(None))
        self.assertEqual(tb.devices["rtr01"].connections["a"]["ip"], None)
        self.assertTrue(report.ok)

    def test_protocol_from_credential(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe")
        cred = FakeCredential(pk=1, protocol=CredentialProtocolChoices.PROTOCOL_TELNET)
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(cred))
        self.assertEqual(tb.devices["rtr01"].connections["a"]["protocol"], "telnet")

    def test_invalid_on_unsupported_raises(self):
        with self.assertRaises(ValueError):
            build_testbed([], on_unsupported="bogus", credential_resolver=_cred_resolver_factory(None))

    def test_enable_secret_attached_when_set(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe")
        cred = FakeCredential(pk=1, enable_secret="enablepass")
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(cred))
        self.assertEqual(tb.devices["rtr01"].credentials["enable"]["password"], "enablepass")

    def test_enable_secret_absent_when_not_set(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe")
        cred = FakeCredential(pk=1, enable_secret="")
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(cred))
        self.assertNotIn("enable", tb.devices["rtr01"].credentials)

    def test_ssh_port_from_credential(self):
        dev = FakeDevice(pk=1, name="rtr01", platform_slug="iosxe")
        cred = FakeCredential(pk=1, ssh_port=2222)
        tb, report = build_testbed([dev], credential_resolver=_cred_resolver_factory(cred))
        self.assertEqual(tb.devices["rtr01"].connections["a"]["port"], 2222)
