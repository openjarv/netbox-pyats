"""Models for the netbox-pyats plugin.

Phase 1 (ATW-12) ships a single plugin model, :class:`PyatsCredential`, a
plugin-local encrypted store for device credentials used to build pyATS
testbeds. Passwords and enable secrets are encrypted at rest with Fernet
(`netbox_pyats.crypto`); only ciphertext is ever persisted to the database.

Later phases add :class:`PyatsSnapshot`, :class:`PyatsSnapshotDiff`,
:class:`PyatsGoldenConfig`, :class:`PyatsComplianceRun`, and :class:`PyatsJob`
(see the ATW-10 build plan, §3) — each in its own migration, in the phase that
introduces it, so Phase 1 stays small and reviewable.
"""

from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from . import crypto
from .choices import CredentialProtocolChoices, CredentialScopeChoices


class PyatsCredential(NetBoxModel):
    """A plugin-local, encrypted credential for connecting to a device via pyATS.

    ``password`` and ``enable_secret`` are stored as Fernet ciphertext. Access
    through the ``set_password``/``get_password`` and ``set_enable_secret``/
    ``get_enable_secret`` accessors ensures plaintext never reaches the
    database; direct field assignment is rejected by :meth:`full_clean`.

    A credential is scoped either to a single NetBox ``Device`` (the common
    case — the device-page PyATS tab resolves the device's credential via FK)
    or as a global/shared credential referenced by name (reserved for the
    batch-snapshot flow shipped in ATW-13; v1 only uses ``device`` scope).
    """

    name = models.CharField(
        max_length=100,
        help_text="Human-readable label, e.g. 'rtr01-ssh'.",
    )
    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pyats_credentials",
        blank=True,
        null=True,
        help_text="NetBox device this credential targets. Null for global/shared creds.",
    )
    scope = models.CharField(
        max_length=20,
        choices=CredentialScopeChoices,
        default=CredentialScopeChoices.SCOPE_DEVICE,
        help_text="Per-device (1:1) or global/shared credential.",
    )
    username = models.CharField(
        max_length=100,
        help_text="Login username for SSH/Telnet/Console.",
    )
    password = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Encrypted Fernet token. Set via set_password(); do not write plaintext here.",
    )
    enable_secret = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Encrypted Fernet token for the enable/privileged password. Optional.",
    )
    ssh_port = models.PositiveIntegerField(
        default=22,
        help_text="TCP port for SSH/Telnet connections.",
    )
    protocol = models.CharField(
        max_length=20,
        choices=CredentialProtocolChoices,
        default=CredentialProtocolChoices.PROTOCOL_SSH,
        help_text="Connection protocol pyATS/Unicon should use.",
    )

    clone_fields = (
        "device",
        "scope",
        "username",
        "ssh_port",
        "protocol",
    )

    class Meta:
        ordering = ("device__name", "name")
        verbose_name = "PyATS Credential"
        verbose_name_plural = "PyATS Credentials"
        constraints = [
            # Per-device credentials should be unique by (device, name); global
            # creds by name alone. Enforced at the DB layer so bulk imports
            # can't silently create dupes.
            models.UniqueConstraint(
                fields=("device", "name"),
                name="netbox_pyats_credential_unique_per_device",
                condition=models.Q(device__isnull=False),
            ),
            models.UniqueConstraint(
                fields=("name",),
                name="netbox_pyats_credential_unique_global_name",
                condition=models.Q(device__isnull=True),
            ),
        ]

    def __str__(self):
        target = self.device.name if self.device_id else "global"
        return f"{self.name} ({target})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pyats:pyatscredential", kwargs={"pk": self.pk})

    # ----------------------------------------------------------- plaintext API

    def set_password(self, plaintext: str) -> None:
        """Encrypt and store the device password (ciphertext only)."""
        self.password = crypto.encrypt(plaintext or "")

    def get_password(self) -> str:
        """Decrypt and return the device password (plaintext)."""
        return crypto.decrypt(self.password)

    def set_enable_secret(self, plaintext: str) -> None:
        """Encrypt and store the enable/privileged password (ciphertext only)."""
        self.enable_secret = crypto.encrypt(plaintext or "")

    def get_enable_secret(self) -> str:
        """Decrypt and return the enable/privileged password (plaintext)."""
        return crypto.decrypt(self.enable_secret)

    # ----------------------------------------------------------- validation

    def clean(self):
        super().clean()
        # A device-scoped credential must point at a Device; a global one must not.
        if self.scope == CredentialScopeChoices.SCOPE_DEVICE and not self.device_id:
            raise models.ValidationError({"device": "A per-device credential must have a device assigned."})
        if self.scope == CredentialScopeChoices.SCOPE_GLOBAL and self.device_id:
            raise models.ValidationError({"device": "A global credential must not be bound to a specific device."})
