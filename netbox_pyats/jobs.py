"""NetBox background jobs for the netbox-pyats plugin.

Phase 2 (ATW-13) ships the ``capture_snapshot`` RQ job, which runs
:func:`netbox_pyats.capture.capture_snapshot_for_netbox_device` against a
NetBox Device and persists the result as a
:class:`netbox_pyats.models.PyatsSnapshot` row.

Phase 3 (ATW-14) adds the ``run_diff`` RQ job, which loads two
:class:`PyatsSnapshot` rows of the same device, runs
:func:`netbox_pyats.diff.diff_snapshots` over their ``data`` JSONB, and
persists the structured diff as a :class:`PyatsSnapshotDiff` row.

Phase 4 (ATW-15) adds the ``run_compliance`` RQ job, which loads a
:class:`PyatsGoldenConfig` row and a :class:`PyatsSnapshot` row for the same
device, parses the golden ``config_text`` into a comparable dict on the
worker (using the snapshot's own parsed config as the parsing scaffold, so
no extra device connection is needed), runs
:func:`netbox_pyats.compliance.run_compliance` over golden vs. snapshot
config, and persists the classified result as a :class:`PyatsComplianceRun`
row. The diff tree has the same shape as :class:`PyatsSnapshotDiff.diff`, so
the Phase 3 diff-tree viewer partial renders it unchanged.

Queue isolation: all three jobs run on the dedicated ``pyats`` RQ queue
(declared via :attr:`NetBoxPyATSConfig.queues`), so pyATS/Genie work — which
requires ``pyats[full]`` installed on the worker — does not block NetBox's
default RQ workers. The diff and compliance jobs themselves do not need
pyATS installed (they operate on persisted JSONB), but they still run on the
``pyats`` queue for isolation and so a single worker image services all
plugin work; an operator who only wants diffs/compliance can run the default
worker if they prefer (no pyATS install needed for diffs/compliance alone
when the golden config is already parsed — v1 parses the golden text using
the snapshot's parsed config as a scaffold, so no live device connection is
required for compliance).

The web process enqueues via :func:`enqueue_capture` / :func:`enqueue_diff`
/ :func:`enqueue_compliance`, passing the NetBox Device and capture/diff/
compliance kwargs. NetBox's :class:`core.models.Job` tracks the run (status,
log entries, notifications); the actual RQ work is the module-level
:func:`capture_snapshot_job` / :func:`run_diff_job` /
:func:`run_compliance_job` callable, which the worker invokes with the Job
row plus the kwargs.
"""

from __future__ import annotations

import logging
import traceback

from .choices import SnapshotKindChoices, SnapshotTriggerChoices

logger = logging.getLogger(__name__)


# Name of the dedicated RQ queue for pyATS work. Declared on
# NetBoxPyATSConfig.queues so NetBox creates it at startup; workers pick it
# up by name. Kept as a module constant so views/jobs/tests reference one name.
PYATS_QUEUE = "pyats"


def enqueue_capture(
    device,
    *,
    kind: str = SnapshotKindChoices.KIND_FULL,
    user=None,
    triggered_by: str = SnapshotTriggerChoices.TRIGGER_USER,
):
    """Enqueue a snapshot capture job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS tab calls when the operator
    clicks "Capture snapshot". It creates a NetBox :class:`core.models.Job`
    row (for status tracking in the NetBox jobs UI) and enqueues the actual
    RQ work on the ``pyats`` queue.

    Args:
        device: a NetBox ``dcim.Device`` instance.
        kind: :class:`SnapshotKindChoices` value (config / state / full).
        user: the NetBox user initiating the capture (for the Job row).
        triggered_by: :class:`SnapshotTriggerChoices` value (user / job).

    Returns:
        The NetBox :class:`core.models.Job` row tracking this capture.
    """
    # Local import: core.models is only available inside a running NetBox
    # process; this function is called from views, which are only loaded
    # inside NetBox.
    from core.models import Job

    return Job.enqueue(
        capture_snapshot_job,
        instance=device,
        name=f"PyATS snapshot: {device} ({kind})",
        user=user,
        queue_name=PYATS_QUEUE,
        # Passed through to capture_snapshot_job() as kwargs by RQ.
        kind=kind,
        triggered_by=triggered_by,
    )


def capture_snapshot_job(
    job, kind: str = SnapshotKindChoices.KIND_FULL, triggered_by: str = SnapshotTriggerChoices.TRIGGER_USER, **kwargs
):
    """RQ worker entry point — capture a snapshot and persist it.

    NetBox's :class:`core.models.Job.enqueue` calls this with ``job`` (the
    tracking :class:`core.models.Job` row) plus the kwargs passed through
    from :func:`enqueue_capture`. ``job.object`` is the NetBox Device.

    The capture logic lives in :mod:`netbox_pyats.capture`; this function
    only handles the NetBox-side plumbing (load the Device, run the capture,
    write the :class:`PyatsSnapshot` row, log to the Job). Multi-vendor
    graceful degradation is enforced in :func:`capture.capture_snapshot` —
    unsupported platforms and capture errors still produce a row so the
    device-page history shows the outcome in-line.
    """
    from dcim.models import Device

    from .capture import capture_snapshot_for_netbox_device
    from .models import PyatsSnapshot

    device: Device = job.object
    logger.info("Capturing %s snapshot for device %s", kind, device)

    try:
        result = capture_snapshot_for_netbox_device(device, kind=kind)
    except Exception as exc:  # noqa: BLE001 - any uncaught error → error row + job failure
        # Still write a row so the operator sees the failure in the history,
        # then re-raise so NetBox marks the Job as errored.
        try:
            snapshot = PyatsSnapshot(
                device=device,
                kind=kind,
                status="error",
                triggered_by=triggered_by,
                data={},
                parser_warnings=[f"capture error: {exc}", traceback.format_exc()],
                genie_version="",
                pyats_version="",
                size_bytes=0,
            )
            snapshot.full_clean()
            snapshot.save()
        except Exception:  # noqa: BLE001 - never mask the original error
            logger.exception("netbox_pyats: failed to persist error-row snapshot")
        raise

    snapshot = PyatsSnapshot(
        device=device,
        kind=kind,
        status=result.status,
        triggered_by=triggered_by,
        data=result.data,
        parser_warnings=result.warnings,
        genie_version=result.genie_version,
        pyats_version=result.pyats_version,
        size_bytes=result.size_bytes,
    )
    snapshot.full_clean()
    snapshot.save()

    logger.info(
        "Snapshot %s stored (status=%s, %d bytes)",
        snapshot.pk,
        result.status,
        result.size_bytes,
    )
    if result.warnings:
        for w in result.warnings[:5]:  # keep the job log readable
            logger.warning("snapshot warning: %s", w)

    return snapshot.pk


# --------------------------------------------------------------------------- #
# Diff job (Phase 3, ATW-14)
# --------------------------------------------------------------------------- #


def enqueue_diff(device, *, before_id, after_id, user=None):
    """Enqueue a snapshot diff job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS panel calls when the operator
    picks two snapshots and clicks "Diff". It creates a NetBox
    :class:`core.models.Job` row (for status tracking in the NetBox jobs UI)
    and enqueues the actual RQ work on the ``pyats`` queue.

    Args:
        device: the NetBox ``dcim.Device`` the two snapshots belong to. Used as
            the :class:`Job` instance for status linkage; the job re-loads the
            snapshots by id.
        before_id: primary key of the earlier :class:`PyatsSnapshot`.
        after_id: primary key of the later :class:`PyatsSnapshot`.
        user: the NetBox user initiating the diff (for the Job row).

    Returns:
        The NetBox :class:`core.models.Job` row tracking this diff.
    """
    from core.models import Job

    return Job.enqueue(
        run_diff_job,
        instance=device,
        name=f"PyATS diff: {device} ({before_id}→{after_id})",
        user=user,
        queue_name=PYATS_QUEUE,
        before_id=before_id,
        after_id=after_id,
    )


def run_diff_job(job, before_id: int, after_id: int, **kwargs):
    """RQ worker entry point — diff two snapshots and persist the result.

    NetBox's :class:`core.models.Job.enqueue` calls this with ``job`` (the
    tracking :class:`core.models.Job` row) plus the kwargs passed through from
    :func:`enqueue_diff`. ``job.object`` is the NetBox Device (passed as
    ``instance`` for status linkage); we re-load the two snapshots by id.

    The diff logic lives in :mod:`netbox_pyats.diff`; this function only handles
    the NetBox-side plumbing (load the snapshots, run the diff, write the
    :class:`PyatsSnapshotDiff` row, log to the Job). Graceful degradation is
    enforced in :func:`diff.diff_snapshots` — empty inputs and malformed
    payloads still produce a row so the operator sees the outcome in-line,
    mirroring Phase 2's unsupported/error snapshot rows.
    """
    from dcim.models import Device

    from .diff import diff_snapshots
    from .models import PyatsSnapshot, PyatsSnapshotDiff

    device: Device = job.object
    logger.info("Diffing snapshots %s → %s for device %s", before_id, after_id, device)

    try:
        before_snap = PyatsSnapshot.objects.get(pk=before_id)
        after_snap = PyatsSnapshot.objects.get(pk=after_id)
    except PyatsSnapshot.DoesNotExist as exc:
        # Snapshot was deleted between the user clicking "Diff" and the worker
        # picking up the job. Write an error row so the operator sees it.
        diff_row = PyatsSnapshotDiff(
            device=device,
            before_id=before_id,
            after_id=after_id,
            status="error",
            diff={},
            summary={},
            parser_warnings=[f"snapshot missing: {exc}"],
            size_bytes=0,
        )
        diff_row.full_clean()
        diff_row.save()
        raise

    # Enforce same-device invariant: a diff across two different devices is a
    # programmer error (the picker only offers snapshots of one device), but
    # the worker must still produce a row rather than crash silently.
    if before_snap.device_id != device.pk or after_snap.device_id != device.pk:
        diff_row = PyatsSnapshotDiff(
            device=device,
            before=before_snap,
            after=after_snap,
            status="error",
            diff={},
            summary={},
            parser_warnings=[
                f"device mismatch: before.device_id={before_snap.device_id}, "
                f"after.device_id={after_snap.device_id}, job.device_id={device.pk}"
            ],
            size_bytes=0,
        )
        diff_row.full_clean()
        diff_row.save()
        raise ValueError("diff inputs belong to different devices")

    try:
        result = diff_snapshots(before_snap.data, after_snap.data, name=str(device))
    except Exception as exc:  # noqa: BLE001 - any uncaught error → error row + job failure
        try:
            diff_row = PyatsSnapshotDiff(
                device=device,
                before=before_snap,
                after=after_snap,
                status="error",
                diff={},
                summary={},
                parser_warnings=[f"diff error: {exc}", traceback.format_exc()],
                size_bytes=0,
            )
            diff_row.full_clean()
            diff_row.save()
        except Exception:  # noqa: BLE001 - never mask the original error
            logger.exception("netbox_pyats: failed to persist error-row diff")
        raise

    diff_row = PyatsSnapshotDiff(
        device=device,
        before=before_snap,
        after=after_snap,
        status=result.status,
        diff=result.diff,
        summary=result.summary,
        parser_warnings=result.warnings,
        size_bytes=result.size_bytes,
    )
    diff_row.full_clean()
    diff_row.save()

    logger.info(
        "Diff %s stored (status=%s, %d bytes, summary=%s)",
        diff_row.pk,
        result.status,
        result.size_bytes,
        result.summary,
    )
    if result.warnings:
        for w in result.warnings[:5]:  # keep the job log readable
            logger.warning("diff warning: %s", w)

    return diff_row.pk


# --------------------------------------------------------------------------- #
# Compliance job (Phase 4, ATW-15)
# --------------------------------------------------------------------------- #


def enqueue_compliance(device, *, golden_id, snapshot_id, user=None):
    """Enqueue a compliance run job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS compliance sub-tab calls
    when the operator picks a golden config + snapshot and clicks "Run
    compliance". It creates a NetBox :class:`core.models.Job` row (for status
    tracking in the NetBox jobs UI) and enqueues the actual RQ work on the
    ``pyats`` queue.

    Args:
        device: the NetBox ``dcim.Device`` the golden + snapshot belong to.
            Used as the :class:`Job` instance for status linkage; the job
            re-loads the golden + snapshot by id.
        golden_id: primary key of the :class:`PyatsGoldenConfig` to compare.
        snapshot_id: primary key of the :class:`PyatsSnapshot` to compare.
        user: the NetBox user initiating the compliance run (for the Job row).

    Returns:
        The NetBox :class:`core.models.Job` row tracking this compliance run.
    """
    from core.models import Job

    return Job.enqueue(
        run_compliance_job,
        instance=device,
        name=f"PyATS compliance: {device} (golden #{golden_id} vs snapshot #{snapshot_id})",
        user=user,
        queue_name=PYATS_QUEUE,
        golden_id=golden_id,
        snapshot_id=snapshot_id,
    )


def _golden_text_to_config_dict(golden_text: str) -> dict:
    """Parse golden config text into a comparable dict.

    v1 uses a lightweight line-oriented parse of the golden config text into a
    dict keyed by section header, so it can be diffed against the snapshot's
    parsed ``data["config"]`` payload without requiring a live pyATS device
    connection to drive the Genie parser. This keeps the compliance job
    runnable on the ``pyats`` worker with no extra device round-trip — the
    snapshot already carries the parsed "actual" config, and the golden text
    is the "expected" config.

    The parse is intentionally simple and documented as a v1 limitation: it
    groups indented lines under the most recent non-indented section header
    (the Cisco running-config convention). A ``!`` delimiter flushes the
    current section. Lines that appear before any section header are grouped
    under a synthetic ``"_preamble"`` key. Feature-specific compliance (e.g.
    "the BGP section must contain neighbor 10.0.0.1") is deferred to v2, where
    the golden config can be parsed with the same Genie parser the snapshot
    used (requiring a device connection or a parser-only harness).

    The empty-golden case is handled by the caller (compliance engine returns
    ``error`` with a "golden config is empty" warning).
    """
    config: dict = {}
    if not golden_text:
        return config
    current_section: str | None = None
    current_lines: list = []

    def _flush():
        nonlocal current_section, current_lines
        if current_section is not None or current_lines:
            key = current_section if current_section is not None else "_preamble"
            config.setdefault(key, []).extend(current_lines)
        current_section = None
        current_lines = []

    for raw_line in golden_text.splitlines():
        line = raw_line.rstrip()
        if line == "!":
            _flush()
            continue
        is_indented = line.startswith(" ") or line.startswith("\t")
        if not is_indented and line:
            # A new top-level (non-indented) line: flush the previous section
            # first, then treat this line as the new section header.
            _flush()
            current_section = line
        else:
            current_lines.append(line)
    # Flush any trailing section (no trailing "!" in the config text).
    _flush()
    return config


def run_compliance_job(job, golden_id: int, snapshot_id: int, **kwargs):
    """RQ worker entry point — run compliance and persist the result.

    NetBox's :class:`core.models.Job.enqueue` calls this with ``job`` (the
    tracking :class:`core.models.Job` row) plus the kwargs passed through from
    :func:`enqueue_compliance`. ``job.object`` is the NetBox Device (passed as
    ``instance`` for status linkage); we re-load the golden + snapshot by id.

    The compliance logic lives in :mod:`netbox_pyats.compliance`; this function
    only handles the NetBox-side plumbing (load the golden + snapshot, parse
    the golden text into a comparable dict, run the compliance, write the
    :class:`PyatsComplianceRun` row, log to the Job). Graceful degradation is
    enforced in :func:`compliance.run_compliance` — empty/unsupported inputs
    still produce a row so the operator sees the outcome in-line, mirroring
    Phase 2/3's unsupported/error/diff rows.
    """
    from dcim.models import Device

    from .compliance import run_compliance
    from .models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot

    device: Device = job.object
    logger.info("Compliance run for device %s: golden=%s snapshot=%s", device, golden_id, snapshot_id)

    try:
        golden = PyatsGoldenConfig.objects.get(pk=golden_id)
        snapshot = PyatsSnapshot.objects.get(pk=snapshot_id)
    except (PyatsGoldenConfig.DoesNotExist, PyatsSnapshot.DoesNotExist) as exc:
        # Golden or snapshot was deleted between the user clicking "Run
        # compliance" and the worker picking up the job. Write an error row so
        # the operator sees it.
        run_row = PyatsComplianceRun(
            device=device,
            golden_id=golden_id,
            snapshot_id=snapshot_id,
            result="error",
            diff={},
            summary={},
            parser_warnings=[f"golden or snapshot missing: {exc}"],
            size_bytes=0,
        )
        run_row.full_clean()
        run_row.save()
        raise

    # Enforce same-device invariant: a compliance run across golden + snapshot
    # of different devices is a programmer error (the picker only offers
    # same-device pairs), but the worker must still produce a row rather than
    # crash silently.
    if golden.device_id != device.pk or snapshot.device_id != device.pk:
        run_row = PyatsComplianceRun(
            device=device,
            golden=golden,
            snapshot=snapshot,
            result="error",
            diff={},
            summary={},
            parser_warnings=[
                f"device mismatch: golden.device_id={golden.device_id}, "
                f"snapshot.device_id={snapshot.device_id}, job.device_id={device.pk}"
            ],
            size_bytes=0,
        )
        run_row.full_clean()
        run_row.save()
        raise ValueError("compliance inputs belong to different devices")

    # Extract the snapshot's parsed config payload (the "actual" config). For
    # a config or full snapshot, this is data["config"]; for a state-only
    # snapshot there is no config key and the compliance engine will classify
    # as error with a warning.
    snapshot_config = (snapshot.data or {}).get("config") or {}

    # Parse the golden config text into a comparable dict. v1 uses a
    # lightweight line-oriented parse (see _golden_text_to_config_dict) so the
    # compliance job runs on the worker with no extra device connection.
    golden_config = _golden_text_to_config_dict(golden.config_text or "")

    try:
        result = run_compliance(golden_config, snapshot_config, name=str(device))
    except Exception as exc:  # noqa: BLE001 - any uncaught error → error row + job failure
        try:
            run_row = PyatsComplianceRun(
                device=device,
                golden=golden,
                snapshot=snapshot,
                result="error",
                diff={},
                summary={},
                parser_warnings=[f"compliance error: {exc}", traceback.format_exc()],
                size_bytes=0,
            )
            run_row.full_clean()
            run_row.save()
        except Exception:  # noqa: BLE001 - never mask the original error
            logger.exception("netbox_pyats: failed to persist error-row compliance run")
        raise

    run_row = PyatsComplianceRun(
        device=device,
        golden=golden,
        snapshot=snapshot,
        result=result.result,
        diff=result.diff,
        summary=result.summary,
        parser_warnings=result.warnings,
        size_bytes=result.size_bytes,
    )
    run_row.full_clean()
    run_row.save()

    logger.info(
        "Compliance run %s stored (result=%s, %d bytes, summary=%s)",
        run_row.pk,
        result.result,
        result.size_bytes,
        result.summary,
    )
    if result.warnings:
        for w in result.warnings[:5]:  # keep the job log readable
            logger.warning("compliance warning: %s", w)

    return run_row.pk


__all__ = (
    "PYATS_QUEUE",
    "capture_snapshot_job",
    "enqueue_capture",
    "enqueue_compliance",
    "enqueue_diff",
    "run_compliance_job",
    "run_diff_job",
)
