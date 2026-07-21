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
device, extracts the golden ``config_text`` and the snapshot's raw
``data["config_raw"]`` running-config text, runs
:func:`netbox_pyats.compliance.run_compliance` over the two texts (a
line-set diff — see :mod:`netbox_pyats.compliance` for why v1 is text-based
and not Genie-structured), and persists the classified result as a
:class:`PyatsComplianceRun` row. The diff tree has the same shape as
:class:`PyatsSnapshotDiff.diff`, so the Phase 3 diff-tree viewer partial
renders it unchanged.

Queue isolation: all three jobs run on the dedicated ``pyats`` RQ queue
(declared via :attr:`NetBoxPyATSConfig.queues`), so pyATS/Genie work — which
requires ``pyats[full]`` installed on the worker — does not block NetBox's
default RQ workers. The diff and compliance jobs themselves do not need
pyATS installed (they operate on persisted JSONB / raw text), but they still
run on the ``pyats`` queue for isolation and so a single worker image
services all plugin work; an operator who only wants diffs/compliance can run
the default worker if they prefer (no pyATS install needed for
diffs/compliance alone — the compliance engine compares raw config text, no
live device connection is required).

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
from datetime import datetime

from .choices import (
    PyatsJobStatusChoices,
    PyatsJobTypeChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)

logger = logging.getLogger(__name__)


# Name of the dedicated RQ queue for pyATS work. Declared on
# NetBoxPyATSConfig.queues so NetBox creates it at startup; workers pick it
# up by name. Kept as a module constant so views/jobs/tests reference one name.
PYATS_QUEUE = "pyats"


def _create_pyats_job(*, job_type, device=None, core_job=None, rq_job_id=""):
    """Create a :class:`PyatsJob` row in ``pending`` status (ADR-0005 §3).

    Local import: :mod:`netbox_pyats.models` is only available inside a
    running NetBox process; this helper is called from the ``enqueue_*``
    functions, which run in the web process.

    Args:
        job_type: a :class:`PyatsJobTypeChoices` value.
        device: the NetBox Device the job targets (None for batch_capture).
        core_job: the NetBox ``core.models.Job`` row tracking the RQ run.
        rq_job_id: the RQ job id (for operator cross-reference with rq-dashboard).

    Returns:
        The saved :class:`PyatsJob` row (status=pending).
    """
    from .models import PyatsJob

    job = PyatsJob(
        job_type=job_type,
        status=PyatsJobStatusChoices.STATUS_PENDING,
        device=device,
        core_job=core_job,
        rq_job_id=rq_job_id or "",
    )
    job.full_clean()
    job.save()
    return job


def _mark_running(job, pyats_job_id: int) -> None:
    """Set a :class:`PyatsJob` to ``running`` with ``started_at=now()``.

    Called at entry by every job callable (ADR-0005 §3 step 1). Local import
    so this module remains importable without NetBox.
    """
    from .models import PyatsJob

    job_row = PyatsJob.objects.get(pk=pyats_job_id)
    job_row.status = PyatsJobStatusChoices.STATUS_RUNNING
    job_row.started_at = datetime.now()
    job_row.full_clean()
    job_row.save()


def _finish_success(
    job, pyats_job_id: int, *, related_snapshot=None, related_diff=None, related_compliance=None, summary=None
) -> None:
    """Set a :class:`PyatsJob` to ``success`` with the result-row FK and ``finished_at=now()`` (ADR-0005 §3 step 2).

    Exactly one of ``related_snapshot`` / ``related_diff`` / ``related_compliance`` is
    set per job on success, by ``job_type``.
    """
    from .models import PyatsJob

    job_row = PyatsJob.objects.get(pk=pyats_job_id)
    job_row.status = PyatsJobStatusChoices.STATUS_SUCCESS
    job_row.related_snapshot = related_snapshot
    job_row.related_diff = related_diff
    job_row.related_compliance = related_compliance
    if summary is not None:
        job_row.summary = summary
    job_row.finished_at = datetime.now()
    job_row.full_clean()
    job_row.save()


def _finish_partial(job, pyats_job_id: int, *, summary: dict) -> None:
    """Set a batch :class:`PyatsJob` to ``partial`` with batch counts (ADR-0005 §3 + §2).

    ``partial`` is the batch-only status for a batch that completed without
    crashing but had per-device failures or unsupported platforms. The
    ``summary`` dict carries ``{supported, unsupported, errored, total}``.
    """
    from .models import PyatsJob

    job_row = PyatsJob.objects.get(pk=pyats_job_id)
    job_row.status = PyatsJobStatusChoices.STATUS_PARTIAL
    job_row.summary = summary
    job_row.finished_at = datetime.now()
    job_row.full_clean()
    job_row.save()


def _record_error(job, pyats_job_id: int, exc: BaseException) -> None:
    """Set a :class:`PyatsJob` to ``error`` with the exception text (ADR-0005 §3 step 4).

    Called from the top-level ``try/finally`` on every job callable when the
    job raised and the result row could *not* be written. ``error`` is a
    TextField populated only for this path (not a duplicate of the result
    row's ``parser_warnings``). The caller re-raises so RQ/``core.Job`` is
    also marked failed.
    """
    from .models import PyatsJob

    try:
        job_row = PyatsJob.objects.get(pk=pyats_job_id)
        job_row.status = PyatsJobStatusChoices.STATUS_ERROR
        job_row.error = f"{exc}\n{traceback.format_exc()}"
        job_row.finished_at = datetime.now()
        job_row.full_clean()
        job_row.save()
    except Exception:  # noqa: BLE001 - never mask the original error
        logger.exception("netbox_pyats: failed to record PyatsJob error row")


def enqueue_capture(
    device,
    *,
    kind: str = SnapshotKindChoices.KIND_FULL,
    user=None,
    triggered_by: str = SnapshotTriggerChoices.TRIGGER_USER,
):
    """Enqueue a snapshot capture job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS tab calls when the operator
    clicks "Capture snapshot". It creates a plugin :class:`PyatsJob` row
    (for the unified PyATS jobs view + result-row link — ADR-0005 §3), then a
    NetBox :class:`core.models.Job` row (for status tracking in the NetBox
    jobs UI), then enqueues the actual RQ work on the ``pyats`` queue.

    The ``PyatsJob`` row is created in ``pending`` status *before*
    ``Job.enqueue``; its pk is passed to the job callable as ``pyats_job_id``
    so the callable can update its status + result-row FK (ADR-0005 §3).

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

    # ADR-0005 §3: create the plugin-side PyatsJob row *before* Job.enqueue,
    # so we can pass its pk to the job callable. The core.Job FK is linked
    # after enqueue (the core.Job row must exist to be linked).
    pyats_job = _create_pyats_job(job_type=PyatsJobTypeChoices.JOB_CAPTURE, device=device)

    core_job = Job.enqueue(
        capture_snapshot_job,
        instance=device,
        name=f"PyATS snapshot: {device} ({kind})",
        user=user,
        queue_name=PYATS_QUEUE,
        # Passed through to capture_snapshot_job() as kwargs by RQ.
        kind=kind,
        triggered_by=triggered_by,
        pyats_job_id=pyats_job.pk,
    )
    # Link the core.Job back onto the PyatsJob row (created before enqueue
    # with core_job=None). rq_job_id mirrors core.Job.job_id for operator
    # cross-reference with rq-dashboard.
    pyats_job.core_job = core_job
    pyats_job.rq_job_id = getattr(core_job, "job_id", "") or ""
    pyats_job.full_clean()
    pyats_job.save()
    return core_job


def capture_snapshot_job(
    job,
    kind: str = SnapshotKindChoices.KIND_FULL,
    triggered_by: str = SnapshotTriggerChoices.TRIGGER_USER,
    pyats_job_id: int | None = None,
    **kwargs,
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

    ADR-0005 §3 plumbing: if ``pyats_job_id`` was passed through from
    :func:`enqueue_capture`, this callable sets the :class:`PyatsJob` row to
    ``running`` at entry, ``success`` (with the snapshot FK) on a clean
    capture, or ``error`` (with the exception text) when the job raised and
    the result row could not be written. The success path sets the result-row
    FK even for an ``unsupported``/``error`` *snapshot row* — that is a
    successful *job* producing an unsupported/*error* result row (ADR-0002).
    The ``error`` status is reserved for the swallowed-exception path where
    no snapshot row could be written at all.
    """
    from dcim.models import Device

    from .capture import capture_snapshot_for_netbox_device
    from .models import PyatsSnapshot

    device: Device = job.object
    logger.info("Capturing %s snapshot for device %s", kind, device)

    if pyats_job_id is not None:
        _mark_running(job, pyats_job_id)

    snapshot = None
    try:
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
                    parsed_os="",
                    size_bytes=0,
                )
                snapshot.full_clean()
                snapshot.save()
            except Exception:  # noqa: BLE001 - never mask the original error
                logger.exception("netbox_pyats: failed to persist error-row snapshot")
            # ADR-0005 §3 step 3: the result row was still created, so the
            # PyatsJob is a success-of-plumbing with an error result row (FK
            # set, status=error, error text empty — the row carries the
            # failure detail). Mirrors run_diff_job / run_compliance_job.
            if pyats_job_id is not None and snapshot is not None:
                _finish_success(job, pyats_job_id, related_snapshot=snapshot)
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
            parsed_os=result.parsed_os,
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

        if pyats_job_id is not None:
            _finish_success(job, pyats_job_id, related_snapshot=snapshot)

        return snapshot.pk
    except Exception as exc:  # noqa: BLE001 - top-level try/finally re-raises (ADR-0005 §3 step 4)
        if pyats_job_id is not None and snapshot is None:
            _record_error(job, pyats_job_id, exc)
        raise


# --------------------------------------------------------------------------- #
# Diff job (Phase 3, ATW-14)
# --------------------------------------------------------------------------- #


def enqueue_diff(device, *, before_id, after_id, user=None):
    """Enqueue a snapshot diff job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS panel calls when the operator
    picks two snapshots and clicks "Diff". It creates a plugin
    :class:`PyatsJob` row (ADR-0005 §3), a NetBox :class:`core.models.Job` row
    (for status tracking in the NetBox jobs UI), and enqueues the actual RQ
    work on the ``pyats`` queue.

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

    pyats_job = _create_pyats_job(job_type=PyatsJobTypeChoices.JOB_DIFF, device=device)

    core_job = Job.enqueue(
        run_diff_job,
        instance=device,
        name=f"PyATS diff: {device} ({before_id}→{after_id})",
        user=user,
        queue_name=PYATS_QUEUE,
        before_id=before_id,
        after_id=after_id,
        pyats_job_id=pyats_job.pk,
    )
    pyats_job.core_job = core_job
    pyats_job.rq_job_id = getattr(core_job, "job_id", "") or ""
    pyats_job.full_clean()
    pyats_job.save()
    return core_job


def run_diff_job(job, before_id: int, after_id: int, pyats_job_id: int | None = None, **kwargs):
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

    ADR-0005 §3 plumbing: the :class:`PyatsJob` row (resolved via
    ``pyats_job_id``) is set to ``running`` at entry, ``success`` (with the
    diff FK) on a clean diff (including the ``empty``/``error`` *diff row*
    statuses — those are successful *jobs* producing error result rows per
    ADR-0002), or ``error`` when the job raised and the result row could not
    be written. The top-level ``try/finally`` re-raises so RQ/``core.Job`` is
    also marked failed.

    Error-row persistence: ``PyatsSnapshotDiff.before`` / ``.after`` are
    nullable (``on_delete=SET_NULL``) so a diff where the before or after
    snapshot row was deleted between the user clicking "Diff" and the worker
    picking up the job can still write an error row (recording the missing ids
    in ``parser_warnings``) rather than failing ``full_clean()`` on a dangling
    FK. This matches the Phase 4 compliance job's error-row contract
    (``PyatsComplianceRun.golden`` / ``.snapshot`` are also nullable — see
    migration ``0006_compliance_run_nullable_fks``). See ATW-68.
    """
    from dcim.models import Device

    from .diff import diff_snapshots
    from .models import PyatsSnapshot, PyatsSnapshotDiff

    device: Device = job.object
    logger.info("Diffing snapshots %s → %s for device %s", before_id, after_id, device)

    if pyats_job_id is not None:
        _mark_running(job, pyats_job_id)

    diff_row = None
    try:
        try:
            before_snap = PyatsSnapshot.objects.get(pk=before_id)
            after_snap = PyatsSnapshot.objects.get(pk=after_id)
        except PyatsSnapshot.DoesNotExist as exc:
            # Snapshot was deleted between the user clicking "Diff" and the worker
            # picking up the job. Write an error row (with before/after NULL — the
            # FKs dangle) so the operator sees it. before/after are nullable on
            # PyatsSnapshotDiff exactly for this path (see model docstring +
            # migration 0008).
            diff_row = PyatsSnapshotDiff(
                device=device,
                before=None,
                after=None,
                status="error",
                diff={},
                summary={},
                parser_warnings=[
                    f"before or after snapshot missing before run: {exc}",
                    f"before_id={before_id}, after_id={after_id}",
                ],
                size_bytes=0,
            )
            diff_row.full_clean()
            diff_row.save()
            if pyats_job_id is not None:
                # The error-row write succeeded → success at the *job* level
                # (ADR-0002: an error result row is a successful job). The
                # caller then re-raises so core.Job is marked failed, but the
                # PyatsJob is success because the result row exists.
                _finish_success(job, pyats_job_id, related_diff=diff_row)
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
            if pyats_job_id is not None:
                _finish_success(job, pyats_job_id, related_diff=diff_row)
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
            if pyats_job_id is not None and diff_row is not None:
                _finish_success(job, pyats_job_id, related_diff=diff_row)
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

        if pyats_job_id is not None:
            _finish_success(job, pyats_job_id, related_diff=diff_row)

        return diff_row.pk
    except Exception as exc:  # noqa: BLE001 - top-level try/finally re-raises (ADR-0005 §3 step 4)
        if pyats_job_id is not None and diff_row is None:
            _record_error(job, pyats_job_id, exc)
        raise


# --------------------------------------------------------------------------- #
# Compliance job (Phase 4, ATW-15)
# --------------------------------------------------------------------------- #


def enqueue_compliance(device, *, golden_id, snapshot_id, user=None):
    """Enqueue a compliance run job on the dedicated ``pyats`` RQ queue.

    This is the entry point the device-page PyATS compliance sub-tab calls
    when the operator picks a golden config + snapshot and clicks "Run
    compliance". It creates a plugin :class:`PyatsJob` row (ADR-0005 §3), a
    NetBox :class:`core.models.Job` row (for status tracking in the NetBox jobs
    UI), and enqueues the actual RQ work on the ``pyats`` queue.

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

    pyats_job = _create_pyats_job(job_type=PyatsJobTypeChoices.JOB_COMPLIANCE, device=device)

    core_job = Job.enqueue(
        run_compliance_job,
        instance=device,
        name=f"PyATS compliance: {device} (golden #{golden_id} vs snapshot #{snapshot_id})",
        user=user,
        queue_name=PYATS_QUEUE,
        golden_id=golden_id,
        snapshot_id=snapshot_id,
        pyats_job_id=pyats_job.pk,
    )
    pyats_job.core_job = core_job
    pyats_job.rq_job_id = getattr(core_job, "job_id", "") or ""
    pyats_job.full_clean()
    pyats_job.save()
    return core_job


def run_compliance_job(job, golden_id: int, snapshot_id: int, pyats_job_id: int | None = None, **kwargs):
    """RQ worker entry point — run compliance and persist the result.

    NetBox's :class:`core.models.Job.enqueue` calls this with ``job`` (the
    tracking :class:`core.models.Job` row) plus the kwargs passed through from
    :func:`enqueue_compliance`. ``job.object`` is the NetBox Device (passed as
    ``instance`` for status linkage); we re-load the golden + snapshot by id.

    The compliance logic lives in :mod:`netbox_pyats.compliance`; this function
    only handles the NetBox-side plumbing (load the golden + snapshot,
    extract the golden text and the snapshot's raw config text, run the
    compliance, write the :class:`PyatsComplianceRun` row, log to the Job).
    Graceful degradation is enforced in :func:`compliance.run_compliance` —
    empty/unsupported inputs still produce a row so the operator sees the
    outcome in-line, mirroring Phase 2/3's unsupported/error/diff rows.

    ADR-0005 §3 plumbing: the :class:`PyatsJob` row is set to ``running`` at
    entry, ``success`` (with the compliance FK) on a clean compliance run
    (including the ``error`` *compliance-row* result — that is a successful
    *job* producing an error result row per ADR-0002), or ``error`` when the
    job raised and the result row could not be written. The top-level
    ``try/finally`` re-raises so RQ/``core.Job`` is also marked failed.

    Error-row persistence: ``PyatsComplianceRun.golden`` / ``.snapshot`` are
    nullable (``on_delete=SET_NULL``) so a compliance run where the golden or
    snapshot row was deleted between the user clicking "Run compliance" and
    the worker picking up the job can still write an error row (recording the
    missing ids in ``parser_warnings``) rather than failing ``full_clean()``
    on a dangling FK. This matches the Phase 3 diff job's error-row contract
    (``PyatsSnapshotDiff.before`` / ``.after`` are also nullable — see
    migration ``0008_pyatssnapshotdiff_nullable_fks``, ATW-68).
    """
    from dcim.models import Device

    from .compliance import run_compliance
    from .models import PyatsComplianceRun, PyatsGoldenConfig, PyatsSnapshot

    device: Device = job.object
    logger.info("Compliance run for device %s: golden=%s snapshot=%s", device, golden_id, snapshot_id)

    if pyats_job_id is not None:
        _mark_running(job, pyats_job_id)

    run_row = None
    try:
        golden: PyatsGoldenConfig | None = None
        snapshot: PyatsSnapshot | None = None
        try:
            golden = PyatsGoldenConfig.objects.get(pk=golden_id)
            snapshot = PyatsSnapshot.objects.get(pk=snapshot_id)
        except (PyatsGoldenConfig.DoesNotExist, PyatsSnapshot.DoesNotExist) as exc:
            # Golden or snapshot was deleted between the user clicking "Run
            # compliance" and the worker picking up the job. Write an error row
            # (with golden/snapshot NULL — the FKs dangle) so the operator sees it.
            # golden/snapshot are nullable on PyatsComplianceRun exactly for this
            # path (see model docstring + migration 0006).
            run_row = PyatsComplianceRun(
                device=device,
                golden=None,
                snapshot=None,
                result="error",
                diff={},
                summary={},
                parser_warnings=[
                    f"golden or snapshot missing before run: {exc}",
                    f"golden_id={golden_id}, snapshot_id={snapshot_id}",
                ],
                size_bytes=0,
            )
            run_row.full_clean()
            run_row.save()
            if pyats_job_id is not None:
                _finish_success(job, pyats_job_id, related_compliance=run_row)
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
            if pyats_job_id is not None:
                _finish_success(job, pyats_job_id, related_compliance=run_row)
            raise ValueError("compliance inputs belong to different devices")

        # Extract the snapshot's raw running-config text (the "actual" config).
        # v1 compliance is line-oriented (see netbox_pyats.compliance): we compare
        # the golden config text against the snapshot's raw config text. For a
        # config or full snapshot this is data["config_raw"]; for a state-only
        # snapshot there is no config_raw key and the compliance engine will
        # classify as error with a warning. Legacy snapshots captured before
        # config_raw was added (migration 0006 onward populates it) fall back to
        # data["config"]["raw"] if the parser had failed at capture time.
        snapshot_data = snapshot.data or {}
        snapshot_raw = snapshot_data.get("config_raw") or ""
        if not snapshot_raw:
            legacy_config = snapshot_data.get("config") or {}
            if isinstance(legacy_config, dict):
                snapshot_raw = legacy_config.get("raw") or ""
        golden_text = golden.config_text or ""

        try:
            result = run_compliance(golden_text, snapshot_raw, name=str(device))
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
            if pyats_job_id is not None and run_row is not None:
                _finish_success(job, pyats_job_id, related_compliance=run_row)
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

        if pyats_job_id is not None:
            _finish_success(job, pyats_job_id, related_compliance=run_row)

        return run_row.pk
    except Exception as exc:  # noqa: BLE001 - top-level try/finally re-raises (ADR-0005 §3 step 4)
        if pyats_job_id is not None and run_row is None:
            _record_error(job, pyats_job_id, exc)
        raise


# --------------------------------------------------------------------------- #
# Batch capture job (Phase 5, ATW-16)
# --------------------------------------------------------------------------- #


def enqueue_batch_capture(devices_qs, *, kind: str = SnapshotKindChoices.KIND_FULL, user=None):
    """Enqueue a batch snapshot capture job on the dedicated ``pyats`` RQ queue.

    The batch entry point (Phase 5, ATW-16). The operator selects a set of
    NetBox Devices (e.g. via the device list's bulk-action) and the view calls
    this helper. It creates a plugin :class:`PyatsJob` row with
    ``job_type=batch_capture`` (no device — batch jobs target a queryset, not
    a single device), a NetBox :class:`core.models.Job` row, and enqueues the
    :func:`batch_capture_job` callable on the ``pyats`` queue.

    The device queryset is re-resolved inside the job (by id) so the worker
    sees the current state of the DB at run time, not a stale snapshot taken
    at enqueue. This matches the per-device capture job's pattern (re-load by
    id in the callable) and avoids serializing large device objects through
    RQ kwargs.

    Args:
        devices_qs: a NetBox ``dcim.Device`` queryset (or iterable of Devices).
            The ids are extracted here and re-resolved in the job callable.
        kind: :class:`SnapshotKindChoices` value (config / state / full).
        user: the NetBox user initiating the batch (for the Job row).

    Returns:
        The NetBox :class:`core.models.Job` row tracking this batch.
    """
    from core.models import Job

    # Materialize the device ids at enqueue time. Re-resolving by id in the
    # job means a device deleted between enqueue and run is silently skipped
    # (consistent with the per-device job's "snapshot missing before run"
    # error-row path, but at the batch level a missing device just drops out
    # of the iteration rather than producing a per-device error row — the
    # batch summary's `total` reflects the devices that were actually
    # iterated, not the enqueue-time count).
    device_ids = [d.pk for d in devices_qs]

    pyats_job = _create_pyats_job(job_type=PyatsJobTypeChoices.JOB_BATCH_CAPTURE, device=None)

    core_job = Job.enqueue(
        batch_capture_job,
        name=f"PyATS batch capture: {len(device_ids)} devices ({kind})",
        user=user,
        queue_name=PYATS_QUEUE,
        device_ids=device_ids,
        kind=kind,
        pyats_job_id=pyats_job.pk,
    )
    pyats_job.core_job = core_job
    pyats_job.rq_job_id = getattr(core_job, "job_id", "") or ""
    pyats_job.full_clean()
    pyats_job.save()
    return core_job


def batch_capture_job(
    job, device_ids: list[int], kind: str = SnapshotKindChoices.KIND_FULL, pyats_job_id: int | None = None, **kwargs
):
    """RQ worker entry point — capture snapshots for a batch of devices.

    NetBox's :class:`core.models.Job.enqueue` calls this with ``job`` (the
    tracking :class:`core.models.Job` row) plus the kwargs passed through from
    :func:`enqueue_batch_capture`. The device ids are re-resolved against the
    current DB state (a device deleted between enqueue and run is skipped
    silently — it just drops out of the iteration; the batch summary reflects
    what was actually iterated).

    For each device the job reuses :func:`capture.capture_snapshot_for_netbox_device`
    with ``build_testbed(on_unsupported="skip")`` so unsupported platforms are
    skipped without an exception (the testbed builder's report carries the
    unsupported count). Per-device capture failures are caught and counted
    rather than crashing the whole batch — the batch's :class:`PyatsJob` is
    set to ``partial`` (with ``summary = {supported, unsupported, errored, total}``)
    when any per-device capture errored or was unsupported, and ``success``
    when every device captured cleanly.

    ADR-0005 §3 plumbing: the :class:`PyatsJob` row is set to ``running`` at
    entry, ``success`` or ``partial`` on completion (no result-row FK — a
    batch produces N result rows, not one). The top-level ``try/finally``
    records ``error`` only if the batch itself crashed before producing a
    summary (an uncaught exception in the iteration loop, not a per-device
    capture failure — those are counted as ``errored``).
    """
    from dcim.models import Device

    from .capture import capture_snapshot_for_netbox_device
    from .models import PyatsSnapshot

    if pyats_job_id is not None:
        _mark_running(job, pyats_job_id)

    counts = {"supported": 0, "unsupported": 0, "errored": 0, "total": 0}
    try:
        for device_id in device_ids:
            device = Device.objects.filter(pk=device_id).first()
            if device is None:
                # Device deleted between enqueue and run: silently skip. The
                # batch summary reflects what was actually iterated, so we do
                # not bump `total` for a missing device.
                logger.info("netbox_pyats: batch capture skipping deleted device pk=%s", device_id)
                continue
            counts["total"] += 1
            try:
                result = capture_snapshot_for_netbox_device(device, kind=kind)
            except Exception as exc:  # noqa: BLE001 - per-device failure is counted, not fatal
                counts["errored"] += 1
                logger.exception("netbox_pyats: batch capture errored for device %s: %s", device, exc)
                continue
            if result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED:
                counts["unsupported"] += 1
                continue
            if result.status == SnapshotStatusChoices.STATUS_ERROR:
                counts["errored"] += 1
                continue
            # Persist the snapshot row (the successful path). capture_snapshot_for_netbox_device
            # returns a CaptureResult; the per-device capture job's row-write
            # logic is duplicated here because the batch path does not enqueue
            # a per-device job (one batch → N snapshots, not N jobs).
            snapshot = PyatsSnapshot(
                device=device,
                kind=kind,
                status=result.status,
                triggered_by=SnapshotTriggerChoices.TRIGGER_JOB,
                data=result.data,
                parser_warnings=result.warnings,
                genie_version=result.genie_version,
                pyats_version=result.pyats_version,
                parsed_os=result.parsed_os,
                size_bytes=result.size_bytes,
            )
            snapshot.full_clean()
            snapshot.save()
            counts["supported"] += 1
            logger.info(
                "Batch capture: snapshot %s stored for device %s (status=%s, %d bytes)",
                snapshot.pk,
                device,
                result.status,
                result.size_bytes,
            )

        if pyats_job_id is not None:
            # success if every device captured cleanly; partial if any errored
            # or were unsupported (ADR-0005 §2). A batch with zero supported
            # devices (all unsupported/errored) is `partial`, not `error` — the
            # job ran fine, it just had no workable devices.
            if counts["errored"] or counts["unsupported"]:
                _finish_partial(job, pyats_job_id, summary=counts)
            else:
                _finish_success(job, pyats_job_id, summary=counts)
        return counts
    except Exception as exc:  # noqa: BLE001 - top-level try/finally re-raises (ADR-0005 §3 step 4)
        if pyats_job_id is not None:
            _record_error(job, pyats_job_id, exc)
        raise


__all__ = (
    "PYATS_QUEUE",
    "batch_capture_job",
    "capture_snapshot_job",
    "enqueue_batch_capture",
    "enqueue_capture",
    "enqueue_compliance",
    "enqueue_diff",
    "run_compliance_job",
    "run_diff_job",
)
