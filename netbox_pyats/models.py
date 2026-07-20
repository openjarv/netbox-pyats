"""Models for the netbox-pyats plugin.

Phase 1 (ATW-12) shipped :class:`PyatsCredential`, a plugin-local encrypted
store for device credentials used to build pyATS testbeds. Passwords and
enable secrets are encrypted at rest with Fernet (`netbox_pyats.crypto`); only
ciphertext is ever persisted to the database.

Phase 2 (ATW-13) adds :class:`PyatsSnapshot`, a JSONB-backed row per captured
config/state/full snapshot, written by the `capture_snapshot` RQ job. Later
phases add :class:`PyatsGoldenConfig`, :class:`PyatsComplianceRun`,
and :class:`PyatsJob` (see the ATW-10 build plan, §3) — each in its own
migration, in the phase that introduces it.

Phase 3 (ATW-14) adds :class:`PyatsSnapshotDiff`, a JSONB-backed structured
diff between two :class:`PyatsSnapshot` rows of the same device, written by the
`run_diff` RQ job.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from . import crypto
from .choices import (
    ComplianceResultChoices,
    CredentialProtocolChoices,
    CredentialScopeChoices,
    DiffStatusChoices,
    GoldenConfigSourceChoices,
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
            raise ValidationError({"device": "A per-device credential must have a device assigned."})
        if self.scope == CredentialScopeChoices.SCOPE_GLOBAL and self.device_id:
            raise ValidationError({"device": "A global credential must not be bound to a specific device."})


class PyatsSnapshot(NetBoxModel):
    """One captured config/state/full snapshot for a NetBox Device.

    Populated by the ``capture_snapshot`` RQ job (see ``netbox_pyats.jobs``).
    The job builds a pyATS testbed from the NetBox Device + its
    :class:`PyatsCredential`, connects via Unicon, runs parser-based config
    capture (``show running-config``) and/or state capture (a small
    OS-agnostic command set via ``device.parse(...)``), serializes the
    result to JSON, and stores it in :attr:`data` (JSONB).

    Multi-vendor graceful degradation: if the device's platform has no Genie
    parser, the job writes a row with ``status=unsupported``, an empty
    ``data`` payload, and a ``parser_warnings`` entry explaining the skip —
    so the device-page PyATS tab can surface "unsupported" in the history
    rather than silently omitting the device. Capture errors are recorded
    with ``status=error`` and the exception message in ``parser_warnings``;
    the row is still created so the operator sees the failure in-line.

    The ``data`` payload shape depends on ``kind``:

    - ``config``: ``{"config": {<parsed show-running-config output>}}``
    - ``state``:  ``{"state": {<command: <parsed output>, ...>}}`` — one entry
      per command in :data:`netbox_pyats.capture.STATE_COMMANDS`; commands
      whose parser is missing for the device's os are recorded as ``None``
      with a warning.
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
            # Explicit names match 0002_pyatssnapshot and pin the indexes against
            # Django 5.x auto-rename suggestions (see ATW-32).
            models.Index(fields=("device", "-captured_at"), name="pyats_snap_dev_capt_idx"),
            models.Index(fields=("device", "kind", "-captured_at"), name="pyats_snap_dev_kind_idx"),
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


class PyatsSnapshotDiff(NetBoxModel):
    """One structured diff between two :class:`PyatsSnapshot` rows of a device.

    Populated by the ``run_diff`` RQ job (see ``netbox_pyats.jobs``). The job
    loads two snapshots of the same device, runs
    :func:`netbox_pyats.diff.diff_snapshots` over their ``data`` JSONB, and
    stores the structured diff tree plus a flat summary of counts (added /
    removed / changed / unchanged) on this row.

    Why a recursive JSONB diff rather than ``Genie.diff``: the stored snapshots
    are *already-serialized* JSONB (the output of ``device.parse(...)``), detached
    from the live Genie object model. ``Genie.diff`` operates on Genie's own
    runtime objects; by the time a diff is requested the worker only has the
    persisted JSONB. A recursive diff over the JSONB is portable, deterministic,
    and testable without Genie installed (see ``netbox_pyats.diff``). This
    mirrors the Phase 2 decision to use ``device.parse(...)`` rather than the
    non-existent top-level ``genie.learn``.

    Multi-vendor graceful degradation carries through from Phase 2: diffing two
    empty (unsupported-platform) snapshots yields ``status="empty"`` with a
    neutral badge rather than erroring; diffing two snapshots whose data is
    malformed yields ``status="error"`` with a warning. The row is still created
    so the operator sees the outcome in-line, consistent with Phase 2's
    unsupported/error snapshot rows.

    The ``diff`` payload shape is::

        {
          "name": "root",
          "type": "dict",
          "status": "changed" | "unchanged",
          "children": {
            <key>: {
              "type": "dict" | "list" | "leaf" | "string" | ...,
              "status": "added" | "removed" | "changed" | "unchanged",
              # container nodes: "children": {<nested>}
              # added leaf: "after": <value>
              # removed leaf: "before": <value>
              # changed leaf: "before": <v1>, "after": <v2>
              # unchanged leaf: "value": <v>
            },
            ...
          }
        }
    """

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pyats_snapshot_diffs",
        help_text="NetBox device whose snapshots were diffed (must match both before and after).",
    )
    before = models.ForeignKey(
        to="netbox_pyats.PyatsSnapshot",
        on_delete=models.CASCADE,
        related_name="diffs_as_before",
        help_text="The earlier snapshot (the 'before' side of the diff).",
    )
    after = models.ForeignKey(
        to="netbox_pyats.PyatsSnapshot",
        on_delete=models.CASCADE,
        related_name="diffs_as_after",
        help_text="The later snapshot (the 'after' side of the diff).",
    )
    status = models.CharField(
        max_length=20,
        choices=DiffStatusChoices,
        default=DiffStatusChoices.STATUS_SUCCESS,
        help_text="Outcome of the diff: success, empty inputs, or error.",
    )
    diff = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "Structured diff tree as JSON. Root is a dict node with children "
            "keyed by snapshot key; each child is an added/removed/changed/"
            "unchanged leaf or a nested container. Rendered as a collapsible "
            "tree in the diff viewer."
        ),
    )
    summary = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "Flat counts per status: {added, removed, changed, unchanged}. "
            "Surfaced as a compact summary in the diff list and viewer header."
        ),
    )
    parser_warnings = models.JSONField(
        blank=True,
        default=list,
        help_text=(
            "List of human-readable warnings/errors from the diff: malformed "
            "input payloads, etc. Empty for clean diffs."
        ),
    )
    size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of the JSON-serialized `diff` payload in bytes (set by the job).",
    )

    clone_fields = ("device",)

    class Meta:
        ordering = ("-created",)
        verbose_name = "PyATS Snapshot Diff"
        verbose_name_plural = "PyATS Snapshot Diffs"
        indexes = [
            # Most common queries: "recent diffs for this device" and
            # "diffs between snapshots of this device by status".
            # Explicit names match 0003_pyatssnapshotdiff and pin the indexes
            # against Django 5.x auto-rename suggestions (see ATW-32).
            models.Index(fields=("device", "-created"), name="pyats_diff_dev_created_idx"),
            models.Index(fields=("device", "status", "-created"), name="pyats_diff_dev_status_idx"),
        ]

    def __str__(self):
        return (
            f"{self.device} · diff {self.before_id}→{self.after_id} · "
            f"{self.get_status_display()} · {self.created:%Y-%m-%d %H:%M:%S}"
        )

    def get_absolute_url(self):
        return reverse("plugins:netbox_pyats:pyatssnapshotdiff", kwargs={"pk": self.pk})

    def get_status_color(self):
        """Map status to a NetBox color label for table badges."""
        return {
            DiffStatusChoices.STATUS_SUCCESS: "success",
            DiffStatusChoices.STATUS_EMPTY: "secondary",
            DiffStatusChoices.STATUS_ERROR: "danger",
        }.get(self.status, "secondary")

    @property
    def has_changes(self) -> bool:
        """True if the diff found any added/removed/changed leaves."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))

    @property
    def has_warnings(self) -> bool:
        """True if this diff row carries warnings / error context."""
        return bool(self.parser_warnings)


class PyatsGoldenConfig(NetBoxModel):
    """A golden / reference running-config for a NetBox Device (Phase 4, ATW-15).

    The operator's "expected" device config. The compliance pipeline diffs a
    captured :class:`PyatsSnapshot` against one of these rows and classifies
    the device as ``compliant`` / ``drift`` / ``error`` (see
    :class:`PyatsComplianceRun`).

    v1 uses simple Genie abstract-config diff against the snapshot's
    ``data["config"]`` payload: the golden ``config_text`` is parsed into a
    JSON-serializable dict (when a snapshot is available to drive the parser)
    and diffed with :func:`netbox_pyats.diff.diff_snapshots`. Feature-specific
    compliance rules (e.g. "interface X must be present with MTU 1500") are
    deferred to v2 — v1 answers "does the running config match the golden?".

    The ``config_text`` is operator-authored free text (or promoted from a
    snapshot via the "use snapshot as golden" flow). ``source`` records whether
    it was typed manually or derived from a snapshot, so the compliance history
    can show provenance without re-deriving it. Multiple golden configs per
    device are allowed (e.g. "baseline", "post-maintenance-window"); the
    compliance picker lets the operator choose which golden to compare against.
    """

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pyats_golden_configs",
        help_text="NetBox device this golden config applies to.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable label, e.g. 'baseline-rtr01'.",
    )
    config_text = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Golden running-config text (the 'expected' device config). "
            "Diffed against a snapshot's parsed config payload by the "
            "compliance pipeline. May be empty only for a placeholder golden; "
            "compliance runs against an empty golden classify as 'error'."
        ),
    )
    source = models.CharField(
        max_length=20,
        choices=GoldenConfigSourceChoices,
        default=GoldenConfigSourceChoices.SOURCE_MANUAL,
        help_text="How the golden config was authored: typed manually or promoted from a snapshot.",
    )
    source_snapshot = models.ForeignKey(
        to="netbox_pyats.PyatsSnapshot",
        on_delete=models.SET_NULL,
        related_name="golden_configs_promoted_from",
        blank=True,
        null=True,
        help_text=(
            "When source=snapshot, the PyatsSnapshot row this golden config was "
            "promoted from. Null for manually-authored goldens. Kept for "
            "provenance so the compliance history can link back to the "
            "known-good snapshot."
        ),
    )

    clone_fields = ("device", "source")

    class Meta:
        ordering = ("device__name", "name")
        verbose_name = "PyATS Golden Config"
        verbose_name_plural = "PyATS Golden Configs"
        constraints = [
            # A golden config is unique by (device, name) so the compliance
            # picker can label each golden unambiguously per device. The
            # UniqueConstraint implicitly creates a B-tree index on
            # (device, name), so there is no separate `indexes` entry here —
            # Django 5.2's models.E041 system check rejects an explicit Index
            # that overlaps a UniqueConstraint on the same field set, and
            # Postgres already backs the unique constraint with an index.
            models.UniqueConstraint(
                fields=("device", "name"),
                name="netbox_pyats_goldenconfig_unique_per_device",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.device})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pyats:pyatsgoldenconfig", kwargs={"pk": self.pk})

    @property
    def is_from_snapshot(self) -> bool:
        """True if this golden config was promoted from a snapshot row."""
        return self.source == GoldenConfigSourceChoices.SOURCE_SNAPSHOT


class PyatsComplianceRun(NetBoxModel):
    """One compliance check result: golden config vs. captured snapshot (Phase 4, ATW-15).

    Populated by the ``run_compliance`` RQ job (see ``netbox_pyats.jobs``). The
    job loads a :class:`PyatsGoldenConfig` and a :class:`PyatsSnapshot` for the
    same device, diffs the snapshot's parsed config payload against the golden
    config text (parsed into a comparable dict), and classifies the device as
    ``compliant`` (no drift), ``drift`` (differences found), or ``error`` (bad
    inputs / unsupported platform / job raised). The structured diff tree is
    stored in ``diff`` (same shape as :class:`PyatsSnapshotDiff.diff`) and the
    flat summary counts in ``summary``, so the compliance run detail page can
    reuse the Phase 3 diff-tree viewer partial.

    Why JSONB ``diff`` rather than just a pass/fail flag: the operator needs to
    see *what* drifted, not just that it did. The same recursive JSONB diff
    engine from Phase 3 (:func:`netbox_pyats.diff.diff_snapshots`) is reused —
    the snapshot's config payload is already a parsed dict (Genie's structured
    output of ``show running-config``), and the golden config text is parsed
    into the same shape on the worker. This keeps the compliance viewer
    identical to the diff viewer, with zero new rendering code.

    Multi-vendor graceful degradation carries through from Phase 2/3: a
    compliance run against an unsupported-platform snapshot (empty ``data``)
    is classified as ``error`` with a warning, not silently skipped — the row
    is still created so the operator sees the failure in the compliance
    history, mirroring Phase 2's unsupported/error snapshot rows and Phase 3's
    empty/error diff rows.

    The ``diff`` payload shape is the same as :class:`PyatsSnapshotDiff.diff`
    (see that model's docstring) so the ``inc/diff_tree.html`` partial renders
    it unchanged.
    """

    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="pyats_compliance_runs",
        help_text="NetBox device this compliance run checked (must match both golden and snapshot).",
    )
    golden = models.ForeignKey(
        to="netbox_pyats.PyatsGoldenConfig",
        on_delete=models.CASCADE,
        related_name="compliance_runs",
        help_text="The golden config this run compared against.",
    )
    snapshot = models.ForeignKey(
        to="netbox_pyats.PyatsSnapshot",
        on_delete=models.CASCADE,
        related_name="compliance_runs",
        help_text="The snapshot this run compared against the golden config.",
    )
    result = models.CharField(
        max_length=20,
        choices=ComplianceResultChoices,
        default=ComplianceResultChoices.RESULT_ERROR,
        help_text="Compliance outcome: compliant, drift, or error.",
    )
    diff = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "Structured diff tree as JSON (same shape as PyatsSnapshotDiff.diff) "
            "showing golden vs. snapshot config differences. Empty for compliant "
            "and error runs (no tree to render). Rendered with the Phase 3 "
            "diff-tree viewer partial."
        ),
    )
    summary = models.JSONField(
        blank=True,
        default=dict,
        help_text=(
            "Flat counts per diff status: {added, removed, changed, unchanged}. "
            "All zero for compliant runs; non-zero for drift; empty for error."
        ),
    )
    parser_warnings = models.JSONField(
        blank=True,
        default=list,
        help_text=(
            "List of human-readable warnings/errors from the compliance run: "
            "unsupported platform, empty golden, snapshot missing config, "
            "diff engine errors. Empty for clean compliant/drift runs."
        ),
    )
    size_bytes = models.PositiveBigIntegerField(
        default=0,
        help_text="Size of the JSON-serialized `diff` payload in bytes (set by the job).",
    )

    clone_fields = ("device",)

    class Meta:
        ordering = ("-created",)
        verbose_name = "PyATS Compliance Run"
        verbose_name_plural = "PyATS Compliance Runs"
        indexes = [
            # Most common queries: "recent compliance runs for this device" and
            # "runs for this device by result" (compliance history picker).
            models.Index(fields=("device", "-created"), name="pyats_compl_dev_created_idx"),
            models.Index(fields=("device", "result", "-created"), name="pyats_compl_dev_result_idx"),
        ]

    def __str__(self):
        return (
            f"{self.device} · {self.get_result_display()} · "
            f"golden #{self.golden_id} vs snapshot #{self.snapshot_id} · "
            f"{self.created:%Y-%m-%d %H:%M:%S}"
        )

    def get_absolute_url(self):
        return reverse("plugins:netbox_pyats:pyatscompliancerun", kwargs={"pk": self.pk})

    def get_result_color(self):
        """Map result to a NetBox color label for table badges."""
        return {
            ComplianceResultChoices.RESULT_COMPLIANT: "success",
            ComplianceResultChoices.RESULT_DRIFT: "warning",
            ComplianceResultChoices.RESULT_ERROR: "danger",
        }.get(self.result, "secondary")

    @property
    def has_drift(self) -> bool:
        """True if the diff found any added/removed/changed leaves (drift)."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))

    @property
    def has_warnings(self) -> bool:
        """True if this compliance run row carries warnings / error context."""
        return bool(self.parser_warnings)
