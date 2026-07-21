"""Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15).

:func:`run_compliance` is the Phase 4 counterpart to
:func:`netbox_pyats.diff.diff_snapshots`. It takes the golden config *text* and
the snapshot's raw running-config *text* (``data["config_raw"]``), normalizes
both into line sets, diffs them, and returns a :class:`ComplianceResult`
classified as ``compliant`` / ``drift`` / ``error``.

Why line-oriented text diff and not a Genie-structured dict diff for v1: the
snapshot's ``data["config"]`` is Genie's *abstract-config* structured dict
(nested dicts/scalars), produced by ``device.parse("show running-config")`` on
the worker. There is no worker-only harness that parses a free-text golden
config into that same Genie shape — ``device.parse("show running-config")``
requires a live device connection, and the Genie abstract-config parser is not
in the standard parser registry (``get_parser("show running-config", dev)``
raises ``ParserNotFound``; it is driven by the Genie abstract tree which is only
built on a connected device). The original v1 docstring claimed a "scaffold"
parse using the snapshot's parsed config; that scaffold was never implemented,
and a line-oriented parse into a dict-of-lists produced a shape that was not
comparable to the Genie dict (a matching golden run always classified as
``drift``).

v1 therefore compares the **raw text** of the golden config against the **raw
text** of the snapshot's running config, both captured/stored as plain strings.
This:

- Delivers the Phase 4 intent ("does the running config match the golden?") —
  a matching golden against a matching snapshot classifies as ``compliant``.
- Runs on the ``pyats`` worker with no extra device connection (the snapshot
  already carries the raw text; the golden is operator-authored text).
- Is unit-testable without Genie installed (the pure-Python tests feed strings).
- Is additive: ``data["config"]`` (the Genie structured dict) is still captured
  for Phase 3 snapshot-vs-snapshot diffs; compliance uses the new
  ``data["config_raw"]`` text path.

Classification rules (v1):

- If either input is missing/empty (no golden text, snapshot has no
  ``config_raw``) → ``error`` with a warning naming the missing input. The row
  is still created so the operator sees the failure in-line (same UX contract as
  Phase 2/3).
- If the line-set diff has no added/removed lines → ``compliant`` (the device
  matches the golden).
- If the line-set diff has any added/removed lines → ``drift`` (the device
  diverges from the golden; the diff tree shows *what* drifted).

v1 line-set diff semantics (documented limitation): lines are compared as a
**set** (order-independent), after stripping trailing whitespace and dropping
blank lines and lone ``!`` delimiter lines (Cisco running-config noise). This
means a re-ordered config classifies as ``compliant`` — correct for the common
"does the device carry the golden lines?" question, but it will miss
order-sensitive drift (e.g. ACL entry order). Ordered/structured compliance is
v2, where the golden can be parsed with the same Genie parser the snapshot used
(requiring a device connection or a parser-only harness).

The returned :class:`ComplianceResult` is JSON-serializable end-to-end so the
RQ job can store it directly on the
:class:`~netbox_pyats.models.PyatsComplianceRun` row's JSONB ``diff`` /
``summary`` / ``parser_warnings`` columns. The ``diff`` tree has the same shape
as :class:`~netbox_pyats.models.PyatsSnapshotDiff.diff` (a ``dict`` root node
with ``children`` keyed by line, each child a ``leaf`` node with
``status`` ``unchanged`` / ``added`` / ``removed``) so the Phase 3
``inc/diff_tree.html`` partial renders it unchanged.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from .choices import ComplianceResultChoices

logger = logging.getLogger(__name__)

# Diff-tree node tags, kept identical to :mod:`netbox_pyats.diff` so the
# Phase 3 ``inc/diff_tree.html`` partial renders compliance diffs unchanged.
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
        """True if the diff found any added/removed/changed leaves (drift)."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))


def _normalize_lines(text: str) -> list[str]:
    """Normalize a running-config text into a list of comparable lines.

    Drops blank lines and lone ``!`` delimiter lines (Cisco running-config
    section separators — they carry no config meaning and would create
    spurious drift between two equivalent configs that differ only in
    delimiter placement). Strips trailing whitespace so ``" hostname rtr01\\n"``
    and ``"hostname rtr01"`` compare equal. Preserves leading indentation
    (significant for sub-section lines like `` ip address ...``).

    Returns an empty list for ``None`` / empty input.
    """
    if not text:
        return []
    out: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        # Lone "!" is a Cisco running-config section delimiter — noise for
        # set-comparison purposes.
        if line == "!":
            continue
        out.append(line)
    return out


def run_compliance(
    golden_text: str | None,
    snapshot_text: str | None,
    *,
    name: str = "compliance",
) -> ComplianceResult:
    """Compare a golden config text against a snapshot's raw config text and classify.

    This is the pure-Python core. The caller (the RQ job) is responsible for
    loading the :class:`PyatsGoldenConfig` row's ``config_text``, loading the
    :class:`PyatsSnapshot` row's ``data["config_raw"]`` (the raw
    ``show running-config`` text captured alongside the Genie structured dict),
    and persisting the returned :class:`ComplianceResult`. This function only
    normalizes the two texts, runs the line-set diff, and classifies.

    Graceful degradation: missing/empty inputs are classified as ``error`` with
    a warning naming the missing side, not silently skipped — the caller still
    writes a row so the operator sees the failure in-line, mirroring Phase 2/3.

    Args:
        golden_text: the golden config text (the "expected" config). ``None`` /
            empty string means the golden was empty. A golden with only blank
            lines / ``!`` delimiters is treated as empty (no comparable lines).
        snapshot_text: the snapshot's raw running-config text (the "actual"
            config, i.e. ``snapshot.data["config_raw"]``). ``None`` / empty
            string means the snapshot had no raw config (unsupported platform,
            error snapshot, or a state-only capture).
        name: the label for the root diff node (shown in the viewer header).

    Returns:
        A :class:`ComplianceResult` with ``result`` (``compliant`` / ``drift``
        / ``error``), the nested ``diff`` tree (same shape as
        :func:`netbox_pyats.diff.diff_snapshots`), a flat ``summary`` of counts,
        and any ``warnings``. Never raises for bad input — missing inputs are
        recorded as ``result="error"`` with a warning so the compliance row is
        still created and the operator sees the failure in-line.
    """
    golden_lines = _normalize_lines(golden_text)
    snapshot_lines = _normalize_lines(snapshot_text)

    if not golden_lines:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=["golden config is empty; cannot run compliance"],
        )
    if not snapshot_lines:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=[
                "snapshot raw config is empty (unsupported platform, error "
                "snapshot, or state-only capture); cannot run compliance"
            ],
        )

    golden_set = set(golden_lines)
    snapshot_set = set(snapshot_lines)

    added = sorted(snapshot_set - golden_set)
    removed = sorted(golden_set - snapshot_set)
    unchanged = sorted(golden_set & snapshot_set)

    summary = {
        "added": len(added),
        "removed": len(removed),
        "changed": 0,  # line-set diff has no "changed" (a line is either present or not)
        "unchanged": len(unchanged),
    }

    children: dict = {}
    for line in unchanged:
        children[line] = {
            "type": _NODE_TYPE_LEAF,
            "status": _STATUS_UNCHANGED,
            "value": line,
        }
    for line in added:
        children[line] = {
            "type": _NODE_TYPE_LEAF,
            "status": _STATUS_ADDED,
            "after": line,
        }
    for line in removed:
        children[line] = {
            "type": _NODE_TYPE_LEAF,
            "status": _STATUS_REMOVED,
            "before": line,
        }

    has_drift = bool(summary["added"] or summary["removed"] or summary["changed"])
    root_status = _STATUS_CHANGED if has_drift else _STATUS_UNCHANGED
    tree = {
        "name": name,
        "type": _NODE_TYPE_DICT,
        "status": root_status,
        "children": children,
    }

    result = ComplianceResultChoices.RESULT_DRIFT if has_drift else ComplianceResultChoices.RESULT_COMPLIANT
    return ComplianceResult(
        result=result,
        diff=tree,
        summary=summary,
        warnings=[],
    )


__all__ = (
    "ComplianceResult",
    "run_compliance",
)
