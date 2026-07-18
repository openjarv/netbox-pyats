"""Dynamic pyATS testbed materialization from the NetBox ORM.

:func:`build_testbed` is the core integration point: instead of maintaining a
static YAML testbed file, we build a pyATS :class:`Testbed` object directly
from NetBox ``Device``/``Interface``/``IPAddress``/``Platform`` rows plus a
resolved :class:`~netbox_pyats.models.PyatsCredential`.

Multi-vendor: the platform → pyATS ``os`` map is bounded by Genie parser
availability. Devices whose platform is not in the map are surfaced as
``unsupported - no parser`` and skipped in batch runs (graceful degradation)
rather than raising or silently mislabelling the ``os``.

The pyATS/Genie import is deferred so this module is importable without
``pyats[full]`` installed; :func:`build_testbed` raises a clear error if the
runtime dependency is missing when actually called.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

# Map NetBox Platform.slug/name -> pyATS ``os`` string.
# Bounded by Genie parser coverage; see
# https://pubhub.devnetcloud.org/download/genie-doc/genie_libs/reference/tables/operator-platform.html
# Keep this list conservative — adding an entry is a claim that Genie parsers
# exist for that platform/os combo.
PLATFORM_TO_PYATS_OS: dict[str, str] = {
    # Cisco
    "cisco-ios": "ios",
    "cisco-iosxe": "iosxe",
    "cisco-iosxr": "iosxr",
    "ios": "ios",
    "iosxe": "iosxe",
    "iosxr": "iosxr",
    "nxos": "nxos",
    "cisco-nxos": "nxos",
    "cisco-nx-os": "nxos",
    # Juniper
    "junos": "junos",
    "juniper-junos": "junos",
    "juniper": "junos",
    # Arista
    "eos": "eos",
    "arista-eos": "eos",
    "arista": "eos",
    # Nokia
    "sros": "sros",
    "nokia-sros": "sros",
    "nokia": "sros",
}

UNSUPPORTED_OS_MARKER = "unsupported - no parser"


def resolve_os(platform: Any) -> str:
    """Resolve a pyATS ``os`` string from a NetBox ``Platform`` object.

    Returns :data:`UNSUPPORTED_OS_MARKER` when the platform has no matching
    Genie parser in :data:`PLATFORM_TO_PYATS_OS`.
    """
    if platform is None:
        return UNSUPPORTED_OS_MARKER
    slug = getattr(platform, "slug", None) or ""
    name = getattr(platform, "name", None) or ""
    for candidate in (slug, name, slug.replace("_", "-")):
        if not candidate:
            continue
        key = candidate.lower().strip()
        if key in PLATFORM_TO_PYATS_OS:
            return PLATFORM_TO_PYATS_OS[key]
    return UNSUPPORTED_OS_MARKER


def is_supported_os(os_value: str) -> bool:
    """Return True if ``os_value`` is a supported pyATS os (has Genie parsers)."""
    return bool(os_value) and os_value != UNSUPPORTED_OS_MARKER


@dataclass
class ResolvedDevice:
    """Resolved testbed entry for a single device.

    Captured so callers can inspect what was resolved (mgmt IP, os, credential,
    unsupported flag) without holding the pyATS objects.
    """

    name: str
    device_id: int | None = None
    mgmt_ip: str | None = None
    os: str = UNSUPPORTED_OS_MARKER
    protocol: str = "ssh"
    port: int = 22
    username: str | None = None
    has_credential: bool = False
    unsupported: bool = True
    errors: list[str] = field(default_factory=list)

    def as_testbed_dict(self) -> dict[str, Any]:
        """Render as a pyATS testbed device dict (the YAML-equivalent structure).

        Includes a ``custom:unsupported`` marker so callers and later phases can
        filter unsupported devices out of batch runs.
        """
        d: dict[str, Any] = {
            "os": self.os,
            "type": "unknown",
            "credentials": {},
            "custom": {"unsupported": self.unsupported},
        }
        if self.mgmt_ip:
            d["connections"] = {
                "cli": {
                    "ip": self.mgmt_ip,
                    "protocol": self.protocol,
                    "port": self.port,
                }
            }
        if self.username:
            d["credentials"]["default"] = {
                "username": self.username,
            }
        return d


@dataclass
class TestbedBuildResult:
    """Outcome of :func:`build_testbed`.

    Holds the pyATS ``Testbed`` object (when pyATS is importable) plus the
    list of :class:`ResolvedDevice` entries so callers can report which
    devices were unsupported or had no credential/mgmt IP.
    """

    testbed: Any | None
    devices: list[ResolvedDevice]
    unsupported: list[ResolvedDevice] = field(default_factory=list)
    missing_credential: list[ResolvedDevice] = field(default_factory=list)
    missing_mgmt_ip: list[ResolvedDevice] = field(default_factory=list)

    @property
    def supported(self) -> list[ResolvedDevice]:
        return [d for d in self.devices if not d.unsupported]


def _resolve_mgmt_ip(device: Any) -> str | None:
    """Pick the management IP for a NetBox Device.

    Prefers the device's primary_ip4 / primary_ip6 (the NetBox-native "primary
    management address"), falling back to the first IPAddress found on any of
    the device's interfaces that has an address. Returns the bare address
    without the prefix length.
    """
    primary = getattr(device, "primary_ip", None) or getattr(device, "primary_ip4", None)
    if primary is None:
        primary = getattr(device, "primary_ip6", None)
    if primary is not None:
        return str(primary.address).split("/", 1)[0]

    # Fall back to the first IPAddress on any interface.
    try:
        for iface in device.interfaces.all():
            for ip in iface.ip_addresses.all():
                return str(ip.address).split("/", 1)[0]
    except Exception:
        return None
    return None


def _resolve_credential(device: Any) -> Any | None:
    """Resolve the PyatsCredential for a device.

    Looks for a PyatsCredential attached to this device first, then any
    group/shared credential (device is null). Returns None if no credential
    is found or the credential ORM isn't available (e.g. NetBox not installed).
    """
    from .models import PyatsCredential  # local import to avoid Django app-loading races

    manager = getattr(PyatsCredential, "objects", None)
    if manager is None:
        # No ORM available (placeholder model / NetBox not installed).
        return None
    cred = manager.filter(device=device).first()
    if cred is not None:
        return cred
    return manager.filter(device__isnull=True).first()


def build_testbed(
    device_qs: Iterable[Any],
    *,
    name: str = "netbox_pyats_testbed",
    require_credential: bool = True,
) -> TestbedBuildResult:
    """Materialize a pyATS :class:`Testbed` from a NetBox Device queryset.

    Parameters
    ----------
    device_qs:
        Iterable of NetBox ``Device`` objects. Pass a queryset (or list); the
        function iterates once and does not modify the queryset.
    name:
        Name for the resulting Testbed.
    require_credential:
        When True (default), devices without a resolved credential are recorded
        in ``missing_credential`` and excluded from the Testbed. When False,
        devices without credentials are still added with no credentials so
        callers can attempt unauthenticated connections.

    Returns
    -------
    TestbedBuildResult
        Holds the pyATS Testbed (when ``pyats`` is importable) plus resolved
        per-device metadata (mgmt IP, os, credential, unsupported flag).
    """
    resolved: list[ResolvedDevice] = []
    for device in device_qs:
        rd = ResolvedDevice(
            name=str(getattr(device, "name", None) or f"device-{device.pk}"),
            device_id=getattr(device, "pk", None),
            os=resolve_os(getattr(device, "platform", None)),
        )
        if not is_supported_os(rd.os):
            rd.unsupported = True
            rd.errors.append(f"Unsupported platform for pyATS/Genie: {getattr(device, 'platform', None)}")
        else:
            rd.unsupported = False
        rd.mgmt_ip = _resolve_mgmt_ip(device)
        if not rd.mgmt_ip:
            rd.errors.append("No management IP address found in NetBox.")

        cred = _resolve_credential(device)
        if cred is not None:
            rd.has_credential = True
            rd.username = cred.username
            rd.protocol = cred.protocol
            rd.port = cred.ssh_port
        elif require_credential:
            rd.errors.append("No PyatsCredential resolved for this device.")
        resolved.append(rd)

    unsupported = [d for d in resolved if d.unsupported]
    missing_credential = [d for d in resolved if not d.has_credential and require_credential]
    missing_mgmt_ip = [d for d in resolved if not d.mgmt_ip]

    # Build the pyATS Testbed object if pyATS is importable. We include only
    # devices that are supported, have a mgmt IP, and (when require_credential)
    # have a credential. Unsupported / missing-IP / missing-cred devices are
    # returned in the result lists for the caller to surface in the UI.
    testbed = _build_pyats_testbed(
        name, [d for d in resolved if not d.unsupported and d.mgmt_ip and (d.has_credential or not require_credential)]
    )

    return TestbedBuildResult(
        testbed=testbed,
        devices=resolved,
        unsupported=unsupported,
        missing_credential=missing_credential,
        missing_mgmt_ip=missing_mgmt_ip,
    )


def _build_pyats_testbed(name: str, devices: list[ResolvedDevice]) -> Any | None:
    """Build a pyATS Testbed object from resolved devices.

    Returns ``None`` if pyATS is not importable (so this module is usable in
    pure-Python tests and in environments without ``pyats[full]`` installed).
    """
    try:
        from pyats.topology import Device as PyatsDevice  # noqa: F401
        from pyats.topology import Testbed
    except ModuleNotFoundError:
        return None

    testbed = Testbed(name=name)
    for rd in devices:
        # pyATS Device requires a Testbed instance and a name.
        d = PyatsDevice(name=rd.name, testbed=testbed)
        d.os = rd.os
        if rd.mgmt_ip:
            d.connections = {
                "cli": {
                    "ip": rd.mgmt_ip,
                    "protocol": rd.protocol,
                    "port": rd.port,
                }
            }
        if rd.username:
            d.credentials = {
                "default": {
                    "username": rd.username,
                }
            }
        d.custom = {"unsupported": False}
        testbed.devices[rd.name] = d
    return testbed
