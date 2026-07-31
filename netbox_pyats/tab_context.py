"""Pure-Python helpers for the device-page PyATS tab (ATW-393, ADR-0007).

This module carries no NetBox or Django model imports so it can be imported
in the unit test lane without NetBox installed. The tab view
(:class:`netbox_pyats.views.DevicePyATSTabView`) calls
:func:`group_snapshots_by_kind` from its ``get_extra_context``; the unit tests
import it directly to verify the ATW-252 kind-grouping contract.
"""

from __future__ import annotations

from .choices import SnapshotKindChoices


def group_snapshots_by_kind(snapshots):
    """Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).

    Returns an ordered list of ``(kind_value, kind_label, [snapshots])`` tuples
    so the template can render one ``<optgroup>`` per kind. The order follows
    ``SnapshotKindChoices.choices`` (the single source of truth for kind order);
    kinds with no snapshots are omitted. Keeping the grouping server-side
    avoids any JS in the picker (ADR-0001 §4).
    """
    by_kind = {}
    for snap in snapshots:
        by_kind.setdefault(snap.kind, []).append(snap)
    return [(value, label, by_kind[value]) for value, label in SnapshotKindChoices.choices if value in by_kind]
