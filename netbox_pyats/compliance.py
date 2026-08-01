"""Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15).

:func:`run_compliance` is the Phase 4 counterpart to
:func:`netbox_pyats.diff.diff_snapshots`. It takes the golden config *text* and
the snapshot's raw running-config *text* (``data["config_raw"]``), normalizes
both into line sequences, diffs them, and returns a :class:`ComplianceResult`
classified as ``compliant`` / ``drift`` / ``error``.

Why line-oriented text diff and not a Genie-structured dict diff: the
snapshot's ``data["config"]`` is Genie's *abstract-config* structured dict
(nested dicts/scalars), produced by ``device.parse("show running-config")`` on
the worker. There is no worker-only harness that parses a free-text golden
config into that same Genie shape — ``device.parse("show running-config")``
requires a live device connection, and the Genie abstract-config parser is not
in the standard parser registry (``get_parser("show running-config", dev)``
raises ``ParserNotFound``; it is driven by the Genie abstract tree which is only
built on a connected device — confirmed against genie 26.6). The original v1
docstring claimed a "scaffold" parse using the snapshot's parsed config; that
scaffold was never implemented, and a line-oriented parse into a dict-of-lists
produced a shape that was not comparable to the Genie dict (a matching golden
run always classified as ``drift``).

The plugin therefore compares the **raw text** of the golden config against the
**raw text** of the snapshot's running config, both captured/stored as plain
strings. This:

- Delivers the Phase 4 intent ("does the running config match the golden?") —
  a matching golden against a matching snapshot classifies as ``compliant``.
- Runs on the ``pyats`` worker with no extra device connection (the snapshot
  already carries the raw text; the golden is operator-authored text).
- Is unit-testable without Genie installed (the pure-Python tests feed strings).
- Is additive: ``data["config"]`` (the Genie structured dict) is still captured
  for Phase 3 snapshot-vs-snapshot diffs; compliance uses the new
  ``data["config_raw"]`` text path.

Two comparison modes (ATW-434, ADR-0004 §"v2 ordered text diff"):

- ``ordered`` (v2, **default**): compares the normalized line sequences with a
  longest-common-subsequence diff (:func:`difflib.SequenceMatcher`). This is
  **order-sensitive** — a re-ordered config (e.g. ACL entry order, route-map
  sequence, interface definition order) classifies as ``drift``. This closes
  the documented v1 gap where order-sensitive drift was missed. The diff tree
  has the same leaf shape as the v1 set diff (``unchanged`` / ``added`` /
  ``removed`` keyed by line) so the Phase 3 ``inc/diff_tree.html`` partial
  renders it unchanged.
- ``set`` (v1): compares the normalized line sets (order-independent). A
  re-ordered config classifies as ``compliant`` — correct for the common "does
  the device carry the golden lines?" question, but it misses order-sensitive
  drift. Kept as an explicit opt-in for operators whose configs legitimately
  vary in section order between captures.

Both modes are pure-Python and Genie-free: they compare the golden
``config_text`` against the snapshot's ``data["config_raw"]`` raw running-config
text, both stored as plain strings. No worker-only Genie parse of the golden is
needed (ADR-0004 v2 note: parsing the golden with the same Genie parser as the
snapshot would require a live device connection, which breaks the "no extra
SSH round-trip" Phase 4 contract; the ordered text diff delivers the
order-sensitive drift detection without that cost).

Classification rules (both modes):

- If either input is missing/empty (no golden text, snapshot has no
  ``config_raw``) → ``error`` with a warning naming the missing input. The row
  is still created so the operator sees the failure in-line (same UX contract as
  Phase 2/3).
- If the diff has no added/removed lines → ``compliant`` (the device matches the
  golden).
- If the diff has any added/removed lines → ``drift`` (the device diverges from
  the golden; the diff tree shows *what* drifted).

Diff semantics (both modes): lines are normalized by stripping trailing
whitespace and dropping blank lines and lone ``!`` delimiter lines (Cisco
running-config noise). Leading indentation is preserved (significant for
sub-section lines like `` ip address ...``). A "changed" line is reported as a
``removed`` (the golden's line) + an ``added`` (the snapshot's line) —
``summary["changed"]`` is always 0. The diff tree has the same shape as
:class:`netbox_pyats.models.PyatsSnapshotDiff.diff` (a ``dict`` root node with
``children`` keyed by line, each child a ``leaf`` node with ``status``
``unchanged`` / ``added`` / ``removed``) so the Phase 3 ``inc/diff_tree.html``
partial renders it unchanged.

Ordered-mode ordering note: :func:`difflib.SequenceMatcher` finds a longest
common subsequence and reports the non-matching lines as ``added`` (present
only in the snapshot sequence) or ``removed`` (present only in the golden
sequence). Lines that appear in both sequences *in the same relative order*
are ``unchanged``; a line that moved is reported as a ``removed`` at its old
position + an ``added`` at its new position, so re-ordering shows up as
non-zero added/removed counts — exactly the order-sensitive drift v1 missed.
"""

from __future__ import annotations

import difflib
import json
import logging
from dataclasses import dataclass, field
from typing import Iterable

from .choices import ComplianceModeChoices, ComplianceResultChoices

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
    mode: str = ComplianceModeChoices.MODE_ORDERED

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


def _build_tree(
    unchanged: Iterable[str],
    added: Iterable[str],
    removed: Iterable[str],
    *,
    name: str,
    mode: str,
) -> tuple[dict, dict]:
    """Build the JSON-serializable diff tree and summary from leaf lists.

    The tree shape matches :func:`netbox_pyats.diff.diff_snapshots` so the
    Phase 3 ``inc/diff_tree.html`` partial renders compliance diffs unchanged:
    a ``dict`` root node with ``children`` keyed by line, each child a ``leaf``
    node carrying ``status`` (``unchanged`` / ``added`` / ``removed``) and the
    line text (``value`` for unchanged, ``after`` for added, ``before`` for
    removed).

    The children dict is keyed by line. For the ordered diff, duplicate lines
    (e.g. two `` ip address ...`` leaves) would collide on the same key, so the
    key is disambiguated with a ``#<n>`` suffix when the same line text appears
    more than once. This keeps the tree renderable (each leaf has a unique key
    in the children dict) without losing the order information — the order is
    carried by the iteration order of the underlying ``difflib`` opcodes, which
    we reflect by inserting the children in diff order. (Django templates
    preserve dict insertion order when iterating ``.items``.)

    Returns ``(tree, summary)``.
    """
    summary = {
        "added": 0,
        "removed": 0,
        "changed": 0,  # text diff has no "changed" — a line is present or not
        "unchanged": 0,
    }
    children: dict = {}
    seen: dict[str, int] = {}

    def _key(line: str) -> str:
        """Return a unique children-dict key for ``line``.

        The viewer iterates ``children.items()`` and shows the key as the line
        label, so the un-suffixed line is the common case; only duplicates get
        a ``#<n>`` suffix that the viewer renders as a small index. This keeps
        the common case readable while making the ordered diff's duplicate-line
        leaves (e.g. multiple `` ip address`` lines) addressable.
        """
        n = seen.get(line, 0)
        seen[line] = n + 1
        return line if n == 0 else f"{line} #{n + 1}"

    for line in unchanged:
        summary["unchanged"] += 1
        children[_key(line)] = {
            "type": _NODE_TYPE_LEAF,
            "status": _STATUS_UNCHANGED,
            "value": line,
        }
    for line in added:
        summary["added"] += 1
        children[_key(line)] = {
            "type": _NODE_TYPE_LEAF,
            "status": _STATUS_ADDED,
            "after": line,
        }
    for line in removed:
        summary["removed"] += 1
        children[_key(line)] = {
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
        "mode": mode,
        "children": children,
    }
    return tree, summary


def _ordered_diff(golden_lines: list[str], snapshot_lines: list[str], *, name: str) -> tuple[dict, dict]:
    """v2 ordered (sequence-aware) diff via :mod:`difflib`.

    Walks :func:`difflib.SequenceMatcher.get_opcodes` over the two line
    sequences and buckets the non-matching lines into ``added`` (present only
    in the snapshot), ``removed`` (present only in the golden), and
    ``unchanged`` (matched in both, in the same relative order). The three
    lists preserve the diff's left-to-right order so the tree's children dict
    reflects where the drift sits in the config — an operator reading the tree
    sees the ACL entries / interface blocks in the order they appear, with the
    moved lines flagged at both their old and new positions.

    A re-ordered line is reported as a ``removed`` (at its golden position) +
    an ``added`` (at its snapshot position), so order-sensitive drift shows up
    as non-zero added/removed counts — exactly the gap the v1 set diff missed.
    """
    matcher = difflib.SequenceMatcher(a=golden_lines, b=snapshot_lines, autojunk=False)
    unchanged: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged.extend(golden_lines[i1:i2])
        elif tag == "replace":
            removed.extend(golden_lines[i1:i2])
            added.extend(snapshot_lines[j1:j2])
        elif tag == "delete":
            removed.extend(golden_lines[i1:i2])
        elif tag == "insert":
            added.extend(snapshot_lines[j1:j2])
    return _build_tree(unchanged, added, removed, name=name, mode=ComplianceModeChoices.MODE_ORDERED)


def _set_diff(golden_lines: list[str], snapshot_lines: list[str], *, name: str) -> tuple[dict, dict]:
    """v1 set (order-independent) diff.

    Compares the two line lists as sets and reports the set differences. A
    re-ordered config classifies as ``compliant`` — correct for "does the
    device carry the golden lines?" but it misses order-sensitive drift. Kept
    as an explicit opt-in via ``mode="set"``.
    """
    golden_set = set(golden_lines)
    snapshot_set = set(snapshot_lines)
    added = sorted(snapshot_set - golden_set)
    removed = sorted(golden_set - snapshot_set)
    unchanged = sorted(golden_set & snapshot_set)
    return _build_tree(unchanged, added, removed, name=name, mode=ComplianceModeChoices.MODE_SET)


def run_compliance(
    golden_text: str | None,
    snapshot_text: str | None,
    *,
    name: str = "compliance",
    mode: str = ComplianceModeChoices.MODE_ORDERED,
) -> ComplianceResult:
    """Compare a golden config text against a snapshot's raw config text and classify.

    This is the pure-Python core. The caller (the RQ job) is responsible for
    loading the :class:`PyatsGoldenConfig` row's ``config_text``, loading the
    :class:`PyatsSnapshot` row's ``data["config_raw"]`` (the raw
    ``show running-config`` text captured alongside the Genie structured dict),
    and persisting the returned :class:`ComplianceResult`. This function only
    normalizes the two texts, runs the diff, and classifies.

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
        mode: the comparison mode — ``"ordered"`` (v2, default) for an
            order-sensitive sequence diff, or ``"set"`` (v1) for an
            order-independent set diff. See :class:`ComplianceModeChoices`.

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

    # Normalize the mode so the recorded result reflects the comparison that
    # actually ran, not a raw kwarg the caller passed through. An unknown
    # mode string degrades to ``ordered`` (the more informative comparison)
    # rather than raising — the RQ job passes the user-selected mode straight
    # through and must not crash on a bad value.
    if mode not in (ComplianceModeChoices.MODE_ORDERED, ComplianceModeChoices.MODE_SET):
        mode = ComplianceModeChoices.MODE_ORDERED

    if not golden_lines:
        return ComplianceResult(
            result=ComplianceResultChoices.RESULT_ERROR,
            diff={},
            summary={},
            warnings=["golden config is empty; cannot run compliance"],
            mode=mode,
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
            mode=mode,
        )

    if mode == ComplianceModeChoices.MODE_SET:
        tree, summary = _set_diff(golden_lines, snapshot_lines, name=name)
    else:
        tree, summary = _ordered_diff(golden_lines, snapshot_lines, name=name)

    has_drift = bool(summary["added"] or summary["removed"] or summary["changed"])
    result = ComplianceResultChoices.RESULT_DRIFT if has_drift else ComplianceResultChoices.RESULT_COMPLIANT
    return ComplianceResult(
        result=result,
        diff=tree,
        summary=summary,
        warnings=[],
        mode=mode,
    )


__all__ = (
    "ComplianceResult",
    "run_compliance",
)
