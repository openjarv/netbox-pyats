"""Compliance engine — golden config vs. snapshot diff (Phase 4, ATW-15).

:func:`run_compliance` is the Phase 4 counterpart to
:func:`netbox_pyats.diff.diff_snapshots`. It takes a parsed golden-config
dict (produced by :func:`netbox_pyats.golden_parse.parse_golden_config_text`
on the worker, using the same Genie parser the snapshot used) and a captured
snapshot's ``data["config"]`` payload, diffs them using the Phase 3
:func:`netbox_pyats.diff.diff_snapshots` engine, and returns a
:class:`ComplianceResult` classified as ``compliant`` / ``drift`` / ``error``.

Why reuse the Phase 3 diff engine instead of a new diff path: the snapshot's
``data["config"]`` is *already* a parsed dict (Genie's structured output of
``show running-config`` via ``device.parse(...)``). The golden config text is
parsed into the same shape on the worker via
:func:`netbox_pyats.golden_parse.parse_golden_config_text` — the same Genie
parser, fed the golden text instead of a live device's output. This keeps
both sides in the same structured shape so the Phase 3 diff tree and
``inc/diff_tree.html`` partial render unchanged. This module is pure-Python
and NetBox/RQ/Genie-free so it is unit-testable without a device: the caller
passes the already-parsed ``golden_config`` dict and the snapshot's
``data["config"]`` dict, and this function only classifies + packages the diff.

Classification rules (v1):

- If either input is missing/empty (no golden config, snapshot has no
  ``config`` key, snapshot is unsupported/error) → ``error`` with a warning
  naming the missing input. The row is still created so the operator sees the
  failure in-line (same UX contract as Phase 2/3).
- If the structured diff has no added/removed/changed leaves → ``compliant``
  (the device matches the golden).
- If the structured diff has any added/removed/changed leaves → ``drift`` (the
  device diverges from the golden; the diff tree shows *what* drifted).

The returned :class:`ComplianceResult` is JSON-serializable end-to-end so the
RQ job can store it directly on the
:class:`~netbox_pyats.models.PyatsComplianceRun` row's JSONB ``diff`` /
``summary`` / ``parser_warnings`` columns. The ``diff`` tree has the same shape
as :class:`~netbox_pyats.models.PyatsSnapshotDiff.diff` so the Phase 3
``inc/diff_tree.html`` partial renders it unchanged.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from .choices import ComplianceResultChoices, DiffStatusChoices
from .diff import diff_snapshots

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Outcome of a single :func:`run_compliance` call.

    The RQ job (:func:`netbox_pyats.jobs.run_compliance_job`) writes this to a
    :class:`~netbox_pyats.models.PyatsComplianceRun` row: ``result`` →
    ``result``, ``diff`` → ``diff``, ``summary`` → ``summary``, ``warnings``
    → ``parser_warnings``. ``size_bytes`` is derived from the JSON-serialized
    ``diff`` payload so the UI can render it without re-serializing.
    """

    result: str = ComplianceResultChoices.RESULT_ERROR
    diff: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    @property
    def size_bytes(self) -> int:
        """Length of the JSON-serialized ``diff`` payload, in bytes."""
        if not self.diff:
            return 0
        return len(json.dumps(self.diff, default=str).encode("utf-8"))

    @property
    def has_drift(self) -> bool:
        """True if the diff found any added/removed/changed leaves (drift)."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))


def run_compliance(
    golden_config: dict | None,
    snapshot_config: dict | None,
    *,
    name: str = "compliance",
) -> ComplianceResult:
    """Compare a golden config dict against a snapshot's config dict and classify.

    This is the pure-Python core. The caller (the RQ job) is responsible for
    loading the :class:`PyatsGoldenConfig` row, parsing its ``config_text`` into
    a Genie abstract-config dict on the worker via
    :func:`netbox_pyats.golden_parse.parse_golden_config_text` (same Genie
    parser the snapshot used, no live device), loading the
    :class:`PyatsSnapshot` row, extracting its ``data["config"]`` payload, and
    persisting the returned :class:`ComplianceResult`. This function only runs
    the diff + classification.

    Graceful degradation: missing/empty inputs are classified as ``error`` with
    a warning naming the missing side, not silently skipped — the caller still
    writes a row so the operator sees the failure in-line, mirroring Phase 2/3.

    Args:
        golden_config: the parsed golden config dict (the "expected" config).
            ``None`` / empty dict means the golden was empty/unparseable.
        snapshot_config: the snapshot's parsed config payload (the "actual"
            config, i.e. ``snapshot.data["config"]``). ``None`` / empty dict
            means the snapshot had no config (unsupported platform, error
            snapshot, or a state-only capture).
        name: the label for the root diff node (shown in the viewer header).

    Returns:
        A :class:`ComplianceResult` with ``result`` (``compliant`` / ``drift``
        / ``error``), the nested ``diff`` tree (same shape as
        :func:`netbox_pyats.diff.diff_snapshots`), a flat ``summary`` of counts,
        and any ``warnings``. Never raises for bad input — missing inputs are
        recorded as ``result="error"`` with a warning so the compliance row is
        still created and the operator sees the failure in-line.
    """
    golden_config = golden_config or {}
    snapshot_config = snapshot_config or {}

    if not golden_config:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=["golden config is empty; cannot run compliance"],
        )
    if not snapshot_config:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=[
                "snapshot config is empty (unsupported platform, error snapshot, "
                "or state-only capture); cannot run compliance"
            ],
        )

    diff_result = diff_snapshots(golden_config, snapshot_config, name=name)

    # The diff engine itself reported an error (malformed inputs). Surface as
    # compliance error with the engine's warnings so the row is still created.
    if diff_result.status == DiffStatusChoices.STATUS_ERROR:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff=diff_result.diff,
            summary=diff_result.summary,
            warnings=diff_result.warnings or ["diff engine returned an error"],
        )

    # Empty-inputs diff (both sides empty) is unreachable here because we
    # already rejected empty golden/snapshot above, but guard anyway: an empty
    # diff with both sides non-empty would mean both are empty dicts, which we
    # already short-circuited. Treat as compliant (no drift).
    if not diff_result.has_changes:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff=diff_result.diff,
            summary=diff_result.summary,
            warnings=diff_result.warnings,
        )

    return ComplianceResult(
        result=ComplianceResultChoices.RESULT_DRIFT,
        diff=diff_result.diff,
        summary=diff_result.summary,
        warnings=diff_result.warnings,
    )


__all__ = (
    "ComplianceResult",
    "run_compliance",
)
