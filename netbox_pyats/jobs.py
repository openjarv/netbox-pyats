"""NetBox background jobs for the netbox-pyats plugin.

Phase 2 (ATW-13) ships the ``capture_snapshot`` RQ job, which runs
:func:`netbox_pyats.capture.capture_snapshot_for_netbox_device` against a
NetBox Device and persists the result as a
:class:`netbox_pyats.models.PyatsSnapshot` row.

Queue isolation: the job is enqueued on the dedicated ``pyats`` RQ queue
(declared via :attr:`NetBoxPyATSConfig.queues`), so pyATS/Genie work — which
requires ``pyats[full]`` installed on the worker — does not block NetBox's
default RQ workers. Operators run a second worker pointed at the ``pyats``
queue (see the worker Dockerfile and ``docs/workers.md``); the default NetBox
worker container does not need pyATS installed.

The web process enqueues via :func:`enqueue_capture`, passing the NetBox
Device instance and the capture ``kind``. NetBox's :class:`core.models.Job`
tracks the run (status, log entries, notifications); the actual RQ work is
the module-level :func:`capture_snapshot_job` callable, which the worker
invokes with the Job row plus the capture kwargs.
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


__all__ = (
    "PYATS_QUEUE",
    "capture_snapshot_job",
    "enqueue_capture",
)
