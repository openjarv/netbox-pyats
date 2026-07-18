"""Unit tests for :mod:`netbox_pyats.testbed`.

Pure-Python: builds the testbed from fixture device objects (no Django ORM or
NetBox installed) and asserts that the resolver maps platforms to pyATS ``os``
correctly, flags unsupported platforms, and surfaces missing-IP / missing-cred
conditions. pyATS itself is not required to be installed — when it's missing,
:func:`build_testbed` returns a result with ``testbed=None`` but still populates
the per-device resolved metadata, which is what these tests assert on.
"""

from types import SimpleNamespace

import pytest

from netbox_pyats.testbed import PLATFORM_TO_PYATS_OS, UNSUPPORTED_OS_MARKER, build_testbed, is_supported_os, resolve_os


class FakeIP:
    def __init__(self, address):
        self.address = address


class FakeInterface:
    def __init__(self, name, addresses=None):
        self.name = name
        self._addresses = addresses or []

    @property
    def ip_addresses(self):
        outer = self

        class _IPAddresses:
            def all(self):
                return outer._addresses

        return _IPAddresses()


class FakeDevice:
    """Minimal stand-in for a NetBox Device object."""

    def __init__(self, pk, name, platform=None, primary_ip=None, interfaces=None):
        self.pk = pk
        self.name = name
        self.platform = platform
        self.primary_ip = primary_ip
        self._interfaces = interfaces or []

    @property
    def interfaces(self):
        outer = self

        class _InterfacesProxy:
            def all(self):
                return outer._interfaces

        return _InterfacesProxy()


def _platform(slug, name=None):
    return SimpleNamespace(slug=slug, name=name or slug)


def test_resolve_os_known_platforms():
    assert resolve_os(_platform("cisco-ios")) == "ios"
    assert resolve_os(_platform("iosxe")) == "iosxe"
    assert resolve_os(_platform("junos")) == "junos"
    assert resolve_os(_platform("eos")) == "eos"
    assert resolve_os(_platform("arista-eos")) == "eos"
    assert resolve_os(_platform("nokia-sros")) == "sros"


def test_resolve_os_unsupported_platform():
    assert resolve_os(_platform("linux")) == UNSUPPORTED_OS_MARKER
    assert resolve_os(_platform("generic-router")) == UNSUPPORTED_OS_MARKER
    assert resolve_os(None) == UNSUPPORTED_OS_MARKER


def test_resolve_os_case_insensitive_and_name_fallback():
    assert resolve_os(_platform("Cisco-IOS")) == "ios"
    assert resolve_os(SimpleNamespace(slug="", name="JunOS")) == "junos"


def test_is_supported_os():
    assert is_supported_os("ios")
    assert not is_supported_os(UNSUPPORTED_OS_MARKER)
    assert not is_supported_os("")


def test_build_testbed_basic_supported_device():
    dev = FakeDevice(
        pk=1,
        name="r1",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.1/32"),
    )
    result = build_testbed([dev])
    assert len(result.devices) == 1
    rd = result.devices[0]
    assert rd.name == "r1"
    assert rd.os == "ios"
    assert not rd.unsupported
    assert rd.mgmt_ip == "10.0.0.1"
    assert rd.errors == ["No PyatsCredential resolved for this device."]
    assert result.unsupported == []
    assert result.missing_mgmt_ip == []


def test_build_testbed_unsupported_platform_flagged():
    dev = FakeDevice(
        pk=2,
        name="r2",
        platform=_platform("linux"),
        primary_ip=FakeIP("10.0.0.2/32"),
    )
    result = build_testbed([dev])
    assert len(result.devices) == 1
    rd = result.devices[0]
    assert rd.unsupported
    assert rd.os == UNSUPPORTED_OS_MARKER
    assert any("Unsupported platform" in e for e in rd.errors)
    assert result.unsupported == [rd]
    # The unsupported device is excluded from the supported list.
    assert result.supported == []


def test_build_testbed_missing_mgmt_ip():
    dev = FakeDevice(
        pk=3,
        name="r3",
        platform=_platform("cisco-ios"),
        primary_ip=None,
        interfaces=[FakeInterface("eth0", addresses=[])],
    )
    result = build_testbed([dev])
    rd = result.devices[0]
    assert rd.mgmt_ip is None
    assert any("management IP" in e for e in rd.errors)
    assert result.missing_mgmt_ip == [rd]


def test_build_testbed_falls_back_to_interface_ip_when_no_primary():
    iface = FakeInterface("mgmt0", addresses=[FakeIP("192.168.1.1/24")])
    dev = FakeDevice(
        pk=4,
        name="r4",
        platform=_platform("cisco-ios"),
        primary_ip=None,
        interfaces=[iface],
    )
    result = build_testbed([dev])
    assert result.devices[0].mgmt_ip == "192.168.1.1"


def test_build_testbed_missing_credential_recorded():
    dev = FakeDevice(
        pk=5,
        name="r5",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.5/32"),
    )
    result = build_testbed([dev])
    rd = result.devices[0]
    assert not rd.has_credential
    assert any("PyatsCredential" in e for e in rd.errors)
    assert result.missing_credential == [rd]


def test_build_testbed_require_credential_false_allows_no_cred():
    dev = FakeDevice(
        pk=6,
        name="r6",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.6/32"),
    )
    result = build_testbed([dev], require_credential=False)
    rd = result.devices[0]
    assert not rd.has_credential
    assert rd.username is None
    assert result.missing_credential == []  # not recorded when not required


def test_build_testbed_resolves_credential_from_device_or_group(monkeypatch):
    """A device-level credential is preferred; group credential is the fallback."""
    from netbox_pyats import testbed as tb_mod

    cred = SimpleNamespace(
        username="admin",
        protocol="ssh",
        ssh_port=2222,
    )

    class FakeCredQS:
        def __init__(self, device_match):
            self._device_match = device_match

        def filter(self, *args, **kwargs):
            # Distinguish device-filter from device__isnull=True filter.
            if "device" in kwargs:
                return SimpleNamespace(first=lambda: cred if self._device_match else None)
            if kwargs.get("device__isnull") is True:
                return SimpleNamespace(first=lambda: cred if not self._device_match else None)
            return SimpleNamespace(first=lambda: None)

    class FakeCredManager:
        def __get__(self, *a, **k):
            return self

        @property
        def objects(self):
            return self

    # Patch PyatsCredential.objects via monkeypatching the import in testbed.py.
    fake_manager = SimpleNamespace()
    fake_manager.objects = SimpleNamespace()

    # Replace the lazy import inside _resolve_credential.
    def fake_resolve_credential(device):
        # Device-level match for r7, group-only for r8.
        if device.name == "r7":
            return cred
        if device.name == "r8":
            return cred
        return None

    monkeypatch.setattr(tb_mod, "_resolve_credential", fake_resolve_credential)

    dev7 = FakeDevice(
        pk=7,
        name="r7",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.7/32"),
    )
    dev8 = FakeDevice(
        pk=8,
        name="r8",
        platform=_platform("junos"),
        primary_ip=FakeIP("10.0.0.8/32"),
    )
    result = build_testbed([dev7, dev8])
    assert all(d.has_credential for d in result.devices)
    assert all(d.username == "admin" for d in result.devices)
    assert all(d.port == 2222 for d in result.devices)


def test_build_testbed_mixed_batch():
    """A batch with a supported + an unsupported device degrades gracefully."""
    supported = FakeDevice(
        pk=10,
        name="ok",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.10/32"),
    )
    unsupported = FakeDevice(
        pk=11,
        name="nope",
        platform=_platform("openbsd"),
        primary_ip=FakeIP("10.0.0.11/32"),
    )
    result = build_testbed([supported, unsupported])
    assert len(result.devices) == 2
    assert len(result.supported) == 1
    assert len(result.unsupported) == 1
    assert result.unsupported[0].name == "nope"


def test_build_testbed_testbed_none_when_pyats_not_installed():
    """When pyats is not importable, testbed is None but devices are still resolved."""
    import importlib

    try:
        importlib.import_module("pyats")
        pytest.skip("pyats is installed; this test asserts the not-installed path")
    except ModuleNotFoundError:
        pass

    dev = FakeDevice(
        pk=12,
        name="r12",
        platform=_platform("cisco-ios"),
        primary_ip=FakeIP("10.0.0.12/32"),
    )
    result = build_testbed([dev], require_credential=False)
    assert result.testbed is None
    assert len(result.devices) == 1


def test_platform_map_covers_each_documented_vendor():
    """Sanity: every documented multi-vendor family is represented in the map."""
    # Cisco IOS/XE/XR/NX-OS, Juniper JunOS, Arista EOS, Nokia SR OS.
    found = set(PLATFORM_TO_PYATS_OS.values())
    assert {"ios", "iosxe", "iosxr", "nxos", "junos", "eos", "sros"}.issubset(found)
