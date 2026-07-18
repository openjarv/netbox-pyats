"""Models for the netbox-pyats plugin.

Phase 1 (ATW-12) shipped :class:`PyatsCredential`, a plugin-local encrypted
store for device credentials used to build pyATS testbeds. Passwords and
enable secrets are encrypted at rest with Fernet (`netbox_pyats.crypto`); only
ciphertext is ever persisted to the database.

Phase 2 (ATW-13) adds :class:`PyatsSnapshot`, a JSONB-backed row per captured
config/state/full snapshot, written by the `capture_snapshot` RQ job. Later
phases add :class:`PyatsSnapshotDiff`, :class:`PyatsGoldenConfig`,
:class:`PyatsComplianceRun`, and :class:`PyatsJob` (see the ATW-10 build plan,
§3) — each in its own migration, in the phase that introduces it.
"""

from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from . import crypto
from .choices import (
    CredentialProtocolChoices,
    CredentialScopeChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)


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


class PyatsSnapshot(NetBoxModel):
    """One captured config/state/full snapshot for a NetBox Device.

    Populated by the ``capture_snapshot`` RQ job (see ``netbox_pyats.jobs``).
    The job builds a pyATS testbed from the NetBox Device + its
    :class:`PyatsCredential`, connects via Unicon, runs ``Genie.learn`` (state)
    and/or parser-based config capture, serializes the result to JSON, and
    stores it in :attr:`data` (JSONB).

    Multi-vendor graceful degradation: if the device's platform has no Genie
    parser, the job writes a row with ``status=unsupported``, an empty
    ``data`` payload, and a ``parser_warnings`` entry explaining the skip —
    so the device-page PyATS tab can surface "unsupported" in the history
    rather than silently omitting the device. Capture errors are recorded
    with ``status=error`` and the exception message in ``parser_warnings``;
    the row is still created so the operator sees the failure in-line.

    The ``data`` payload shape depends on ``kind``:

    - ``config``: ``{"config": {<parsed show-running output>}}``
    - ``state``:  ``{"state":  {<Genie.learn "ops" output>}}``
    - ``full``:   ``{"config": {...}, "state": {...}}``

    ``size_bytes`` is the length of the JSON-serialized ``data`` payload, set
    by the job so the UI can render it without re-serializing. ``genie_version``
    and ``pyats_version`` are captured from the worker environment so snapshots
    taken with different Genie releases are distinguishable (Genie's parsed
    output shape drifts between releases).
    """

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pyats_snapshots",
        help_text="NetBox device this snapshot was captured from.",
    )
    kind = models.CharField(
        max_length=20,
        choices=SnapshotKindChoices,
        default=SnapshotKindChoices.KIND_FULL,
        help_text="What was captured: config, state, or full (config + state).",
    )
    status = models.CharField(
        max_length=20,
        choices=SnapshotStatusChoices,
        default=SnapshotStatusChoices.STATUS_SUCCESS,
        help_text="Outcome of the capture: success, unsupported platform, or error.",
    )
    triggered_by = models.CharField(
        max_length=20,
        choices=SnapshotTriggerChoices,
        default=SnapshotTriggerChoices.TRIGGER_USER,
        help_text="Who/what initiated the capture: a user (manual) or a job (automated).",
    )
    captured_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the snapshot was captured (set on row creation).",
    )
    data = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "Captured snapshot payload as JSON. Shape depends on kind: "
            "config → {config: ...}, state → {state: ...}, full → {config, state}. "
            "Empty for unsupported/error rows."
        ),
    )
    parser_warnings = models.JSONField(
        blank=True,
        default=list,
        help_text=(
            "List of human-readable warnings/errors from the capture: parser "
            "unsupported messages, Unicon connection issues, exception text. "
            "Surfaced in the UI as a 'warnings' indicator on the snapshot row."
        ),
    )
    genie_version = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="genie version on the worker at capture time (e.g. '26.6').",
    )
    pyats_version = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="pyats version on the worker at capture time (e.g. '26.6').",
    )
    size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of the JSON-serialized `data` payload in bytes (set by the job).",
    )

    clone_fields = ("device", "kind", "triggered_by")

    class Meta:
        ordering = ("-captured_at",)
        verbose_name = "PyATS Snapshot"
        verbose_name_plural = "PyATS Snapshots"
        indexes = [
            # Most common queries: "recent snapshots for this device" and
            # "snapshots of this kind for this device" (diff/compliance pickers).
            models.Index(fields=("device", "-captured_at")),
            models.Index(fields=("device", "kind", "-captured_at")),
        ]

    def __str__(self):
        return f"{self.device} · {self.get_kind_display()} · {self.captured_at:%Y-%m-%d %H:%M:%S}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pyats:pyatssnapshot", kwargs={"pk": self.pk})

    def get_status_color(self):
        """Map status to a NetBox color label for table badges."""
        return {
            SnapshotStatusChoices.STATUS_SUCCESS: "success",
            SnapshotStatusChoices.STATUS_UNSUPPORTED: "warning",
            SnapshotStatusChoices.STATUS_ERROR: "danger",
        }.get(self.status, "secondary")

    @property
    def has_warnings(self) -> bool:
        """True if this snapshot row carries parser warnings / error context."""
        return bool(self.parser_warnings)
