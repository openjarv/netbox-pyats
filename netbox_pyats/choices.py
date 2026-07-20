"""Choice sets for the netbox-pyats plugin."""

from django.db import models


class CredentialProtocolChoices(models.TextChoices):
    """Connection protocol for a PyATS credential."""

    PROTOCOL_SSH = "ssh", "SSH"
    PROTOCOL_TELNET = "telnet", "Telnet"
    PROTOCOL_CONSOLE = "console", "Console"


class CredentialScopeChoices(models.TextChoices):
    """How a credential is assigned.

    ``device`` credentials attach to a single NetBox Device (1:1). ``global``
    credentials are not bound to a specific device and can be referenced by name
    from a testbed build (useful for shared lab creds).
    """

    SCOPE_DEVICE = "device", "Per device"
    SCOPE_GLOBAL = "global", "Global (shared)"


class SnapshotKindChoices(models.TextChoices):
    """What a :class:`PyatsSnapshot` captures from a device.

    ``config`` runs parser-based config capture (``show running-config`` via
    ``device.parse(...)``). ``state`` runs a small OS-agnostic state command
    set (``show version``, ``show inventory``, ``show ip interface brief``),
    each parsed via ``device.parse(...)``; commands whose parser is missing
    for the device's os are skipped with a warning. ``full`` runs both and
    stores them under ``data["config"]`` and ``data["state"]`` respectively,
    so a single row captures a complete pre/post-change picture.
    """

    KIND_CONFIG = "config", "Config"
    KIND_STATE = "state", "State"
    KIND_FULL = "full", "Full (config + state)"


class SnapshotTriggerChoices(models.TextChoices):
    """Who/what triggered a snapshot capture.

    ``user`` captures are initiated from the device-page PyATS tab (a logged-in
    operator clicked "Capture snapshot"). ``job`` captures are initiated by an
    automated flow (batch capture, scheduled run, compliance pipeline). The
    distinction is recorded so the snapshot history can show "captured by Alice"
    vs "captured by scheduled job" without re-deriving it.
    """

    TRIGGER_USER = "user", "User (manual)"
    TRIGGER_JOB = "job", "Job (automated)"


class SnapshotStatusChoices(models.TextChoices):
    """Outcome of a snapshot capture attempt.

    ``success`` means a JSONB ``data`` payload was written. ``unsupported`` means
    the device's platform has no Genie parser (the row is still created with an
    empty ``data`` and a ``parser_warnings`` entry explaining the skip, so the
    UI can surface "unsupported" in the history). ``error`` means the capture
    raised; the exception message is stored in ``parser_warnings``.
    """

    STATUS_SUCCESS = "success", "Success"
    STATUS_UNSUPPORTED = "unsupported", "Unsupported platform"
    STATUS_ERROR = "error", "Error"


class DiffStatusChoices(models.TextChoices):
    """Outcome of a snapshot diff (Phase 3, ATW-14).

    ``success`` means a structured diff JSONB tree was produced (it may be
    empty of changes — ``summary`` records the counts). ``empty`` means both
    input snapshots had no data (e.g. two unsupported-platform rows being
    diffed for completeness); the row is still created so the operator sees
    the outcome in-line, with a neutral badge rather than red. ``error`` means
    the diff inputs were malformed (non-dict top-level payloads) or the job
    raised; the exception message is stored in ``parser_warnings``.
    """

    STATUS_SUCCESS = "success", "Success"
    STATUS_EMPTY = "empty", "Empty inputs"
    STATUS_ERROR = "error", "Error"


class GoldenConfigSourceChoices(models.TextChoices):
    """How a :class:`PyatsGoldenConfig` row was authored (Phase 4, ATW-15).

    ``manual`` means an operator typed/pasted the golden config text directly
    in the NetBox UI (the common case — the "expected" running config). ``snapshot``
    means the golden config text was promoted from a captured snapshot's
    config payload, so the golden tracks a known-good device state. The
    distinction is recorded so the compliance history can show "golden authored
    by hand" vs "golden derived from snapshot #N" without re-deriving it.
    """

    SOURCE_MANUAL = "manual", "Manual"
    SOURCE_SNAPSHOT = "snapshot", "From snapshot"


class ComplianceResultChoices(models.TextChoices):
    """Outcome of a compliance run (Phase 4, ATW-15).

    ``compliant`` means the device's snapshot matched the golden config (the
    structured diff had no added/removed/changed leaves — ``summary`` counts
    are all zero for changes). ``drift`` means the structured diff found
    differences (added/removed/changed > 0); the operator sees the diff tree
    inline on the compliance run detail page. ``error`` means the inputs were
    malformed or the job raised (e.g. snapshot was unsupported/error, golden
    config was empty, or the diff engine returned an error status); the
    exception message is stored in ``parser_warnings`` and the row is still
    created so the operator sees the failure in-line, consistent with Phase 2/3.
    """

    RESULT_COMPLIANT = "compliant", "Compliant"
    RESULT_DRIFT = "drift", "Drift"
    RESULT_ERROR = "error", "Error"
