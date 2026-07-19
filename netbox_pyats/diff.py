"""Structured snapshot diff engine — pure-Python, NetBox/RQ/Genie-free.

:func:`diff_snapshots` is the Phase 3 (ATW-14) counterpart to
:func:`netbox_pyats.capture.capture_snapshot`. It takes two already-serialized
snapshot payloads (the JSONB ``data`` dicts stored on
:class:`~netbox_pyats.models.PyatsSnapshot` rows) and returns a
:class:`DiffResult` with a structured, JSON-serializable diff tree plus a
summary (added / removed / changed / unchanged counts).

Why a pure-Python recursive diff and not ``Genie.diff``: the snapshots we store
are *already-serialized* JSONB dicts (the output of ``device.parse(...)``),
captured at capture time and detached from the live Genie object model.
``Genie.diff`` operates on Genie's own runtime objects (Ops/feature instances
with ``to_dict`` output and Genie-specific comparison semantics); by the time a
diff is requested the worker no longer has the live device or the Genie
objects, only the persisted JSONB. A recursive diff over the JSONB is portable,
deterministic, testable without Genie installed, and produces a tree the
viewer can render directly. This mirrors the Phase 2 decision to use
``device.parse(...)`` rather than the (non-existent as a top-level callable)
``genie.learn`` — see the ATW-10 build plan §6.1: "multi-vendor bounded by
Genie parser availability"; the diff layer is bounded by *what the captured
JSONB contains*.

Diff semantics (v1):

- **dicts** are diffed by key. A key present only in ``after`` is ``added``; a
  key present only in ``before`` is ``removed``; a key in both is recursed. A
  leaf value that differs is ``changed`` (with both values recorded).
- **lists** are diffed positionally (index-by-index). A longer ``after`` list
  appends ``added`` entries for the tail; a shorter ``after`` list appends
  ``removed`` entries for the tail. Positional diffing is a v1 limitation:
  Genie parser outputs are predominantly dict-keyed by interface/neighbor
  names, so list ordering is rare in the captured payloads. Order-sensitive
  diff (e.g. LCS) is v2.
- **scalars** (str/int/float/bool/None) compare by equality. A type change
  (e.g. ``"10.0.0.1"`` vs ``10.0.0.1``) is recorded as ``changed`` with both
  values; we do not coerce types — the operator sees the raw discrepancy.

The returned :class:`DiffResult` is JSON-serializable end-to-end so the RQ job
can store it directly on the :class:`~netbox_pyats.models.PyatsSnapshotDiff`
row's JSONB ``diff`` column. The viewer template renders the tree without
further processing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .choices import DiffStatusChoices

logger = logging.getLogger(__name__)

# Node "type" tags in the diff tree. Kept as strings (not an enum) because the
# tree is serialized to JSONB and rendered in the viewer; string tags keep the
# JSONB human-readable.
_NODE_TYPE_DICT = "dict"
_NODE_TYPE_LIST = "list"
_NODE_TYPE_LEAF = "leaf"

# Node "status" tags.
_STATUS_ADDED = "added"
_STATUS_REMOVED = "removed"
_STATUS_CHANGED = "changed"
_STATUS_UNCHANGED = "unchanged"


@dataclass
class DiffResult:
    """Outcome of a single :func:`diff_snapshots` call.

    The RQ job (:func:`netbox_pyats.jobs.run_diff_job`) writes this to a
    :class:`~netbox_pyats.models.PyatsSnapshotDiff` row: ``diff`` → ``diff``,
    ``summary`` → ``summary``, ``status`` → ``status``, ``warnings`` →
    ``warnings``. ``size_bytes`` is derived from the JSON-serialized ``diff``
    payload so the UI can render it without re-serializing.
    """

    status: str = DiffStatusChoices.STATUS_SUCCESS
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
    def has_changes(self) -> bool:
        """True if the diff found any added/removed/changed leaves."""
        s = self.summary or {}
        return bool(s.get("added") or s.get("removed") or s.get("changed"))


def diff_snapshots(
    before: dict | None,
    after: dict | None,
    *,
    name: str = "root",
) -> DiffResult:
    """Diff two serialized snapshot payloads and return a structured result.

    Args:
        before: the ``data`` dict from the earlier :class:`PyatsSnapshot`, or
            ``None`` / empty dict if there is no "before" (every key in
            ``after`` is then ``added``).
        after: the ``data`` dict from the later :class:`PyatsSnapshot`, or
            ``None`` / empty dict if there is no "after" (every key in
            ``before`` is then ``removed``).
        name: the label for the root node (used by the viewer header; defaults
            to ``"root"``).

    Returns:
        A :class:`DiffResult` with ``status`` (``success`` / ``empty`` /
        ``error``), the nested ``diff`` tree, a flat ``summary`` of counts per
        status, and any ``warnings``. Never raises for bad input — programmer
        error (non-dict top-level payloads) is recorded as ``status="error"``
        with a warning, so the diff row is still created and the operator sees
        the failure in-line (same UX contract as Phase 2 capture).
    """
    before = before or {}
    after = after or {}

    if not isinstance(before, dict) or not isinstance(after, dict):
        return DiffResult(
            status=DiffStatusChoices.STATUS_ERROR,
            diff={},
            summary={},
            warnings=[
                f"diff inputs must be dicts; got before={type(before).__name__}, " f"after={type(after).__name__}"
            ],
        )

    if not before and not after:
        # Both empty (e.g. two unsupported-platform rows) → empty diff, not an
        # error: the operator explicitly asked to diff them and the answer is
        # "no differences because both are empty". Distinct from error so the
        # UI shows a neutral badge rather than red.
        return DiffResult(
            status=DiffStatusChoices.STATUS_EMPTY,
            diff={"name": name, "type": _NODE_TYPE_DICT, "status": _STATUS_UNCHANGED, "children": {}},
            summary={"added": 0, "removed": 0, "changed": 0, "unchanged": 0},
            warnings=[],
        )

    warnings: list = []
    summary = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    children = _diff_dict(before, after, summary, warnings)
    tree = {
        "name": name,
        "type": _NODE_TYPE_DICT,
        "status": _node_status(children),
        "children": children,
    }

    status = DiffStatusChoices.STATUS_SUCCESS
    # If every leaf errored (shouldn't happen — _diff_dict records errors per
    # leaf as warnings but still produces a tree), surface as error. In
    # practice this only triggers on truly malformed payloads that survived the
    # isinstance check above (e.g. a dict whose value is a non-JSON-serializable
    # object — the default=str in size_bytes catches it for serialization, but
    # we want the diff row to still be written).
    if warnings and summary["added"] + summary["removed"] + summary["changed"] + summary["unchanged"] == 0:
        status = DiffStatusChoices.STATUS_ERROR

    return DiffResult(
        status=status,
        diff=tree,
        summary=summary,
        warnings=warnings,
    )


def _diff_dict(before: dict, after: dict, summary: dict, warnings: list) -> dict:
    """Diff two dicts by key; mutate ``summary`` and append to ``warnings``.

    Returns a dict of ``{key: node}`` where each ``node`` is the recursive diff
    of that key's value. The returned dict is the ``children`` of a
    ``_NODE_TYPE_DICT`` node.
    """
    children: dict[str, Any] = {}
    all_keys = set(before.keys()) | set(after.keys())
    for key in sorted(all_keys, key=lambda k: str(k)):
        in_before = key in before
        in_after = key in after
        if in_before and not in_after:
            summary["removed"] += 1
            children[key] = {
                "type": _leaf_type(before[key]),
                "status": _STATUS_REMOVED,
                "before": before[key],
            }
        elif in_after and not in_before:
            summary["added"] += 1
            children[key] = {
                "type": _leaf_type(after[key]),
                "status": _STATUS_ADDED,
                "after": after[key],
            }
        else:
            children[key] = _diff_value(before[key], after[key], summary, warnings)
    return children


def _diff_value(before: Any, after: Any, summary: dict, warnings: list) -> dict:
    """Diff two values; return a node describing the change.

    Recurses into dicts and lists; compares scalars by equality.
    """
    if isinstance(before, dict) and isinstance(after, dict):
        children = _diff_dict(before, after, summary, warnings)
        return {
            "type": _NODE_TYPE_DICT,
            "status": _node_status(children),
            "children": children,
        }
    if isinstance(before, list) and isinstance(after, list):
        return _diff_list(before, after, summary, warnings)
    # Scalar or mixed-type comparison.
    if before == after:
        summary["unchanged"] += 1
        return {"type": _leaf_type(before), "status": _STATUS_UNCHANGED, "value": before}
    summary["changed"] += 1
    return {
        "type": _leaf_type(before) if _leaf_type(before) == _leaf_type(after) else "mixed",
        "status": _STATUS_CHANGED,
        "before": before,
        "after": after,
    }


def _diff_list(before: list, after: list, summary: dict, warnings: list) -> dict:
    """Diff two lists positionally (v1 limitation — see module docstring).

    Common-length indices are recursed; the longer list's tail is
    ``added``/``removed`` per index.
    """
    children: dict[str, Any] = {}
    common = min(len(before), len(after))
    for i in range(common):
        children[str(i)] = _diff_value(before[i], after[i], summary, warnings)
    if len(after) > len(before):
        for i in range(common, len(after)):
            summary["added"] += 1
            children[str(i)] = {
                "type": _leaf_type(after[i]),
                "status": _STATUS_ADDED,
                "after": after[i],
            }
    elif len(before) > len(after):
        for i in range(common, len(before)):
            summary["removed"] += 1
            children[str(i)] = {
                "type": _leaf_type(before[i]),
                "status": _STATUS_REMOVED,
                "before": before[i],
            }
    return {
        "type": _NODE_TYPE_LIST,
        "status": _node_status(children),
        "children": children,
    }


def _leaf_type(value: Any) -> str:
    """Return a short type tag for a leaf value, for the viewer's badge."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return _NODE_TYPE_DICT
    if isinstance(value, list):
        return _NODE_TYPE_LIST
    return type(value).__name__


def _node_status(children: dict) -> str:
    """Aggregate a container's status from its children.

    Returns ``"changed"`` if any child differs (added/removed/changed),
    otherwise ``"unchanged"``. The viewer uses this to collapse unchanged
    subtrees by default and expand changed ones.
    """
    for node in children.values():
        status = node.get("status")
        if status in (_STATUS_ADDED, _STATUS_REMOVED, _STATUS_CHANGED):
            return _STATUS_CHANGED
    return _STATUS_UNCHANGED


__all__ = (
    "DiffResult",
    "diff_snapshots",
)
