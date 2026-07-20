"""Compliance engine — golden config vs. snapshot raw-text diff (Phase 4, ATW-15).

:func:`run_compliance` is the Phase 4 compliance core. It compares the
**raw text** of an operator-authored golden running-config against the
**raw text** of a snapshot's running config (``snapshot.data["config_raw"]``),
both as plain strings, via a line-set diff. This is Option 3 of ADR-0004:
Option 1 (Genie parser harness on the worker) is structurally unachievable in
Genie 26.6 — there is no bare ``show running-config`` parser registered for
``iosxe``/``ios`` (verified three ways; see ADR-0004 "Empirical finding"). The
snapshot side is also raw text in practice (``_capture_config`` falls through
to the ``execute("show running-config")`` fallback), so a line-set diff on
both sides is the honest v1 comparison.

The module is pure-Python and NetBox/RQ/Genie-free so it is unit-testable
without a device, without Genie installed, and without a live connection.
The caller passes the already-captured raw text strings; this function only
normalizes, diffs, and classifies.

Normalization (v1, order-independent):

- Both texts are split into lines.
- Blank lines and lone ``!`` delimiters are dropped (they carry no config
  semantics and would otherwise inflate the diff).
- Trailing whitespace is stripped from each line.
- The remaining lines form a set per side. Set diff classifies lines present
  only in the golden as ``removed`` (the device is missing them), lines
  present only in the snapshot as ``added`` (the device has extra config),
  and lines present in both as ``unchanged``.

Classification rules (v1):

- If either input is missing/empty (no golden text, snapshot has no
  ``config_raw``) → ``error`` with a warning naming the missing input. The
  row is still created so the operator sees the failure in-line (same UX
  contract as Phase 2/3).
- If the line-set diff has no added/removed lines → ``compliant`` (the device
  carries the golden lines; order-independent — see "Documented v1
  limitation" below).
- If the line-set diff has any added/removed lines → ``drift`` (the device
  diverges from the golden; the diff tree shows *what* drifted, keyed by
  line).

Documented v1 limitation: line-set diff is order-independent — a re-ordered
config classifies as ``compliant``. This is correct for the common "does the
device carry the golden lines?" question but misses order-sensitive drift
(e.g. ACL entry order). Ordered/structured compliance is v2 — it requires
either a Genie version with a bare config parser, a standalone config parser
outside Genie, or an ordered line-diff. v2 is explicitly out of scope for the
re-land (ADR-0004).

The returned :class:`ComplianceResult` is JSON-serializable end-to-end so the
RQ job can store it directly on the
:class:`~netbox_pyats.models.PyatsComplianceRun` row's JSONB ``diff`` /
``summary`` / ``parser_warnings`` columns. The ``diff`` tree has the same
``{name, type, status, children}`` shape as
:class:`~netbox_pyats.models.PyatsSnapshotDiff.diff` so the Phase 3
``inc/diff_tree.html`` partial renders it unchanged — the root is a ``dict``
node whose ``children`` are leaf nodes keyed by line, each tagged
``added`` / ``removed`` / ``unchanged``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .choices import ComplianceResultChoices

logger = logging.getLogger(__name__)

# Node "type" / "status" tags — kept as strings (not an enum) because the tree
# is serialized to JSONB and rendered in the Phase 3 viewer; string tags keep
# the JSONB human-readable and match :mod:`netbox_pyats.diff`.
_NODE_TYPE_DICT = "dict"
_NODE_TYPE_LEAF = "leaf"
_STATUS_ADDED = "added"
_STATUS_REMOVED = "removed"
_STATUS_CHANGED = "changed"
_STATUS_UNCHANGED = "unchanged"


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
        """True if the line-set diff found any added/removed lines (drift)."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))


def _normalize_lines(text: str) -> set[str]:
    """Normalize raw config text into a set of meaningful lines.

    Drops blank lines and lone ``!`` delimiters (they carry no config
    semantics and would otherwise inflate the diff), and strips trailing
    whitespace per line. Leading whitespace is **preserved** — indented
    sub-mode lines (e.g. `` ip address ...``) are semantically distinct
    from top-level lines and must compare as such.

    Args:
        text: the raw running-config text (golden or snapshot).

    Returns:
        A set of normalized lines. Empty if ``text`` is empty/whitespace-only.
    """
    if not text:
        return set()
    lines: set[str] = set()
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        # Lone ``!`` is a section delimiter in IOS-style configs — it carries
        # no config semantics and its presence/absence varies between capture
        # paths (e.g. `execute` vs a parser's text output). Drop it so it
        # doesn't inflate the diff.
        if line == "!":
            continue
        lines.add(line)
    return lines


def run_compliance(
    golden_text: str | None,
    snapshot_text: str | None,
    *,
    name: str = "compliance",
) -> ComplianceResult:
    """Compare golden config text against snapshot config text and classify.

    This is the pure-Python core. The caller (the RQ job) is responsible for
    loading the :class:`PyatsGoldenConfig` row's ``config_text``, loading the
    :class:`PyatsSnapshot` row, extracting its ``data["config_raw"]`` payload,
    and persisting the returned :class:`ComplianceResult`. This function only
    normalizes, diffs, and classifies.

    Graceful degradation: missing/empty inputs are classified as ``error``
    with a warning naming the missing side, not silently skipped — the caller
    still writes a row so the operator sees the failure in-line, mirroring
    Phase 2/3.

    Args:
        golden_text: the raw golden running-config text (the "expected"
            config). ``None`` / empty string means the golden was empty.
        snapshot_text: the snapshot's raw running-config text (the "actual"
            config, i.e. ``snapshot.data["config_raw"]``). ``None`` / empty
            string means the snapshot had no raw config (unsupported platform,
            error snapshot, or a state-only capture).
        name: the label for the root diff node (shown in the viewer header).

    Returns:
        A :class:`ComplianceResult` with ``result`` (``compliant`` / ``drift``
        / ``error``), the nested ``diff`` tree (same ``{name, type, status,
        children}`` shape as :func:`netbox_pyats.diff.diff_snapshots`, with
        leaves keyed by line), a flat ``summary`` of counts (``added`` /
        ``removed`` / ``unchanged`` — ``changed`` is always 0 for a line-set
        diff), and any ``warnings``. Never raises for bad input — missing
        inputs are recorded as ``result="error"`` with a warning so the
        compliance row is still created and the operator sees the failure
        in-line.
    """
    golden_lines = _normalize_lines(golden_text)
    snapshot_lines = _normalize_lines(snapshot_text)

    if not golden_lines:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=["golden config text is empty; cannot run compliance"],
        )
    if not snapshot_lines:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=[
                "snapshot config text is empty (unsupported platform, error "
                "snapshot, or state-only capture); cannot run compliance"
            ],
        )

    added = snapshot_lines - golden_lines
    removed = golden_lines - snapshot_lines
    unchanged = golden_lines & snapshot_lines

    summary = {
        "added": len(added),
        "removed": len(removed),
        "changed": 0,
        "unchanged": len(unchanged),
    }

    children: dict[str, Any] = {}
    # Sort for deterministic JSONB; the diff is order-independent semantically
    # but the stored tree must be stable across runs.
    for line in sorted(added):
        children[line] = {"type": _NODE_TYPE_LEAF, "status": _STATUS_ADDED, "after": line}
    for line in sorted(removed):
        children[line] = {"type": _NODE_TYPE_LEAF, "status": _STATUS_REMOVED, "before": line}
    for line in sorted(unchanged):
        children[line] = {"type": _NODE_TYPE_LEAF, "status": _STATUS_UNCHANGED, "value": line}

    root_status = _STATUS_CHANGED if (added or removed) else _STATUS_UNCHANGED
    diff_tree = {
        "name": name,
        "type": _NODE_TYPE_DICT,
        "status": root_status,
        "children": children,
    }

    if not added and not removed:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_COMPLIANT,
            diff=diff_tree,
            summary=summary,
            warnings=[],
        )

    return ComplianceResult(
        result=ComplianceResultChoices.RESULT_DRIFT,
        diff=diff_tree,
        summary=summary,
        warnings=[],
    )


__all__ = (
    "ComplianceResult",
    "run_compliance",
)
