"""NetBox → pyATS testbed bridge.

:func:`build_testbed` constructs a :class:`pyats.topology.Testbed` object
directly from the NetBox ORM (Device / Interface / IPAddress / Platform) plus a
resolved :class:`netbox_pyats.models.PyatsCredential`. No static YAML file is
required: the plugin materializes the testbed at runtime, which is the core
integration insight from the ATW-10 research doc.

Multi-vendor support is bounded by Genie parser availability. NetBox
``Platform`` rows carry a ``slug`` and ``name``; we map the slug (and, as a
fallback, the manufacturer name) to a pyATS ``os`` string. Devices whose
platform has no matching Genie parser are surfaced as "unsupported - no parser"
on the returned testbed entry (stored in ``device.custom['netbox_pyats']``)
rather than raising, so batch operations can skip them gracefully — the UX
contract locked in ATW-10 scoping.

The pyATS import is lazy (module-level function call) so the NetBox web process
can import the plugin without pyATS installed; pyATS only needs to be present
on the worker that actually connects to devices (documented in the README).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Optional

from .choices import CredentialProtocolChoices

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids runtime netbox import
    from .models import PyatsCredential

logger = logging.getLogger(__name__)


def _resolve_credential(device):
    """Return the PyatsCredential for a NetBox Device, or None if none exists.

    v1 only resolves device-scoped credentials. Global/shared credential
    resolution by name is shipped with the batch-snapshot flow in ATW-13.

    The :class:`PyatsCredential` import is lazy so this module is importable in
    the NetBox web process without pyATS or a configured DB (the testbed builder
    is only exercised on the worker, and ``models.py`` imports ``netbox``).
    """
    if device is None:
        return None
    from .models import PyatsCredential  # lazy: avoids netbox import at module load

    return PyatsCredential.objects.filter(device=device).first()


# NetBox Platform slug → pyATS ``os`` string. The right-hand values are the
# Genie/Unicon ``os`` identifiers used to select parser packages and Unicon
# plugins. Coverage is exactly what Genie ships parsers for; anything not in
# this map degrades to 'unsupported - no parser'.
#
# This map is deliberately conservative: we map only the platforms Genie has
# real parser coverage for. Adding a slug here is a commitment that snapshots
# for that os will actually produce structured output. Unknown slugs surface
# as unsupported rather than silently producing empty snapshots.
PLATFORM_SLUG_TO_PYATS_OS: dict[str, str] = {
    # Cisco
    "cisco-ios": "ios",
    "ios": "ios",
    "cisco-iosxe": "iosxe",
    "iosxe": "iosxe",
    "cisco-iosxr": "iosxr",
    "iosxr": "iosxr",
    "cisco-nxos": "nxos",
    "nxos": "nxos",
    "cisco-nx-os": "nxos",
    "cisco-asa": "asa",
    "asa": "asa",
    # Juniper
    "juniper-junos": "junos",
    "junos": "junos",
    # Arista
    "arista-eos": "eos",
    "eos": "eos",
    # Nokia
    "nokia-sros": "sros",
    "sros": "sros",
}

# Manufacturer name (lowercased) → pyATS os. Used as a fallback when the platform
# slug is generic (e.g. "iosxe" with no vendor prefix and an explicit
# manufacturer). Conservative: only mapped where Genie has parser coverage.
MANUFACTURER_NAME_TO_PYATS_OS: dict[str, str] = {
    "cisco": "iosxe",  # default Cisco os; specific platforms override via slug
    "juniper": "junos",
    "arista": "eos",
    "nokia": "sros",
}

# Sentinel os value used to mark devices Genie cannot parse. Surfaced verbatim
# in the UI as "unsupported - no parser".
UNSUPPORTED_OS = "unsupported - no parser"


def platform_to_pyats_os(platform) -> str:
    """Map a NetBox ``Platform`` to a pyATS ``os`` string.

    Returns the :data:`UNSUPPORTED_OS` sentinel for platforms Genie does not
    ship parsers for, so callers can degrade gracefully without raising.

    Args:
        platform: a NetBox ``dcim.Platform`` instance (has ``slug``,
            ``name``, and a ``manufacturer`` FK). ``None`` is tolerated and
            returns the unsupported sentinel.
    """
    if platform is None or not getattr(platform, "slug", None):
        return UNSUPPORTED_OS
    slug = platform.slug.lower()
    if slug in PLATFORM_SLUG_TO_PYATS_OS:
        return PLATFORM_SLUG_TO_PYATS_OS[slug]
    # Try the manufacturer as a fallback (e.g. a platform named "IOS-XE" with
    # slug "ios-xe" but no explicit slug match).
    manufacturer = getattr(platform, "manufacturer", None)
    if manufacturer and (manufacturer.name or "").lower() in MANUFACTURER_NAME_TO_PYATS_OS:
        return MANUFACTURER_NAME_TO_PYATS_OS[(manufacturer.name or "").lower()]
    return UNSUPPORTED_OS


def is_supported_os(os_value: str) -> bool:
    """True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)."""
    return bool(os_value) and os_value != UNSUPPORTED_OS


def _mgmt_address(device) -> Optional[str]:
    """Return the management IP for a NetBox Device, preferring primary_ip4.

    Returns a bare address string (no prefix length). Falls back to
    primary_ip6. Returns None if neither is set.
    """
    ip = getattr(device, "primary_ip4", None) or getattr(device, "primary_ip6", None)
    if ip is None:
        return None
    address = getattr(ip, "address", None)
    if address is None:
        return None
    # NetBox IPAddress.address is a netaddr IPNetwork-like; str() yields
    # '10.0.0.1/24'. Strip the prefix for the pyATS connection meta.
    return str(address).split("/", 1)[0]


def _protocol_for(pyats_os: str, credential: Optional["PyatsCredential"]) -> str:
    """Pick the pyATS connection protocol from the credential, defaulting to ssh."""
    if credential and credential.protocol:
        return credential.protocol
    return CredentialProtocolChoices.PROTOCOL_SSH


def _build_device_entry(netbox_device, *, credential: Optional["PyatsCredential"], on_unsupported: str):
    """Build a pyATS Device-like dict entry from a NetBox Device.

    Returns a ``(pyats_device, status)`` tuple where ``status`` is either
    ``"supported"`` or ``"unsupported"``. ``pyats_device`` is configured with
    os, connections, and credentials; for unsupported devices we still return
    a populated entry but with ``os = UNSUPPORTED_OS`` so the caller (and the
    UI) can surface the reason without an exception.

    ``on_unsupported`` controls what happens to unsupported devices:
      - ``"flag"`` (default): include the device on the testbed with
        ``os=UNSUPPORTED_OS`` so callers can iterate and render it as
        unsupported in the UI.
      - ``"skip"``: omit unsupported devices entirely (used by batch runs that
        want to silently skip rather than report).
    """
    os_value = platform_to_pyats_os(getattr(netbox_device, "platform", None))
    supported = is_supported_os(os_value)
    status = "supported" if supported else "unsupported"
    if not supported and on_unsupported == "skip":
        return None, status

    name = netbox_device.name or f"netbox-device-{netbox_device.pk}"
    mgmt_ip = _mgmt_address(netbox_device)
    protocol = _protocol_for(os_value, credential)

    # Build the pyATS Device. We set the os and a single 'a' connection entry
    # (the default alias Unicon uses). Credentials are attached via the
    # Device.credentials API so pyATS can pick them up at connect time without
    # us embedding plaintext in the connection dict.
    Device = _pyats_device_cls()
    d = Device(name=name, os=os_value, type=getattr(netbox_device.device_type, "model", None) or "unknown")
    # Connection meta. mgmt IP may be missing for devices that are not yet
    # fully populated; we leave the connection entry present but with ip=None
    # so callers can detect and warn.
    d.connections = {
        "a": {
            "protocol": protocol,
            "ip": mgmt_ip,
            "port": getattr(credential, "ssh_port", 22) if credential else 22,
        }
    }
    # Attach credentials (plaintext) to the pyATS Device so the worker can
    # connect. This is the only place plaintext lives in-memory, and only for
    # the lifetime of the testbed object.
    if credential is not None:
        d.credentials.setdefault("default", {})
        d.credentials["default"]["username"] = credential.username
        d.credentials["default"]["password"] = credential.get_password()
        if credential.get_enable_secret():
            d.credentials.setdefault("enable", {})
            d.credentials["enable"]["password"] = credential.get_enable_secret()
    # Stash NetBox metadata so downstream code (and the UI) can trace the
    # pyATS device back to the NetBox row and surface the supported/unsupported
    # status without re-querying.
    d.custom = {
        "netbox_pyats": {
            "netbox_device_id": netbox_device.pk,
            "netbox_device_name": netbox_device.name,
            "platform_slug": getattr(netbox_device.platform, "slug", None) if netbox_device.platform else None,
            "os": os_value,
            "supported": supported,
            "mgmt_ip": mgmt_ip,
            "credential_id": credential.pk if credential else None,
        }
    }
    return d, status


def _pyats_testbed_cls():
    """Lazy import of pyATS Testbed class.

    pyATS is an optional install (worker-only); the NetBox web process imports
    this module without pyats installed. We only need the class when
    build_testbed is actually called, which happens on the worker.
    """
    from pyats.topology import Testbed

    return Testbed


def _pyats_device_cls():
    """Lazy import of pyATS Device class (see _pyats_testbed_cls)."""
    from pyats.topology import Device

    return Device


def build_testbed(
    device_qs,
    *,
    name: str = "netbox-pyats",
    on_unsupported: str = "flag",
    credential_resolver=_resolve_credential,
):
    """Build a pyATS :class:`Testbed` from a NetBox Device queryset.

    This is the core NetBox→pyATS bridge. For each NetBox Device we resolve its
    pyATS ``os`` from the Platform, attach the management IP from
    ``primary_ip4``/``primary_ip6``, and attach the device's
    :class:`PyatsCredential` (plaintext, in-memory only).

    Multi-vendor graceful degradation: devices whose Platform has no matching
    Genie parser are surfaced with ``os = 'unsupported - no parser'`` and
    ``custom['netbox_pyats']['supported'] = False``. They are included on the
    testbed by default (``on_unsupported="flag"``) so the UI can show them as
    unsupported; pass ``on_unsupported="skip"`` to omit them entirely (used by
    batch snapshot runs that silently skip unsupported devices).

    Args:
        device_qs: a NetBox Device queryset (or any iterable of Device-like
            objects with ``name``, ``platform``, ``primary_ip4``, ``device_type``).
        name: testbed name (appears in pyATS logs).
        on_unsupported: ``"flag"`` (include unsupported devices, marked) or
            ``"skip"`` (omit them).
        credential_resolver: callable(device) -> Optional[PyatsCredential].
            Overridable for tests (e.g. to inject a mock credential without
            touching the DB).

    Returns:
        A tuple ``(testbed, report)`` where ``testbed`` is the pyATS
        :class:`Testbed` and ``report`` is a :class:`TestbedBuildReport` with
        per-device supported/unsupported status and reasons, so the caller can
        surface a summary in the UI without re-iterating the testbed.
    """
    if on_unsupported not in ("flag", "skip"):
        raise ValueError(f"on_unsupported must be 'flag' or 'skip', got {on_unsupported!r}")

    Testbed = _pyats_testbed_cls()
    tb = Testbed(name=name)
    report = TestbedBuildReport()

    for netbox_device in _iter_devices(device_qs):
        credential = credential_resolver(netbox_device)
        d, status = _build_device_entry(
            netbox_device,
            credential=credential,
            on_unsupported=on_unsupported,
        )
        if d is None:
            # on_unsupported="skip" path
            report.add_unsupported(netbox_device, reason="unsupported platform - skipped")
            continue
        # ``Device(testbed=tb)`` would auto-attach in the constructor and make
        # ``tb.add_device(d)`` raise ``DuplicateDeviceError``. We construct the
        # Device *without* a testbed and attach it explicitly here so the
        # already-present edge case (re-iteration, name collision) is caught.
        try:
            tb.add_device(d)
        except Exception:
            # If the device is already on the testbed (e.g. re-iteration, or a
            # duplicate name), skip rather than crash the whole build.
            logger.warning("netbox_pyats: device %s already on testbed, skipping", d.name)
            report.add_unsupported(netbox_device, reason="duplicate device name on testbed")
            continue
        if status == "supported":
            report.add_supported(netbox_device, d)
        else:
            report.add_unsupported(netbox_device, reason=f"platform maps to {UNSUPPORTED_OS}")
    return tb, report


def _iter_devices(device_qs) -> Iterable:
    """Yield devices from a queryset or plain iterable.

    Accepts either a Django queryset (iterate via ``.all()`` is not needed; the
    queryset is itself iterable) or a list/tuple. We do not materialize the
    queryset ourselves so callers can chain filters before passing it in.
    """
    # NetBox querysets are iterable directly; lists/tuples too.
    for d in device_qs:
        yield d


class TestbedBuildReport:
    """Summary of a :func:`build_testbed` run.

    Keeps track of which devices were included as supported, which were
    flagged as unsupported, and why — so the caller (UI view, RQ job) can
    surface a human-readable summary without re-iterating the testbed.
    """

    def __init__(self):
        self.supported: list[dict] = []
        self.unsupported: list[dict] = []

    def add_supported(self, netbox_device, pyats_device) -> None:
        self.supported.append(
            {
                "netbox_device_id": netbox_device.pk,
                "name": netbox_device.name,
                "pyats_device_name": pyats_device.name,
                "os": pyats_device.os,
                "mgmt_ip": pyats_device.custom["netbox_pyats"]["mgmt_ip"],
            }
        )

    def add_unsupported(self, netbox_device, *, reason: str) -> None:
        self.unsupported.append(
            {
                "netbox_device_id": netbox_device.pk,
                "name": netbox_device.name,
                "reason": reason,
            }
        )

    @property
    def total(self) -> int:
        return len(self.supported) + len(self.unsupported)

    @property
    def ok(self) -> bool:
        """True if at least one device was supported AND none errored.

        ``build_testbed`` never raises for unsupported platforms (they are
        flagged/skipped), so ``ok`` is effectively "did we get any workable
        devices". Batch callers can use this to short-circuit an empty run.
        """
        return bool(self.supported)

    def summary(self) -> str:
        return f"{len(self.supported)} supported, {len(self.unsupported)} unsupported " f"({self.total} total)"
