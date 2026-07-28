"""QA-independent verification for the ATW-252 diff picker kind filter.

Written by QA (ATW-294) to cover behavior NOT already exercised by the
author-supplied ``test_diff_form.py``:

- ``template_content._group_snapshots_by_kind``: ordering follows
  ``SnapshotKindChoices.choices``; kinds with no snapshots are omitted;
  snapshots are partitioned by their ``kind`` attribute only.
- The device-panel template renders one ``<optgroup>`` per present kind and
  includes the "diff two of the same kind" helper text.

Pure-Python where possible (the grouping helper has no NetBox dependency);
the template-render assertion is NetBox-gated because it needs the Django
template engine + plugin URL config.
"""

import pytest

from netbox_pyats.choices import SnapshotKindChoices
from netbox_pyats.template_content import _group_snapshots_by_kind


class FakeSnapshot:
    """Minimal stand-in: only ``kind`` and ``pk`` are read by the helper."""

    def __init__(self, kind, pk):
        self.kind = kind
        self.pk = pk


class TestGroupSnapshotsByKind:
    def test_empty_input_returns_empty_list(self):
        assert _group_snapshots_by_kind([]) == []

    def test_single_kind_returns_single_group(self):
        snaps = [FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 1), FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 2)]
        grouped = _group_snapshots_by_kind(snaps)
        assert len(grouped) == 1
        kind_value, kind_label, group_snaps = grouped[0]
        assert kind_value == SnapshotKindChoices.KIND_PARSE
        assert kind_label == "Parse (on-demand commands)"
        assert [s.pk for s in group_snaps] == [1, 2]

    def test_kinds_with_no_snapshots_are_omitted(self):
        # Only parse + state present; config and full must NOT appear as empty
        # optgroups (the template would render an empty <optgroup> otherwise).
        snaps = [FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 1), FakeSnapshot(SnapshotKindChoices.KIND_STATE, 2)]
        grouped = _group_snapshots_by_kind(snaps)
        present_values = [g[0] for g in grouped]
        assert present_values == [
            SnapshotKindChoices.KIND_CONFIG,
            SnapshotKindChoices.KIND_STATE,
        ] or present_values == [
            SnapshotKindChoices.KIND_STATE,
            SnapshotKindChoices.KIND_PARSE,
        ]
        # The key invariant: no empty groups.
        for _value, _label, group_snaps in grouped:
            assert len(group_snaps) > 0

    def test_ordering_follows_choices_definition(self):
        # All four kinds present -> order must match SnapshotKindChoices.choices
        # (config, state, full, parse) so the picker grouping is stable.
        snaps = [
            FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 4),
            FakeSnapshot(SnapshotKindChoices.KIND_FULL, 3),
            FakeSnapshot(SnapshotKindChoices.KIND_STATE, 2),
            FakeSnapshot(SnapshotKindChoices.KIND_CONFIG, 1),
        ]
        grouped = _group_snapshots_by_kind(snaps)
        assert [g[0] for g in grouped] == [c[0] for c in SnapshotKindChoices.choices]

    def test_snapshots_partitioned_exclusively_by_kind(self):
        # A snapshot must appear in exactly one group (no duplication, no
        # cross-kind leakage) — this is what makes the <optgroup> grouping a
        # correct visual hint for the form-level kind filter.
        snaps = [
            FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 1),
            FakeSnapshot(SnapshotKindChoices.KIND_STATE, 2),
            FakeSnapshot(SnapshotKindChoices.KIND_PARSE, 3),
            FakeSnapshot(SnapshotKindChoices.KIND_FULL, 4),
        ]
        grouped = _group_snapshots_by_kind(snaps)
        all_pks = []
        for _value, _label, group_snaps in grouped:
            all_pks.extend(s.pk for s in group_snaps)
        assert sorted(all_pks) == [1, 2, 3, 4]
        # Each pk appears exactly once.
        assert len(all_pks) == len(set(all_pks))


# --- NetBox-gated template render check ------------------------------------- #

pytest.importorskip("netbox")

from django.template.loader import render_to_string  # noqa: E402


class TestDevicePanelTemplateOptgroup:
    """Render the device-panel diff-picker partial and assert the ATW-252
    contract: one <optgroup> per present kind, helper text mentions same-kind.
    """

    def test_template_renders_optgroup_per_kind_and_helper_text(self):
        kind_a = SnapshotKindChoices.KIND_PARSE
        kind_b = SnapshotKindChoices.KIND_STATE
        # Build fake snapshot objects with just the attributes the template
        # reads: pk, captured_at, kind (via get_kind_display). captured_at is
        # only used inside a date filter, so a None is fine (renders empty).

        class Snap:
            def __init__(self, pk, kind):
                self.pk = pk
                self.kind = kind

            def get_kind_display(self):
                return dict(SnapshotKindChoices.choices).get(self.kind, self.kind)

        snaps = [Snap(1, kind_a), Snap(2, kind_a), Snap(3, kind_b)]
        diff_snapshots_by_kind = _group_snapshots_by_kind(snaps)
        html = render_to_string(
            "netbox_pyats/inc/device_panel.html",
            {
                "snapshots": snaps,
                "diff_snapshots_by_kind": diff_snapshots_by_kind,
                "diffs": [],
                "golden_configs": [],
                "compliance_runs": [],
                "config_snapshots": [],
                "snapshot_kinds": SnapshotKindChoices.choices,
                "platform_supported": True,
                "pyats_os": "iosxe",
                "capture_url": "/capture/",
                "diff_url": "/diff/",
                "compliance_url": "/compliance/",
                "snapshot_list_url": "/snapshots/",
                "device": None,
            },
        )
        # One <optgroup> per present kind, per <select> (before + after = 2
        # selects x 2 kinds = 4 optgroups total).
        assert html.count("<optgroup") == 4
        # Both kind labels appear as optgroup labels.
        assert "Parse (on-demand commands)" in html
        assert "State" in html
        # Helper text calls out the same-kind rule.
        assert "diff two of the same kind" in html
        # Each snapshot pk appears as an option value.
        assert 'value="1"' in html
        assert 'value="2"' in html
        assert 'value="3"' in html
