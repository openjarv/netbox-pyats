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
    set (see :data:`netbox_pyats.capture.STATE_COMMANDS`), each parsed via
    ``device.parse(...)``; commands whose parser is missing for the device's
    os are skipped with a warning. ``full`` runs both and stores them under
    ``data["config"]`` and ``data["state"]`` respectively, so a single row
    captures a complete pre/post-change picture.

    ``parse`` (ATW-241 child 3) is the on-demand, user-driven capture: the
    operator types or selects one or more CLI commands on the device-page
    PyATS tab and the worker runs ``device.parse(<command>)`` for each, then
    stores the parsed outputs under ``data["state"]`` — the **same shape** the
    automated ``state`` capture writes — so the existing snapshot detail
    template, diff engine, and compliance engine work unchanged. When a
    command has no Genie parser (the manual text-box case), the worker falls
    back to raw ``device.execute(<command>)`` output (matching ``genie parse``
    CLI behavior); if that also fails, the command is recorded in
    ``parser_warnings``. ``parse`` captures are always
    ``triggered_by='user'`` (see :class:`SnapshotTriggerChoices`).
    """

    KIND_CONFIG = "config", "Config"
    KIND_STATE = "state", "State"
    KIND_FULL = "full", "Full (config + state)"
    KIND_PARSE = "parse", "Parse (on-demand commands)"


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


class ComplianceModeChoices(models.TextChoices):
    """How :func:`netbox_pyats.compliance.run_compliance` compares configs.

    ``ordered`` (v2, default) compares the golden and snapshot config lines as
    an **ordered sequence** — a longest-common-subsequence diff via
    :mod:`difflib`. This catches order-sensitive drift (ACL entry order,
    route-map sequence, interface definition order) that the v1 set diff
    misses, while still detecting added/removed/changed lines. The diff tree
    has the same leaf shape as the v1 set diff (``unchanged`` / ``added`` /
    ``removed`` keyed by line) so the Phase 3 ``inc/diff_tree.html`` partial
    renders it unchanged. ``summary["changed"]`` is always 0 for the ordered
    diff too — a "changed" line is reported as a ``removed`` (the golden's
    line) + an ``added`` (the snapshot's line), same as the set diff.

    ``set`` (v1) compares lines as an order-independent set. A re-ordered
    config classifies as ``compliant`` — correct for "does the device carry
    the golden lines?" but it misses ACL/route-map/interface order drift.
    Kept as an explicit opt-in for operators who want the v1 semantics (e.g.
    configs whose section order legitimately varies between captures and is
    not a compliance concern).

    Both modes are pure-Python and Genie-free: they compare the golden
    ``config_text`` against the snapshot's ``data["config_raw"]`` raw
    running-config text, both stored as plain strings. No worker-only Genie
    parse of the golden is needed (ADR-0004 v2 note: parsing the golden with
    the same Genie parser as the snapshot would require a live device
    connection, which breaks the "no extra SSH round-trip" Phase 4 contract;
    the ordered text diff delivers the order-sensitive drift detection
    without that cost). See ADR-0004 §"v2 ordered text diff".
    """

    MODE_ORDERED = "ordered", "Ordered (sequence-aware)"
    MODE_SET = "set", "Set (order-independent, v1)"


class PyatsJobTypeChoices(models.TextChoices):
    """Kind of plugin job a :class:`PyatsJob` row tracks (Phase 5, ATW-16).

    Extends the plugin's job-tracking surface (ADR-0005 §1) so the unified jobs
    view can filter by the kind of work. ``capture`` / ``diff`` / ``compliance``
    are the single-device jobs shipped in Phases 2/3/4; ``batch_capture`` is
    the multi-device batch capture introduced in Phase 5; ``parse`` is the
    on-demand, user-driven parse job (ATW-241 child 3) that runs an explicit
    command list via ``device.parse(...)`` with a raw ``execute()`` fallback.
    ``refresh_parser_catalog`` is the worker-only catalog refresh introduced
    by ATW-241 child 1 (ATW-249): it rebuilds the
    :class:`PyatsParserCatalog` rows from the installed ``genie.libs`` parser
    registry. Each maps 1:1 to an ``enqueue_*`` helper in
    :mod:`netbox_pyats.jobs`.
    """

    JOB_CAPTURE = "capture", "Capture"
    JOB_DIFF = "diff", "Diff"
    JOB_COMPLIANCE = "compliance", "Compliance"
    JOB_BATCH_CAPTURE = "batch_capture", "Batch capture"
    JOB_PARSE = "parse", "Parse (on-demand)"
    JOB_REFRESH_PARSER_CATALOG = "refresh_catalog", "Refresh parser catalog"


class PyatsJobStatusChoices(models.TextChoices):
    """Lifecycle status of a :class:`PyatsJob` row (Phase 5, ATW-16).

    Extends ADR-0002's status-vocabulary table (see ADR-0005 §2). ``pending`` is
    set at enqueue, before the worker picks the job up. ``running`` is set by
    the job callable at entry. ``success`` is set when the job produced its
    result row (the result row itself may be ``unsupported`` — that is a
    successful *job* producing an unsupported *row*, per ADR-0002). ``error`` is
    set when the job raised and the result row could not be written
    (``PyatsJob.error`` carries the exception text; the job re-raises so
    RQ/``core.Job`` is also marked failed). ``partial`` is the batch-only
    status for a batch that completed without crashing but had per-device
    failures or unsupported platforms (``PyatsJob.summary`` carries the counts).

    The per-result-row statuses (``PyatsSnapshot.status``,
    ``PyatsSnapshotDiff.status``, ``PyatsComplianceRun.result``) are unchanged
    — ADR-0002's contract on the result rows holds exactly. ``PyatsJob.status``
    is the job-level mirror; the result row is the outcome-level record.
    """

    STATUS_PENDING = "pending", "Pending"
    STATUS_RUNNING = "running", "Running"
    STATUS_SUCCESS = "success", "Success"
    STATUS_ERROR = "error", "Error"
    STATUS_PARTIAL = "partial", "Partial"
