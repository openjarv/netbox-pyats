"""Models for the netbox_pyats plugin.

Phase 1 ships a single bookkeeping model, :class:`PyatsCredential`, which
stores per-device (or group) credentials with field-level Fernet encryption
for the secret fields. Later phases add :class:`PyatsSnapshot`,
:class:`PyatsSnapshotDiff`, :class:`PyatsGoldenConfig`,
:class:`PyatsComplianceRun`, and :class:`PyatsJob`.

The model is defined in two layers so the package stays importable without
NetBox installed (used by the pure-Python test suite and by environments that
only need the testbed builder / crypto helpers):

- When NetBox is importable, :class:`PyatsCredential` is a real
  :class:`netbox.models.NetBoxModel` with a FK to ``dcim.Device``.
- When NetBox is not importable, :class:`PyatsCredential` is a minimal
  non-ORM placeholder that exposes the same encryption helper surface
  (``set_password`` / ``get_password`` / ``set_enable_secret`` /
  ``get_enable_secret``) so tests and tooling can construct fixtures.
"""

from . import crypto
from .choices import CredentialProtocolChoices

try:
    from netbox.models import NetBoxModel

    _NETBOX_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - exercised in pure-Python tests
    _NETBOX_AVAILABLE = False

from django.db import models

if _NETBOX_AVAILABLE:
    # Real model registered inside a NetBox environment.
    class PyatsCredential(NetBoxModel):
        """Plugin-local encrypted credential for connecting to a device via pyATS.

        ``password`` and ``enable_secret`` are stored encrypted at rest with
        Fernet (see :mod:`netbox_pyats.crypto`). Plaintext is only resolved on
        demand by :func:`netbox_pyats.testbed.build_testbed` (and later, by
        the capture job).
        """

        name = models.CharField(max_length=100, help_text="Human-readable label for this credential.")
        device = models.ForeignKey(
            to="dcim.Device",
            on_delete=models.CASCADE,
            null=True,
            blank=True,
            related_name="pyats_credentials",
            help_text="Device this credential applies to. Leave blank for a group/shared credential.",
        )
        username = models.CharField(max_length=100)
        password = models.CharField(
            max_length=512,
            help_text="Encrypted at rest with Fernet. Set the plaintext value; it is encrypted on save.",
        )
        enable_secret = models.CharField(
            max_length=512,
            blank=True,
            default="",
            help_text="Optional enable secret. Encrypted at rest with Fernet.",
        )
        ssh_port = models.PositiveIntegerField(default=22, help_text="SSH/Telnet TCP port.")
        protocol = models.CharField(
            max_length=10,
            choices=CredentialProtocolChoices,
            default=CredentialProtocolChoices.PROTOCOL_SSH,
            help_text="Transport protocol used for the pyATS connection.",
        )

        # In-memory plaintext cache (not persisted) for the encrypt-on-save path.
        _plaintext_password: str | None = None
        _plaintext_enable_secret: str | None = None

        class Meta:
            ordering = ("name", "device__name")
            verbose_name = "PyATS Credential"
            verbose_name_plural = "PyATS Credentials"
            constraints = [
                models.UniqueConstraint(
                    fields=("device",),
                    name="netbox_pyats_credential_one_per_device",
                    condition=models.Q(device__isnull=False),
                ),
            ]

        def __str__(self) -> str:
            if getattr(self, "device_id", None):
                return f"{self.name} ({self.device})"
            return self.name

        def get_absolute_url(self) -> str:
            from django.urls import reverse

            return reverse("plugins:netbox_pyats:pyatscredential", kwargs={"pk": self.pk})

        def set_password(self, plaintext: str) -> None:
            self._plaintext_password = plaintext or ""

        def set_enable_secret(self, plaintext: str) -> None:
            self._plaintext_enable_secret = plaintext or ""

        def get_password(self) -> str:
            if self._plaintext_password is not None:
                return self._plaintext_password
            return crypto.decrypt(self.password)

        def get_enable_secret(self) -> str:
            if self._plaintext_enable_secret is not None:
                return self._plaintext_enable_secret
            return crypto.decrypt(self.enable_secret)

        def save(self, *args, **kwargs):
            if self._plaintext_password is not None:
                self.password = crypto.encrypt(self._plaintext_password)
                self._plaintext_password = None
            if self._plaintext_enable_secret is not None:
                self.enable_secret = crypto.encrypt(self._plaintext_enable_secret)
                self._plaintext_enable_secret = None
            super().save(*args, **kwargs)

else:
    # Minimal non-ORM placeholder so the package imports without NetBox.
    # The pure-Python test suite does not exercise the ORM path; it constructs
    # fixture credentials directly and only asserts on the encryption helpers.
    class PyatsCredential:  # type: ignore[no-redef]
        """Non-ORM placeholder for environments without NetBox.

        Exposes the same encryption-helper surface as the real model so tooling
        and tests can build fixture credentials. Not persisted.
        """

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self._plaintext_password = None
            self._plaintext_enable_secret = None

        def set_password(self, plaintext: str) -> None:
            self._plaintext_password = plaintext or ""

        def set_enable_secret(self, plaintext: str) -> None:
            self._plaintext_enable_secret = plaintext or ""

        def get_password(self) -> str:
            if self._plaintext_password is not None:
                return self._plaintext_password
            return crypto.decrypt(getattr(self, "password", "") or "")

        def get_enable_secret(self) -> str:
            if self._plaintext_enable_secret is not None:
                return self._plaintext_enable_secret
            return crypto.decrypt(getattr(self, "enable_secret", "") or "")
